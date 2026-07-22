"""Semantic duplicate detection via code embeddings.

This module provides semantic duplicate detection using transformer models
like CodeBERT to find functionally similar code despite different implementations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
    "in",
    "let",
    "none",
    "null",
    "return",
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


def semantic_document(block: CodeBlock) -> str:
    """Build a code+intent document suitable for cross-language code embeddings."""
    profile = build_intent_profile(block)
    fields = [
        f"language: {profile['language']}",
        f"purpose: {' '.join(profile['purpose'])}",
        f"calls: {' '.join(profile['calls'])}",
        f"data: {' '.join(profile['data'])}",
        f"domain: {' '.join(profile['domain'])}",
        f"operations: {' '.join(profile['operations'])}",
    ]
    if profile["comments"]:
        fields.append(f"description: {' '.join(profile['comments'])}")
    fields.append(f"implementation:\n{block.text[:6000]}")
    return "\n".join(fields)


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
        union = left_terms.union(right_terms)
        if union:
            score += weight * len(left_terms.intersection(right_terms)) / len(union)
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

    def __init__(self, model_name: str = "microsoft/codebert-base", threshold: float = 0.80):
        self.threshold = threshold
        self.model_name = model_name
        self._model = None

    def _ensure_model(self):
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
        self._ensure_model()
        from sentence_transformers import util

        if len(blocks) < 2:
            return []

        # Encode (batched for efficiency)
        profiles = [build_intent_profile(block) for block in blocks]
        texts = [semantic_document(block) for block in blocks]
        embeddings = self._model.encode(
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

        for i in range(len(blocks)):
            for j in range(i + 1, len(blocks)):
                score = cos_scores[i][j].item()
                if score >= self.threshold:
                    # Skip same-file same-function matches
                    if (
                        blocks[i].file == blocks[j].file
                        and blocks[i].line_start == blocks[j].line_start
                    ):
                        continue

                    pair = (min(i, j), max(i, j))
                    if pair not in seen:
                        seen.add(pair)
                        matches.append(
                            SemanticMatch(
                                block_a=blocks[i],
                                block_b=blocks[j],
                                similarity=score,
                                model=self.model_name,
                                evidence=_match_evidence(profiles[i], profiles[j]),
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
        self._ensure_model()
        from sentence_transformers import util

        if len(blocks) < 2:
            return []

        profiles = [build_intent_profile(block) for block in blocks]
        texts = [semantic_document(block) for block in blocks]
        embeddings = self._model.encode(texts, convert_to_tensor=True)

        matches: list[SemanticMatch] = []
        seen: set[tuple[int, int]] = set()
        hits = util.semantic_search(
            embeddings,
            embeddings,
            top_k=min(top_k + 1, len(blocks)),
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
                matches.append(
                    SemanticMatch(
                        block_a=blocks[pair[0]],
                        block_b=blocks[pair[1]],
                        similarity=score,
                        model=self.model_name,
                        evidence=_match_evidence(profiles[pair[0]], profiles[pair[1]]),
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

        embeddings = self._model.encode([text_a, text_b], convert_to_tensor=True)
        cosine_score = util.cos_sim(embeddings[0], embeddings[1])
        return float(cosine_score.item())
