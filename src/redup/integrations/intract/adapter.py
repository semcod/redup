"""Intract intent duplicate detection adapter for reDUP."""

from __future__ import annotations

from pathlib import Path

from redup.core.models import DuplicateFragment, DuplicateGroup, DuplicateType, ScanConfig
from redup.core.scanner_types import CodeBlock


def _block_text_for(blocks: list[CodeBlock], file_path: str, start_line: int) -> str:
    for block in blocks:
        if block.file == file_path and block.line_start <= start_line <= block.line_end:
            return block.text
    return ""


def _resolve_manifest_path(config: ScanConfig) -> str | None:
    if config.intent_manifest_path:
        path = config.intent_manifest_path
        if not path.is_absolute():
            path = config.root / path
        return str(path) if path.exists() else None

    for candidate in ("intent.yaml", "intract.yaml", ".intract.yaml"):
        path = config.root / candidate
        if path.exists():
            return str(path)
    return None


def detect_intent_duplicates(blocks: list[CodeBlock], config: ScanConfig) -> list[DuplicateGroup]:
    if not config.intent_enabled:
        return []

    try:
        from intract.integrations.redup import find_intent_duplicate_groups
    except ImportError as exc:
        raise RuntimeError(
            "Intent duplicate detection requires installing reDUP with the intent extra: "
            "pip install 'redup[intent]'"
        ) from exc

    raw_groups = find_intent_duplicate_groups(
        blocks=blocks,
        manifest_path=_resolve_manifest_path(config),
        threshold=config.intent_threshold,
    )

    groups: list[DuplicateGroup] = []
    for item in raw_groups:
        fragments: list[DuplicateFragment] = []
        for frag in item.get("fragments", []):
            file_path = str(frag.get("file_path", ""))
            start_line = int(frag.get("start_line", 1))
            end_line = int(frag.get("end_line", start_line))
            fragments.append(
                DuplicateFragment(
                    file=file_path,
                    line_start=start_line,
                    line_end=end_line,
                    text=_block_text_for(blocks, file_path, start_line),
                )
            )

        if len(fragments) < 2:
            continue

        evidence = item.get("evidence", {})
        contracts = evidence.get("contracts", [])
        metadata = dict(item.get("metadata", {}))
        metadata["evidence"] = evidence
        metadata["engine"] = "intract"

        groups.append(
            DuplicateGroup(
                id=str(item.get("group_id", f"I{len(groups) + 1:04d}")),
                duplicate_type=DuplicateType.INTENT,
                fragments=fragments,
                similarity_score=float(item.get("similarity", 0.0)),
                normalized_hash=f"intent:{item.get('group_id', len(groups) + 1)}",
                normalized_name=contracts[0] if contracts else "intent_duplicate",
                metadata=metadata,
            )
        )

    return groups
