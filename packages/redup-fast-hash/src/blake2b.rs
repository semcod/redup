//! Minimal zero-dependency RFC 7693 BLAKE2b implementation.

const IV: [u64; 8] = [
    0x6a09e667f3bcc908, 0xbb67ae8584caa73b,
    0x3c6ef372fe94f82b, 0xa54ff53a5f1d36f1,
    0x510e527fade682d1, 0x9b05688c2b3e6c1f,
    0x1f83d9abfb41bd6b, 0x5be0cd19137e2179,
];

const SIGMA: [[usize; 16]; 12] = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    [14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3],
    [11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4],
    [7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8],
    [9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13],
    [2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9],
    [12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11],
    [13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10],
    [6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5],
    [10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0],
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    [14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3],
];

#[inline(always)]
fn g(v: &mut [u64; 16], a: usize, b: usize, c: usize, d: usize, x: u64, y: u64) {
    v[a] = v[a].wrapping_add(v[b]).wrapping_add(x);
    v[d] = (v[d] ^ v[a]).rotate_right(32);
    v[c] = v[c].wrapping_add(v[d]);
    v[b] = (v[b] ^ v[c]).rotate_right(24);
    v[a] = v[a].wrapping_add(v[b]).wrapping_add(y);
    v[d] = (v[d] ^ v[a]).rotate_right(16);
    v[c] = v[c].wrapping_add(v[d]);
    v[b] = (v[b] ^ v[c]).rotate_right(63);
}

fn compress(h: &mut [u64; 8], block: &[u8; 128], count: u64, is_last: bool) {
    let mut m = [0u64; 16];
    for i in 0..16 {
        m[i] = u64::from_le_bytes(block[i * 8..(i + 1) * 8].try_into().unwrap());
    }

    let mut v = [0u64; 16];
    v[0..8].copy_from_slice(h);
    v[8..16].copy_from_slice(&IV);
    v[12] ^= count;
    if is_last {
        v[14] ^= !0;
    }

    for round in 0..12 {
        let s = &SIGMA[round];
        g(&mut v, 0, 4, 8, 12, m[s[0]], m[s[1]]);
        g(&mut v, 1, 5, 9, 13, m[s[2]], m[s[3]]);
        g(&mut v, 2, 6, 10, 14, m[s[4]], m[s[5]]);
        g(&mut v, 3, 7, 11, 15, m[s[6]], m[s[7]]);
        g(&mut v, 0, 5, 10, 15, m[s[8]], m[s[9]]);
        g(&mut v, 1, 6, 11, 12, m[s[10]], m[s[11]]);
        g(&mut v, 2, 7, 8, 13, m[s[12]], m[s[13]]);
        g(&mut v, 3, 4, 9, 14, m[s[14]], m[s[15]]);
    }

    for i in 0..8 {
        h[i] ^= v[i] ^ v[i + 8];
    }
}

/// Compute BLAKE2b hash with 8-byte digest matching hashlib.blake2b(data, digest_size=8).
pub fn blake2b_8(data: &[u8]) -> [u8; 8] {
    let mut h = IV;
    // Parameter block: digest_size = 8, key_len = 0, fanout = 1, depth = 1
    h[0] ^= 0x01010008;

    let mut block = [0u8; 128];
    let mut offset = 0;
    let len = data.len();

    if len == 0 {
        compress(&mut h, &block, 0, true);
    } else {
        while offset + 128 < len {
            block.copy_from_slice(&data[offset..offset + 128]);
            offset += 128;
            compress(&mut h, &block, offset as u64, false);
        }
        let remainder = len - offset;
        block.fill(0);
        block[..remainder].copy_from_slice(&data[offset..]);
        compress(&mut h, &block, len as u64, true);
    }

    let mut out = [0u8; 8];
    out.copy_from_slice(&h[0].to_le_bytes());
    out
}

/// Return BLAKE2b 8-byte digest interpreted as big-endian u64,
/// exactly matching `int.from_bytes(hashlib.blake2b(data, digest_size=8).digest(), "big")`.
pub fn blake2b_8_u64(data: &[u8]) -> u64 {
    let digest = blake2b_8(data);
    u64::from_be_bytes(digest)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_blake2b_empty() {
        let digest = blake2b_8(b"");
        let hex: String = digest.iter().map(|b| format!("{:02x}", b)).collect();
        assert_eq!(hex, "e4a6a0577479b2b4");
    }

    #[test]
    fn test_blake2b_hello() {
        let digest = blake2b_8(b"hello");
        let hex: String = digest.iter().map(|b| format!("{:02x}", b)).collect();
        assert_eq!(hex, "a7b6eda801e5347d");
    }
}
