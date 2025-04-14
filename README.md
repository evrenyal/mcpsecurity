# Vulnerable MCP Server

This project is an intentionally vulnerable **MCP (Model Context Protocol)** app, designed for **security research**. 

> **DO NOT use in production environments.**  
> It executes raw SQL and system commands with no authentication or restrictions.

---

## ⚙️ MCP SERVER

A command execution server that combines:

- **FastAPI** for the HTTP interface  
- **SQLite** as a persistent database  
- **Ollama LLM** to interpret natural language queries  
- **JSON-RPC** as the main API protocol

This system routes natural language input to either SQL queries or shell commands, using a locally running LLM via Ollama.

> Built to test **SQL Injection (SQLi)** and **Remote Code Execution (RCE)** vulnerabilities  
> via **FastAPI**, **JSON-RPC**, and **LLM-based decision logic**.

---

## ⚙️ WARNING: Security Notice

This app is intentionally insecure:

- ❗ No authentication or access control
- ❗ Accepts and executes raw SQL queries and shell commands
- ❗ No input validation
- ❗ LLM responses are blindly executed

**Use only in isolated environments, CTFs, or research labs.**

---

## ⚙️ Features

- LLM-based decision logic for command routing (SQL or CLI)
- Native execution of SQL and terminal commands
- Auto-initializing SQLite database with sample data
- Simple, pluggable JSON-RPC methods
- Vulnerable by design — suitable for offensive/defensive testing

---
## ⚙️ Installation

```bash
git clone https://github.com/your-repo/mcp-vulnerable-app.git
cd mcp-vulnerable-app

docker-compose up --build
docker network connect mcplab ollama
docker network connect mcplab mcp_internal
docker network connect mcplab mcp_remote
