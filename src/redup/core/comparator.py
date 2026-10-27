"""Cross-project comparison using reDUP as engine.

Scans two project roots independently, then cross-matches their code blocks
using hash, LSH, and (optionally) semantic similarity.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

from redup.core.comparison_evidence import revision, source_observation
from redup.core.hasher import hash_block, hash_block_structural
from redup.core.lsh_matcher import LSHIndex
from redup.core.models import ScanConfig
from redup.core.scanner import scan_project
from redup.core.scanner_models import CodeBlock, ScannedFile


@dataclass
class CrossProjectMatch:
    """A pair of similar functions from two different projects."""

    project_a: str
    project_b: str
    file_a: str
    file_b: str
    function_a: str
    function_b: str
    similarity: float
    similarity_type: str  # "exact" | "structural" | "lsh" | "semantic"
    lines_a: tuple[int, int]
    lines_b: tuple[int, int]
    intent_contracts: list[str] = field(default_factory=list)


@dataclass
class CrossProjectComparison:
    """Full comparison result between two projects."""

    project_a: Path
    project_b: Path
    matches: list[CrossProjectMatch] = field(default_factory=list)
    stats_a: dict = field(default_factory=dict)
    stats_b: dict = field(default_factory=dict)
    sources: dict = field(default_factory=dict)
    analysis_status: dict = field(default_factory=dict)
    intent_matches: list[CrossProjectMatch] = field(default_factory=list)

    @property
    def total_matches(self) -> int:
        return len(self.matches)

    @property
    def shared_loc_potential(self) -> int:
        """Lines that could be saved by extracting shared code."""
        return sum(
            max(
                m.lines_a[1] - m.lines_a[0] + 1,
                m.lines_b[1] - m.lines_b[0] + 1,
            )
            for m in self.matches
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compare_projects(
    project_a: Path,
    project_b: Path,
    similarity_threshold: float = 0.75,
    use_semantic: bool = False,
    extensions: list[str] | None = None,
    min_lines: int = 3,
    functions_only: bool = True,
    *,
    origins_a: dict[str, str] | None = None,
    origins_b: dict[str, str] | None = None,
    use_intent: bool = False,
) -> CrossProjectComparison:
    """Compare two projects using reDUP's scan engine.

    Args:
        project_a: Root of first project.
        project_b: Root of second project.
        similarity_threshold: Minimum similarity for LSH / semantic matches.
        use_semantic: Enable the slower intent-profile embedding tier.
        extensions: File extensions to scan (default: [".py"]).
        min_lines: Minimum block line count.
        functions_only: Only compare function-level blocks.
        origins_a: Explicit source-origin declarations keyed by relative file path.
        origins_b: Corresponding declarations for the second project. Unknown by default.
        use_intent: Match inline declarations through optional Intract, separately from LOC.

    Returns:
        CrossProjectComparison with all matches and per-project stats.
    """
    exts = extensions or [".py"]
    project_a, project_b = project_a.expanduser().resolve(), project_b.expanduser().resolve()
    head_a, head_b = revision(project_a), revision(project_b)

    # Scan each project independently using reDUP
    blocks_a, stats_a, files_a = _scan_project_blocks(project_a, exts, min_lines, functions_only)
    blocks_b, stats_b, files_b = _scan_project_blocks(project_b, exts, min_lines, functions_only)
    sources = {
        "a": source_observation(project_a, files_a, blocks_a, head_a, origins_a),
        "b": source_observation(project_b, files_b, blocks_b, head_b, origins_b),
    }
    semantic_status = {"status": "not_requested"}
    intent_status = {"status": "not_requested", "scope": "inline_scanned_blocks"}

    proj_a_str = str(project_a)
    proj_b_str = str(project_b)

    matches: list[CrossProjectMatch] = []

    # Tier 1: structural hash matches (fast, O(n+m))
    matches.extend(_find_hash_matches(blocks_a, blocks_b, proj_a_str, proj_b_str))

    # Deduplicate seen pairs so LSH doesn't re-report them
    seen_pairs = {(m.file_a, m.lines_a, m.file_b, m.lines_b) for m in matches}

    # Tier 2: LSH near-duplicates
    lsh_matches = _find_lsh_matches(
        blocks_a,
        blocks_b,
        similarity_threshold,
        proj_a_str,
        proj_b_str,
    )
    for m in lsh_matches:
        key = (m.file_a, m.lines_a, m.file_b, m.lines_b)
        if key not in seen_pairs:
            matches.append(m)
            seen_pairs.add(key)

    # Tier 3: semantic (optional, slow)
    if use_semantic:
        sem_matches = _find_semantic_matches(
            blocks_a,
            blocks_b,
            similarity_threshold,
            proj_a_str,
            proj_b_str,
            diagnostics=semantic_status,
        )
        for m in sem_matches:
            key = (m.file_a, m.lines_a, m.file_b, m.lines_b)
            if key not in seen_pairs:
                matches.append(m)
                seen_pairs.add(key)

    intent_matches = (
        _find_intent_matches(
            blocks_a, blocks_b, similarity_threshold, proj_a_str, proj_b_str, intent_status
        )
        if use_intent
        else []
    )
    return CrossProjectComparison(
        project_a=project_a,
        project_b=project_b,
        matches=matches,
        stats_a={"files": stats_a.files_scanned, "lines": stats_a.total_lines},
        stats_b={"files": stats_b.files_scanned, "lines": stats_b.total_lines},
        sources=sources,
        intent_matches=intent_matches,
        analysis_status={
            "semantic": semantic_status,
            "declared_intent": intent_status,
            "configuration": {
                "extensions": exts,
                "min_lines": min_lines,
                "functions_only": functions_only,
                "similarity_threshold": similarity_threshold,
            },
        },
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _scan_project_blocks(
    root: Path,
    extensions: list[str],
    min_lines: int,
    functions_only: bool,
) -> tuple[list[CodeBlock], object, list[ScannedFile]]:
    """Scan a single project and return all code blocks + stats."""
    config = ScanConfig(
        root=root,
        extensions=extensions,
        min_block_lines=min_lines,
        functions_only=functions_only,
    )
    scanned_files, stats = scan_project(config, function_level_only=functions_only)

    blocks: list[CodeBlock] = []
    for sf in scanned_files:
        for block in sf.blocks:
            if functions_only and block.function_name is None:
                continue
            # Scanner paths are relative to each root. Qualify before cross-project
            # matching so a/code.py and b/code.py cannot collapse to one file.
            blocks.append(replace(block, file=str(root / block.file)))

    return blocks, stats, scanned_files


def _find_hash_matches(
    blocks_a: list[CodeBlock],
    blocks_b: list[CodeBlock],
    proj_a: str,
    proj_b: str,
) -> list[CrossProjectMatch]:
    """Find exact / structural hash matches cross-project."""
    # Index project A by structural hash
    index: dict[str, list[CodeBlock]] = {}
    for block in blocks_a:
        h = hash_block_structural(block.text)
        index.setdefault(h, []).append(block)

    matches: list[CrossProjectMatch] = []
    for block_b in blocks_b:
        h = hash_block_structural(block_b.text)
        for block_a in index.get(h, []):
            similarity_type = (
                "exact" if hash_block(block_a.text) == hash_block(block_b.text) else "structural"
            )
            matches.append(
                CrossProjectMatch(
                    project_a=proj_a,
                    project_b=proj_b,
                    file_a=block_a.file,
                    file_b=block_b.file,
                    function_a=block_a.function_name or "",
                    function_b=block_b.function_name or "",
                    similarity=1.0,
                    similarity_type=similarity_type,
                    lines_a=(block_a.line_start, block_a.line_end),
                    lines_b=(block_b.line_start, block_b.line_end),
                )
            )
    return matches


def _find_lsh_matches(
    blocks_a: list[CodeBlock],
    blocks_b: list[CodeBlock],
    threshold: float,
    proj_a: str,
    proj_b: str,
) -> list[CrossProjectMatch]:
    """Find LSH near-duplicate matches cross-project."""
    if not blocks_a or not blocks_b:
        return []

    # Build LSH index from project A blocks
    lsh = LSHIndex(threshold=threshold)
    for block in blocks_a:
        lsh.add(block)

    # Query each project B block against the index
    matches: list[CrossProjectMatch] = []
    for block_b in blocks_b:
        near = lsh.find_near_duplicates(block_b)
        for block_a, sim in near:
            matches.append(
                CrossProjectMatch(
                    project_a=proj_a,
                    project_b=proj_b,
                    file_a=block_a.file,
                    file_b=block_b.file,
                    function_a=block_a.function_name or "",
                    function_b=block_b.function_name or "",
                    similarity=sim,
                    similarity_type="lsh",
                    lines_a=(block_a.line_start, block_a.line_end),
                    lines_b=(block_b.line_start, block_b.line_end),
                )
            )
    return matches


def _is_cross_project_match(match, a_files: set[str], b_files: set[str]) -> bool:
    """Check if a semantic match spans both projects."""
    return (match.block_a.file in a_files and match.block_b.file in b_files) or (
        match.block_a.file in b_files and match.block_b.file in a_files
    )


def _normalize_match_order(match, a_files: set[str]) -> tuple[CodeBlock, CodeBlock]:
    """Normalize block order so project_a block is always first."""
    if match.block_a.file in a_files:
        return match.block_a, match.block_b
    return match.block_b, match.block_a


def _create_cross_project_match(
    block_a: CodeBlock,
    block_b: CodeBlock,
    similarity: float,
    proj_a: str,
    proj_b: str,
) -> CrossProjectMatch:
    """Create a CrossProjectMatch from normalized blocks."""
    return CrossProjectMatch(
        project_a=proj_a,
        project_b=proj_b,
        file_a=block_a.file,
        file_b=block_b.file,
        function_a=block_a.function_name or "",
        function_b=block_b.function_name or "",
        similarity=similarity,
        similarity_type="semantic",
        lines_a=(block_a.line_start, block_a.line_end),
        lines_b=(block_b.line_start, block_b.line_end),
    )


def _find_semantic_matches(
    blocks_a: list[CodeBlock],
    blocks_b: list[CodeBlock],
    threshold: float,
    proj_a: str,
    proj_b: str,
    *,
    diagnostics: dict | None = None,
) -> list[CrossProjectMatch]:
    """Find semantically similar functions cross-project."""
    diagnostics = diagnostics if diagnostics is not None else {}
    try:
        from redup.core.semantic import SemanticDetector
    except ImportError:
        diagnostics.update(status="unavailable", reason="optional_dependency_missing")
        return []

    all_blocks = blocks_a + blocks_b
    if len(all_blocks) < 2:
        diagnostics.update(status="insufficient_blocks")
        return []

    try:
        detector = SemanticDetector(threshold=threshold)
        semantic_matches = detector.find_semantic_duplicates_fast(all_blocks)
    except Exception:
        diagnostics.update(status="unavailable", reason="semantic_analysis_failed")
        return []
    diagnostics.update(status="evaluated")

    a_files = {block.file for block in blocks_a}
    b_files = {block.file for block in blocks_b}

    cross: list[CrossProjectMatch] = []
    for m in semantic_matches:
        if not _is_cross_project_match(m, a_files, b_files):
            continue

        ba, bb = _normalize_match_order(m, a_files)
        cross.append(_create_cross_project_match(ba, bb, m.similarity, proj_a, proj_b))

    return cross


def _find_intent_matches(blocks_a, blocks_b, threshold, proj_a, proj_b, diagnostics):
    """Delegate parsing and matching to Intract; never infer a declaration from code."""
    try:
        from intract.integrations.redup import BlockAdapter, find_intent_duplicate_groups
    except ImportError:
        diagnostics.update(status="unavailable", reason="optional_dependency_missing")
        return []
    try:
        groups = find_intent_duplicate_groups(
            blocks=[
                BlockAdapter(b.text, b.file, b.line_start, b.line_end) for b in blocks_a + blocks_b
            ],
            threshold=threshold,
        )
    except Exception:
        diagnostics.update(status="unavailable", reason="intent_analysis_failed")
        return []
    diagnostics.update(status="evaluated", engine="intract")
    by_side = [
        {(b.file, b.line_start, b.line_end): b for b in blocks} for blocks in (blocks_a, blocks_b)
    ]
    matches = []
    for group in groups:
        fragments = {
            (f.get("file_path"), f.get("start_line"), f.get("end_line"))
            for f in group.get("fragments", [])
        }
        for key_a in sorted(fragments & by_side[0].keys()):
            for key_b in sorted(fragments & by_side[1].keys()):
                a, b = by_side[0][key_a], by_side[1][key_b]
                matches.append(
                    CrossProjectMatch(
                        project_a=proj_a,
                        project_b=proj_b,
                        file_a=a.file,
                        file_b=b.file,
                        function_a=a.function_name or "",
                        function_b=b.function_name or "",
                        lines_a=(a.line_start, a.line_end),
                        lines_b=(b.line_start, b.line_end),
                        similarity=group.get("similarity", 0.0),
                        similarity_type="intent",
                        intent_contracts=sorted(group.get("evidence", {}).get("contracts", [])),
                    )
                )
    return matches
