"""TOON reporter — LLM-optimized compact duplication diagnostic."""

from __future__ import annotations

from datetime import datetime, timezone

from redup.core.models import DuplicationMap


def to_toon(dup_map: DuplicationMap) -> str:
    """Serialize a DuplicationMap to TOON format.

    TOON is a compact, token-efficient format designed for LLM context windows.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines: list[str] = []

    # Header
    lines.append(
        f"# redup/duplication | {dup_map.total_groups} groups "
        f"| {dup_map.stats.files_scanned}f {dup_map.stats.total_lines}L | {now}"
    )
    lines.append("")

    # Summary
    lines.append("SUMMARY:")
    lines.append(f"  files_scanned: {dup_map.stats.files_scanned}")
    lines.append(f"  total_lines:   {dup_map.stats.total_lines}")
    lines.append(f"  dup_groups:    {dup_map.total_groups}")
    lines.append(f"  dup_fragments: {dup_map.total_fragments}")
    lines.append(f"  saved_lines:   {dup_map.total_saved_lines}")
    lines.append(f"  scan_ms:       {dup_map.stats.scan_time_ms:.0f}")
    lines.append("")

    # Duplicate groups ranked by impact
    ranked = dup_map.sorted_by_impact()
    if ranked:
        lines.append(f"DUPLICATES[{len(ranked)}] (ranked by impact):")
        for group in ranked:
            marker = "!!" if group.impact_score > 100 else "!" if group.impact_score > 30 else " "
            type_tag = group.duplicate_type.value.upper()[:4]
            name = group.normalized_name or f"block_{group.id}"
            lines.append(
                f"  [{group.id}] {marker} {type_tag:<5} {name}  "
                f"L={group.total_lines} N={group.occurrences} "
                f"saved={group.saved_lines_potential} sim={group.similarity_score:.2f}"
            )
            for frag in group.fragments:
                fn_info = f"  ({frag.function_name})" if frag.function_name else ""
                lines.append(f"      {frag.file}:{frag.line_start}-{frag.line_end}{fn_info}")
        lines.append("")

    # Refactoring plan
    if dup_map.suggestions:
        lines.append(f"REFACTOR[{len(dup_map.suggestions)}] (ranked by priority):")
        for s in dup_map.suggestions:
            risk_icon = {"low": "○", "medium": "◐", "high": "●"}.get(s.risk_level.value, "?")
            lines.append(
                f"  [{s.priority}] {risk_icon} {s.action.value:<18} → {s.new_module}"
            )
            lines.append(f"      WHY: {s.rationale}")
            files_str = ", ".join(s.original_files[:5])
            if len(s.original_files) > 5:
                files_str += f" +{len(s.original_files) - 5} more"
            lines.append(f"      FILES: {files_str}")
        lines.append("")

    # Metrics target
    if ranked:
        lines.append("METRICS-TARGET:")
        lines.append(f"  dup_groups:  {dup_map.total_groups} → 0")
        lines.append(f"  saved_lines: {dup_map.total_saved_lines} lines recoverable")
        lines.append("")

    return "\n".join(lines)
