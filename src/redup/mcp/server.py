"""MCP JSON-RPC server core."""

from __future__ import annotations

import json
import sys
from typing import Any

from redup import __version__
from redup.mcp.handlers import TOOL_HANDLERS
from redup.mcp.schemas import TOOL_SCHEMA_REDUP

_PROTOCOL_VERSION = "2024-11-05"
_NOTIFICATIONS = frozenset({"notifications/initialized", "notifications/cancelled"})


def handle_initialize(request_id: Any, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Handle MCP initialize request."""
    client_version = (params or {}).get("protocolVersion", _PROTOCOL_VERSION)
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": client_version,
            "serverInfo": {
                "name": "redup",
                "version": __version__,
            },
            "capabilities": {
                "tools": {},
            },
        },
    }


def handle_tools_list(request_id: Any) -> dict[str, Any]:
    """Handle MCP tools/list request."""
    tools = [
        {
            "name": tool_schema["name"],
            "description": tool_schema["description"],
            "inputSchema": tool_schema["inputSchema"],
        }
        for tool_schema in TOOL_SCHEMA_REDUP.values()
    ]

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"tools": tools},
    }


def handle_tools_call(request_id: Any, params: dict[str, Any]) -> dict[str, Any]:
    """Handle MCP tools/call request."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {}) or {}

    if tool_name not in TOOL_HANDLERS:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Tool '{tool_name}' not found",
            },
        }

    try:
        result = TOOL_HANDLERS[tool_name](arguments)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"content": [{"type": "text", "text": result}]},
        }
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"Tool execution failed: {exc}",
            },
        }


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    """Route MCP request to appropriate handler."""
    method = request.get("method", "")
    params = request.get("params", {}) or {}
    request_id = request.get("id")

    if method in _NOTIFICATIONS:
        return {}
    if method == "initialize":
        return handle_initialize(request_id, params)
    if method == "tools/list":
        return handle_tools_list(request_id)
    if method == "tools/call":
        return handle_tools_call(request_id, params)

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32601,
            "message": f"Method '{method}' not found",
        },
    }


def run_server() -> None:
    """Run the MCP server (entry point)."""
    print("reDUP MCP Server started", file=sys.stderr)
    available_tools = ", ".join(sorted(TOOL_SCHEMA_REDUP.keys()))
    print(f"Available tools: {available_tools}", file=sys.stderr)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_request(request)
            if response:
                print(json.dumps(response), flush=True)
        except json.JSONDecodeError as exc:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {exc}",
                },
            }
            print(json.dumps(error_response), flush=True)
        except Exception as exc:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {exc}",
                },
            }
            print(json.dumps(error_response), flush=True)
