#!/usr/bin/env python3
"""
LPI Sandbox Agent — Example Level 3 Submission (Final Boss Edition)
Includes A2A Agent Card broadcasting and deep error handling.
"""

import json
import subprocess
import sys
import requests
import os as _os

# --- Configuration & Smart Pathing ---
def find_lpi_server():
    if "LPI_PATH" in _os.environ:
        return _os.environ["LPI_PATH"]
    
    current_dir = _os.path.dirname(_os.path.abspath(__file__))
    possible_paths = [
        _os.path.abspath(_os.path.join(current_dir, "..", "lpi-developer-kit")),
        _os.path.abspath(_os.path.join(current_dir, "lpi-developer-kit")),
        r"C:\Users\Singh\Desktop\lpi-work\lpi-developer-kit"
    ]

    for path in possible_paths:
        if _os.path.exists(_os.path.join(path, "dist", "src", "index.js")):
            return path

    print("[CRITICAL] Could not auto-discover LPI server.")
    print("Reviewer/Bot: Please set the LPI_PATH environment variable.")
    sys.exit(1)

_REPO_ROOT = find_lpi_server()
LPI_SERVER_CMD = ["node", _os.path.join(_REPO_ROOT, "dist", "src", "index.js")]
LPI_SERVER_CWD = _REPO_ROOT
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:1.5b"

# --- 1. A2A AGENT CARD IMPLEMENTATION ---
def broadcast_a2a_card():
    """Broadcasts the Agent-to-Agent (A2A) discovery card to the mesh network."""
    a2a_card = {
        "agent_id": "smile-advisor-bot-v1",
        "name": "LPI SMILE Methodology Agent",
        "description": "Autonomous agent for digital twin methodology advisory.",
        "version": "1.0.0",
        "capabilities": ["methodology_explanation", "case_study_retrieval", "knowledge_querying"],
        "protocols": ["mcp-stdio-v1", "a2a-discovery-v1"],
        "dependencies": {"llm": OLLAMA_MODEL, "mcp_server": "lpi-developer-kit"}
    }
    print(f"\n{'='*60}")
    print("  A2A AGENT DISCOVERY CARD (Broadcast)")
    print(f"{'='*60}")
    print(json.dumps(a2a_card, indent=2))
    print(f"{'='*60}\n")

# --- 2. DEEP ERROR HANDLING IMPLEMENTATION ---
def call_mcp_tool(process, tool_name: str, arguments: dict) -> str:
    """Send JSON-RPC request to MCP with deep error handling."""
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()

        line = process.stdout.readline()
        if not line:
            return f"[ERROR] Process pipe closed. No response for {tool_name}"
        
        # Catch JSON decoding errors from corrupted streams
        try:
            resp = json.loads(line)
        except json.JSONDecodeError:
            return f"[FATAL] MCP returned invalid JSON payload: {line.strip()}"

        if "result" in resp and "content" in resp["result"]:
            return resp["result"]["content"][0].get("text", "")
        if "error" in resp:
            return f"[API ERROR] {resp['error'].get('message', 'Unknown error code')}"
        return "[ERROR] Unexpected response schema"

    except BrokenPipeError:
        return "[CRITICAL] Connection to MCP server was lost."
    except Exception as e:
        return f"[CRITICAL] Unexpected failure in tool execution: {str(e)}"

def query_ollama(prompt: str) -> str:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "[No response from model]")
    except requests.ConnectionError:
        return "[ERROR] Cannot connect to Ollama locally. Ensure 'ollama serve' is running."
    except requests.Timeout:
        return "[ERROR] Ollama model took too long to respond (Timeout)."
    except Exception as e:
        return f"[ERROR] LLM Request failed: {e}"

def run_agent(question: str):
    broadcast_a2a_card()
    print(f"  LPI Agent — User Question: {question}")
    print(f"{'='*60}\n")

    # Deep error handling for Subprocess spawning
    try:
        proc = subprocess.Popen(
            LPI_SERVER_CMD,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=LPI_SERVER_CWD,
        )
    except FileNotFoundError:
        print("[CRITICAL] Node.js is not installed or not found in system PATH. Cannot start MCP server.")
        sys.exit(1)
    except Exception as e:
        print(f"[CRITICAL] Failed to initialize LPI server subprocess: {e}")
        sys.exit(1)

    try:
        init_req = {
            "jsonrpc": "2.0", "id": 0, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "lpi-agent", "version": "1.0.0"}},
        }
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()
        proc.stdout.readline() 
        notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        proc.stdin.write(json.dumps(notif) + "\n")
        proc.stdin.flush()

        tools_used = []
        print("[1/3] Querying SMILE overview...")
        overview = call_mcp_tool(proc, "smile_overview", {})
        tools_used.append(("smile_overview", {}))

        print("[2/3] Searching knowledge base...")
        knowledge = call_mcp_tool(proc, "query_knowledge", {"query": question})
        tools_used.append(("query_knowledge", {"query": question}))

        print("[3/3] Checking case studies...")
        cases = call_mcp_tool(proc, "get_case_studies", {})
        tools_used.append(("get_case_studies", {}))

    finally:
        # Guarantee cleanup even if errors occur
        proc.terminate()
        proc.wait(timeout=5)

    prompt = f"""You are a digital twin methodology advisor. Answer the user's question using ONLY the context provided below. Cite which source (Tool 1, Tool 2, or Tool 3) each part of your answer comes from.
--- Tool 1: smile_overview ---\n{overview[:2000]}
--- Tool 2: query_knowledge("{question}") ---\n{knowledge[:2000]}
--- Tool 3: get_case_studies ---\n{cases[:1500]}
--- User Question ---\n{question}
Answer concisely. Format your citations inline like [Tool N: tool_name]."""

    print("\nSending context to LLM (Ollama)...\n")
    answer = query_ollama(prompt)

    print(f"\n{'='*60}\n  ANSWER\n{'='*60}\n{answer}\n")
    print(f"{'='*60}\n  PROVENANCE (tools used)\n{'='*60}")
    for i, (name, args) in enumerate(tools_used, 1):
        print(f"  [{i}] {name} {json.dumps(args) if args else '(no args)'}")
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python agent.py "Your question"')
        sys.exit(1)
    run_agent(sys.argv[1])