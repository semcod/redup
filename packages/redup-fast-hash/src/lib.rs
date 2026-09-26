//! redup-fast-hash: high performance fingerprinting, tokenization, and similarity engine.

pub mod blake2b;
pub mod simhash;
pub mod similarity;

pub use simhash::compute_fuzzy_simhash;
pub use similarity::sequence_ratio;
