"""TOON reporter — LLM-optimized compact duplication diagnostic."""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from redup.core.models import DuplicationMap


def _render_header(dup_map: DuplicationMap) -> list[str]:
    """Render TOON header with project summary."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [
        f"# redup/duplication | {dup_map.total_groups} groups "
        f"| {dup_map.stats.files_scanned}f {dup_map.stats.total_lines}L | {now}",
        ""
    ]


def _render_summary(dup_map: DuplicationMap) -> list[str]:
    """Render summary statistics."""
    return [
        "SUMMARY:",
        f"  files_scanned: {dup_map.stats.files_scanned}",
        f"  total_lines:   {dup_map.stats.total_lines}",
        f"  dup_groups:    {dup_map.total_groups}",
        f"  dup_fragments: {dup_map.total_fragments}",
        f"  saved_lines:   {dup_map.total_saved_lines}",
        f"  scan_ms:       {dup_map.stats.scan_time_ms:.0f}",
        ""
    ]


def _render_duplicates(groups: list) -> list[str]:
    """Render duplicate groups ranked by impact."""
    lines: list[str] = []

    if groups:
        lines.append(f"DUPLICATES[{len(groups)}] (ranked by impact):")
        for group in groups:
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

    return lines


def _render_refactor(suggestions: list) -> list[str]:
    """Render refactoring suggestions."""
    lines: list[str] = []

    if suggestions:
        lines.append(f"REFACTOR[{len(suggestions)}] (ranked by priority):")
        for s in suggestions:
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

    return lines


def _render_hotspots(dup_map: DuplicationMap) -> list[str]:
    """Render top files with most duplication — where to focus effort."""
    file_stats: dict[str, dict] = defaultdict(lambda: {"dup_lines": 0, "groups": 0, "fragments": 0})

    for group in dup_map.groups:
        files_in_group: set[str] = set()
        for frag in group.fragments:
            file_stats[frag.file]["dup_lines"] += frag.line_count
            file_stats[frag.file]["fragments"] += 1
            files_in_group.add(frag.file)
        for f in files_in_group:
            file_stats[f]["groups"] += 1

    if not file_stats:
        return []

    ranked = sorted(file_stats.items(), key=lambda x: x[1]["dup_lines"], reverse=True)
    top = ranked[:7]

    lines: list[str] = [f"HOTSPOTS[{len(top)}] (files with most duplication):"]
    for path, s in top:
        pct = (s["dup_lines"] / max(dup_map.stats.total_lines, 1)) * 100
        lines.append(
            f"  {path}  dup={s['dup_lines']}L  groups={s['groups']}  "
            f"frags={s['fragments']}  ({pct:.1f}%)"
        )
    lines.append("")
    return lines


def _render_dependency_risk(dup_map: DuplicationMap) -> list[str]:
    """Render cross-module dependency risk for each duplicate group."""
    if not dup_map.groups:
        return []

    risky: list[tuple[str, int, list[str]]] = []
    for group in dup_map.groups:
        files = sorted({frag.file for frag in group.fragments})
        packages = {f.split(os.sep)[0] for f in files if os.sep in f}
        if len(packages) >= 2:
            name = group.normalized_name or group.fragments[0].function_name or f"block_{group.id[:8]}"
            risky.append((name, len(packages), files))

    if not risky:
        return []

    risky.sort(key=lambda x: x[1], reverse=True)
    lines: list[str] = [f"DEPENDENCY_RISK[{len(risky)}] (duplicates spanning multiple packages):"]
    for name, pkg_count, files in risky[:7]:
        lines.append(f"  {name}  packages={pkg_count}  files={len(files)}")
        for f in files[:4]:
            lines.append(f"      {f}")
        if len(files) > 4:
            lines.append(f"      +{len(files) - 4} more")
    lines.append("")
    return lines


def _render_quick_wins(dup_map: DuplicationMap) -> list[str]:
    """Render low-risk, high-savings suggestions — do these first."""
    if not dup_map.suggestions:
        return []

    wins = [
        s for s in dup_map.suggestions
        if s.risk_level.value == "low" and _saved_for_suggestion(s, dup_map) >= 6
    ]
    wins.sort(key=lambda s: _saved_for_suggestion(s, dup_map), reverse=True)

    if not wins:
        return []

    lines: list[str] = [f"QUICK_WINS[{len(wins)}] (low risk, high savings — do first):"]
    for s in wins[:10]:
        saved = _saved_for_suggestion(s, dup_map)
        files_str = ", ".join(Path(f).name for f in s.original_files[:3])
        if len(s.original_files) > 3:
            files_str += f" +{len(s.original_files) - 3}"
        lines.append(
            f"  [{s.priority}] {s.action.value:<18} saved={saved}L  "
            f"→ {s.new_module}"
        )
        lines.append(f"      FILES: {files_str}")
    lines.append("")
    return lines


def _calculate_group_effort(group: DuplicateGroup) -> tuple[str, str, float]:
    """Calculate effort estimate for a single group.
    
    Returns: (name, difficulty, minutes)
    """
    name = group.normalized_name or group.fragments[0].function_name or f"block_{group.id[:8]}"
    files = {frag.file for frag in group.fragments}
    packages = {f.split(os.sep)[0] for f in files if os.sep in f}

    base_min = group.saved_lines_potential * 2.0  # ~2 min per saved line
    if len(packages) >= 2:
        base_min *= 2.0  # cross-package doubles effort
    if group.total_lines > 30:
        base_min *= 1.5  # large blocks are harder

    difficulty = "easy" if base_min < 30 else "medium" if base_min < 90 else "hard"
    return name, difficulty, base_min


def _format_estimate_lines(
    estimates: list[tuple[str, str, int, float]],
    total_minutes: float,
) -> list[str]:
    """Format effort estimate lines."""
    hours = total_minutes / 60
    lines: list[str] = [f"EFFORT_ESTIMATE (total ≈ {hours:.1f}h):"]
    
    for name, diff, saved, mins in estimates[:10]:
        lines.append(f"  {diff:<6} {name:<35} saved={saved}L  ~{mins:.0f}min")
    
    if len(estimates) > 10:
        remaining = sum(m for _, _, _, m in estimates[10:])
        lines.append(f"  ... +{len(estimates) - 10} more (~{remaining:.0f}min)")
    
    lines.append("")
    return lines


def _render_effort_estimate(dup_map: DuplicationMap) -> list[str]:
    """Render effort estimate per duplicate group.

    Heuristic: ~5min per LOC for simple extract, ×2 for cross-package, ×1.5 for >30 LOC.
    """
    if not dup_map.groups:
        return []

    estimates: list[tuple[str, str, int, float]] = []
    total_minutes = 0.0

    for group in dup_map.sorted_by_impact():
        if group.saved_lines_potential == 0:
            continue
        name, difficulty, minutes = _calculate_group_effort(group)
        estimates.append((name, difficulty, group.saved_lines_potential, minutes))
        total_minutes += minutes

    if not estimates:
        return []

    return _format_estimate_lines(estimates, total_minutes)


def _saved_for_suggestion(s, dup_map: DuplicationMap) -> int:
    """Look up saved_lines_potential for a suggestion's group."""
    for g in dup_map.groups:
        if g.id == s.group_id:
            return g.saved_lines_potential
    return 0


def _render_metrics_target(dup_map: DuplicationMap, groups: list) -> list[str]:
    """Render metrics target section."""
    lines: list[str] = []

    if groups:
        lines.append("METRICS-TARGET:")
        lines.append(f"  dup_groups:  {dup_map.total_groups} → 0")
        lines.append(f"  saved_lines: {dup_map.total_saved_lines} lines recoverable")
        lines.append("")

    return lines


def to_toon(dup_map: DuplicationMap) -> str:
    """Serialize a DuplicationMap to TOON format.

    TOON is a compact, token-efficient format designed for LLM context windows.
    """
    ranked = dup_map.sorted_by_impact()

    sections = [
        _render_header(dup_map),
        _render_summary(dup_map),
        _render_hotspots(dup_map),
        _render_duplicates(ranked),
        _render_refactor(dup_map.suggestions),
        _render_quick_wins(dup_map),
        _render_dependency_risk(dup_map),
        _render_effort_estimate(dup_map),
        _render_metrics_target(dup_map, ranked),
    ]

    return "\n".join(line for section in sections for line in section)
