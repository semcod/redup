//! High-performance sequence similarity engine (Gestalt pattern matching / Ratcliff-Obershelp).
//!
//! Provides exact ratio matching with Python's difflib.SequenceMatcher.ratio() and rapidfuzz.fuzz.ratio.

/// Find the longest common contiguous slice between a[alo..ahi] and b[blo..bhi].
fn find_best_match(
    a: &[u8],
    alo: usize,
    ahi: usize,
    b: &[u8],
    blo: usize,
    bhi: usize,
    b_pos: &[Vec<usize>; 256],
) -> (usize, usize, usize) {
    let mut best_i = alo;
    let mut best_j = blo;
    let mut best_size = 0;

    let mut i = alo;
    while i < ahi {
        let byte = a[i] as usize;
        let positions = &b_pos[byte];

        for &j in positions {
            if j < blo {
                continue;
            }
            if j >= bhi {
                break;
            }

            // Quick check: can this match exceed best_size?
            if (ahi - i).min(bhi - j) <= best_size {
                continue;
            }

            let mut k = 1;
            while i + k < ahi && j + k < bhi && a[i + k] == b[j + k] {
                k += 1;
            }

            if k > best_size {
                best_i = i;
                best_j = j;
                best_size = k;
            }
        }
        i += 1;
    }

    (best_i, best_j, best_size)
}

/// Recursively sum lengths of all matching contiguous blocks.
fn count_matches(
    a: &[u8],
    alo: usize,
    ahi: usize,
    b: &[u8],
    blo: usize,
    bhi: usize,
    b_pos: &[Vec<usize>; 256],
) -> usize {
    let (best_i, best_j, best_size) = find_best_match(a, alo, ahi, b, blo, bhi, b_pos);
    if best_size == 0 {
        return 0;
    }

    let left = if best_i > alo && best_j > blo {
        count_matches(a, alo, best_i, b, blo, best_j, b_pos)
    } else {
        0
    };

    let right = if best_i + best_size < ahi && best_j + best_size < bhi {
        count_matches(
            a,
            best_i + best_size,
            ahi,
            b,
            best_j + best_size,
            bhi,
            b_pos,
        )
    } else {
        0
    };

    left + best_size + right
}

/// Return sequence similarity ratio between 0.0 and 1.0.
///
/// Matches difflib.SequenceMatcher(None, a, b).ratio() and rapidfuzz.fuzz.ratio(a, b) / 100.0.
pub fn sequence_ratio(a: &str, b: &str) -> f64 {
    let a_bytes = a.as_bytes();
    let b_bytes = b.as_bytes();
    let total_len = a_bytes.len() + b_bytes.len();

    if total_len == 0 {
        return 1.0;
    }
    if a_bytes == b_bytes {
        return 1.0;
    }

    // Build byte index for b
    let mut b_pos: [Vec<usize>; 256] = std::array::from_fn(|_| Vec::new());
    for (idx, &byte) in b_bytes.iter().enumerate() {
        b_pos[byte as usize].push(idx);
    }

    let matches = count_matches(a_bytes, 0, a_bytes.len(), b_bytes, 0, b_bytes.len(), &b_pos);
    (2.0 * matches as f64) / (total_len as f64)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_identical_strings() {
        assert_eq!(sequence_ratio("x = 1", "x = 1"), 1.0);
        assert_eq!(sequence_ratio("", ""), 1.0);
    }

    #[test]
    fn test_completely_different() {
        let sim = sequence_ratio("abc", "xyz");
        assert_eq!(sim, 0.0);
    }

    #[test]
    fn test_close_code_snippets() {
        let a = "def foo(x):\n    return x + 1";
        let b = "def foo(y):\n    return y + 1";
        let sim = sequence_ratio(a, b);
        let expected = 52.0 / 56.0;
        assert!((sim - expected).abs() < 1e-6);
        assert!(sim > 0.9);
    }
}
