"""Helpers for comparing reDUP scan results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from redup.core.models import DuplicateGroup


def _group_files(group: DuplicateGroup) -> set[str]:
    return {fragment.file for fragment in group.fragments}


def _groups_match(group1: DuplicateGroup, group2: DuplicateGroup) -> bool:
    """Check whether two duplicate groups likely represent the same finding."""
    if group1.duplicate_type != group2.duplicate_type:
        return False

    if abs(group1.similarity_score - group2.similarity_score) > 0.1:
        return False

    files1 = _group_files(group1)
    files2 = _group_files(group2)
    if not files1 or not files2:
        return False

    overlap = len(files1.intersection(files2))
    union = len(files1.union(files2))
    if union == 0:
        return False

    return overlap / union >= 0.5


@dataclass(slots=True)
class _MatchResult:
    before: DuplicateGroup
    after: DuplicateGroup


class GroupMatcher:
    """Match duplicate groups between two scan results."""

    def __init__(self, before_groups: dict[str, DuplicateGroup], after_groups: dict[str, DuplicateGroup]) -> None:
        self.before_groups = before_groups
        self.after_groups = after_groups
        self._matches: list[_MatchResult] | None = None

    def _ensure_matches(self) -> None:
        if self._matches is not None:
            return

        matches: list[_MatchResult] = []
        matched_before: set[str] = set()
        matched_after: set[str] = set()

        # First, prefer exact id matches when the groups are otherwise compatible.
        for group_id, before_group in self.before_groups.items():
            after_group = self.after_groups.get(group_id)
            if after_group is None:
                continue
            if _groups_match(before_group, after_group):
                matches.append(_MatchResult(before=before_group, after=after_group))
                matched_before.add(group_id)
                matched_after.add(group_id)

        # Then, match remaining groups by structural similarity.
        remaining_before = [
            group
            for group_id, group in self.before_groups.items()
            if group_id not in matched_before
        ]
        remaining_after = [
            group
            for group_id, group in self.after_groups.items()
            if group_id not in matched_after
        ]

        remaining_before.sort(key=lambda group: group.impact_score, reverse=True)
        remaining_after.sort(key=lambda group: group.impact_score, reverse=True)

        for before_group in remaining_before:
            best_index: int | None = None
            best_score = -1.0

            for index, after_group in enumerate(remaining_after):
                if after_group.id in matched_after:
                    continue
                if not _groups_match(before_group, after_group):
                    continue

                score = self._match_score(before_group, after_group)
                if score > best_score:
                    best_score = score
                    best_index = index

            if best_index is None:
                continue

            after_group = remaining_after[best_index]
            matched_before.add(before_group.id)
            matched_after.add(after_group.id)
            matches.append(_MatchResult(before=before_group, after=after_group))

        self._matches = matches

    @staticmethod
    def _match_score(before_group: DuplicateGroup, after_group: DuplicateGroup) -> float:
        files_before = _group_files(before_group)
        files_after = _group_files(after_group)
        overlap = len(files_before.intersection(files_after))
        union = len(files_before.union(files_after))
        file_score = overlap / union if union else 0.0

        score = file_score
        if before_group.normalized_hash and before_group.normalized_hash == after_group.normalized_hash:
            score += 1.0
        if before_group.normalized_name and before_group.normalized_name == after_group.normalized_name:
            score += 0.5
        score += max(0.0, 1.0 - abs(before_group.similarity_score - after_group.similarity_score))
        return score

    def get_resolved_groups(self) -> list[DuplicateGroup]:
        """Groups that disappeared between scans."""
        self._ensure_matches()
        matched_before = {match.before.id for match in self._matches or []}
        return [group for group_id, group in self.before_groups.items() if group_id not in matched_before]

    def get_new_groups(self) -> list[DuplicateGroup]:
        """Groups that appeared in the later scan."""
        self._ensure_matches()
        matched_after = {match.after.id for match in self._matches or []}
        return [group for group_id, group in self.after_groups.items() if group_id not in matched_after]

    def get_unchanged_groups(self) -> list[DuplicateGroup]:
        """Groups that are present in both scans."""
        self._ensure_matches()
        return [match.after for match in self._matches or []]


class DiffCalculator:
    """Aggregate statistics for scan diffs."""

    @staticmethod
    def calculate_diff_stats(
        resolved_groups: Iterable[DuplicateGroup],
        new_groups: Iterable[DuplicateGroup],
        unchanged_groups: Iterable[DuplicateGroup],
    ) -> dict[str, int]:
        resolved_groups = list(resolved_groups)
        new_groups = list(new_groups)
        unchanged_groups = list(unchanged_groups)

        return {
            "resolved_count": len(resolved_groups),
            "new_count": len(new_groups),
            "unchanged_count": len(unchanged_groups),
            "resolved_lines": sum(group.saved_lines_potential for group in resolved_groups),
            "new_lines": sum(group.saved_lines_potential for group in new_groups),
            "unchanged_lines": sum(group.saved_lines_potential for group in unchanged_groups),
        }
