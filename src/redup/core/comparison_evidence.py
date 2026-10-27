"""Source observations for the existing comparator; no ranking or ticket effects."""

from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from pathlib import Path

from redup.core.scanner_types import CodeBlock, ScannedFile

SCHEMA = "redup.comparison-evidence/v1"
ORIGINS = {"authored", "generated_copy", "deployment_copy", "unknown"}


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def revision(root: Path) -> str | None:
    """Observe HEAD without interpreting it as the revision of dirty file content."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        value = result.stdout.strip()
        if result.returncode == 0 and len(value) in {40, 64}:
            return value if all(c in "0123456789abcdef" for c in value) else None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def source_observation(
    root: Path,
    files: list[ScannedFile],
    blocks: list[CodeBlock],
    before_revision: str | None,
    origins: dict[str, str] | None = None,
) -> dict:
    """Bind scanned text to file bytes only when their decoded lines agree.

    Origins are explicit caller declarations keyed by relative source path.
    A filename, common function name or similarity score cannot prove provenance.
    Git identity enrichment belongs to the caller (for example Diagit).
    """
    origins = origins or {}
    if any(
        value not in ORIGINS or Path(key).is_absolute() or ".." in Path(key).parts
        for key, value in origins.items()
    ):
        raise ValueError("source origins require relative paths and a supported origin")
    observed_files = {}
    for scanned in files:
        path = root / scanned.path
        try:
            relative = path.resolve().relative_to(root).as_posix()
        except ValueError:
            continue  # An external symlink is not evidence owned by this root.
        row = {
            "scan_content_sha256": _digest("\n".join(scanned.lines)),
            "file_sha256": None,
            "freshness": "unknown",
            "origin": origins.get(relative, "unknown"),
            "origin_evidence": "caller_declaration" if relative in origins else "unknown",
        }
        try:
            raw = path.read_bytes()
            if raw.decode("utf-8", errors="replace").splitlines() == scanned.lines:
                row.update(file_sha256=hashlib.sha256(raw).hexdigest(), freshness="current")
            else:
                row["freshness"] = "stale"
        except OSError:
            pass
        observed_files[relative] = row
    after_revision = revision(root)
    return {
        "root": str(root),
        "identity": root.as_uri(),
        "identity_evidence": "local_checkout_path",
        "observed_head": before_revision,
        "revision_binding": "observed_head_only",
        "revision_freshness": (
            "unknown"
            if before_revision is None
            else "current"
            if before_revision == after_revision
            else "stale"
        ),
        "files": observed_files,
        "blocks": {
            json.dumps([b.file, b.line_start, b.line_end, b.function_name or ""]): _digest(b.text)
            for b in blocks
        },
        "coverage": {
            "files_scanned": len(files),
            "files_bound": sum(x["freshness"] == "current" for x in observed_files.values()),
            "blocks_compared": len(blocks),
            "scope": "selected_files_and_blocks",
            "behavioral_tests": "unknown",
            "runtime_verification": "unknown",
        },
    }


def _fresh_source(source: dict) -> dict:
    result = deepcopy(source)
    root = Path(source["root"])
    if source["observed_head"] is not None and revision(root) != source["observed_head"]:
        result["revision_freshness"] = "stale"
    for relative, row in result["files"].items():
        if row["freshness"] != "current":
            continue  # Never upgrade an unbound or stale scan during serialization.
        path = root / relative
        try:
            if (
                not path.resolve().is_relative_to(root)
                or hashlib.sha256(path.read_bytes()).hexdigest() != row["file_sha256"]
            ):
                row["freshness"] = "stale"
        except OSError:
            row["freshness"] = "unknown"
    result["coverage"]["files_current"] = sum(
        row["freshness"] == "current" for row in result["files"].values()
    )
    return result


def candidate_projection(comparison, *, max_candidates: int | None = None) -> dict:
    """Serialize hash-bound candidates, keeping similarity separate from quality."""
    sources = {side: _fresh_source(s) for side, s in comparison.sources.items()}
    candidates = {}
    for match in comparison.matches + comparison.intent_matches:
        endpoints = []
        for side in ("a", "b"):
            source = sources.get(side, {})
            file = getattr(match, "file_" + side)
            lines = getattr(match, "lines_" + side)
            function = getattr(match, "function_" + side)
            try:
                relative = Path(file).resolve().relative_to(Path(source["root"])).as_posix()
            except (KeyError, ValueError):
                relative = None
            row = source.get("files", {}).get(relative, {})
            block_hash = source.get("blocks", {}).get(json.dumps([file, *lines, function]))
            endpoints.append(
                {
                    "repository": source.get("identity"),
                    "file": relative,
                    "function": function,
                    "lines": list(lines),
                    "block_sha256": block_hash,
                    "file_sha256": row.get("file_sha256"),
                    "observed_head": source.get("observed_head"),
                    "freshness": row.get("freshness", "unknown"),
                    "origin": row.get("origin", "unknown"),
                    "origin_evidence": row.get("origin_evidence", "unknown"),
                }
            )
        identity = [
            [
                x["repository"],
                x["file"] or getattr(match, "file_" + side),
                x["function"],
                x["lines"],
                x["block_sha256"],
            ]
            for side, x in zip(("a", "b"), endpoints, strict=True)
        ]
        candidate_id = _digest(json.dumps(sorted(identity, key=repr), separators=(",", ":")))
        # A legacy hand-built comparison has no snapshot and cannot claim a stable identity.
        bound = all(x["repository"] and x["file"] and x["block_sha256"] for x in endpoints)
        key = (candidate_id, match.similarity_type)
        previous = candidates.get(key, {})
        candidates[key] = {
            "id": candidate_id if bound else None,
            "source_a": endpoints[0],
            "source_b": endpoints[1],
            "similarity_type": match.similarity_type,
            "similarity": max(match.similarity, previous.get("similarity", 0.0)),
            "intent_evidence": {"semantic": "inferred", "intent": "declared"}.get(
                match.similarity_type, "unknown"
            ),
            "intent_contracts": sorted(
                set(match.intent_contracts) | set(previous.get("intent_contracts", []))
            ),
            "semantic_equivalence": "unknown",
            "quality_winner": None,
            "usable_source_evidence": bound
            and all(x["freshness"] == "current" for x in endpoints)
            and all(s["revision_freshness"] != "stale" for s in sources.values()),
        }
    for source in sources.values():
        source.pop("blocks", None)
    ordered = [candidates[k] for k in sorted(candidates)]
    selected = ordered[:max_candidates] if max_candidates else ordered
    return {
        "schema": SCHEMA,
        "analyzer": "redup/comparison-evidence-v1",
        "authority": "advisory_only",
        "sources": sources,
        "analysis": dict(comparison.analysis_status),
        "candidates": selected,
        "selection": {
            "total_candidates": len(ordered),
            "returned_candidates": len(selected),
            "truncated": len(selected) < len(ordered),
        },
        "quality_winner": None,
    }
