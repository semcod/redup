//! redup-fast-hash: high performance fingerprinting and tokenization engine.

pub mod blake2b;
pub mod simhash;

pub use simhash::compute_fuzzy_simhash;
