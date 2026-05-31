"""Intract policy checks for reDUP CLI and scan gates."""

from __future__ import annotations

from pathlib import Path

from redup.core.models import ScanConfig
from redup.core.scanner_types import CodeBlock

from .adapter import _resolve_manifest_path, detect_intent_duplicates


def intent_groups_from_dup_map(dup_map) -> list[dict]:
    from redup.core.models import DuplicateType

    payload: list[dict] = []
    for group in getattr(dup_map, "groups", []) or []:
        if group.duplicate_type != DuplicateType.INTENT:
            continue
        payload.append(
            {
                "group_id": group.id,
                "similarity": group.similarity_score,
                "evidence": group.metadata.get("evidence", {}),
                "metadata": group.metadata,
            }
        )
    return payload


def resolve_intract_policy(config: ScanConfig, *, fail_on: list[str] | None = None, warn_on: list[str] | None = None):
    from intract.integrations.redup import parse_policy_tokens

    resolved_fail_on = fail_on or parse_policy_tokens(getattr(config, "intent_fail_on", None))
    resolved_warn_on = warn_on or parse_policy_tokens(getattr(config, "intent_warn_on", None))
    if not resolved_fail_on:
        resolved_fail_on = ["violation", "missing_required_p1", "invalid_manifest"]
    if not resolved_warn_on:
        resolved_warn_on = ["partial", "unknown"]
    return resolved_fail_on, resolved_warn_on


def run_intract_policy_check(
    root: Path,
    config: ScanConfig,
    *,
    blocks: list[CodeBlock] | None = None,
    fail_on: list[str] | None = None,
    warn_on: list[str] | None = None,
):
    from intract.integrations.redup import validate_for_redup

    intent_groups: list[dict] = []
    if config.intent_enabled or blocks is not None:
        scan_blocks = blocks or []
        if config.intent_enabled and scan_blocks:
            groups = detect_intent_duplicates(scan_blocks, config)
            intent_groups = [
                {
                    "group_id": group.id,
                    "similarity": group.similarity_score,
                    "evidence": group.metadata.get("evidence", {}),
                    "metadata": group.metadata,
                }
                for group in groups
            ]

    resolved_fail_on, resolved_warn_on = resolve_intract_policy(
        config,
        fail_on=fail_on,
        warn_on=warn_on,
    )
    manifest = _resolve_manifest_path(config)
    return validate_for_redup(
        root,
        manifest=manifest,
        intent_groups=intent_groups,
        fail_on=resolved_fail_on,
        warn_on=resolved_warn_on,
    )
