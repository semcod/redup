"""MCP server entry point - backward compatibility wrapper.

This module re-exports all MCP functionality from the redup.mcp package.
New code should import directly from redup.mcp.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Re-export all public APIs from the mcp package
from redup.mcp import (
    SCAN_PROPERTIES,
    TOOL_HANDLERS,
    TOOL_SCHEMA_REDUP,
    handle_analyze_project,
    handle_check_project,
    handle_compare_scans,
    handle_initialize,
    handle_project_info,
    handle_request,
    handle_suggest_refactoring,
    handle_tools_call,
    handle_tools_list,
    json_safe,
    parse_extensions,
    resolve_path,
    run_server,
)

# Backward compatibility aliases
_json_safe = json_safe
_resolve_path = resolve_path
_parse_extensions = parse_extensions
_handle_analyze_project = handle_analyze_project
_handle_suggest_refactoring = handle_suggest_refactoring
_handle_compare_scans = handle_compare_scans
_handle_check_project = handle_check_project
_handle_project_info = handle_project_info
handle_tools_list = handle_tools_list
handle_tools_call = handle_tools_call
handle_request = handle_request
handle_initialize = handle_initialize
run_server = run_server

# Backward compatibility: rebuild TOOL_SCHEMA_REDUP in legacy format
import json
from typing import Any

def _build_legacy_tool_schema() -> dict[str, Any]:
    """Build legacy tool schema format for backward compatibility."""
    legacy = {}
    for key, schema in TOOL_SCHEMA_REDUP.items():
        legacy[key] = {
            "name": schema["name"],
            "description": schema["description"],
            "inputSchema": schema["inputSchema"],
        }
    return legacy


TOOL_SCHEMA_REDUP = _build_legacy_tool_schema()
TOOL_SCHEMA_REDUP_HANDLERS = TOOL_HANDLERS
MCP_HANDLERS = TOOL_HANDLERS

__all__ = [
    "SCAN_PROPERTIES",
    "TOOL_SCHEMA_REDUP",
    "TOOL_HANDLERS",
    "MCP_HANDLERS",
    "handle_initialize",
    "handle_tools_list",
    "handle_tools_call",
    "handle_request",
    "run_server",
]

if __name__ == "__main__":
    run_server()
