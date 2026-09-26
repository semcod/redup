"""Pure tokenization, normalization, and fingerprinting engine for redup.

This module isolates pure algorithmic computation from domain models, AST objects,
and filesystem I/O. It provides exact, deterministic mathematical operations:
- Code normalization and comment/literal stripping
- Fuzzy token extraction and n-gram feature generation
- 64-bit SimHash calculation and LSH band candidate generation
- Permutation-based MinHash generation and Jaccard similarity estimation
"""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from collections.abc import Sequence

# ---------------------------------------------------------------------------
# Text Normalization
# ---------------------------------------------------------------------------

_MAX_CACHE_SIZE = 10_000
_normalize_cache: dict[str, str] = {}
_COMMENT_RE = re.compile(r"#.*$")
_MULTILINE_STRING_RE = re.compile(r'^\s*("""|\'\'\')')


def normalize_text(text: str) -> str:
    """Normalize code text for exact/structural comparison with caching."""
    cached = _normalize_cache.get(text)
    if cached is not None:
        return cached

    result_lines: list[str] = []
    for line in text.splitlines():
        if _MULTILINE_STRING_RE.match(line):
            continue
        cleaned = _COMMENT_RE.sub("", line).strip()
        if cleaned:
            result_lines.append(cleaned)

    result = "\n".join(result_lines)
    if len(_normalize_cache) >= _MAX_CACHE_SIZE:
        _normalize_cache.pop(next(iter(_normalize_cache)))
    _normalize_cache[text] = result
    return result


def clear_normalize_cache() -> None:
    """Clear internal text normalization cache."""
    _normalize_cache.clear()


# ---------------------------------------------------------------------------
# Fuzzy Tokenizer & SimHash
# ---------------------------------------------------------------------------

FUZZY_KEYWORDS: frozenset[str] = frozenset(
    {
        "and",
        "as",
        "async",
        "await",
        "break",
        "case",
        "catch",
        "class",
        "const",
        "continue",
        "def",
        "do",
        "else",
        "except",
        "false",
        "finally",
        "for",
        "foreach",
        "from",
        "function",
        "if",
        "import",
        "in",
        "let",
        "match",
        "new",
        "none",
        "not",
        "null",
        "or",
        "pass",
        "raise",
        "return",
        "switch",
        "throw",
        "true",
        "try",
        "var",
        "while",
        "with",
        "yield",
    }
)

_FUZZY_TOKEN_RE = re.compile(
    r"[A-Za-z_$][A-Za-z0-9_$]*|==={0,1}|!==?|<=|>=|=>|\+\+|--|&&|\|\||\?\?|\S"
)
_IDENTIFIER_START_RE = re.compile(r"^[A-Za-z_$]")


def extract_fuzzy_tokens(text: str) -> list[str]:
    """Tokenize code text, masking identifiers and string/numeric literals."""
    cleaned = re.sub(r"/\*.*?\*/|//[^\n]*|#[^\n]*", " ", text, flags=re.DOTALL)
    cleaned = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', " STR ", cleaned)
    cleaned = re.sub(r"\b\d+(?:\.\d+)?\b", " NUM ", cleaned)

    tokens: list[str] = []
    for token in _FUZZY_TOKEN_RE.findall(cleaned):
        lowered = token.lower()
        if _IDENTIFIER_START_RE.match(token) and lowered not in FUZZY_KEYWORDS:
            tokens.append("ID")
        else:
            tokens.append(lowered)
    return tokens


def compute_simhash_from_tokens(tokens: Sequence[str], width: int = 3) -> int:
    """Compute 64-bit SimHash from normalized token sequence."""
    ngram_width = width if len(tokens) >= width else 1
    features = [
        "\x1f".join(tokens[i : i + ngram_width])
        for i in range(len(tokens) - ngram_width + 1)
    ]
    if not features:
        return 0

    weights = [0] * 64
    for feature in features:
        value = int.from_bytes(
            hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest(), "big"
        )
        for bit in range(64):
            weights[bit] += 1 if value & (1 << bit) else -1

    return sum(1 << bit for bit, weight in enumerate(weights) if weight >= 0)


def fuzzy_simhash(text: str) -> int:
    """Return a language-neutral 64-bit SimHash for fuzzy shortlisting."""
    tokens = extract_fuzzy_tokens(text)
    return compute_simhash_from_tokens(tokens, width=3)


def get_simhash_bands(fingerprint: int, num_bands: int = 4, band_bits: int = 16) -> list[int]:
    """Extract integer bands from 64-bit fingerprint."""
    mask = (1 << band_bits) - 1
    return [(fingerprint >> (band * band_bits)) & mask for band in range(num_bands)]


def find_simhash_band_candidates(
    items: Sequence[tuple[int, int, str, int]],
    min_matching_bands: int = 2,
    max_line_diff: int = 4,
    num_bands: int = 4,
) -> dict[int, set[int]]:
    """Build candidate pairs from SimHash bands.

    Args:
        items: list of tuples (item_index, fingerprint, group_tag, line_count).
        min_matching_bands: minimum number of shared 16-bit bands to form a candidate pair.
        max_line_diff: maximum line count difference between candidate items.
        num_bands: number of bands to slice (default 4 x 16 bits = 64 bits).

    Returns:
        dict mapping left item index to set of right item indices.
    """
    buckets: dict[tuple[str, int, int], list[int]] = defaultdict(list)
    band_hits: dict[tuple[int, int], int] = defaultdict(int)
    result: dict[int, set[int]] = defaultdict(set)

    for index, fingerprint, group_tag, line_count in items:
        for band in range(num_bands):
            band_val = (fingerprint >> (band * 16)) & 0xFFFF
            key = (group_tag, band, band_val)
            for other_index in buckets[key]:
                other_line_count = items[other_index][3]
                if abs(other_line_count - line_count) <= max_line_diff:
                    band_hits[(other_index, index)] += 1
            buckets[key].append(index)

    for (left, right), matching_bands in band_hits.items():
        if matching_bands >= min_matching_bands:
            result[left].add(right)

    return result


# ---------------------------------------------------------------------------
# MinHash & Jaccard Estimation
# ---------------------------------------------------------------------------

def extract_minhash_features(text: str, num_features: int = 10) -> list[str]:
    """Extract n-gram text features for MinHash without external dependencies."""
    normalized = normalize_text(text)
    words = normalized.split()
    if not words:
        return []

    features: list[str] = []
    # Single words
    features.extend(words[: num_features // 2])

    # 2-grams
    max_2grams = min(len(words) - 1, num_features - len(features))
    for i in range(max_2grams):
        features.append(f"{words[i]} {words[i + 1]}")

    # 3-grams
    remaining = num_features - len(features)
    max_3grams = min(len(words) - 2, remaining)
    for i in range(max_3grams):
        features.append(f"{words[i]} {words[i + 1]} {words[i + 2]}")

    return features[:num_features]


def compute_simple_minhash_values(
    features: Sequence[str], num_perm: int = 128
) -> list[int]:
    """Compute MinHash permutation array for given features."""
    hash_values: list[int] = []
    for i in range(num_perm):
        seed = i + 1
        min_hash = float("inf")
        for feature in features:
            hash_input = f"{feature}_{seed}"
            hash_val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            if hash_val < min_hash:
                min_hash = hash_val
        hash_values.append(int(min_hash))
    return hash_values


def compute_jaccard_similarity(
    hash_values_a: Sequence[int], hash_values_b: Sequence[int]
) -> float:
    """Estimate Jaccard similarity between two MinHash permutation vectors."""
    if not hash_values_a or len(hash_values_a) != len(hash_values_b):
        return 0.0
    matches = sum(1 for a, b in zip(hash_values_a, hash_values_b, strict=True) if a == b)
    return matches / len(hash_values_a)


class SimpleMinHash:
    """Simple MinHash implementation for fallback without datasketch."""

    def __init__(self, features: list[str], num_perm: int = 128) -> None:
        self.num_perm = num_perm
        self.hash_values = compute_simple_minhash_values(features, num_perm)

    def jaccard(self, other: SimpleMinHash) -> float:
        """Estimate Jaccard similarity."""
        return compute_jaccard_similarity(self.hash_values, other.hash_values)


def create_simple_minhash(text: str, num_perm: int = 128) -> SimpleMinHash:
    """Create simple MinHash from text without external dependencies."""
    features = extract_minhash_features(text)
    return SimpleMinHash(features, num_perm)


# Backward compatibility aliases
_normalize_text = normalize_text
_fuzzy_simhash = fuzzy_simhash
_text_to_minhash_features = extract_minhash_features
_create_simple_minhash = create_simple_minhash
_SimpleMinHash = SimpleMinHash
