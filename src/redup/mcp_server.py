from __future__ import annotations

import json
import platform
import sys
from enum import Enum
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from redup import __version__
from redup.core.config import config_to_scan_config, load_config
from redup.core.differ import compare_scans, format_diff_result
from redup.core.models import ScanConfig
from redup.core.pipeline import analyze, analyze_optimized, analyze_parallel
from redup.reporters.code2llm_reporter import to_code2llm_context, to_code2llm_toon
from redup.reporters.enhanced_reporter import EnhancedReporter
from redup.reporters.json_reporter import to_json
from redup.reporters.markdown_reporter import to_markdown
from redup.reporters.toon_reporter import to_toon
from redup.reporters.yaml_reporter import to_yaml

SCAN_PROPERTIES = {
    "path": {
        "type": "string",
        "description": "Path to the project directory",
    },
    "format": {
        "type": "string",
        "enum": ["json", "yaml", "toon", "markdown", "enhanced", "code2llm", "all"],
        "default": "json",
        "description": "Output format",
    },
    "mode": {
        "type": "string",
        "enum": ["standard", "optimized", "parallel"],
        "default": "standard",
        "description": "Analysis mode",
    },
    "extensions": {
        "type": "string",
        "description": "Comma-separated file extensions",
    },
    "min_lines": {
        "type": "integer",
        "default": 3,
        "description": "Minimum block size in lines",
    },
    "min_similarity": {
        "type": "number",
        "default": 0.85,
        "description": "Minimum similarity score",
    },
    "include_tests": {
        "type": "boolean",
        "default": False,
        "description": "Include test files",
    },
    "functions_only": {
        "type": "boolean",
        "default": True,
        "description": "Only analyze function-level blocks",
    },
    "parallel": {
        "type": "boolean",
        "default": False,
        "description": "Use parallel scanning for large projects",
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
    "max_workers": {
        "type": "integer",
        "description": "Maximum number of parallel workers",
    },
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
    "include_snippets": {
        "type": "boolean",
        "default": False,
        "description": "Include code snippets in JSON output",
    },
}

TOOL_SCHEMA_REDUP = {
    "analyze_project": {
        "name": "analyze_project",
        "description": "Analyze a project and generate duplication findings",
        "inputSchema": {
            "type": "object",
            "properties": SCAN_PROPERTIES,
            "required": ["path"],
        },
    },
    "find_duplicates": {
        "name": "find_duplicates",
        "description": "Find duplicate code blocks in a project",
        "inputSchema": {
            "type": "object",
            "properties": SCAN_PROPERTIES,
            "required": ["path"],
        },
    },
    "compare_scans": {
        "name": "compare_scans",
        "description": "Compare two saved reDUP scan outputs",
        "inputSchema": {
            "type": "object",
            "properties": {
                "before": {
                    "type": "string",
                    "description": "Path to the earlier scan file",
                },
                "after": {
                    "type": "string",
                    "description": "Path to the later scan file",
                },
            },
            "required": ["before", "after"],
        },
    },
    "compare_projects": {
        "name": "compare_projects",
        "description": "Compare two saved reDUP scan outputs",
        "inputSchema": {
            "type": "object",
            "properties": {
                "before": {
                    "type": "string",
                    "description": "Path to the earlier scan file",
                },
                "after": {
                    "type": "string",
                    "description": "Path to the later scan file",
                },
            },
            "required": ["before", "after"],
        },
    },
    "check_project": {
        "name": "check_project",
        "description": "Analyze a project and evaluate duplication quality gates",
        "inputSchema": {
            "type": "object",
            "properties": {
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
                "max_lines": {
                    "type": "integer",
                    "description": "Compatibility alias for max_saved_lines",
                },
            },
            "required": ["path"],
        },
    },
    "suggest_refactoring": {
        "name": "suggest_refactoring",
        "description": "Analyze a project and return prioritized refactoring suggestions",
        "inputSchema": {
            "type": "object",
            "properties": SCAN_PROPERTIES,
            "required": ["path"],
        },
    },
    "project_info": {
        "name": "project_info",
        "description": "Show reDUP version and environment information",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    "info": {
        "name": "info",
        "description": "Show reDUP version and environment information",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
}


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(_json_safe(key)): _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in value]
    return value


def _resolve_path(raw: Any) -> Path:
    if raw is None:
        raise ValueError("Path is required")
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def _parse_extensions(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        parts = value.split(",")
    else:
        parts = list(value)
    extensions = []
    for part in parts:
        ext = str(part).strip()
        if not ext:
            continue
        extensions.append(ext if ext.startswith(".") else f".{ext}")
    return extensions or None


def _build_scan_config(path: Path, params: dict[str, Any]) -> ScanConfig:
    scan_config = config_to_scan_config(load_config(), path)

    extensions = _parse_extensions(params.get("extensions"))
    if extensions is not None:
        scan_config.extensions = extensions

    if params.get("min_lines") is not None:
        scan_config.min_block_lines = int(params["min_lines"])
    if params.get("min_similarity") is not None:
        scan_config.min_similarity = float(params["min_similarity"])
    if params.get("include_tests") is not None:
        scan_config.include_tests = bool(params["include_tests"])
    if params.get("functions_only") is not None:
        scan_config.functions_only = bool(params["functions_only"])
    if params.get("parallel") is not None:
        scan_config._parallel_enabled = bool(params["parallel"])
    if params.get("memory_cache") is not None:
        scan_config._memory_cache = bool(params["memory_cache"])
    if params.get("incremental") is not None:
        scan_config.enable_cache = bool(params["incremental"])
    if params.get("max_workers") is not None:
        scan_config.parallel_workers = int(params["max_workers"])
    if params.get("fuzzy") is not None:
        scan_config.fuzzy_enabled = bool(params["fuzzy"])
    if params.get("fuzzy_threshold") is not None:
        scan_config.fuzzy_threshold = float(params["fuzzy_threshold"])

    return scan_config


def _run_analysis(path: Path, params: dict[str, Any]) -> tuple[ScanConfig, Any]:
    scan_config = _build_scan_config(path, params)
    mode = str(params.get("mode", "standard")).lower()
    functions_only = bool(params.get("functions_only", scan_config.functions_only))
    parallel_requested = bool(params.get("parallel", False)) or mode == "parallel"
    memory_cache_requested = params.get("memory_cache")
    use_memory_cache = True if memory_cache_requested is None else bool(memory_cache_requested)

    if parallel_requested:
        result = analyze_parallel(
            scan_config,
            function_level_only=functions_only,
            max_workers=scan_config.parallel_workers,
        )
    elif mode == "optimized" or use_memory_cache or bool(params.get("incremental", False)):
        result = analyze_optimized(
            scan_config,
            function_level_only=functions_only,
            use_memory_cache=use_memory_cache,
            max_cache_mb=int(params.get("max_cache_mb", 512)),
        )
    else:
        result = analyze(scan_config, function_level_only=functions_only)

    return scan_config, result


def _estimate_code2llm_counts(dup_map: Any) -> tuple[int, int]:
    functions = set()
    classes = set()
    for group in dup_map.groups:
        for fragment in group.fragments:
            if fragment.function_name:
                functions.add(fragment.function_name)
            if fragment.class_name:
                classes.add(fragment.class_name)
    return len(functions), len(classes)


def _handle_analyze_project(params: dict[str, Any]) -> str:
    path = _resolve_path(params.get("path"))
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Project directory not found: {path}")

    scan_config, dup_map = _run_analysis(path, params)
    fmt = str(params.get("format", "json")).lower()

    if fmt == "json":
        return to_json(dup_map, include_snippets=bool(params.get("include_snippets", False)))
    if fmt == "yaml":
        return to_yaml(dup_map)
    if fmt == "toon":
        return to_toon(dup_map)
    if fmt == "markdown":
        return to_markdown(dup_map)
    if fmt == "enhanced":
        reporter = EnhancedReporter(dup_map)
        payload = {
            "project_path": dup_map.project_path,
            "scan_config": {
                "root": scan_config.root.as_posix(),
                "extensions": scan_config.extensions,
                "min_block_lines": scan_config.min_block_lines,
                "min_similarity": scan_config.min_similarity,
                "include_tests": scan_config.include_tests,
                "functions_only": scan_config.functions_only,
            },
            "metrics": reporter.generate_metrics_report(),
            "visualizations": reporter.generate_visualization_data(),
        }
        return json.dumps(_json_safe(payload), indent=2, ensure_ascii=False)
    if fmt == "code2llm":
        files_scanned = dup_map.stats.files_scanned
        total_lines = dup_map.stats.total_lines
        functions_count, classes_count = _estimate_code2llm_counts(dup_map)
        payload = {
            "analysis.toon": to_code2llm_toon(
                dup_map,
                files_scanned=files_scanned,
                total_lines=total_lines,
                functions_count=functions_count,
                classes_count=classes_count,
            ),
            "context.md": to_code2llm_context(
                dup_map,
                files_scanned=files_scanned,
                total_lines=total_lines,
                functions_count=functions_count,
                classes_count=classes_count,
            ),
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    raise ValueError(f"Unsupported format: {fmt}")


def _handle_suggest_refactoring(params: dict[str, Any]) -> str:
    path = _resolve_path(params.get("path"))
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Project directory not found: {path}")

    scan_config, dup_map = _run_analysis(path, params)
    reporter = EnhancedReporter(dup_map)

    payload = {
        "project_path": dup_map.project_path,
        "scan_config": {
            "root": scan_config.root.as_posix(),
            "extensions": scan_config.extensions,
            "min_block_lines": scan_config.min_block_lines,
            "min_similarity": scan_config.min_similarity,
            "include_tests": scan_config.include_tests,
            "functions_only": scan_config.functions_only,
        },
        "summary": {
            "total_groups": dup_map.total_groups,
            "total_fragments": dup_map.total_fragments,
            "total_saved_lines": dup_map.total_saved_lines,
            "files_scanned": dup_map.stats.files_scanned,
        },
        "refactor_suggestions": [
            {
                "group_id": suggestion.group_id,
                "priority": suggestion.priority,
                "action": suggestion.action.value,
                "new_module": suggestion.new_module,
                "function_name": suggestion.function_name,
                "class_name": suggestion.class_name,
                "original_files": suggestion.original_files,
                "risk_level": suggestion.risk_level.value,
                "rationale": suggestion.rationale,
            }
            for suggestion in dup_map.suggestions
        ],
        "metrics": reporter.generate_metrics_report(),
    }

    return json.dumps(_json_safe(payload), indent=2, ensure_ascii=False)


def _handle_compare_scans(params: dict[str, Any]) -> str:
    before = _resolve_path(params.get("before"))
    after = _resolve_path(params.get("after"))
    diff = compare_scans(before, after)
    payload = {
        "success": True,
        "summary": {
            "resolved_count": diff.resolved_count,
            "new_count": diff.new_count,
            "unchanged_count": diff.unchanged_count,
            "resolved_lines": diff.resolved_lines,
            "new_lines": diff.new_lines,
            "unchanged_lines": diff.unchanged_lines,
        },
        "report": format_diff_result(diff),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _handle_check_project(params: dict[str, Any]) -> str:
    path = _resolve_path(params.get("path"))
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Project directory not found: {path}")

    _, dup_map = _run_analysis(path, params)
    max_groups = int(params.get("max_groups", 10))
    max_saved_lines = int(params.get("max_saved_lines", params.get("max_lines", 100)))

    violations = []
    if dup_map.total_groups > max_groups:
        violations.append(
            {
                "field": "max_groups",
                "limit": max_groups,
                "actual": dup_map.total_groups,
            }
        )
    if dup_map.total_saved_lines > max_saved_lines:
        violations.append(
            {
                "field": "max_saved_lines",
                "limit": max_saved_lines,
                "actual": dup_map.total_saved_lines,
            }
        )

    payload = {
        "success": True,
        "passed": not violations,
        "thresholds": {
            "max_groups": max_groups,
            "max_saved_lines": max_saved_lines,
            "max_lines": max_saved_lines,
        },
        "summary": {
            "total_groups": dup_map.total_groups,
            "total_saved_lines": dup_map.total_saved_lines,
            "total_fragments": dup_map.total_fragments,
            "files_scanned": dup_map.stats.files_scanned,
        },
        "violations": violations,
        "top_groups": [
            {
                "id": group.id,
                "type": group.duplicate_type.value,
                "name": group.normalized_name,
                "occurrences": group.occurrences,
                "saved_lines_potential": group.saved_lines_potential,
                "similarity_score": round(group.similarity_score, 3),
            }
            for group in dup_map.sorted_by_impact()[: min(max_groups, 10)]
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _handle_project_info(_: dict[str, Any]) -> str:
    deps = {
        "tree_sitter": "tree_sitter",
        "datasketch": "datasketch",
        "rapidfuzz": "rapidfuzz",
    }
    optional = {}
    for name, module in deps.items():
        try:
            __import__(module)
            optional[name] = True
        except ImportError:
            optional[name] = False

    payload = {
        "server": "redup",
        "version": __version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "installation_path": str(Path(__file__).resolve().parent),
        "available_tools": list(TOOL_SCHEMA_REDUP.keys()),
        "optional_dependencies": optional,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


TOOL_SCHEMA_REDUP_HANDLERS = {
    "analyze_project": _handle_analyze_project,
    "scan_project": _handle_analyze_project,
    "find_duplicates": _handle_analyze_project,
    "compare_scans": _handle_compare_scans,
    "compare_projects": _handle_compare_scans,
    "check_project": _handle_check_project,
    "suggest_refactoring": _handle_suggest_refactoring,
    "project_info": _handle_project_info,
    "info": _handle_project_info,
}

MCP_HANDLERS = TOOL_SCHEMA_REDUP_HANDLERS


def handle_initialize(request_id: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "0.1.0",
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
    tools = []
    for tool_schema in TOOL_SCHEMA_REDUP.values():
        tools.append(
            {
                "name": tool_schema["name"],
                "description": tool_schema["description"],
                "inputSchema": tool_schema["inputSchema"],
            }
        )

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "tools": tools,
        },
    }


def handle_tools_call(request_id: Any, params: dict[str, Any]) -> dict[str, Any]:
    tool_name = params.get("name")
    arguments = params.get("arguments", {}) or {}

    if tool_name not in MCP_HANDLERS:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Tool '{tool_name}' not found",
            },
        }

    try:
        result = MCP_HANDLERS[tool_name](arguments)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": result,
                    }
                ]
            },
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
    method = request.get("method", "")
    params = request.get("params", {}) or {}
    request_id = request.get("id")

    if method == "initialize":
        return handle_initialize(request_id)
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
    print("reDUP MCP Server started", file=sys.stderr)
    available_tools = ", ".join(sorted({tool["name"] for tool in TOOL_SCHEMA_REDUP.values()}))
    print(f"Available tools: {available_tools}", file=sys.stderr)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_request(request)
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


if __name__ == "__main__":
    run_server()
