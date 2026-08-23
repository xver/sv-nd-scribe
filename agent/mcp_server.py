# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

"""
Model Context Protocol (MCP) stdio server for SV ND Scribe Agent.
Exposes linter, dry-run checking, batch fixing, and agent status as MCP tools.
"""

import sys
import json
import io
import contextlib
from typing import Dict, Any
from agent.agent import ScribeAgent
from agent.fixer.base_fixer import LinterError

# Singleton agent instance (avoids re-parsing 40 YAML rules per request)
_agent_instance = None

def _get_agent() -> ScribeAgent:
    """Return the cached singleton ScribeAgent, creating it on first call."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ScribeAgent()
    return _agent_instance


TOOL_DEFINITIONS = [
    {
        "name": "list_violations",
        "description": "Run the SystemVerilog NaturalDocs linter on target files and return JSON violations list.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Paths to SystemVerilog (.sv/.svh) source files"
                }
            },
            "required": ["files"]
        }
    },
    {
        "name": "check_file",
        "description": "Run dry-run proposal generation for NaturalDocs violations without writing changes to disk.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Paths to SystemVerilog source files"
                },
                "rules": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of rule IDs to filter by (e.g. ['ND-001', 'ND-009'])"
                },
                "llm_provider": {
                    "type": "string",
                    "description": "LLM provider backend ('none', 'openai', 'ollama')",
                    "default": "none"
                }
            },
            "required": ["files"]
        }
    },
    {
        "name": "fix_file",
        "description": "Automatically apply safe NaturalDocs fixes to target SystemVerilog files in batch mode.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Paths to SystemVerilog source files"
                },
                "rules": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of rule IDs to filter by"
                },
                "llm_provider": {
                    "type": "string",
                    "description": "LLM provider backend ('none', 'openai', 'ollama')",
                    "default": "none"
                },
                "no_backup": {
                    "type": "boolean",
                    "description": "Disable creation of .bak backup files",
                    "default": False
                }
            },
            "required": ["files"]
        }
    },
    {
        "name": "get_status",
        "description": "Get current status and connectivity of the SV ND Scribe AI Agent environment.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "llm_provider": {
                    "type": "string",
                    "description": "LLM provider backend to check ('none', 'openai', 'ollama')",
                    "default": "none"
                }
            }
        }
    }
]


def handle_request(req: Dict[str, Any]) -> Dict[str, Any]:
    method = req.get("method", "")
    params = req.get("params", {})
    rid = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": rid,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "sv-nd-scribe-agent",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "notifications/initialized":
        return None

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": rid,
            "result": {"tools": TOOL_DEFINITIONS}
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        agent = _get_agent()

        try:
            if tool_name == "list_violations":
                files = args.get("files", [])
                res = agent.run_linter(files)
                return {
                    "jsonrpc": "2.0",
                    "id": rid,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(res, indent=2)}]
                    }
                }

            elif tool_name == "check_file":
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    agent.run(
                        files=args.get("files", []),
                        mode="batch",
                        rules_filter=args.get("rules"),
                        llm_provider=args.get("llm_provider", "none"),
                        dry_run=True,
                        json_output=False
                    )
                return {
                    "jsonrpc": "2.0",
                    "id": rid,
                    "result": {
                        "content": [{"type": "text", "text": buf.getvalue()}]
                    }
                }

            elif tool_name == "fix_file":
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    exit_code = agent.run(
                        files=args.get("files", []),
                        mode="batch",
                        rules_filter=args.get("rules"),
                        llm_provider=args.get("llm_provider", "none"),
                        no_backup=args.get("no_backup", False),
                        dry_run=False,
                        json_output=False
                    )
                return {
                    "jsonrpc": "2.0",
                    "id": rid,
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": f"Fix status: {'SUCCESS' if exit_code == 0 else 'FAILURE'}\n\n{buf.getvalue()}"
                        }]
                    }
                }

            elif tool_name == "get_status":
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    agent.print_status(llm_provider=args.get("llm_provider", "none"))
                return {
                    "jsonrpc": "2.0",
                    "id": rid,
                    "result": {
                        "content": [{"type": "text", "text": buf.getvalue()}]
                    }
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": rid,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                }
        except LinterError as e:
            return {
                "jsonrpc": "2.0",
                "id": rid,
                "error": {"code": -32603, "message": f"Linter error: {e}"}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": rid,
                "error": {"code": -32603, "message": str(e)}
            }

    else:
        if rid is not None:
            return {
                "jsonrpc": "2.0",
                "id": rid,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
        return None


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_request(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            pass

if __name__ == "__main__":
    main()
