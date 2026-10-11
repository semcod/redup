//! redup-fast-hash: high performance fingerprinting, tokenization, and similarity engine.

pub mod blake2b;
pub mod simhash;
pub mod similarity;

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

/// A Python module implemented in Rust.
#[pymodule]
fn redup_fast_hash(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(py_sequence_ratio, m)?)?;
    m.add_function(wrap_pyfunction!(py_compute_fuzzy_simhash, m)?)?;
    m.add_function(wrap_pyfunction!(batch_similarity, m)?)?;
    // Add aliases matching standard function names
    m.add("sequence_ratio", m.getattr("py_sequence_ratio")?)?;
    m.add("compute_fuzzy_simhash", m.getattr("py_compute_fuzzy_simhash")?)?;
    Ok(())
}
