"""Semantic duplicate detection via language-neutral intent embeddings."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from redup.core.models import DEFAULT_SEMANTIC_MODEL, DEFAULT_SEMANTIC_THRESHOLD
from redup.core.scanner import CodeBlock

_INTENT_ALIASES = {
    "amount": "total",
    "aggregate": "aggregate",
    "basket": "cart",
    "build": "create",
    "calculate": "aggregate",
    "check": "validate",
    "compute": "aggregate",
    "convert": "parse",
    "create": "create",
    "deserialize": "parse",
    "emit": "write",
    "fetch": "read",
    "format": "format",
    "generate": "create",
    "get": "read",
    "launch": "start",
    "list": "list",
    "load": "read",
    "make": "create",
    "post": "write",
    "read": "read",
    "remove": "delete",
    "render": "format",
    "serialize": "format",
    "send": "write",
    "sum": "aggregate",
    "terminate": "stop",
    "total": "total",
    "valid": "validate",
    "validate": "validate",
    "verify": "validate",
}
_GENERIC_IDENTIFIERS = {
    "args",
    "async",
    "await",
    "class",
    "const",
    "def",
    "else",
    "false",
    "for",
    "function",
    "if",
    "impl",
    "in",
    "init",
    "initializer",
    "is",
    "let",
    "main",
    "method",
    "none",
    "null",
    "handler",
    "callback",
    "arrow",
    "return",
    "run",
    "self",
    "this",
    "true",
    "var",
    "while",
}


def _identifier_words(value: str) -> list[str]:
    """Split snake/camel/kebab identifiers and normalize common intent synonyms."""
    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    words = re.findall(r"[A-Za-z][A-Za-z0-9]*", expanded.replace("_", " ").replace("-", " "))
    return [_INTENT_ALIASES.get(word.lower(), word.lower()) for word in words]


def _ordered_unique(values: list[str], *, limit: int = 24) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if len(value) < 2 or value in _GENERIC_IDENTIFIERS or value in seen:
            continue
        seen.add(value)
        result.append(value)
        if len(result) >= limit:
            break
    return result


def build_intent_profile(block: CodeBlock) -> dict[str, Any]:
    """Extract explainable, language-neutral intent clues from a function block."""
    text = block.text
    purpose = _ordered_unique(_identifier_words(block.function_name or ""), limit=10)

    call_names = re.findall(r"\b([A-Za-z_$][A-Za-z0-9_$.]*)\s*\(", text)
    calls = _ordered_unique(
        [word for name in call_names for word in _identifier_words(name.split(".")[-1])]
    )

    string_values = re.findall(r'"([^"\n]{1,80})"|\'([^\'\n]{1,80})\'', text)
    data_terms = _ordered_unique(
        [
            word
            for pair in string_values
            for value in pair
            if value
            for word in _identifier_words(value)
        ]
    )

    identifier_values = re.findall(r"\b[A-Za-z_$][A-Za-z0-9_$]*\b", text)
    domain_terms = _ordered_unique(
        [word for value in identifier_values for word in _identifier_words(value)]
    )

    operations: list[str] = []
    operation_patterns = {
        "iterate": r"\b(for|foreach|map|reduce|filter|while)\b",
        "branch": r"\b(if|else|switch|case|match)\b",
        "error_handling": r"\b(try|except|catch|raise|throw)\b",
        "async": r"\b(async|await|promise)\b",
        "return": r"\breturn\b",
        "arithmetic": r"(?<![+*])(?:\+|\*|/|%)(?![+*])",
        "comparison": r"(?:===?|!==?|<=|>=|<|>)",
    }
    lowered = text.lower()
    for operation, pattern in operation_patterns.items():
        if re.search(pattern, lowered):
            operations.append(operation)

    comments = re.findall(r"(?:#|//)\s*([^\n]{3,160})", text)
    return {
        "language": Path(block.file).suffix.lower().lstrip(".") or "unknown",
        "purpose": purpose,
        "calls": calls,
        "data": data_terms,
        "domain": domain_terms,
        "operations": operations,
        "comments": comments[:3],
    }


def _profile_document(profile: dict[str, Any]) -> str:
    """Render one extracted intent profile as embedding input."""
    labels = {
        "purpose": "Purpose",
        "calls": "Calls",
        "data": "Data",
        "domain": "Domain",
        "operations": "Operations",
        "comments": "Description",
    }
    fields = [
        f"{label}: {' '.join(profile[field])}" for field, label in labels.items() if profile[field]
    ]
    return "\n".join(fields)


def semantic_document(block: CodeBlock) -> str:
    """Build a compact language-neutral document for sentence embeddings.

    The default model is trained for natural-language similarity rather than raw
    source code. Embedding the extracted intent signals also avoids making two
    implementations look different solely because they use different languages.
    """
    return _profile_document(build_intent_profile(block))


def _embedding_inputs(
    blocks: list[CodeBlock],
) -> tuple[list[CodeBlock], list[dict[str, Any]], list[str]]:
    """Keep only blocks with enough intent information for meaningful embeddings."""
    candidates: list[CodeBlock] = []
    profiles: list[dict[str, Any]] = []
    documents: list[str] = []
    for block in blocks:
        profile = build_intent_profile(block)
        anchors = profile["purpose"] + profile["calls"] + profile["data"] + profile["comments"]
        if not anchors:
            continue
        document = _profile_document(profile)
        if not document:
            continue
        candidates.append(block)
        profiles.append(profile)
        documents.append(document)
    return candidates, profiles, documents


def intent_profile_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    """Score explainable intent overlap independently from embedding similarity."""
    weights = {
        "purpose": 0.35,
        "calls": 0.15,
        "data": 0.15,
        "domain": 0.15,
        "operations": 0.20,
    }
    score = 0.0
    for field, weight in weights.items():
        left_terms = set(left[field])
        right_terms = set(right[field])
        denominator = len(left_terms) + len(right_terms)
        if denominator:
            # Sørensen-Dice rewards a compact shared intent vocabulary without
            # penalizing language-specific implementation details as strongly
            # as Jaccard similarity.
            score += weight * 2 * len(left_terms.intersection(right_terms)) / denominator
    shared_purpose = set(left["purpose"]).intersection(right["purpose"])
    shared_operations = set(left["operations"]).intersection(right["operations"])
    if len(shared_purpose) >= 2:
        score += 0.10
    if len(shared_operations) >= 2:
        score += 0.05
    return min(score, 1.0)


def _match_evidence(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    fields = ("purpose", "calls", "data", "domain", "operations")
    shared = {
        field: sorted(set(left[field]).intersection(right[field]))
        for field in fields
        if set(left[field]).intersection(right[field])
    }
    return {
        "languages": [left["language"], right["language"]],
        "intent_similarity": round(intent_profile_similarity(left, right), 3),
        "shared": shared,
    }


def _has_semantic_support(evidence: dict[str, Any], threshold: float) -> bool:
    """Require shared purpose and independent profile support for an embedding hit."""
    shared_purpose = evidence.get("shared", {}).get("purpose", [])
    intent_similarity = float(evidence.get("intent_similarity", 0.0))
    support_threshold = max(0.50, threshold - 0.25)
    return bool(shared_purpose) and intent_similarity >= support_threshold


@dataclass
class SemanticMatch:
    """A pair of semantically similar code blocks."""

    block_a: CodeBlock
    block_b: CodeBlock
    similarity: float
    model: str
    evidence: dict[str, Any] | None = None


class SemanticDetector:
    """Detects semantically similar code using transformer embeddings."""

    def __init__(
        self,
        model_name: str = DEFAULT_SEMANTIC_MODEL,
        threshold: float = DEFAULT_SEMANTIC_THRESHOLD,
    ):
        self.threshold = threshold
        self.model_name = model_name
        self._model: Any | None = None

    def _ensure_model(self) -> None:
        """Lazy-load the model only when needed."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers is required for semantic detection. "
                    "Install with: pip install redup[semantic]"
                ) from exc

    def _find_intent_profile_duplicates(
        self,
        blocks: list[CodeBlock],
        *,
        top_k: int = 10,
    ) -> list[SemanticMatch]:
        """Find explainable semantic candidates without transformer dependencies.

        Candidate pairs share at least one non-ubiquitous purpose, call or data
        term. The final score uses the language-neutral intent profile, so the
        fallback can match different implementations and languages without
        downloading a GPU/ML runtime.
        """
        if len(blocks) < 2:
            return []

        profiles = [build_intent_profile(block) for block in blocks]
        postings: dict[str, list[int]] = defaultdict(list)
        for index, profile in enumerate(profiles):
            block = blocks[index]
            if block.line_end - block.line_start + 1 < 3 or not profile["purpose"]:
                continue
            anchors = set(profile["purpose"] + profile["calls"] + profile["data"])
            for anchor in anchors:
                postings[anchor].append(index)

        # Avoid quadratic explosions from generic project-wide vocabulary.
        max_postings = max(24, min(96, len(blocks) // 20))
        candidates: set[tuple[int, int]] = set()
        for indices in postings.values():
            if len(indices) < 2 or len(indices) > max_postings:
                continue
            for offset, left in enumerate(indices[:-1]):
                for right in indices[offset + 1 :]:
                    candidates.add((left, right))

        # The explainable profile is intentionally sparse, so its calibrated
        # threshold is lower than an embedding cosine threshold.
        profile_threshold = max(0.70, min(0.82, self.threshold - 0.10))
        ranked: list[SemanticMatch] = []
        for left, right in candidates:
            shared_purpose = set(profiles[left]["purpose"]).intersection(profiles[right]["purpose"])
            shared_support = set(profiles[left]["calls"] + profiles[left]["data"]).intersection(
                profiles[right]["calls"] + profiles[right]["data"]
            )
            if not shared_purpose or (len(shared_purpose) == 1 and len(shared_support) < 2):
                continue
            score = intent_profile_similarity(profiles[left], profiles[right])
            if score < profile_threshold:
                continue
            ranked.append(
                SemanticMatch(
                    block_a=blocks[left],
                    block_b=blocks[right],
                    similarity=score,
                    model="redup/intent-profile-v1",
                    evidence=_match_evidence(profiles[left], profiles[right]),
                )
            )

        ranked.sort(key=lambda match: match.similarity, reverse=True)
        retained: list[SemanticMatch] = []
        neighbor_counts: dict[tuple[str, int], int] = defaultdict(int)
        # Connected-component grouping is deliberately used by the embedding
        # engine, but weak lexical links can otherwise form giant transitive
        # chains. Greedy one-to-one pairs keep fallback findings reviewable.
        neighbor_limit = 1
        max_matches = min(200, max(20, len(blocks) // 25))
        for match in ranked:
            left_key = (match.block_a.file, match.block_a.line_start)
            right_key = (match.block_b.file, match.block_b.line_start)
            if (
                neighbor_counts[left_key] >= neighbor_limit
                or neighbor_counts[right_key] >= neighbor_limit
            ):
                continue
            retained.append(match)
            neighbor_counts[left_key] += 1
            neighbor_counts[right_key] += 1
            if len(retained) >= max_matches:
                break
        return retained

    def find_semantic_duplicates(
        self,
        blocks: list[CodeBlock],
        batch_size: int = 32,
    ) -> list[SemanticMatch]:
        """Find semantically similar code blocks using embeddings.

        Pipeline:
        1. Encode all blocks to vectors (batched, GPU if available)
        2. Compute cosine similarity matrix
        3. Filter pairs above threshold

        Args:
            blocks: List of code blocks to analyze
            batch_size: Batch size for encoding (for memory efficiency)

        Returns:
            List of semantic matches sorted by similarity (highest first)
        """
        candidates, profiles, texts = _embedding_inputs(blocks)
        if len(candidates) < 2:
            return []

        try:
            self._ensure_model()
        except ImportError:
            return self._find_intent_profile_duplicates(blocks)
        from sentence_transformers import util

        # Encode (batched for efficiency)
        model = self._model
        assert model is not None
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_tensor=True,
            show_progress_bar=False,
        )

        # Cosine similarity matrix
        cos_scores = util.cos_sim(embeddings, embeddings)

        # Extract pairs above threshold
        matches: list[SemanticMatch] = []
        seen: set[tuple[int, int]] = set()

        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                score = cos_scores[i][j].item()
                if score >= self.threshold:
                    # Skip same-file same-function matches
                    if (
                        candidates[i].file == candidates[j].file
                        and candidates[i].line_start == candidates[j].line_start
                    ):
                        continue

                    pair = (min(i, j), max(i, j))
                    if pair not in seen:
                        evidence = _match_evidence(profiles[i], profiles[j])
                        if not _has_semantic_support(evidence, self.threshold):
                            continue
                        seen.add(pair)
                        matches.append(
                            SemanticMatch(
                                block_a=candidates[i],
                                block_b=candidates[j],
                                similarity=score,
                                model=self.model_name,
                                evidence=evidence,
                            )
                        )

        # Sort by similarity (highest first)
        matches.sort(key=lambda m: m.similarity, reverse=True)
        return matches

    def find_semantic_duplicates_fast(
        self,
        blocks: list[CodeBlock],
        top_k: int = 10,
    ) -> list[SemanticMatch]:
        """Fast semantic search — uses approximate kNN instead of full matrix.

        O(n * log(n)) instead of O(n²). Better for >1000 blocks.

        Args:
            blocks: List of code blocks to analyze
            top_k: Maximum number of top similar pairs to return

        Returns:
            List of semantic matches sorted by similarity (highest first)
        """
        candidates, profiles, texts = _embedding_inputs(blocks)
        if len(candidates) < 2:
            return []

        try:
            self._ensure_model()
        except ImportError:
            return self._find_intent_profile_duplicates(blocks, top_k=top_k)
        from sentence_transformers import util

        model = self._model
        assert model is not None
        embeddings = model.encode(texts, convert_to_tensor=True)

        matches: list[SemanticMatch] = []
        seen: set[tuple[int, int]] = set()
        hits = util.semantic_search(
            embeddings,
            embeddings,
            top_k=min(top_k + 1, len(candidates)),
        )
        for i, neighbors in enumerate(hits):
            for neighbor in neighbors:
                j = int(neighbor["corpus_id"])
                if i == j:
                    continue
                pair = (min(i, j), max(i, j))
                if pair in seen:
                    continue
                seen.add(pair)
                score = float(neighbor["score"])
                if score < self.threshold:
                    continue
                evidence = _match_evidence(profiles[pair[0]], profiles[pair[1]])
                if not _has_semantic_support(evidence, self.threshold):
                    continue
                matches.append(
                    SemanticMatch(
                        block_a=candidates[pair[0]],
                        block_b=candidates[pair[1]],
                        similarity=score,
                        model=self.model_name,
                        evidence=evidence,
                    )
                )

        matches.sort(key=lambda match: match.similarity, reverse=True)
        return matches

    def compute_semantic_similarity(self, text_a: str, text_b: str) -> float:
        """Compute semantic similarity between two code snippets.

        Args:
            text_a: First code snippet
            text_b: Second code snippet

        Returns:
            Similarity score between 0.0 and 1.0
        """
        self._ensure_model()
        from sentence_transformers import util

        model = self._model
        assert model is not None
        embeddings = model.encode([text_a, text_b], convert_to_tensor=True)
        cosine_score = util.cos_sim(embeddings[0], embeddings[1])
        return float(cosine_score.item())
