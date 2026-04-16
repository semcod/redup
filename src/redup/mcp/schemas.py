from typing import Any

SCAN_PROPERTIES = {
    "path": {"type": "string", "description": "Path to the project directory"},
    "format": {"type": "string", "enum": ["json", "yaml", "toon", "markdown", "enhanced", "code2llm", "all"], "default": "json", "description": "Output format"},
    "mode": {"type": "string", "enum": ["standard", "optimized", "parallel"], "default": "standard", "description": "Analysis mode"},
    "extensions": {"type": "string", "description": "Comma-separated file extensions"},
    "min_lines": {"type": "integer", "default": 3, "description": "Minimum block size in lines"},
    "min_similarity": {"type": "number", "default": 0.85, "description": "Minimum similarity score"},
    "include_tests": {"type": "boolean", "default": False, "description": "Include test files"},
    "functions_only": {"type": "boolean", "default": True, "description": "Only analyze function-level blocks"},
    "parallel": {"type": "boolean", "default": False, "description": "Use parallel scanning for large projects"},
    "memory_cache": {"type": "boolean", "default": True, "description": "Use memory cache for faster scanning"},
    "incremental": {"type": "boolean", "default": False, "description": "Use incremental scanning with caching"},
    "max_workers": {"type": "integer", "description": "Maximum number of parallel workers"},
    "max_cache_mb": {"type": "integer", "default": 512, "description": "Maximum memory cache size in MB"},
    "fuzzy": {"type": "boolean", "default": False, "description": "Enable fuzzy similarity detection"},
    "fuzzy_threshold": {"type": "number", "default": 0.8, "description": "Fuzzy similarity threshold"},
    "include_snippets": {"type": "boolean", "default": False, "description": "Include code snippets in JSON output"},
}

def _make_check_properties() -> dict[str, Any]:
    """Build check_project properties with threshold options."""
    return {
        **SCAN_PROPERTIES,
        "max_groups": {"type": "integer", "default": 10, "description": "Maximum allowed duplicate groups"},
        "max_saved_lines": {"type": "integer", "default": 100, "description": "Maximum allowed recoverable lines"},
        "max_lines": {"type": "integer", "description": "Compatibility alias for max_saved_lines"},
    }


COMPARE_PROPERTIES = {
    "before": {"type": "string", "description": "Path to the earlier scan file"},
    "after": {"type": "string", "description": "Path to the later scan file"},
}

TOOL_SCHEMA_REDUP = {
    "analyze_project": {
        "name": "analyze_project",
        "description": "Analyze a project and generate duplication findings",
        "inputSchema": {"type": "object", "properties": SCAN_PROPERTIES, "required": ["path"]},
    },
    "find_duplicates": {
        "name": "find_duplicates",
        "description": "Find duplicate code blocks in a project",
        "inputSchema": {"type": "object", "properties": SCAN_PROPERTIES, "required": ["path"]},
    },
    "compare_scans": {
        "name": "compare_scans",
        "description": "Compare two saved reDUP scan outputs",
        "inputSchema": {"type": "object", "properties": COMPARE_PROPERTIES, "required": ["before", "after"]},
    },
    "compare_projects": {
        "name": "compare_projects",
        "description": "Compare two saved reDUP scan outputs",
        "inputSchema": {"type": "object", "properties": COMPARE_PROPERTIES, "required": ["before", "after"]},
    },
    "check_project": {
        "name": "check_project",
        "description": "Analyze a project and evaluate duplication quality gates",
        "inputSchema": {"type": "object", "properties": _make_check_properties(), "required": ["path"]},
    },
    "suggest_refactoring": {
        "name": "suggest_refactoring",
        "description": "Analyze a project and return prioritized refactoring suggestions",
        "inputSchema": {"type": "object", "properties": SCAN_PROPERTIES, "required": ["path"]},
    },
    "project_info": {
        "name": "project_info",
        "description": "Show reDUP version and environment information",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "info": {
        "name": "info",
        "description": "Show reDUP version and environment information",
        "inputSchema": {"type": "object", "properties": {}},
    },
}