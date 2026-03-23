"""Planner — generates refactoring suggestions from duplicate groups."""

from __future__ import annotations

import os

from redup.core.models import (
    DuplicateGroup,
    DuplicationMap,
    RefactorAction,
    RefactorSuggestion,
    RiskLevel,
)


def _common_prefix(paths: list[str]) -> str:
    """Find the common directory prefix of a list of file paths."""
    if not paths:
        return ""
    return os.path.commonpath([os.path.dirname(p) for p in paths])


def _suggest_module_name(group: DuplicateGroup) -> str:
    """Suggest a target module name for extracted code."""
    files = [f.file for f in group.fragments]
    prefix = _common_prefix(files)

    if group.normalized_name:
        func_name = group.normalized_name
    elif group.fragments and group.fragments[0].function_name:
        func_name = group.fragments[0].function_name
    else:
        func_name = f"shared_block_{group.id[:8]}"

    if prefix:
        return f"{prefix}/utils/{func_name}.py"
    return f"utils/{func_name}.py"


def _assess_risk(group: DuplicateGroup) -> RiskLevel:
    """Assess the risk of refactoring a duplicate group."""
    files = {f.file for f in group.fragments}

    if len(files) == 1:
        return RiskLevel.LOW

    if group.total_lines > 30:
        return RiskLevel.MEDIUM

    packages = {f.split(os.sep)[0] for f in files if os.sep in f}
    if len(packages) > 2:
        return RiskLevel.HIGH

    return RiskLevel.LOW


def _choose_action(group: DuplicateGroup) -> RefactorAction:
    """Choose the best refactoring action for a group."""
    has_class = any(f.class_name for f in group.fragments)
    all_same_class = (
        has_class
        and len({f.class_name for f in group.fragments if f.class_name}) == 1
    )

    if all_same_class:
        return RefactorAction.EXTRACT_CLASS

    if group.total_lines > 50:
        return RefactorAction.EXTRACT_MODULE

    return RefactorAction.EXTRACT_FUNCTION


def generate_suggestions(dup_map: DuplicationMap) -> list[RefactorSuggestion]:
    """Generate prioritized refactoring suggestions for all duplicate groups."""
    ranked = dup_map.sorted_by_impact()
    suggestions: list[RefactorSuggestion] = []

    for priority, group in enumerate(ranked, start=1):
        if group.saved_lines_potential == 0:
            continue

        action = _choose_action(group)
        new_module = _suggest_module_name(group)
        risk = _assess_risk(group)
        files = sorted({f.file for f in group.fragments})

        func_name = None
        if group.fragments and group.fragments[0].function_name:
            func_name = group.fragments[0].function_name

        rationale = (
            f"{group.occurrences} occurrences of {group.total_lines}-line block "
            f"across {len(files)} files — saves {group.saved_lines_potential} lines"
        )

        suggestions.append(
            RefactorSuggestion(
                group_id=group.id,
                action=action,
                new_module=new_module,
                function_name=func_name,
                original_files=files,
                risk_level=risk,
                priority=priority,
                rationale=rationale,
            )
        )

    return suggestions
