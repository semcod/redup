//! redup-fast-hash: high performance fingerprinting, tokenization, and similarity engine.

pub mod blake2b;
pub mod lsh;
pub mod simhash;
pub mod similarity;

pub use lsh::{compute_minhash_signature, find_simhash_candidates, minhash_jaccard};
pub use simhash::compute_fuzzy_simhash;
pub use similarity::sequence_ratio;

use pyo3::prelude::*;

/// Python wrapper for sequence similarity ratio.
#[pyfunction]
#[pyo3(signature = (a, b))]
fn py_sequence_ratio(a: &str, b: &str) -> f64 {
    similarity::sequence_ratio(a, b)
}

/// Python wrapper for fuzzy simhash computation.
#[pyfunction]
#[pyo3(signature = (text))]
fn py_compute_fuzzy_simhash(text: &str) -> u64 {
    simhash::compute_fuzzy_simhash(text)
}

/// Batch compute sequence similarity ratios in parallel with Rayon, releasing GIL.
#[pyfunction]
#[pyo3(signature = (pairs))]
fn batch_similarity(py: Python<'_>, pairs: Vec<(String, String)>) -> Vec<f64> {
    use rayon::prelude::*;
    py.allow_threads(|| {
        pairs
            .par_iter()
            .map(|(a, b)| similarity::sequence_ratio(a, b))
            .collect()
    })
}

/// Batch compute fuzzy SimHash in parallel with Rayon, releasing GIL.
#[pyfunction]
#[pyo3(signature = (texts))]
fn batch_simhash(py: Python<'_>, texts: Vec<String>) -> Vec<u64> {
    use rayon::prelude::*;
    py.allow_threads(|| {
        texts
            .par_iter()
            .map(|t| simhash::compute_fuzzy_simhash(t))
            .collect()
    })
}

/// Python wrapper for find_simhash_candidates in parallel.
#[pyfunction]
#[pyo3(signature = (items, min_matching_bands = 2, max_line_diff = 4, num_bands = 4))]
fn py_find_simhash_candidates(
    py: Python<'_>,
    items: Vec<(usize, u64, String, usize)>,
    min_matching_bands: usize,
    max_line_diff: usize,
    num_bands: usize,
) -> std::collections::HashMap<usize, Vec<usize>> {
    py.allow_threads(|| {
        lsh::find_simhash_candidates(&items, min_matching_bands, max_line_diff, num_bands)
    })
}

/// Python wrapper for MinHash signature computation.
#[pyfunction]
#[pyo3(signature = (features, num_perm = 128))]
fn py_compute_minhash_signature(features: Vec<String>, num_perm: usize) -> Vec<u64> {
    lsh::compute_minhash_signature(&features, num_perm)
}

/// Python wrapper for MinHash Jaccard similarity.
#[pyfunction]
#[pyo3(signature = (a, b))]
fn py_minhash_jaccard(a: Vec<u64>, b: Vec<u64>) -> f64 {
    lsh::minhash_jaccard(&a, &b)
}

/// A Python module implemented in Rust.
#[pymodule]
fn redup_fast_hash(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(py_sequence_ratio, m)?)?;
    m.add_function(wrap_pyfunction!(py_compute_fuzzy_simhash, m)?)?;
    m.add_function(wrap_pyfunction!(batch_similarity, m)?)?;
    m.add_function(wrap_pyfunction!(batch_simhash, m)?)?;
    m.add_function(wrap_pyfunction!(py_find_simhash_candidates, m)?)?;
    m.add_function(wrap_pyfunction!(py_compute_minhash_signature, m)?)?;
    m.add_function(wrap_pyfunction!(py_minhash_jaccard, m)?)?;

    // Add aliases matching standard function names
    m.add("sequence_ratio", m.getattr("py_sequence_ratio")?)?;
    m.add("compute_fuzzy_simhash", m.getattr("py_compute_fuzzy_simhash")?)?;
    m.add("find_simhash_candidates", m.getattr("py_find_simhash_candidates")?)?;
    m.add("compute_minhash_signature", m.getattr("py_compute_minhash_signature")?)?;
    m.add("minhash_jaccard", m.getattr("py_minhash_jaccard")?)?;
    Ok(())
}

