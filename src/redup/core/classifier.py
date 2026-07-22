"""Classify duplicate provenance before proposing refactors."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from redup.core.models import DuplicateGroup, DuplicateType

_PUBLISHED_SEGMENTS = {"assets", "build", "dist", "httpdocs", "public", "static", "www"}


def _parts(path: str) -> tuple[str, ...]:
    return PurePosixPath(path.replace("\\", "/")).parts


def _without_segment(parts: tuple[str, ...], segment: str) -> tuple[str, ...]:
    try:
        index = parts.index(segment)
    except ValueError:
        return parts
    return parts[:index] + parts[index + 1 :]


def _contains_source_output_pair(paths: list[tuple[str, ...]]) -> bool:
    path_set = set(paths)
    return any("src" in path and _without_segment(path, "src") in path_set for path in paths)


def _contains_nested_mirror_pair(paths: list[tuple[str, ...]]) -> bool:
    for left in paths:
        for right in paths:
            if len(left) <= len(right):
                continue
            if left[-len(right) :] == right:
                return True
    return False


def _same_relative_path_across_roots(paths: list[tuple[str, ...]]) -> bool:
    if len(paths) < 2 or any(len(path) < 2 for path in paths):
        return False
    return len({path[0] for path in paths}) > 1 and len({path[1:] for path in paths}) == 1


def _shared_family_prefix(roots: set[str]) -> bool:
    if len(roots) < 2:
        return False
    tokenized = [re.split(r"[-_.]+", root) for root in roots]
    prefix_length = 0
    for tokens in zip(*tokenized, strict=False):
        if len(set(tokens)) != 1:
            break
        prefix_length += 1
    return prefix_length >= 2


def classify_duplicate_group(group: DuplicateGroup) -> dict[str, object]:
    """Return conservative provenance and actionability metadata for a group."""
    paths = [_parts(fragment.file) for fragment in group.fragments]
    roots = {path[0] for path in paths if path}
    files = {fragment.file for fragment in group.fragments}
    exact = group.duplicate_type == DuplicateType.EXACT

    if len(files) == 1:
        return {
            "provenance": "same_file",
            "actionability": "refactor",
            "reason": "duplicate implementations in one file",
        }
    if exact and _contains_source_output_pair(paths):
        return {
            "provenance": "generated_copy",
            "actionability": "generated",
            "reason": "source file is copied to a published/build location",
        }
    if exact and _contains_nested_mirror_pair(paths):
        return {
            "provenance": "deployment_mirror",
            "actionability": "generated",
            "reason": "one location mirrors the complete path of another deployment",
        }
    basenames = {path[-1] for path in paths if path}
    if exact and len(basenames) == 1 and any(
        _PUBLISHED_SEGMENTS.intersection(path) for path in paths
    ):
        return {
            "provenance": "published_copy",
            "actionability": "generated",
            "reason": "identical asset appears in a published/static location",
        }
    if _same_relative_path_across_roots(paths):
        return {
            "provenance": "platform_variant",
            "actionability": "review",
            "reason": "parallel components contain the same relative source path",
        }
    if _shared_family_prefix(roots):
        return {
            "provenance": "product_family",
            "actionability": "review",
            "reason": "duplicate spans sibling products from the same family",
        }
    if len(roots) <= 1:
        return {
            "provenance": "local_duplicate",
            "actionability": "refactor",
            "reason": "duplicate stays within one component",
        }
    return {
        "provenance": "cross_component",
        "actionability": "review",
        "reason": "duplicate crosses independently owned components",
    }


def classify_duplicate_groups(groups: list[DuplicateGroup]) -> list[DuplicateGroup]:
    """Attach provenance metadata without replacing detector-specific evidence."""
    for group in groups:
        group.metadata.update(classify_duplicate_group(group))
    return groups


__all__ = ["classify_duplicate_group", "classify_duplicate_groups"]
