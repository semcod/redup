//! Fast Local Sensitivity Hashing (LSH) and candidate generation.

use std::collections::{HashMap, HashSet};

/// Interned tag ID for compact integer keys.
#[inline]
fn tag_id(tag: &str, tag_map: &mut HashMap<String, u16>) -> u16 {
    if let Some(&id) = tag_map.get(tag) {
        return id;
    }
    let next_id = tag_map.len() as u16;
    tag_map.insert(tag.to_string(), next_id);
    next_id
}

/// Find candidate pairs from SimHash bands in native Rust.
///
/// Args:
///     items: list of (item_index, fingerprint, group_tag, line_count)
///     min_matching_bands: minimum matching bands (default 2)
///     max_line_diff: maximum line count difference (default 4)
///     num_bands: number of bands (default 4)
///
/// Returns:
///     Map of left_index -> sorted list of candidate right_indices
pub fn find_simhash_candidates(
    items: &[(usize, u64, String, usize)],
    min_matching_bands: usize,
    max_line_diff: usize,
    num_bands: usize,
) -> HashMap<usize, Vec<usize>> {
    let mut tag_map: HashMap<String, u16> = HashMap::new();

    // Map: bucket_key (u64) -> list of item indices
    // bucket_key: [tag_id: 16 bits][band: 16 bits][band_val: 16 bits]
    let mut buckets: HashMap<u64, Vec<usize>> = HashMap::with_capacity(items.len() * num_bands);
    // Key: ((left as u64) << 32) | (right as u64) -> count of hits
    let mut band_hits: HashMap<u64, usize> = HashMap::new();

    for &(index, fingerprint, ref group_tag, line_count) in items {
        let tid = tag_id(group_tag, &mut tag_map) as u64;
        for band in 0..num_bands {
            let band_val = ((fingerprint >> (band * 16)) & 0xFFFF) as u64;
            let key = (tid << 32) | ((band as u64) << 16) | band_val;

            if let Some(other_indices) = buckets.get(&key) {
                for &other_index in other_indices {
                    let other_line_count = items[other_index].3;
                    let diff = if line_count >= other_line_count {
                        line_count - other_line_count
                    } else {
                        other_line_count - line_count
                    };
                    if diff <= max_line_diff {
                        let pair_key = ((other_index as u64) << 32) | (index as u64);
                        *band_hits.entry(pair_key).or_insert(0) += 1;
                    }
                }
            }
            buckets.entry(key).or_default().push(index);
        }
    }

    let mut result: HashMap<usize, HashSet<usize>> = HashMap::new();
    for (pair_key, count) in band_hits {
        if count >= min_matching_bands {
            let left = (pair_key >> 32) as usize;
            let right = (pair_key & 0xFFFF_FFFF) as usize;
            result.entry(left).or_default().insert(right);
        }
    }

    result
        .into_iter()
        .map(|(k, v)| {
            let mut sorted: Vec<usize> = v.into_iter().collect();
            sorted.sort_unstable();
            (k, sorted)
        })
        .collect()
}

/// Compute simple MinHash universal hash array for n-gram features.
///
/// Uses standard linear congruential universal hashing h_i(x) = (a_i * x + b_i) mod p
pub fn compute_minhash_signature(features: &[String], num_perm: usize) -> Vec<u64> {
    if features.is_empty() {
        return vec![0; num_perm];
    }

    // Mersenne prime 2^61 - 1
    const MERSENNE_PRIME: u64 = (1 << 61) - 1;

    let mut min_hashes = vec![u64::MAX; num_perm];

    for feat in features {
        let base_hash = crate::blake2b::blake2b_8_u64(feat.as_bytes());
        for i in 0..num_perm {
            let seed = (i as u64) + 1;
            let a = seed.wrapping_mul(0x517cc1b727220a95).wrapping_add(1);
            let b = seed.wrapping_mul(0x9e3779b97f4a7c15).wrapping_add(3);
            let h = a.wrapping_mul(base_hash).wrapping_add(b) % MERSENNE_PRIME;
            if h < min_hashes[i] {
                min_hashes[i] = h;
            }
        }
    }

    min_hashes
}

/// Calculate Jaccard similarity between two MinHash signature vectors.
pub fn minhash_jaccard(a: &[u64], b: &[u64]) -> f64 {
    if a.is_empty() || a.len() != b.len() {
        return 0.0;
    }
    let matches = a.iter().zip(b.iter()).filter(|(&x, &y)| x == y).count();
    matches as f64 / a.len() as f64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simhash_band_candidates_basic() {
        let items = vec![
            (0, 0x1234_5678_9ABC_DEF0, ".py".to_string(), 10),
            (1, 0x1234_5678_9ABC_0000, ".py".to_string(), 12),
            (2, 0xFFFF_EEEE_DDDD_CCCC, ".py".to_string(), 10),
        ];
        let candidates = find_simhash_candidates(&items, 2, 4, 4);
        assert_eq!(candidates.get(&0), Some(&vec![1]));
        assert!(!candidates.contains_key(&2));
    }

    #[test]
    fn test_simhash_band_candidates_line_diff() {
        let items = vec![
            (0, 0x1234_5678_9ABC_DEF0, ".py".to_string(), 10),
            (1, 0x1234_5678_9ABC_DEF0, ".py".to_string(), 20), // diff 10 > max 4
        ];
        let candidates = find_simhash_candidates(&items, 2, 4, 4);
        assert!(!candidates.contains_key(&0));
    }

    #[test]
    fn test_minhash_signature_identical() {
        let feats = vec!["def foo".to_string(), "foo bar".to_string()];
        let sig1 = compute_minhash_signature(&feats, 128);
        let sig2 = compute_minhash_signature(&feats, 128);
        assert_eq!(sig1, sig2);
        assert_eq!(minhash_jaccard(&sig1, &sig2), 1.0);
    }

    #[test]
    fn test_minhash_signature_different() {
        let f1 = vec!["alpha beta".to_string(), "gamma delta".to_string()];
        let f2 = vec!["one two".to_string(), "three four".to_string()];
        let sig1 = compute_minhash_signature(&f1, 128);
        let sig2 = compute_minhash_signature(&f2, 128);
        let sim = minhash_jaccard(&sig1, &sig2);
        assert!(sim < 0.1);
    }
}
