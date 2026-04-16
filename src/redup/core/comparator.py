"""Cross-project comparison using reDUP as engine.

Scans two project roots independently, then cross-matches their code blocks
using hash, LSH, and (optionally) semantic similarity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from redup.core.hasher import hash_block_structural, HashedBlock, _hashed_block
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


@dataclass
class CrossProjectComparison:
    """Full comparison result between two projects."""

    project_a: Path
    project_b: Path
    matches: list[CrossProjectMatch] = field(default_factory=list)
    stats_a: dict = field(default_factory=dict)
    stats_b: dict = field(default_factory=dict)

    @property
    def total_matches(self) -> int:
        return len(self.matches)

    @property
    def shared_loc_potential(self) -> int:
        """Lines that could be saved by extracting shared code."""
        return sum(
            max(m.lines_a[1] - m.lines_a[0], m.lines_b[1] - m.lines_b[0])
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
) -> CrossProjectComparison:
    """Compare two projects using reDUP's scan engine.

    Args:
        project_a: Root of first project.
        project_b: Root of second project.
        similarity_threshold: Minimum similarity for LSH / semantic matches.
        use_semantic: Enable (slow) semantic tier via CodeBERT.
        extensions: File extensions to scan (default: [".py"]).
        min_lines: Minimum block line count.
        functions_only: Only compare function-level blocks.

    Returns:
        CrossProjectComparison with all matches and per-project stats.
    """
    exts = extensions or [".py"]

    # Scan each project independently using reDUP
    blocks_a, stats_a = _scan_project_blocks(project_a, exts, min_lines, functions_only)
    blocks_b, stats_b = _scan_project_blocks(project_b, exts, min_lines, functions_only)

    proj_a_str = str(project_a)
    proj_b_str = str(project_b)

    matches: list[CrossProjectMatch] = []

    # Tier 1: structural hash matches (fast, O(n+m))
    matches.extend(_find_hash_matches(blocks_a, blocks_b, proj_a_str, proj_b_str))

    # Deduplicate seen pairs so LSH doesn't re-report them
    seen_pairs = {
        (m.file_a, m.lines_a, m.file_b, m.lines_b) for m in matches
    }

    # Tier 2: LSH near-duplicates
    lsh_matches = _find_lsh_matches(
        blocks_a, blocks_b, similarity_threshold, proj_a_str, proj_b_str,
    )
    for m in lsh_matches:
        key = (m.file_a, m.lines_a, m.file_b, m.lines_b)
        if key not in seen_pairs:
            matches.append(m)
            seen_pairs.add(key)

    # Tier 3: semantic (optional, slow)
    if use_semantic:
        sem_matches = _find_semantic_matches(
            blocks_a, blocks_b, similarity_threshold, proj_a_str, proj_b_str,
        )
        for m in sem_matches:
            key = (m.file_a, m.lines_a, m.file_b, m.lines_b)
            if key not in seen_pairs:
                matches.append(m)
                seen_pairs.add(key)

    return CrossProjectComparison(
        project_a=project_a,
        project_b=project_b,
        matches=matches,
        stats_a={"files": stats_a.files_scanned, "lines": stats_a.total_lines},
        stats_b={"files": stats_b.files_scanned, "lines": stats_b.total_lines},
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _scan_project_blocks(
    root: Path,
    extensions: list[str],
    min_lines: int,
    functions_only: bool,
) -> tuple[list[CodeBlock], object]:
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
            blocks.append(block)

    return blocks, stats


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
            matches.append(CrossProjectMatch(
                project_a=proj_a,
                project_b=proj_b,
                file_a=block_a.file,
                file_b=block_b.file,
                function_a=block_a.function_name or "",
                function_b=block_b.function_name or "",
                similarity=1.0,
                similarity_type="structural",
                lines_a=(block_a.line_start, block_a.line_end),
                lines_b=(block_b.line_start, block_b.line_end),
            ))
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
            matches.append(CrossProjectMatch(
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
            ))
    return matches


def _find_semantic_matches(
    blocks_a: list[CodeBlock],
    blocks_b: list[CodeBlock],
    threshold: float,
    proj_a: str,
    proj_b: str,
) -> list[CrossProjectMatch]:
    """Find semantically similar functions cross-project."""
    try:
        from redup.core.semantic import SemanticDetector
    except ImportError:
        return []

    detector = SemanticDetector(threshold=threshold)
    all_blocks = blocks_a + blocks_b
    if len(all_blocks) < 2:
        return []

    try:
        semantic_matches = detector.find_semantic_duplicates_fast(all_blocks)
    except Exception:
        return []

    a_files = {block.file for block in blocks_a}
    b_files = {block.file for block in blocks_b}

    cross: list[CrossProjectMatch] = []
    for m in semantic_matches:
        is_cross = (
            (m.block_a.file in a_files and m.block_b.file in b_files) or
            (m.block_a.file in b_files and m.block_b.file in a_files)
        )
        if not is_cross:
            continue

        # Normalize order so project_a is always first
        if m.block_a.file in a_files:
            ba, bb = m.block_a, m.block_b
        else:
            ba, bb = m.block_b, m.block_a

        cross.append(CrossProjectMatch(
            project_a=proj_a,
            project_b=proj_b,
            file_a=ba.file,
            file_b=bb.file,
            function_a=ba.function_name or "",
            function_b=bb.function_name or "",
            similarity=m.similarity,
            similarity_type="semantic",
            lines_a=(ba.line_start, ba.line_end),
            lines_b=(bb.line_start, bb.line_end),
        ))
    return cross
