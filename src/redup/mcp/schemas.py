from typing import Any

from redup.core.models import DEFAULT_SEMANTIC_MODEL, DEFAULT_SEMANTIC_THRESHOLD

SCAN_PROPERTIES = {
    "path": {"type": "string", "description": "Path to the project directory"},
    "format": {
        "type": "string",
        "enum": ["json", "yaml", "toon", "markdown", "enhanced", "code2llm"],
        "default": "json",
        "description": "Output format; JSON supports result limits and is best for agents",
    },
    "mode": {
        "type": "string",
        "enum": ["standard", "optimized", "parallel"],
        "default": "optimized",
        "description": "Execution strategy; use mode=parallel for large projects",
    },
    "extensions": {
        "type": "string",
        "description": "Comma-separated file extensions; leading dots are optional (py,.js,ts)",
    },
    "min_lines": {"type": "integer", "default": 3, "description": "Minimum block size in lines"},
    "min_similarity": {
        "type": "number",
        "default": 0.85,
        "description": "Minimum similarity score",
    },
    "include_tests": {"type": "boolean", "default": False, "description": "Include test files"},
    "functions_only": {
        "type": "boolean",
        "default": True,
        "description": "Only analyze function-level blocks",
    },
    "memory_cache": {
        "type": "boolean",
        "default": True,
        "description": "Use memory cache for faster scanning",
    },
    "incremental": {
        "type": "boolean",
        "default": False,
        "description": "Use incremental scanning with caching",
    },
    "max_workers": {"type": "integer", "description": "Maximum number of parallel workers"},
    "max_cache_mb": {
        "type": "integer",
        "default": 512,
        "description": "Maximum memory cache size in MB",
    },
    "fuzzy": {
        "type": "boolean",
        "default": False,
        "description": "Enable fuzzy similarity detection",
    },
    "fuzzy_threshold": {
        "type": "number",
        "default": 0.8,
        "description": "Fuzzy similarity threshold",
    },
    "semantic": {
        "type": "boolean",
        "default": False,
        "description": (
            "Enable semantic candidates; without the optional model runtime, the explainable "
            "intent-profile fallback is used and findings are marked for review"
        ),
    },
    "semantic_threshold": {
        "type": "number",
        "default": DEFAULT_SEMANTIC_THRESHOLD,
        "description": "Minimum similarity for semantic duplicate groups",
    },
    "semantic_model": {
        "type": "string",
        "default": DEFAULT_SEMANTIC_MODEL,
        "description": "Sentence Transformers model used for semantic detection",
    },
    "include_snippets": {
        "type": "boolean",
        "default": False,
        "description": "Include code snippets in JSON output",
    },
    "detail": {
        "type": "string",
        "enum": ["compact", "full"],
        "default": "compact",
        "description": "Compact removes redundant hashes and verbose metadata from JSON groups",
    },
    "intent": {
        "type": "boolean",
        "default": False,
        "description": "Enable Intract intent duplicate detection",
    },
    "intent_threshold": {
        "type": "number",
        "default": 0.84,
        "description": "Minimum similarity for intent duplicate groups",
    },
    "intent_manifest": {
        "type": "string",
        "description": "Path to intract.yaml / intent.yaml for intent analysis",
    },
    "group_scope": {
        "type": "string",
        "enum": ["non_generated", "refactor", "review", "generated", "all"],
        "default": "non_generated",
        "description": "JSON result filter; non_generated keeps refactor and review findings",
    },
    "max_groups": {
        "type": "integer",
        "minimum": 0,
        "default": 20,
        "description": "Maximum JSON groups returned; use 0 for every matching group",
    },
    "refresh": {
        "type": "boolean",
        "default": False,
        "description": (
            "Ignore the in-process result cache even when files and options are unchanged"
        ),
    },
}


def _make_check_properties() -> dict[str, Any]:
    """Build check_project properties with threshold options."""
    return {
        **SCAN_PROPERTIES,
        "max_groups": {
            "type": "integer",
            "default": 10,
            "description": "Maximum allowed duplicate groups",
        },
        "max_saved_lines": {
            "type": "integer",
            "default": 100,
            "description": "Maximum allowed recoverable lines",
        },
        "max_lines": {"type": "integer", "description": "Compatibility alias for max_saved_lines"},
    }


def _make_find_properties() -> dict[str, Any]:
    """Build compact first-pass properties with the advertised ten-group default."""
    return {
        **SCAN_PROPERTIES,
        "max_groups": {
            "type": "integer",
            "minimum": 0,
            "default": 10,
            "description": "Maximum JSON groups returned; use 0 for every matching group",
        },
    }


COMPARE_PROPERTIES = {
    "before": {"type": "string", "description": "Path to the earlier scan file"},
    "after": {"type": "string", "description": "Path to the later scan file"},
}

COMPARE_PROJECT_PROPERTIES = {
    "project_a": {"type": "string", "description": "First project directory"},
    "project_b": {"type": "string", "description": "Second project directory"},
    "threshold": {
        "type": "number",
        "minimum": 0,
        "maximum": 1,
        "default": 0.75,
        "description": "Minimum cross-project similarity",
    },
    "semantic": {
        "type": "boolean",
        "default": False,
        "description": "Also evaluate semantic similarity (slower)",
    },
    "extensions": {
        "type": "string",
        "description": "Comma-separated file extensions; leading dots are optional (py,.js,ts)",
    },
    "min_lines": {"type": "integer", "minimum": 1, "default": 3},
    "functions_only": {"type": "boolean", "default": True},
    "max_matches": {
        "type": "integer",
        "minimum": 0,
        "default": 20,
        "description": "Maximum matches returned; use 0 for all matches",
    },
}

TOOL_SCHEMA_REDUP = {
    "analyze_project": {
        "name": "analyze_project",
        "description": (
            "Detailed in-project duplication scan. JSON defaults to the top 20 non-generated "
            "groups; use group_scope=all and max_groups=0 only when a complete raw report is "
            "needed. Call once per unchanged path/config: identical calls return the same cached "
            "analysis and should not be repeated."
        ),
        "inputSchema": {"type": "object", "properties": SCAN_PROPERTIES, "required": ["path"]},
    },
    "find_duplicates": {
        "name": "find_duplicates",
        "description": (
            "Start here for an LLM-friendly first pass: returns the top 10 non-generated duplicate "
            "groups plus complete summary totals. Do not repeat the same call."
        ),
        "inputSchema": {
            "type": "object",
            "properties": _make_find_properties(),
            "required": ["path"],
        },
    },
    "compare_scans": {
        "name": "compare_scans",
        "description": "Compare two saved reDUP scan outputs",
        "inputSchema": {
            "type": "object",
            "properties": COMPARE_PROPERTIES,
            "required": ["before", "after"],
        },
    },
    "compare_projects": {
        "name": "compare_projects",
        "description": "Scan two project directories and report shared or duplicated code",
        "inputSchema": {
            "type": "object",
            "properties": COMPARE_PROJECT_PROPERTIES,
            "required": ["project_a", "project_b"],
        },
    },
    "check_project": {
        "name": "check_project",
        "description": "Analyze a project and evaluate duplication quality gates",
        "inputSchema": {
            "type": "object",
            "properties": _make_check_properties(),
            "required": ["path"],
        },
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
