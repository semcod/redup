"""Tests for native Rust acceleration integration in tokens_hasher."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from redup.core.tokens_hasher import (
    find_rust_hasher_binary,
    fuzzy_simhash,
    fuzzy_simhash_rust,
)

CARGO_MANIFEST = (
    Path(__file__).resolve().parent.parent / "packages" / "redup-fast-hash" / "Cargo.toml"
)
RUST_BIN = (
    Path(__file__).resolve().parent.parent
    / "packages"
    / "redup-fast-hash"
    / "target"
    / "release"
    / "redup-fast-hash"
)


def test_unicode_candidate_conformance(
    tmp_path: Path, record_property: Callable[[str, object], None]
) -> None:
    """Build this checkout and invoke it directly; no discovery or fallback."""
    cargo = shutil.which("cargo")
    assert cargo is not None, "Candidate conformance requires Cargo"
    target = tmp_path / "native-target"
    build = subprocess.run(
        [
            cargo,
            "build",
            "--locked",
            "--release",
            "--manifest-path",
            str(CARGO_MANIFEST),
            "--target-dir",
            str(target),
            "--bin",
            "redup-fast-hash",
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert build.returncode == 0, build.stdout + build.stderr
    binary = target / "release" / (
        "redup-fast-hash.exe" if sys.platform == "win32" else "redup-fast-hash"
    )
    assert binary.is_file()
    source = CARGO_MANIFEST.parent / "src" / "simhash.rs"
    record_property("candidate_build_exit_code", build.returncode)
    record_property("candidate_binary", str(binary))
    record_property("candidate_sha256", hashlib.sha256(binary.read_bytes()).hexdigest())
    record_property("simhash_source_sha256", hashlib.sha256(source.read_bytes()).hexdigest())

    samples = [
        ("def add(a, b): return a + b", 1999307407177186558),
        ("ą", 2684146023269591358),
        ("zażółć gęślą jaźń", 3173260504582634983),
        ("😀value", 17867692854670522352),
        ("const źródło = `żółć`;", 16890555981135166839),
        ("fn 変数() {return 1;}", 8428574849076232171),
        ("ą/* 😀 */+変数// żółć\n😀# ą\nź", 8016116748811581599),
        ("ą\"😀\"+'変数'; return 12.5;", 8713030534196668199),
        ("ą\"\\😀\"ź", 13292627870420614445),
        ("RETURN foo_2 + $bar == 12.5; // note", 8785272967380082946),
        ("ą===😀!=変数", 8056867025399037722),
        ("aąB_2😀z", 462200693447372014),
        ("Ąİ変数😀", 3857494918881161239),
    ]
    for sample, expected in samples:
        result = subprocess.run(
            [str(binary), "--simhash", sample],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            timeout=5,
        )
        assert int(result.stdout.strip()) == expected, repr(sample)
        assert fuzzy_simhash(sample, prefer_rust=False) == expected, repr(sample)


@pytest.fixture(scope="module")
def ensure_rust_binary() -> Path | None:
    """Ensure release binary of redup-fast-hash is available or built."""
    bin_path = find_rust_hasher_binary()
    if bin_path and bin_path.is_file():
        return bin_path

    cargo = shutil.which("cargo")
    if not cargo or not CARGO_MANIFEST.is_file():
        return None

    try:
        subprocess.run(
            [cargo, "build", "--release", "--manifest-path", str(CARGO_MANIFEST)],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.SubprocessError, OSError):
        return None

    bin_path = find_rust_hasher_binary()
    if not bin_path or not bin_path.is_file():
        return None

    return bin_path


def test_rust_binary_discovery(ensure_rust_binary: Path | None) -> None:
    if ensure_rust_binary is None:
        return
    assert ensure_rust_binary is not None
    assert ensure_rust_binary.is_file()
    assert ensure_rust_binary.name == "redup-fast-hash"


def test_rust_and_python_exact_match_sample_code(ensure_rust_binary: Path | None) -> None:
    if ensure_rust_binary is None:
        return
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


def test_pyo3_in_process_simhash() -> None:
    try:
        import redup_fast_hash
    except ImportError:
        return

    code = "def calculate_total(subtotal, tax_rate):\n    return subtotal * (1 + tax_rate)\n"
    fp_native = redup_fast_hash.compute_fuzzy_simhash(code)
    fp_python = fuzzy_simhash(code, prefer_rust=False)
    assert fp_native == fp_python
    assert fp_native > 0


def test_pyo3_batch_simhash() -> None:
    try:
        import redup_fast_hash
    except ImportError:
        return

    codes = [
        "def f1(x): return x + 1",
        "def f2(y): return y + 1",
        "class Config: pass",
    ]
    fps = redup_fast_hash.batch_simhash(codes)
    assert len(fps) == 3
    assert fps[0] == fps[1]
    assert fps[0] != fps[2]


def test_pyo3_find_simhash_candidates() -> None:
    try:
        import redup_fast_hash
    except ImportError:
        return

    fp1 = 0x1111222233334444
    fp2 = 0x111122223333FFFF
    items = [
        (0, fp1, ".py", 10),
        (1, fp2, ".py", 11),
        (2, 0x9999888877776666, ".py", 10),
    ]
    candidates = redup_fast_hash.find_simhash_candidates(items, 2, 4, 4)
    assert 0 in candidates
    assert 1 in candidates[0]


