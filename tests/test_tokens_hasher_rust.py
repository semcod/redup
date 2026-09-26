"""Tests for native Rust acceleration integration in tokens_hasher."""

from __future__ import annotations

from pathlib import Path

from redup.core.tokens_hasher import (
    find_rust_hasher_binary,
    fuzzy_simhash,
    fuzzy_simhash_rust,
)


def test_rust_binary_discovery() -> None:
    bin_path = find_rust_hasher_binary()
    assert bin_path is not None
    assert bin_path.is_file()
    assert bin_path.name == "redup-fast-hash"


def test_rust_and_python_exact_match_sample_code() -> None:
    samples = [
        "def add(a, b):\n    return a + b\n",
        "def multiply(x, y):\n    # Calculate product\n    return x * y\n",
        """
        /* C-style function */
        int process_values(int a, int b) {
            if (a > 100 || b <= 0) {
                printf("Error: invalid values\\n");
                return -1;
            }
            return a + b * 2;
        }
        """,
        """
        function validateOrder(orderId, customerEmail) {
            // Check order validity
            if (!orderId || customerEmail === "") {
                return false;
            }
            let fee = 15.99;
            return fee > 0;
        }
        """,
    ]

    for sample in samples:
        py_hash = fuzzy_simhash(sample, prefer_rust=False)
        rust_hash = fuzzy_simhash(sample, prefer_rust=True)
        assert py_hash == rust_hash
        assert rust_hash > 0


def test_fuzzy_simhash_rust_with_missing_binary() -> None:
    # Explicitly pass non-existent binary path to ensure graceful None return
    res = fuzzy_simhash_rust("def dummy(): pass", binary_path=Path("/tmp/nonexistent_bin_12345"))
    assert res is None
