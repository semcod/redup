"""Diff functionality for comparing reDUP scans."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from redup.core.models import (
    DuplicateGroup,
    DuplicationMap,
    RefactorAction,
    RefactorSuggestion,
    RiskLevel,
    ScanStats,
)
from redup.core.utils.diff_helpers import DiffCalculator, GroupMatcher


@dataclass
class DiffResult:
    """Result of comparing two reDUP scans."""

    resolved_groups: list[DuplicateGroup]
    new_groups: list[DuplicateGroup]
    unchanged_groups: list[DuplicateGroup]

    resolved_count: int
    new_count: int
    unchanged_count: int

    resolved_lines: int
    new_lines: int
    unchanged_lines: int


def _load_duplication_map(file_path: Path) -> DuplicationMap:
    """Load a DuplicationMap from a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")
    data = json.loads(content)

    # Reconstruct DuplicateGroup objects from JSON data
    groups = []
    for group_data in data.get("groups", []):
        # Create fragments
        fragments = []
        for frag_data in group_data.get("fragments", []):
            from redup.core.models import DuplicateFragment

            fragment = DuplicateFragment(
                file=frag_data["file"],
                line_start=frag_data["line_start"],
                line_end=frag_data["line_end"],
                function_name=frag_data.get("function_name"),
                class_name=frag_data.get("class_name"),
            )
            fragments.append(fragment)

        # Create DuplicateGroup
        from redup.core.models import DuplicateGroup, DuplicateType

        metadata = dict(group_data.get("metadata", {}))
        for field in ("actionability", "provenance", "reason"):
            if group_data.get(field) is not None:
                metadata[field] = group_data[field]

        group = DuplicateGroup(
            id=group_data["id"],
            duplicate_type=DuplicateType(group_data["type"]),
            normalized_name=group_data.get("normalized_name"),
            normalized_hash=group_data.get("normalized_hash", ""),
            similarity_score=group_data.get("similarity_score", 1.0),
            fragments=fragments,
            metadata=metadata,
        )
        groups.append(group)

    # Full reports use ``refactor_suggestions``. Keep the old key readable and
    # tolerate compact reports, because compare-scans only requires the groups.
    suggestions = []
    suggestion_items = data.get("refactor_suggestions", data.get("suggestions", []))
    for suggestion_data in suggestion_items:
        group_id = suggestion_data.get("group_id")
        if not group_id:
            continue
        try:
            suggestions.append(
                RefactorSuggestion(
                    group_id=group_id,
                    priority=suggestion_data.get("priority", 0),
                    action=RefactorAction(
                        suggestion_data.get("action", RefactorAction.EXTRACT_FUNCTION.value)
                    ),
                    new_module=suggestion_data.get("new_module", ""),
                    function_name=suggestion_data.get("function_name"),
                    class_name=suggestion_data.get("class_name"),
                    rationale=suggestion_data.get("rationale", ""),
                    original_files=suggestion_data.get("original_files", []),
                    risk_level=RiskLevel(suggestion_data.get("risk_level", RiskLevel.LOW.value)),
                )
            )
        except (TypeError, ValueError):
            continue

    stats_data = data.get("stats", {})
    stats = ScanStats(
        files_scanned=stats_data.get("files_scanned", 0),
        files_skipped=stats_data.get("files_skipped", 0),
        total_lines=stats_data.get("total_lines", 0),
        total_blocks=stats_data.get("total_blocks", 0),
        scan_time_ms=stats_data.get("scan_time_ms", 0.0),
    )

    return DuplicationMap(
        project_path=data.get("project_path", ""),
        config=None,
        stats=stats,
        groups=groups,
        suggestions=suggestions,
    )


def _group_by_id(groups: list[DuplicateGroup]) -> dict[str, DuplicateGroup]:
    """Group DuplicateGroup objects by their ID."""
    result = {}
    for group in groups:
        result[group.id] = group
    return result


def compare_scans(before_file: Path, after_file: Path) -> DiffResult:
    """Compare two reDUP scan results and return the differences."""

    # Load both scans
    before_map = _load_duplication_map(before_file)
    after_map = _load_duplication_map(after_file)

    before_groups = _group_by_id(before_map.groups)
    after_groups = _group_by_id(after_map.groups)

    # Use helper classes to find matching groups and calculate stats
    matcher = GroupMatcher(before_groups, after_groups)

    resolved_groups = matcher.get_resolved_groups()
    new_groups = matcher.get_new_groups()
    unchanged_groups = matcher.get_unchanged_groups()

    stats = DiffCalculator.calculate_diff_stats(resolved_groups, new_groups, unchanged_groups)

    return DiffResult(
        resolved_groups=resolved_groups,
        new_groups=new_groups,
        unchanged_groups=unchanged_groups,
        resolved_count=stats["resolved_count"],
        new_count=stats["new_count"],
        unchanged_count=stats["unchanged_count"],
        resolved_lines=stats["resolved_lines"],
        new_lines=stats["new_lines"],
        unchanged_lines=stats["unchanged_lines"],
    )


def _format_group_header(title: str, width: int) -> list[str]:
    """Format a section header for group listing."""
    return [f"{title}:", "-" * width, ""]


def _format_group_details(group: DuplicateGroup, label: str) -> list[str]:
    """Format a single group's details."""
    return [
        f"  [{group.id}] {group.duplicate_type.value.upper()} {group.normalized_name or 'unnamed'}",
        f"    {label}: {group.saved_lines_potential} lines",
        f"    Files: {', '.join(frag.file for frag in group.fragments)}",
    ]


def _format_groups_section(
    groups: list[DuplicateGroup],
    title: str,
    width: int,
    label: str,
) -> list[str]:
    """Format a section of groups if any exist."""
    if not groups:
        return []

    lines = _format_group_header(title, width)
    for group in sorted(groups, key=lambda g: g.saved_lines_potential, reverse=True):
        lines.extend(_format_group_details(group, label))
    lines.append("")
    return lines


def _format_assessment(new_lines: int, resolved_lines: int) -> str:
    """Format the overall change assessment."""
    total_change = new_lines - resolved_lines
    if total_change > 0:
        return f"Overall: +{total_change} lines of duplication added"
    elif total_change < 0:
        return f"Overall: {total_change} lines of duplication eliminated"
    return "Overall: No net change in duplication"


def format_diff_result(diff: DiffResult) -> str:
    """Format a DiffResult as a human-readable string."""
    lines = [
        "reDUP Diff Analysis",
        "=" * 50,
        "",
        "Summary:",
        f"  RESOLVED: {diff.resolved_count} groups eliminated (saved {diff.resolved_lines} lines)",
        f"  NEW: {diff.new_count} groups added (potential {diff.new_lines} lines)",
        f"  UNCHANGED: {diff.unchanged_count} groups remain ({diff.unchanged_lines} lines)",
        "",
    ]

    # Add group sections
    lines.extend(_format_groups_section(diff.resolved_groups, "Resolved Groups", 20, "Saved"))
    lines.extend(_format_groups_section(diff.new_groups, "New Groups", 15, "Potential"))
    lines.extend(_format_groups_section(diff.unchanged_groups, "Unchanged Groups", 20, "Lines"))

    # Overall assessment
    lines.append(_format_assessment(diff.new_lines, diff.resolved_lines))

    return "\n".join(lines)
