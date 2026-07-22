import sys
import types

from redup.core.scanner_types import CodeBlock
from redup.core.semantic import (
    SemanticDetector,
    build_intent_profile,
    intent_profile_similarity,
    semantic_document,
)


class _FakeModel:
    texts = None

    def encode(self, texts, **kwargs):
        assert len(texts) == 3
        assert kwargs["convert_to_tensor"] is True
        self.texts = texts
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
    model = _FakeModel()
    detector._model = model

    matches = detector.find_semantic_duplicates_fast(blocks)

    assert len(matches) == 1
    assert matches[0].block_a == blocks[0]
    assert matches[0].block_b == blocks[1]
    assert matches[0].similarity == 0.91
    assert model.texts[0].startswith("language: py\npurpose: ")
    assert "implementation:" in model.texts[0]


def test_intent_profiles_align_different_language_cart_implementations():
    blocks = [
        CodeBlock(
            file="cart.py",
            line_start=1,
            line_end=6,
            text=(
                "def calculate_order_total(items):\n"
                "    total = 0\n"
                "    for item in items:\n"
                "        total += item['price'] * item['quantity']\n"
                "    return total\n"
            ),
            function_name="calculate_order_total",
        ),
        CodeBlock(
            file="cart.js",
            line_start=1,
            line_end=3,
            text=(
                "function computeCartAmount(products) {\n"
                "  return products.reduce((sum, item) => sum + item.price * item.quantity, 0);\n"
                "}\n"
            ),
            function_name="computeCartAmount",
        ),
        CodeBlock(
            file="cart.php",
            line_start=1,
            line_end=6,
            text=(
                "function sumBasket($items) {\n"
                "  $total = 0;\n"
                "  foreach ($items as $item) { $total += $item['price'] * $item['quantity']; }\n"
                "  return $total;\n"
                "}\n"
            ),
            function_name="sumBasket",
        ),
    ]

    profiles = [build_intent_profile(block) for block in blocks]

    assert all("aggregate" in profile["purpose"] for profile in profiles)
    assert all("iterate" in profile["operations"] for profile in profiles)
    assert all("arithmetic" in profile["operations"] for profile in profiles)
    assert "total" in profiles[0]["purpose"]
    assert "total" in profiles[1]["purpose"]
    assert "language: php" in semantic_document(blocks[2])
    assert intent_profile_similarity(profiles[0], profiles[1]) >= 0.35
    assert intent_profile_similarity(profiles[1], profiles[2]) >= 0.35
