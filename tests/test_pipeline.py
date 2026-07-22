"""Tests for reDUP pipeline — integration tests."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from redup.core.models import DuplicateType, ScanConfig
from redup.core.pipeline import analyze, analyze_optimized, duplicate_finder
from redup.core.pipeline.duplicate_finder import (
    _fuzzy_candidate_indices,
    find_fuzzy_groups,
    find_semantic_groups,
)
from redup.core.scanner import CodeBlock
from redup.core.semantic import SemanticMatch


def _create_test_project(root: Path) -> None:
    """Create a test project with known duplicates."""
    # Two files with identical functions
    (root / "billing.py").write_text(
        '''def calculate_tax(amount, rate):
    """Calculate tax for given amount."""
    if amount <= 0:
        return 0.0
    tax = amount * rate
    if tax > 1000:
        tax = 1000
    return round(tax, 2)


def process_payment(amount):
    return amount * 1.1
''',
        encoding="utf-8",
    )

    (root / "shipping.py").write_text(
        '''def calculate_tax(total, tax_rate):
    """Calculate tax for given amount."""
    if total <= 0:
        return 0.0
    tax = total * tax_rate
    if tax > 1000:
        tax = 1000
    return round(tax, 2)


def get_shipping_cost(weight):
    return weight * 2.5
''',
        encoding="utf-8",
    )

    (root / "returns.py").write_text(
        '''def calculate_tax(value, rate):
    """Calculate tax for given amount."""
    if value <= 0:
        return 0.0
    tax = value * rate
    if tax > 1000:
        tax = 1000
    return round(tax, 2)


def process_return(item_id):
    return f"returned_{item_id}"
''',
        encoding="utf-8",
    )

    # A unique file with no duplicates
    (root / "unique.py").write_text(
        """def something_unique():
    x = [i**2 for i in range(100)]
    return sum(x)
""",
        encoding="utf-8",
    )


def test_analyze_finds_duplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _create_test_project(root)

        config = ScanConfig(root=root, min_block_lines=3, min_similarity=0.80)
        result = analyze(config=config, function_level_only=True)

        assert result.stats.files_scanned == 4
        assert result.total_groups >= 1

        # The calculate_tax function is duplicated 3 times
        tax_groups = [
            g for g in result.groups if g.normalized_name and "calculate_tax" in g.normalized_name
        ]
        assert len(tax_groups) >= 1
        assert tax_groups[0].occurrences == 3


def test_analyze_generates_suggestions():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _create_test_project(root)

        config = ScanConfig(root=root, min_block_lines=3, min_similarity=0.80)
        result = analyze(config=config, function_level_only=True)

        assert len(result.suggestions) >= 1
        top = result.suggestions[0]
        assert top.priority == 1
        assert len(top.original_files) >= 2


def test_analyze_empty_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        config = ScanConfig(root=root)
        result = analyze(config=config)

        assert result.total_groups == 0
        assert result.total_saved_lines == 0
        assert result.stats.files_scanned == 0


def test_analyze_rejects_missing_scan_root(tmp_path):
    missing = tmp_path / "missing"

    with pytest.raises(FileNotFoundError, match="scan root does not exist"):
        analyze(config=ScanConfig(root=missing))


def test_analyze_skips_quadratic_fuzzy_phase_unless_enabled(tmp_path, monkeypatch):
    (tmp_path / "sample.py").write_text("def sample():\n    return 1\n", encoding="utf-8")

    def unexpected_fuzzy(*args, **kwargs):
        raise AssertionError("fuzzy phase must be opt-in")

    monkeypatch.setattr(duplicate_finder, "find_fuzzy_groups", unexpected_fuzzy)

    result = analyze(config=ScanConfig(root=tmp_path, fuzzy_enabled=False))

    assert result.stats.files_scanned == 1


def test_analyze_runs_semantic_phase_only_when_enabled(tmp_path, monkeypatch):
    (tmp_path / "a.py").write_text("def first():\n    return 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("def second():\n    return 2\n", encoding="utf-8")
    calls = []

    def fake_semantic(blocks, threshold, model_name):
        calls.append((len(blocks), threshold, model_name))
        return []

    monkeypatch.setattr(duplicate_finder, "find_semantic_groups", fake_semantic)

    analyze(config=ScanConfig(root=tmp_path, semantic_enabled=False))
    assert calls == []

    analyze(
        config=ScanConfig(
            root=tmp_path,
            semantic_enabled=True,
            semantic_threshold=0.73,
            semantic_model="example/model",
        )
    )
    assert calls == [(2, 0.73, "example/model")]


def test_find_semantic_groups_maps_cross_language_match(monkeypatch):
    python_block = CodeBlock(
        file="cart.py",
        line_start=1,
        line_end=4,
        text="def cart_total(items):\n    return sum(item.price for item in items)\n",
        function_name="cart_total",
    )
    javascript_block = CodeBlock(
        file="cart.js",
        line_start=1,
        line_end=3,
        text="function cartTotal(items) { return items.reduce((a, x) => a + x.price, 0); }",
        function_name="cartTotal",
    )

    def fake_find(self, blocks):
        return [
            SemanticMatch(
                block_a=blocks[0],
                block_b=blocks[1],
                similarity=0.91,
                model=self.model_name,
            )
        ]

    monkeypatch.setattr(
        "redup.core.semantic.SemanticDetector.find_semantic_duplicates_fast",
        fake_find,
    )
    groups = find_semantic_groups(
        [python_block, javascript_block],
        threshold=0.75,
        model_name="test/code-model",
    )

    assert len(groups) == 1
    assert groups[0].duplicate_type == DuplicateType.SEMANTIC
    assert groups[0].similarity_score == 0.91
    assert groups[0].metadata == {
        "model": "test/code-model",
        "matched_pairs": 1,
        "semantic_evidence": {"languages": [], "intent_similarity": None, "shared": {}},
    }
    assert {fragment.file for fragment in groups[0].fragments} == {"cart.py", "cart.js"}


def test_find_semantic_groups_clusters_transitive_matches(monkeypatch):
    blocks = [
        CodeBlock(
            file=f"cart.{extension}",
            line_start=1,
            line_end=4,
            text=text,
            function_name=name,
        )
        for extension, name, text in (
            ("py", "cart_total", "def cart_total(items): return sum(items)"),
            ("js", "cartTotal", "function cartTotal(items) { return sum(items); }"),
            ("php", "sum_cart", "function sum_cart($items) { return sum($items); }"),
        )
    ]

    def fake_find(self, found_blocks):
        return [
            SemanticMatch(found_blocks[0], found_blocks[1], 0.93, self.model_name),
            SemanticMatch(found_blocks[1], found_blocks[2], 0.87, self.model_name),
        ]

    monkeypatch.setattr(
        "redup.core.semantic.SemanticDetector.find_semantic_duplicates_fast",
        fake_find,
    )

    groups = find_semantic_groups(blocks, model_name="test/code-model")

    assert len(groups) == 1
    assert groups[0].occurrences == 3
    assert groups[0].similarity_score == pytest.approx(0.90)
    assert groups[0].metadata["matched_pairs"] == 2


def test_find_semantic_groups_is_optional_without_dependency(monkeypatch, capsys):
    blocks = [
        CodeBlock("a.py", 1, 3, "def a():\n    return 1\n", function_name="a"),
        CodeBlock("b.py", 1, 3, "def b():\n    return 1\n", function_name="b"),
    ]

    def missing_dependency(self, _blocks):
        raise ImportError("install redup[semantic]")

    monkeypatch.setattr(
        "redup.core.semantic.SemanticDetector.find_semantic_duplicates_fast",
        missing_dependency,
    )

    assert find_semantic_groups(blocks) == []
    assert "Semantic detection unavailable" in capsys.readouterr().out


def test_analyze_no_duplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "a.py").write_text(
            "def foo(x):\n    if x > 0:\n        return x * 2\n    return -1\n"
        )
        (root / "b.py").write_text(
            "def bar(items):\n    total = 0\n    for i in items:\n        total += i\n    return total\n"
        )

        config = ScanConfig(root=root, min_block_lines=3)
        result = analyze(config=config, function_level_only=True)

        assert result.total_groups == 0


def test_analyze_optimized_stores_incremental_cache():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        root = base / "project"
        root.mkdir()
        _create_test_project(root)

        cache_dir = base / "cache"
        config = ScanConfig(
            root=root,
            min_block_lines=3,
            min_similarity=0.80,
            enable_cache=True,
            cache_dir=cache_dir,
        )

        analyze_optimized(config=config, function_level_only=True, use_memory_cache=False)

        db_path = cache_dir / "hash_cache.db"
        assert db_path.exists()

        with sqlite3.connect(db_path) as conn:
            file_count = conn.execute("SELECT COUNT(*) FROM file_hashes").fetchone()[0]

        assert file_count >= 1


def test_find_fuzzy_groups_detects_renamed_env_readers():
    blocks = [
        CodeBlock(
            file="a.py",
            line_start=1,
            line_end=6,
            text=(
                'def read_enter() -> str:\n'
                '    raw = os.environ.get("ENTER", "").strip()\n'
                '    if raw.isdigit():\n'
                '        return raw\n'
                '    return "28"\n'
            ),
            function_name="read_enter",
        ),
        CodeBlock(
            file="b.py",
            line_start=1,
            line_end=6,
            text=(
                'def read_ctrl() -> str:\n'
                '    raw = os.environ.get("CTRL", "").strip()\n'
                '    if raw.isdigit():\n'
                '        return raw\n'
                '    return "29"\n'
            ),
            function_name="read_ctrl",
        ),
    ]
    config = ScanConfig(min_block_lines=3, min_similarity=0.85)
    groups = find_fuzzy_groups(blocks, config)
    assert len(groups) == 1
    assert groups[0].duplicate_type == DuplicateType.FUZZY
    assert groups[0].occurrences == 2


def test_fuzzy_candidate_index_avoids_all_pairs():
    blocks = [
        CodeBlock(
            file=f"module_{index}.py",
            line_start=1,
            line_end=8,
            text=(
                f"def function_{index}(value):\n"
                + ("    if value:\n        return value + 1\n" if index % 2 else "")
                + ("    for item in value:\n        print(item)\n" if index % 3 else "")
                + ("    try:\n        return value[0]\n    except IndexError:\n        return None\n" if index % 5 else "")
            ),
            function_name=f"function_{index}",
        )
        for index in range(120)
    ]

    candidates = _fuzzy_candidate_indices(blocks)
    pair_count = sum(len(indices) for indices in candidates.values())

    assert pair_count < len(blocks) * (len(blocks) - 1) // 4


def test_find_fuzzy_groups_ignores_overlapping_extractor_blocks():
    blocks = [
        CodeBlock(
            file="app.js",
            line_start=10,
            line_end=20,
            text="function render() {\n  const value = load();\n  return value;\n}\n",
            function_name="render",
        ),
        CodeBlock(
            file="app.js",
            line_start=9,
            line_end=21,
            text="function render() {\n  const value = load();\n  return value;\n}\n",
            function_name="arrow_function",
        ),
    ]

    groups = find_fuzzy_groups(
        blocks,
        ScanConfig(min_block_lines=3, fuzzy_enabled=True, fuzzy_threshold=0.9),
    )

    assert groups == []
