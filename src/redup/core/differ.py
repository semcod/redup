"""Diff functionality for comparing reDUP scans."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from redup.core.models import DuplicationMap, DuplicateGroup
from redup.core.utils.diff_helpers import GroupMatcher, DiffCalculator


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
        group = DuplicateGroup(
            id=group_data["id"],
            duplicate_type=DuplicateType(group_data["type"]),
            normalized_name=group_data.get("normalized_name"),
            normalized_hash=group_data["normalized_hash"],
            similarity_score=group_data["similarity_score"],
            fragments=fragments,
        )
        groups.append(group)
    
    # Create suggestions
    suggestions = []
    for suggestion_data in data.get("suggestions", []):
        from redup.core.models import RefactorSuggestion
        suggestion = RefactorSuggestion(
            priority=suggestion_data["priority"],
            action=suggestion_data["action"],
            new_module=suggestion_data["new_module"],
            rationale=suggestion_data["rationale"],
            original_files=suggestion_data["original_files"],
            risk_level=suggestion_data["risk_level"],
        )
        suggestions.append(suggestion)
    
    return DuplicationMap(
        project_path=data.get("project_path", ""),
        config=data.get("config", {}),
        stats=data.get("stats", {}),
        groups=groups,
        suggestions=suggestions,
    )


def _group_by_id(groups: list[DuplicateGroup]) -> dict[str, DuplicateGroup]:
    """Group DuplicateGroup objects by their ID."""
    result = {}
    for group in groups:
        result[group.id] = group
    return result


def _groups_match(group1: DuplicateGroup, group2: DuplicateGroup) -> bool:
    """Check if two groups represent the same duplicate (similar structure and files)."""
    # Check if they have the same type and similar similarity
    if group1.duplicate_type != group2.duplicate_type:
        return False
    
    # Check similarity scores are close
    if abs(group1.similarity_score - group2.similarity_score) > 0.1:
        return False
    
    # Check if they involve similar files (at least 50% overlap)
    files1 = {frag.file for frag in group1.fragments}
    files2 = {frag.file for frag in group2.fragments}
    
    if not files1 or not files2:
        return False
    
    overlap = len(files1.intersection(files2))
    union = len(files1.union(files2))
    
    return overlap / union >= 0.5


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
        resolved_count=stats['resolved_count'],
        new_count=stats['new_count'],
        unchanged_count=stats['unchanged_count'],
        resolved_lines=stats['resolved_lines'],
        new_lines=stats['new_lines'],
        unchanged_lines=stats['unchanged_lines'],
    )


def format_diff_result(diff: DiffResult) -> str:
    """Format a DiffResult as a human-readable string."""
    lines = []
    
    # Header
    lines.append("reDUP Diff Analysis")
    lines.append("=" * 50)
    lines.append("")
    
    # Summary
    lines.append("Summary:")
    lines.append(f"  RESOLVED: {diff.resolved_count} groups eliminated (saved {diff.resolved_lines} lines)")
    lines.append(f"  NEW: {diff.new_count} groups added (potential {diff.new_lines} lines)")
    lines.append(f"  UNCHANGED: {diff.unchanged_count} groups remain ({diff.unchanged_lines} lines)")
    lines.append("")
    
    # Resolved groups
    if diff.resolved_groups:
        lines.append("Resolved Groups:")
        lines.append("-" * 20)
        for group in sorted(diff.resolved_groups, key=lambda g: g.saved_lines_potential, reverse=True):
            lines.append(f"  [{group.id}] {group.duplicate_type.value.upper()} {group.normalized_name or 'unnamed'}")
            lines.append(f"    Saved: {group.saved_lines_potential} lines")
            lines.append(f"    Files: {', '.join(frag.file for frag in group.fragments)}")
        lines.append("")
    
    # New groups
    if diff.new_groups:
        lines.append("New Groups:")
        lines.append("-" * 15)
        for group in sorted(diff.new_groups, key=lambda g: g.saved_lines_potential, reverse=True):
            lines.append(f"  [{group.id}] {group.duplicate_type.value.upper()} {group.normalized_name or 'unnamed'}")
            lines.append(f"    Potential: {group.saved_lines_potential} lines")
            lines.append(f"    Files: {', '.join(frag.file for frag in group.fragments)}")
        lines.append("")
    
    # Unchanged groups
    if diff.unchanged_groups:
        lines.append("Unchanged Groups:")
        lines.append("-" * 20)
        for group in sorted(diff.unchanged_groups, key=lambda g: g.saved_lines_potential, reverse=True):
            lines.append(f"  [{group.id}] {group.duplicate_type.value.upper()} {group.normalized_name or 'unnamed'}")
            lines.append(f"    Lines: {group.saved_lines_potential}")
        lines.append("")
    
    # Overall assessment
    total_change = diff.new_lines - diff.resolved_lines
    if total_change > 0:
        assessment = f"Overall: +{total_change} lines of duplication added"
    elif total_change < 0:
        assessment = f"Overall: {total_change} lines of duplication eliminated"
    else:
        assessment = "Overall: No net change in duplication"
    
    lines.append(assessment)
    
    return "\n".join(lines)
