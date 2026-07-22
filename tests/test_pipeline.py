"""Tests for reDUP pipeline — integration tests."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from redup.core.models import DuplicateType, ScanConfig
from redup.core.pipeline import analyze, analyze_optimized, duplicate_finder
from redup.core.pipeline.duplicate_finder import find_fuzzy_groups
from redup.core.scanner import CodeBlock


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
