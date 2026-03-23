"""Semantic duplicate detection via code embeddings.

This module provides semantic duplicate detection using transformer models
like CodeBERT to find functionally similar code despite different implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from redup.core.scanner import CodeBlock


@dataclass
class SemanticMatch:
    """A pair of semantically similar code blocks."""
    block_a: CodeBlock
    block_b: CodeBlock
    similarity: float
    model: str


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
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for semantic detection. "
                    "Install with: pip install redup[semantic]"
                )

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
        import torch

        if len(blocks) < 2:
            return []

        # Encode (batched for efficiency)
        texts = [b.text for b in blocks]
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
                    if blocks[i].file == blocks[j].file and \
                       blocks[i].line_start == blocks[j].line_start:
                        continue

                    pair = (min(i, j), max(i, j))
                    if pair not in seen:
                        seen.add(pair)
                        matches.append(SemanticMatch(
                            block_a=blocks[i],
                            block_b=blocks[j],
                            similarity=score,
                            model=self.model_name,
                        ))

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

        texts = [b.text for b in blocks]
        embeddings = self._model.encode(texts, convert_to_tensor=True)

        # Paraphrase mining — finds top-k most similar pairs efficiently
        pairs = util.paraphrase_mining(
            self._model,
            texts,
            corpus_embeddings=embeddings,
            top_k=top_k,
            show_progress_bar=False,
        )

        matches: list[SemanticMatch] = []
        for score, i, j in pairs:
            if score >= self.threshold:
                # Skip same-file same-function matches
                if blocks[i].file == blocks[j].file and \
                   blocks[i].line_start == blocks[j].line_start:
                    continue
                matches.append(SemanticMatch(
                    block_a=blocks[i],
                    block_b=blocks[j],
                    similarity=float(score),
                    model=self.model_name,
                ))

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
