"""Duplicate finding phases: exact, structural, near-duplicate, semantic."""

from __future__ import annotations

import hashlib
import re
import time
from collections import defaultdict
from pathlib import Path

from redup.core.cache import HashCache, build_hash_index_with_cache
from redup.core.hasher import (
    HashIndex,
    build_hash_index,
    find_exact_duplicates,
    find_structural_duplicates,
)
from redup.core.lsh_matcher import find_near_duplicates
from redup.core.matcher import refine_structural_matches
from redup.core.models import DuplicateFragment, DuplicateGroup, DuplicateType, ScanConfig
from redup.core.scanner_types import CodeBlock

_FUZZY_KEYWORDS = {
    "and",
    "as",
    "async",
    "await",
    "break",
    "case",
    "catch",
    "class",
    "const",
    "continue",
    "def",
    "do",
    "else",
    "except",
    "false",
    "finally",
    "for",
    "foreach",
    "from",
    "function",
    "if",
    "import",
    "in",
    "let",
    "match",
    "new",
    "none",
    "not",
    "null",
    "or",
    "pass",
    "raise",
    "return",
    "switch",
    "throw",
    "true",
    "try",
    "var",
    "while",
    "with",
    "yield",
}
_FUZZY_TOKEN_RE = re.compile(
    r"[A-Za-z_$][A-Za-z0-9_$]*|==={0,1}|!==?|<=|>=|=>|\+\+|--|&&|\|\||\?\?|\S"
)


def _fuzzy_simhash(text: str) -> int:
    """Return a language-neutral SimHash used only to shortlist fuzzy comparisons."""
    text = re.sub(r"/\*.*?\*/|//[^\n]*|#[^\n]*", " ", text, flags=re.DOTALL)
    text = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', " STR ", text)
    text = re.sub(r"\b\d+(?:\.\d+)?\b", " NUM ", text)
    tokens = []
    for token in _FUZZY_TOKEN_RE.findall(text):
        lowered = token.lower()
        if re.match(r"^[A-Za-z_$]", token) and lowered not in _FUZZY_KEYWORDS:
            tokens.append("ID")
        else:
            tokens.append(lowered)

    width = 3 if len(tokens) >= 3 else 1
    features = ["\x1f".join(tokens[i : i + width]) for i in range(len(tokens) - width + 1)]
    if not features:
        return 0

    weights = [0] * 64
    for feature in features:
        value = int.from_bytes(
            hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest(), "big"
        )
        for bit in range(64):
            weights[bit] += 1 if value & (1 << bit) else -1
    return sum(1 << bit for bit, weight in enumerate(weights) if weight >= 0)


def _fuzzy_candidate_indices(candidates: list[CodeBlock]) -> dict[int, set[int]]:
    """Build bounded candidate sets using four SimHash bands instead of all pairs."""
    buckets: dict[tuple[str, int, int], list[int]] = defaultdict(list)
    band_hits: dict[tuple[int, int], int] = defaultdict(int)
    result: dict[int, set[int]] = defaultdict(set)

    for index, block in enumerate(candidates):
        fingerprint = _fuzzy_simhash(block.text)
        language = Path(block.file).suffix.lower()
        for band in range(4):
            key = (language, band, (fingerprint >> (band * 16)) & 0xFFFF)
            for other_index in buckets[key]:
                if abs(candidates[other_index].line_count - block.line_count) <= 4:
                    band_hits[(other_index, index)] += 1
            buckets[key].append(index)

    # One matching 16-bit band produces too many random candidates in large
    # repositories. Near-identical source normally shares at least two bands.
    for (left, right), matching_bands in band_hits.items():
        if matching_bands >= 2:
            result[left].add(right)

    return result


def find_fuzzy_groups(
    all_blocks: list[CodeBlock],
    config: ScanConfig,
    covered_locations: set[tuple[str, int]] | None = None,
) -> list[DuplicateGroup]:
    """Find high-similarity function pairs missed by exact/structural hashing."""
    from redup.core.matcher import sequence_similarity

    covered = set(covered_locations or ())
    min_lines = config.min_block_lines
    min_similarity = config.fuzzy_threshold

    candidates = [
        block
        for block in all_blocks
        if block.function_name
        and block.line_count >= min_lines
        and (block.file, block.line_start) not in covered
    ]
    if len(candidates) < 2:
        return []

    candidates.sort(key=lambda block: (block.line_count, block.file, block.line_start))
    candidate_indices = _fuzzy_candidate_indices(candidates)
    used: set[tuple[str, int]] = set()
    groups: list[DuplicateGroup] = []

    for index, anchor in enumerate(candidates):
        anchor_key = (anchor.file, anchor.line_start)
        if anchor_key in used:
            continue

        cluster = [anchor]
        for other_index in sorted(candidate_indices.get(index, ())):
            other = candidates[other_index]
            other_key = (other.file, other.line_start)
            if other_key in used:
                continue
            if other.file == anchor.file and other.line_start == anchor.line_start:
                continue
            if other.file == anchor.file and not (
                other.line_end < anchor.line_start or other.line_start > anchor.line_end
            ):
                continue
            similarity = sequence_similarity(anchor.text, other.text)
            if similarity < min_similarity:
                continue
            cluster.append(other)

        if len(cluster) < 2:
            continue

        fragments = [
            DuplicateFragment(
                file=block.file,
                line_start=block.line_start,
                line_end=block.line_end,
                text=block.text,
                function_name=block.function_name,
                class_name=block.class_name,
            )
            for block in cluster
        ]
        avg_similarity = sum(
            sequence_similarity(cluster[0].text, block.text) for block in cluster[1:]
        ) / (len(cluster) - 1)

        groups.append(
            DuplicateGroup(
                id=f"F{len(groups) + 1:04d}",
                duplicate_type=DuplicateType.FUZZY,
                fragments=fragments,
                similarity_score=avg_similarity,
                normalized_hash=f"fuzzy_{anchor.file}_{anchor.line_start}",
                normalized_name=anchor.function_name,
            )
        )
        for block in cluster:
            used.add((block.file, block.line_start))

    return groups


def _covered_locations(groups: list[DuplicateGroup]) -> set[tuple[str, int]]:
    """Collect file/line locations already assigned to duplicate groups."""
    covered: set[tuple[str, int]] = set()
    for group in groups:
        for fragment in group.fragments:
            covered.add((fragment.file, fragment.line_start))
    return covered


def _finalize_duplicate_groups(
    groups: list[DuplicateGroup],
    all_blocks: list[CodeBlock],
    config: ScanConfig,
    start_time: float,
    cache: HashCache | None = None,
) -> list[DuplicateGroup]:
    """Attach near duplicates, sort by impact, and report timing."""
    covered = _covered_locations(groups)
    if config.fuzzy_enabled:
        groups.extend(find_fuzzy_groups(all_blocks, config, covered))
    groups.extend(find_near_duplicate_groups(all_blocks, config))
    if getattr(config, "semantic_enabled", False):
        groups.extend(
            find_semantic_groups(
                all_blocks,
                threshold=config.semantic_threshold,
                model_name=config.semantic_model,
            )
        )
    if getattr(config, "intent_enabled", False):
        groups.extend(find_intent_groups(all_blocks, config))
    groups.sort(key=lambda g: g.impact_score, reverse=True)

    processing_time = (time.time() - start_time) * 1000
    message = f"Duplicate finding completed in {processing_time:.1f}ms"
    if cache is not None:
        cache_stats = cache.get_stats()
        message += f" (cache: {cache_stats.get('cached_files', 0)} files)"
    print(message)

    return groups


def find_exact_groups(index: HashIndex) -> list[DuplicateGroup]:
    """Find exact duplicate groups."""
    from redup.core.pipeline.groups import blocks_to_group

    groups: list[DuplicateGroup] = []
    exact_groups = find_exact_duplicates(index)

    for i, (h, blocks) in enumerate(exact_groups.items(), 1):
        func_blocks = [b for b in blocks if b.block.function_name]
        if len(func_blocks) >= 2:
            g = blocks_to_group(
                group_id=f"E{i:04d}",
                blocks=func_blocks,
                dup_type=DuplicateType.EXACT,
                normalized_hash=h,
            )
            if g.occurrences >= 2:
                groups.append(g)

    return groups


def find_structural_groups(
    index: HashIndex, exact_groups_list: list[DuplicateGroup]
) -> list[DuplicateGroup]:
    """Find structural duplicate groups."""
    from redup.core.pipeline.groups import (
        blocks_to_group,
        calculate_similarity,
        match_results_to_blocks,
    )

    groups: list[DuplicateGroup] = []
    exact_hashes: set[str] = set()
    for group in exact_groups_list:
        exact_hashes.add(group.normalized_hash)

    structural_groups = find_structural_duplicates(index)

    for i, (h, blocks) in enumerate(structural_groups.items(), 1):
        if h in exact_hashes:
            continue

        func_blocks = [b for b in blocks if b.block.function_name]
        if len(func_blocks) >= 2:
            refined = refine_structural_matches(func_blocks)
            refined_blocks = match_results_to_blocks(refined)
            if len(refined_blocks) >= 2:
                g = blocks_to_group(
                    group_id=f"S{i:04d}",
                    blocks=refined_blocks,
                    dup_type=DuplicateType.STRUCTURAL,
                    normalized_hash=h,
                    similarity=calculate_similarity(refined),
                )
                if g.occurrences >= 2:
                    groups.append(g)

    return groups


def find_near_duplicate_groups(
    all_blocks: list[CodeBlock], config: ScanConfig
) -> list[DuplicateGroup]:
    """Find near-duplicate groups using LSH."""
    groups: list[DuplicateGroup] = []

    # Check if LSH is enabled
    if not getattr(config, "lsh_enabled", True):
        return groups

    # Only use LSH for blocks larger than configured threshold
    lsh_min_lines = getattr(config, "lsh_min_lines", 50)
    lsh_threshold = getattr(config, "lsh_threshold", 0.8)

    # Filter blocks for LSH
    lsh_blocks = [b for b in all_blocks if b.line_count >= lsh_min_lines]

    if not lsh_blocks:
        return groups

    try:
        # Find near-duplicates
        near_dup_groups = find_near_duplicates(
            lsh_blocks, threshold=lsh_threshold, min_lines=lsh_min_lines
        )

        for i, (group_id, block_similarities) in enumerate(near_dup_groups.items(), 1):
            if len(block_similarities) < 2:
                continue

            # Convert to DuplicateGroup format
            fragments = []
            avg_similarity = 0.0

            for block, similarity in block_similarities:
                fragments.append(
                    DuplicateFragment(
                        file=block.file,
                        line_start=block.line_start,
                        line_end=block.line_end,
                        text=block.text,
                        function_name=block.function_name,
                        class_name=block.class_name,
                    )
                )
                avg_similarity += similarity

            if len(fragments) >= 2:
                avg_similarity /= len(fragments)

                # Use function name if available
                name = fragments[0].function_name if fragments[0].function_name else None

                group = DuplicateGroup(
                    id=f"L{i:04d}",
                    duplicate_type=DuplicateType.NEAR_DUPLICATE,
                    fragments=fragments,
                    similarity_score=avg_similarity,
                    normalized_hash=f"lsh_{group_id}",
                    normalized_name=name,
                )
                groups.append(group)

    except Exception:
        # Silently fail if LSH is not available or has issues
        pass

    return groups


def find_semantic_groups(
    blocks: list[CodeBlock],
    threshold: float = 0.80,
    model_name: str = "microsoft/codebert-base",
) -> list[DuplicateGroup]:
    """Tier 4: Semantic duplicate detection via embeddings."""
    try:
        from redup.core.semantic import SemanticDetector
    except ImportError:
        return []

    detector = SemanticDetector(model_name=model_name, threshold=threshold)

    # Only function-level blocks (skip sliding window noise)
    func_blocks = [b for b in blocks if b.function_name]
    if len(func_blocks) < 2:
        return []

    try:
        matches = detector.find_semantic_duplicates_fast(func_blocks)
    except ImportError as exc:
        print(f"⚠️  Semantic detection unavailable: {exc}")
        return []
    except Exception as exc:
        print(f"⚠️  Semantic detection failed: {exc}")
        return []

    adjacency: dict[tuple[str, int], set[tuple[str, int]]] = defaultdict(set)
    blocks_by_location: dict[tuple[str, int], CodeBlock] = {}
    scores: dict[frozenset[tuple[str, int]], float] = {}
    models: dict[frozenset[tuple[str, int]], str] = {}
    evidences: dict[frozenset[tuple[str, int]], dict] = {}
    for match in matches:
        left = (match.block_a.file, match.block_a.line_start)
        right = (match.block_b.file, match.block_b.line_start)
        if left == right:
            continue
        adjacency[left].add(right)
        adjacency[right].add(left)
        blocks_by_location[left] = match.block_a
        blocks_by_location[right] = match.block_b
        pair = frozenset((left, right))
        scores[pair] = match.similarity
        models[pair] = match.model
        evidences[pair] = match.evidence or {}

    components: list[list[tuple[str, int]]] = []
    visited: set[tuple[str, int]] = set()
    for start in sorted(adjacency):
        if start in visited:
            continue
        stack = [start]
        component: list[tuple[str, int]] = []
        while stack:
            location = stack.pop()
            if location in visited:
                continue
            visited.add(location)
            component.append(location)
            stack.extend(adjacency[location] - visited)
        if len(component) >= 2:
            components.append(sorted(component))

    groups: list[DuplicateGroup] = []
    for i, component in enumerate(components):
        component_set = set(component)
        component_scores = [
            score for pair, score in scores.items() if pair.issubset(component_set)
        ]
        component_models = [
            model for pair, model in models.items() if pair.issubset(component_set)
        ]
        component_evidence = [
            evidence for pair, evidence in evidences.items() if pair.issubset(component_set)
        ]
        languages = sorted(
            {
                language
                for evidence in component_evidence
                for language in evidence.get("languages", [])
            }
        )
        intent_scores = [
            float(evidence["intent_similarity"])
            for evidence in component_evidence
            if evidence.get("intent_similarity") is not None
        ]
        shared_terms: dict[str, set[str]] = defaultdict(set)
        for evidence in component_evidence:
            for field, terms in evidence.get("shared", {}).items():
                shared_terms[field].update(terms)
        component_blocks = [blocks_by_location[location] for location in component]
        fingerprint = hashlib.sha256(repr(component).encode("utf-8")).hexdigest()[:16]
        groups.append(
            DuplicateGroup(
                id=f"M{i + 1:04d}",
                duplicate_type=DuplicateType.SEMANTIC,
                fragments=[
                    DuplicateFragment(
                        file=block.file,
                        line_start=block.line_start,
                        line_end=block.line_end,
                        text=block.text,
                        function_name=block.function_name,
                        class_name=block.class_name,
                    )
                    for block in component_blocks
                ],
                similarity_score=sum(component_scores) / len(component_scores),
                normalized_hash=f"semantic:{fingerprint}",
                normalized_name=component_blocks[0].function_name,
                metadata={
                    "model": component_models[0],
                    "matched_pairs": len(component_scores),
                    "semantic_evidence": {
                        "languages": languages,
                        "intent_similarity": (
                            sum(intent_scores) / len(intent_scores) if intent_scores else None
                        ),
                        "shared": {
                            field: sorted(terms) for field, terms in shared_terms.items()
                        },
                    },
                },
            )
        )

    return groups


def find_intent_groups(blocks: list[CodeBlock], config: ScanConfig) -> list[DuplicateGroup]:
    """Find duplicate intent contracts via Intract."""
    if not getattr(config, "intent_enabled", False):
        return []

    try:
        from redup.integrations.intract.adapter import detect_intent_duplicates
    except ImportError:
        return []

    try:
        return detect_intent_duplicates(blocks, config)
    except RuntimeError as exc:
        print(f"⚠️  {exc}")
        return []


def find_duplicates_phase_optimized(
    all_blocks: list[CodeBlock], config: ScanConfig
) -> list[DuplicateGroup]:
    """Phase 3: Hash and find duplicate groups with performance optimizations."""
    from redup.core.lazy_grouper import find_all_duplicates_lazy

    start_time = time.time()

    # Build hash index with progress tracking
    index = build_hash_index(all_blocks, min_lines=config.min_block_lines)

    # Find duplicates using lazy evaluation for better performance
    groups = list(find_all_duplicates_lazy(index, min_lines=config.min_block_lines))

    return _finalize_duplicate_groups(groups, all_blocks, config, start_time)


def find_duplicates_phase_lazy(
    all_blocks: list[CodeBlock], config: ScanConfig, cache: HashCache | None = None
) -> list[DuplicateGroup]:
    """Phase 3: Hash and find duplicates with caching and lazy evaluation."""
    from redup.core.lazy_grouper import find_all_duplicates_lazy

    start_time = time.time()

    # Build hash index with optional caching
    if cache is not None:
        # Use cache-aware hash indexing
        index, block_hash_cache = build_hash_index_with_cache(
            all_blocks,
            min_lines=config.min_block_lines,
            cache=cache,
            project_root=config.root,
        )

        # Store cache data for incremental scans
        for file_path, hashes in block_hash_cache.items():
            if file_path.exists():
                try:
                    content = file_path.read_text()
                    cache.store_file_hashes(file_path, content, hashes)
                except OSError:
                    pass
    else:
        index = build_hash_index(all_blocks, min_lines=config.min_block_lines)

    # Use lazy grouping with early exit
    groups = list(find_all_duplicates_lazy(index, min_lines=config.min_block_lines))

    return _finalize_duplicate_groups(groups, all_blocks, config, start_time, cache)
