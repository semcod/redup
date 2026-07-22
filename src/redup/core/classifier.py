"""Classify duplicate provenance before proposing refactors."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from redup.core.models import DuplicateGroup, DuplicateType

_PUBLISHED_SEGMENTS = {"assets", "build", "dist", "httpdocs", "public", "static", "www"}
_COMPONENT_CONTAINERS = {"examples"}
_CONTROL_FLOW = re.compile(r"\b(?:case|catch|else|except|for|if|match|switch|try|while)\b")
_CALL = re.compile(r"\b([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*\(")
_FROM_IMPORT = re.compile(r"\bfrom\s+([A-Za-z_][\w.]*)\s+import\s+")
_TRIPLE_QUOTED = re.compile(r'(?s)(?:""".*?"""|\'\'\'.*?\'\'\')')


def _parts(path: str) -> tuple[str, ...]:
    return PurePosixPath(path.replace("\\", "/")).parts


def _without_segment(parts: tuple[str, ...], segment: str) -> tuple[str, ...]:
    try:
        index = parts.index(segment)
    except ValueError:
        return parts
    return parts[:index] + parts[index + 1 :]


def _component_root(parts: tuple[str, ...]) -> str:
    """Return the ownership root, accounting for umbrella example folders."""
    if len(parts) > 1 and parts[0] in _COMPONENT_CONTAINERS:
        return "/".join(parts[:2])
    return parts[0] if parts else ""


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


def _is_delegating_wrapper_group(group: DuplicateGroup) -> bool:
    """Recognize small public wrappers that intentionally share call structure.

    This check is deliberately conservative and language-neutral: every fragment
    must be short, have a distinct name, contain one return, avoid control flow,
    and delegate to at least one common callee.
    """
    if len(group.fragments) < 2 or any(not fragment.text for fragment in group.fragments):
        return False
    names = [fragment.function_name for fragment in group.fragments]
    if any(not name for name in names) or len(set(names)) != len(names):
        return False

    shared_calls: set[str] | None = None
    shared_imports: set[str] | None = None
    for fragment, name in zip(group.fragments, names, strict=True):
        implementation = _TRIPLE_QUOTED.sub("", fragment.text)
        if fragment.line_count > 20 or _CONTROL_FLOW.search(implementation):
            return False
        if len(re.findall(r"\breturn\b", implementation)) != 1:
            return False
        calls = set(_CALL.findall(implementation))
        calls.discard(name)
        shared_calls = calls if shared_calls is None else shared_calls & calls
        imports = set(_FROM_IMPORT.findall(implementation))
        shared_imports = imports if shared_imports is None else shared_imports & imports
    return bool(shared_calls or shared_imports)


def classify_duplicate_group(group: DuplicateGroup) -> dict[str, object]:
    """Return conservative provenance and actionability metadata for a group."""
    paths = [_parts(fragment.file) for fragment in group.fragments]
    roots = {_component_root(path) for path in paths if path}
    files = {fragment.file for fragment in group.fragments}
    exact = group.duplicate_type == DuplicateType.EXACT

    if len(files) == 1:
        if _is_delegating_wrapper_group(group):
            return {
                "provenance": "delegating_wrappers",
                "actionability": "review",
                "reason": "distinct public APIs intentionally share a thin delegation pattern",
            }
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
