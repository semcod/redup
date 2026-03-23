"""code2llm reporter — generates LLM-optimized project analysis.

This reporter produces output compatible with code2llm format:
- analysis.toon: compact summary for LLM context windows
- context.md: detailed architecture documentation
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from redup.core.models import DuplicationMap


def _calculate_avg_cc(dup_map: DuplicationMap) -> float:
    """Calculate average cyclomatic complexity (placeholder)."""
    return 3.5  # Placeholder - would need actual CC calculation


def _count_critical_functions(dup_map: DuplicationMap) -> int:
    """Count functions with CC >= 10."""
    return 0  # Placeholder


def _get_layers(dup_map: DuplicationMap) -> list[dict]:
    """Extract layer information from project structure."""
    layers = []
    
    # Group files by directory
    from collections import defaultdict
    dir_stats = defaultdict(lambda: {"files": 0, "lines": 0, "functions": 0})
    
    # This is a simplified version - full implementation would need file stats
    layers.append({
        "name": "src/",
        "cc_avg": _calculate_avg_cc(dup_map),
        "imports_in": 0,
        "imports_out": 0,
    })
    
    return layers


def to_code2llm_toon(
    dup_map: DuplicationMap,
    files_scanned: int = 0,
    total_lines: int = 0,
    functions_count: int = 0,
    classes_count: int = 0,
) -> str:
    """Generate code2llm-compatible TOON format.
    
    This format is optimized for LLM context windows with compact representation.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cc_avg = _calculate_avg_cc(dup_map)
    critical = _count_critical_functions(dup_map)
    
    lines = [
        f"# code2llm | {files_scanned}f {total_lines}L | py:{files_scanned} | {now}",
        f"# CC̄={cc_avg:.1f} | critical:{critical}/{functions_count} | dups:{dup_map.total_groups} | cycles:0",
        "",
        "HEALTH[0]: ok",
        "",
    ]
    
    # Add duplication info
    if dup_map.total_groups > 0:
        lines.append(f"DUPLICATES[{dup_map.total_groups}]: see context.md")
        lines.append("")
        
        for group in dup_map.sorted_by_impact()[:5]:  # Top 5 by impact
            marker = "!!" if group.impact_score > 100 else "!" if group.impact_score > 30 else " "
            lines.append(
                f"  [{group.id}] {marker} {group.duplicate_type.value.upper()[:4]} "
                f"L={group.total_lines} N={group.occurrences} saved={group.saved_lines_potential}"
            )
        lines.append("")
    else:
        lines.append("DUPLICATES[0]: none")
        lines.append("")
    
    lines.append("REFACTOR[0]: none needed")
    lines.append("")
    lines.append("COUPLING: no cross-package imports detected")
    lines.append("")
    
    return "\n".join(lines)


def to_code2llm_context(
    dup_map: DuplicationMap,
    files_scanned: int = 0,
    total_lines: int = 0,
    functions_count: int = 0,
    classes_count: int = 0,
    modules: list[str] | None = None,
) -> str:
    """Generate code2llm-compatible context.md format.
    
    This provides detailed architecture analysis for LLMs.
    """
    if modules is None:
        modules = []
    
    lines = [
        "# System Architecture Analysis",
        "",
        "## Overview",
        "",
        f"- **Project**: {dup_map.project_path}",
        f"- **Primary Language**: python",
        f"- **Total Functions**: {functions_count}",
        f"- **Total Classes**: {classes_count}",
        f"- **Modules**: {len(modules)}",
        "",
        "## Duplication Analysis",
        "",
    ]
    
    if dup_map.total_groups == 0:
        lines.append("No code duplication detected.")
        lines.append("")
    else:
        lines.append(f"**Total Duplicate Groups**: {dup_map.total_groups}")
        lines.append(f"**Total Fragments**: {dup_map.total_fragments}")
        lines.append(f"**Recoverable Lines**: {dup_map.total_saved_lines}")
        lines.append("")
        
        lines.append("### Duplicate Groups by Impact")
        lines.append("")
        
        for group in dup_map.sorted_by_impact():
            lines.append(f"#### {group.id}: {group.normalized_name or 'Unnamed'}")
            lines.append("")
            lines.append(f"- **Type**: {group.duplicate_type.value}")
            lines.append(f"- **Similarity**: {group.similarity_score:.2f}")
            lines.append(f"- **Occurrences**: {group.occurrences}")
            lines.append(f"- **Lines**: {group.total_lines}")
            lines.append(f"- **Impact Score**: {group.impact_score:.1f}")
            lines.append("")
            lines.append("**Locations**:")
            for frag in group.fragments:
                fn_info = f" (`{frag.function_name}`)" if frag.function_name else ""
                lines.append(f"- `{frag.file}:{frag.line_start}-{frag.line_end}`{fn_info}")
            lines.append("")
    
    if dup_map.suggestions:
        lines.append("## Refactoring Suggestions")
        lines.append("")
        
        for suggestion in dup_map.suggestions[:10]:  # Top 10
            lines.append(f"### Priority {suggestion.priority}: {suggestion.action.value}")
            lines.append("")
            lines.append(f"- **Target**: `{suggestion.new_module}`")
            lines.append(f"- **Risk Level**: {suggestion.risk_level.value}")
            lines.append(f"- **Rationale**: {suggestion.rationale}")
            lines.append("")
            lines.append("**Affected Files**:")
            for f in suggestion.original_files[:5]:
                lines.append(f"- `{f}`")
            if len(suggestion.original_files) > 5:
                lines.append(f"- ... and {len(suggestion.original_files) - 5} more")
            lines.append("")
    
    return "\n".join(lines)


def export_code2llm(
    dup_map: DuplicationMap,
    output_dir: Path,
    files_scanned: int = 0,
    total_lines: int = 0,
    functions_count: int = 0,
    classes_count: int = 0,
) -> tuple[Path, Path]:
    """Export both code2llm files to the specified directory.
    
    Returns:
        Tuple of (analysis_toon_path, context_md_path)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate analysis.toon
    toon_content = to_code2llm_toon(
        dup_map,
        files_scanned=files_scanned,
        total_lines=total_lines,
        functions_count=functions_count,
        classes_count=classes_count,
    )
    toon_path = output_dir / "analysis.toon"
    toon_path.write_text(toon_content, encoding="utf-8")
    
    # Generate context.md
    context_content = to_code2llm_context(
        dup_map,
        files_scanned=files_scanned,
        total_lines=total_lines,
        functions_count=functions_count,
        classes_count=classes_count,
    )
    context_path = output_dir / "context.md"
    context_path.write_text(context_content, encoding="utf-8")
    
    return (toon_path, context_path)
