"""MCP tool handlers for reDUP analysis operations."""

from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Any

from redup import __version__
from redup.core.config import config_to_scan_config, load_config
from redup.core.differ import compare_scans, format_diff_result
from redup.core.models import ScanConfig
from redup.core.pipeline import analyze, analyze_optimized, analyze_parallel
from redup.mcp.utils import json_safe, resolve_path, parse_extensions
from redup.reporters.code2llm_reporter import to_code2llm_context, to_code2llm_toon
from redup.reporters.enhanced_reporter import EnhancedReporter
from redup.reporters.json_reporter import to_json
from redup.reporters.markdown_reporter import to_markdown
from redup.reporters.toon_reporter import to_toon
from redup.reporters.yaml_reporter import to_yaml


def _build_scan_config(path: Path, params: dict[str, Any]) -> ScanConfig:
    """Build scan config from parameters."""
    scan_config = config_to_scan_config(load_config(), path)

    extensions = parse_extensions(params.get("extensions"))
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
    """Run analysis based on mode and parameters."""
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
    """Estimate function and class counts from duplication map."""
    functions = set()
    classes = set()
    for group in dup_map.groups:
        for fragment in group.fragments:
            if fragment.function_name:
                functions.add(fragment.function_name)
            if fragment.class_name:
                classes.add(fragment.class_name)
    return len(functions), len(classes)


def _format_analysis_result(
    scan_config: ScanConfig,
    dup_map: Any,
    fmt: str,
    include_snippets: bool = False,
) -> str:
    """Format analysis result based on output format."""
    if fmt == "json":
        return to_json(dup_map, include_snippets=include_snippets)
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
        return json.dumps(json_safe(payload), indent=2, ensure_ascii=False)
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


def handle_analyze_project(params: dict[str, Any]) -> str:
    """Analyze a project and return formatted results."""
    path = resolve_path(params.get("path"))
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Project directory not found: {path}")

    scan_config, dup_map = _run_analysis(path, params)
    fmt = str(params.get("format", "json")).lower()

    return _format_analysis_result(
        scan_config, dup_map, fmt,
        include_snippets=bool(params.get("include_snippets", False))
    )


def handle_suggest_refactoring(params: dict[str, Any]) -> str:
    """Analyze and return refactoring suggestions."""
    path = resolve_path(params.get("path"))
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

    return json.dumps(json_safe(payload), indent=2, ensure_ascii=False)


def handle_compare_scans(params: dict[str, Any]) -> str:
    """Compare two saved scan results."""
    before = resolve_path(params.get("before"))
    after = resolve_path(params.get("after"))
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


def _check_thresholds(dup_map: Any, params: dict[str, Any]) -> list[dict]:
    """Check project against quality thresholds."""
    max_groups = int(params.get("max_groups", 10))
    max_saved_lines = int(params.get("max_saved_lines", params.get("max_lines", 100)))

    violations = []
    if dup_map.total_groups > max_groups:
        violations.append({
            "field": "max_groups",
            "limit": max_groups,
            "actual": dup_map.total_groups,
        })
    if dup_map.total_saved_lines > max_saved_lines:
        violations.append({
            "field": "max_saved_lines",
            "limit": max_saved_lines,
            "actual": dup_map.total_saved_lines,
        })

    return violations


def _format_top_groups(dup_map: Any, max_groups: int) -> list[dict]:
    """Format top groups by impact for response."""
    return [
        {
            "id": group.id,
            "type": group.duplicate_type.value,
            "name": group.normalized_name,
            "occurrences": group.occurrences,
            "saved_lines_potential": group.saved_lines_potential,
            "similarity_score": round(group.similarity_score, 3),
        }
        for group in dup_map.sorted_by_impact()[:min(max_groups, 10)]
    ]


def handle_check_project(params: dict[str, Any]) -> str:
    """Check project against quality gates."""
    path = resolve_path(params.get("path"))
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Project directory not found: {path}")

    _, dup_map = _run_analysis(path, params)
    max_groups = int(params.get("max_groups", 10))
    max_saved_lines = int(params.get("max_saved_lines", params.get("max_lines", 100)))

    violations = _check_thresholds(dup_map, params)

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
        "top_groups": _format_top_groups(dup_map, max_groups),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _get_optional_deps() -> dict[str, bool]:
    """Check which optional dependencies are available."""
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
    return optional


def handle_project_info(_: dict[str, Any]) -> str:
    """Return reDUP version and environment information."""
    payload = {
        "server": "redup",
        "version": __version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "installation_path": str(Path(__file__).resolve().parents[2]),
        "optional_dependencies": _get_optional_deps(),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


# Handler registry
TOOL_HANDLERS = {
    "analyze_project": handle_analyze_project,
    "scan_project": handle_analyze_project,
    "find_duplicates": handle_analyze_project,
    "compare_scans": handle_compare_scans,
    "compare_projects": handle_compare_scans,
    "check_project": handle_check_project,
    "suggest_refactoring": handle_suggest_refactoring,
    "project_info": handle_project_info,
    "info": handle_project_info,
}
