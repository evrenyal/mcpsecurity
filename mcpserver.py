import sqlite3
import subprocess
import shlex
import re
import requests
import psutil
import getpass
import time
from datetime import timedelta
import os

from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
from fastapi_jsonrpc import API, Entrypoint

# --- Config ---
OLLAMA_API_URL = "http://ollama7x:11434/api/generate"
DB_PATH = "database.db"
START_TIME = time.time()
port = int(os.environ.get("MCP_PORT", 3333))

# --- FastMCP instance ---
mcp = FastMCP("MCP Server")

# --- JSON-RPC setup ---
rpc = Entrypoint("/")
jsonrpc_api = API()
jsonrpc_api.bind_entrypoint(rpc)

# --- FastAPI app ---
app = FastAPI()
app.mount("/jsonrpc", jsonrpc_api)                        

# --- DB Init ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL
        )
        """)
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO users (name, age) VALUES (?, ?)", [
                ("admin", 30), ("user", 25), ("guest", 20)
            ])
        conn.commit()

# --- Helpers ---
def get_sqlite_tables():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cursor.fetchall()]

def ask_ollama(prompt: str, model: str = "[MODEL]") -> str:
    try:
        payload = {
            "model": model,
            "prompt": (
                "You are an AI assistant that decides how to execute a command. "
                "If the input is an SQL query, return it inside ```sql ... ```. "
                "If it's a terminal command, return it inside ```bash ... ```. "
                f"Task: {prompt}"
            ),
            "stream": False
        }
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"❌ Ollama error: {e}"

# --- MCP TOOL ---
@mcp.tool()
@rpc.method()
def mcp_info() -> dict:
    uptime = str(timedelta(seconds=int(time.time() - START_TIME)))
    mem = psutil.virtual_memory().available / (1024 * 1024)
    return {
        "system": "Hybrid FastMCP Server",
        "version": "1.0.0",
        "uptime": uptime,
        "available_memory_mb": f"{mem:.2f}",
        "current_user": getpass.getuser(),
        "database": DB_PATH,
        "sqlite_tables": get_sqlite_tables(),
        "ollama_model": "[MODEL]",
        "available_methods": [
            "mcp_info", "mcp_sql_tool", "mcp_cli_tool", "mcp_tool_router"
        ]
    }

@mcp.tool()
@rpc.method()
def mcp_sql_tool(query: str) -> str:
    if not query.strip():
        return "⚠️ Empty SQL query."
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            return "\n".join(str(row) for row in results) if results else "✅ No results."
    except Exception as e:
        return f"⚠️ SQL error: {e}"

@mcp.tool()
@rpc.method()
def mcp_cli_tool(command: str) -> str:
    if not command.strip():
        return "⚠️ Empty CLI command."
    try:
        result = subprocess.run(shlex.split(command), capture_output=True, text=True, check=True)
        return result.stdout.strip() or "✅ Command executed with no output."
    except subprocess.CalledProcessError as e:
        return f"⚠️ CLI error: {e.stderr.strip()}"

@mcp.tool()
@rpc.method()
def mcp_tool_router(query: str) -> str:
    if not query.strip():
        return "⚠️ Empty input."
    decision = ask_ollama(query)
    sql = re.search(r"```sql\n(.*?)```", decision, re.DOTALL)
    bash = re.search(r"```bash\n(.*?)```", decision, re.DOTALL)
    if sql:
        return mcp_sql_tool(sql.group(1).strip())
    elif bash:
        return mcp_cli_tool(bash.group(1).strip())
    return f"⚠️ Unrecognized response:\n{decision}"

# --- Entry Point ---
if __name__ == "__main__":
    import uvicorn
    init_db()

    uvicorn.run(app, host="0.0.0.0", port=port)
