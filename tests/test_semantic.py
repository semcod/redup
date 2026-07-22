import sys
import types

from redup.core.scanner_types import CodeBlock
from redup.core.semantic import SemanticDetector


class _FakeModel:
    def encode(self, texts, **kwargs):
        assert len(texts) == 3
        assert kwargs["convert_to_tensor"] is True
        return "fake-embeddings"


def test_fast_semantic_search_deduplicates_symmetric_neighbors(monkeypatch):
    fake_util = types.SimpleNamespace(
        semantic_search=lambda query, corpus, top_k: [
            [
                {"corpus_id": 0, "score": 1.0},
                {"corpus_id": 1, "score": 0.91},
                {"corpus_id": 2, "score": 0.40},
            ],
            [
                {"corpus_id": 1, "score": 1.0},
                {"corpus_id": 0, "score": 0.91},
            ],
            [
                {"corpus_id": 2, "score": 1.0},
                {"corpus_id": 0, "score": 0.40},
            ],
        ]
    )
    fake_package = types.ModuleType("sentence_transformers")
    fake_package.util = fake_util
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_package)

    blocks = [
        CodeBlock(
            file=f"module_{index}.py",
            line_start=1,
            line_end=3,
            text=f"def function_{index}(): return {index}",
            function_name=f"function_{index}",
        )
        for index in range(3)
    ]
    detector = SemanticDetector(model_name="fake/model", threshold=0.8)
    detector._model = _FakeModel()

    matches = detector.find_semantic_duplicates_fast(blocks)

    assert len(matches) == 1
    assert matches[0].block_a == blocks[0]
    assert matches[0].block_b == blocks[1]
    assert matches[0].similarity == 0.91
