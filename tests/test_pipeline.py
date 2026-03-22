"""Tests for reDUP pipeline — integration tests."""

import tempfile
from pathlib import Path

from redup.core.models import ScanConfig
from redup.core.pipeline import analyze


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
        '''def something_unique():
    x = [i**2 for i in range(100)]
    return sum(x)
''',
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
            g for g in result.groups
            if g.normalized_name and "calculate_tax" in g.normalized_name
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


def test_analyze_no_duplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "a.py").write_text("def foo():\n    return 1\n")
        (root / "b.py").write_text("def bar():\n    return 2\n")

        config = ScanConfig(root=root, min_block_lines=3)
        result = analyze(config=config, function_level_only=True)

        assert result.total_groups == 0
