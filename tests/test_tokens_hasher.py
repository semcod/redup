"""Tests for the pure tokens_hasher module."""

from __future__ import annotations

from redup.core.tokens_hasher import (
    SimpleMinHash,
    _fuzzy_simhash,
    _normalize_text,
    _SimpleMinHash,
    clear_normalize_cache,
    create_simple_minhash,
    extract_fuzzy_tokens,
    find_simhash_band_candidates,
    fuzzy_simhash,
    get_simhash_bands,
    normalize_text,
)


def test_normalize_text_strips_comments_and_docstrings() -> None:
    clear_normalize_cache()
    code = """
    # This is a comment
    def add(a, b):
        '''docstring'''
        return a + b  # inline comment
    """
    normalized = normalize_text(code)
    assert "#" not in normalized
    assert "'''docstring'''" not in normalized
    assert "def add(a, b):" in normalized
    assert "return a + b" in normalized


def test_normalize_text_caching() -> None:
    clear_normalize_cache()
    text = "x = 42\n# comment"
    res1 = normalize_text(text)
    res2 = normalize_text(text)
    assert res1 == res2
    assert res1 == "x = 42"


def test_extract_fuzzy_tokens() -> None:
    code = """
    def calculate_total(price, tax_rate):
        message = "Total is"
        multiplier = 1.05
        if price > 100:
            return price * tax_rate
        return 0
    """
    tokens = extract_fuzzy_tokens(code)
    # Check keywords preserved
    assert "def" in tokens
    assert "if" in tokens
    assert "return" in tokens
    # Identifiers and literals are mapped to 'ID'
    assert "id" not in tokens  # uppercase 'ID'
    assert "ID" in tokens
    assert ">" in tokens
    assert "*" in tokens


def test_fuzzy_simhash_stability() -> None:
    code1 = "def foo(a, b):\n    return a + b\n"
    code2 = "def foo(a, b):\n    return a + b\n"
    hash1 = fuzzy_simhash(code1)
    hash2 = fuzzy_simhash(code2)
    assert hash1 == hash2
    assert isinstance(hash1, int)
    assert hash1 > 0


def test_fuzzy_simhash_identifier_invariance() -> None:
    # Renaming variables should produce very similar or identical SimHash
    code1 = "def calculate_sum(val_x, val_y):\n    res = val_x + val_y\n    return res\n"
    code2 = "def compute_sum(arg_a, arg_b):\n    temp = arg_a + arg_b\n    return temp\n"
    hash1 = fuzzy_simhash(code1)
    hash2 = fuzzy_simhash(code2)
    # Both normalize to: def ID(ID, ID): ID = ID + ID return ID
    assert hash1 == hash2


def test_simhash_bands_and_candidates() -> None:
    fp1 = 0x1111222233334444
    bands1 = get_simhash_bands(fp1, num_bands=4, band_bits=16)
    assert len(bands1) == 4
    assert bands1[0] == 0x4444
    assert bands1[1] == 0x3333
    assert bands1[2] == 0x2222
    assert bands1[3] == 0x1111

    # Test candidate matching: item 0 and item 1 share 3 bands and have line_diff = 1
    fp2 = 0x111122223333FFFF  # shares bands 1, 2, 3
    items = [
        (0, fp1, ".py", 10),
        (1, fp2, ".py", 11),
        (2, 0x9999888877776666, ".py", 10),  # disjoint
    ]
    candidates = find_simhash_band_candidates(items, min_matching_bands=2, max_line_diff=4)
    assert 0 in candidates
    assert 1 in candidates[0]
    assert 2 not in candidates.get(0, set())


def test_minhash_features_and_similarity() -> None:
    text_a = "def process_data(items):\n    return [x * 2 for x in items]\n"
    text_b = "def process_data(items):\n    return [x * 2 for x in items]\n"
    text_c = "class ConfigurationManager:\n    def __init__(self):\n        self.timeout = 30\n"

    mh_a = create_simple_minhash(text_a, num_perm=64)
    mh_b = create_simple_minhash(text_b, num_perm=64)
    mh_c = create_simple_minhash(text_c, num_perm=64)

    # Identical text should have Jaccard = 1.0
    assert mh_a.jaccard(mh_b) == 1.0

    # Very different text should have low Jaccard
    assert mh_a.jaccard(mh_c) < 0.3


def test_backward_compatibility_aliases() -> None:
    assert _normalize_text is normalize_text
    assert _fuzzy_simhash is fuzzy_simhash
    assert _SimpleMinHash is SimpleMinHash
