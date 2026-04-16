"""MCP server package for reDUP."""

from .handlers import (
    TOOL_HANDLERS,
    handle_analyze_project,
    handle_check_project,
    handle_compare_scans,
    handle_project_info,
    handle_suggest_refactoring,
)
from .schemas import SCAN_PROPERTIES, TOOL_SCHEMA_REDUP
from .server import handle_initialize, handle_request, handle_tools_call, handle_tools_list, run_server
from .utils import json_safe, parse_extensions, resolve_path

__all__ = [
    # Schemas
    "TOOL_SCHEMA_REDUP",
    "SCAN_PROPERTIES",
    # Utils
    "json_safe",
    "resolve_path",
    "parse_extensions",
    # Handlers
    "TOOL_HANDLERS",
    "handle_analyze_project",
    "handle_suggest_refactoring",
    "handle_compare_scans",
    "handle_check_project",
    "handle_project_info",
    # Server
    "handle_initialize",
    "handle_tools_list",
    "handle_tools_call",
    "handle_request",
    "run_server",
]