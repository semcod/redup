//! Fast SimHash computation with zero external dependencies.

use crate::blake2b::blake2b_8_u64;

pub const FUZZY_KEYWORDS: &[&str] = &[
    "and", "as", "async", "await", "break", "case", "catch", "class", "const", "continue", "def",
    "do", "else", "except", "false", "finally", "for", "foreach", "from", "function", "if",
    "import", "in", "let", "match", "new", "none", "not", "null", "or", "pass", "raise", "return",
    "switch", "throw", "true", "try", "var", "while", "with", "yield",
];

#[inline]
pub fn is_fuzzy_keyword(word: &str) -> bool {
    FUZZY_KEYWORDS.contains(&word)
}

/// Strip comments, string literals, and numbers from code text.
pub fn clean_code_for_fuzzy(text: &str) -> String {
    let bytes = text.as_bytes();
    let len = bytes.len();
    let mut out = String::with_capacity(len);
    let mut i = 0;

    while i < len {
        let b = bytes[i];

        // Keep unmatched Unicode intact. The scanners below recognize ASCII
        // delimiters; UTF-8 continuation bytes cannot be those delimiters.
        if !b.is_ascii() {
            let ch = text[i..].chars().next().unwrap();
            out.push(ch);
            i += ch.len_utf8();
            continue;
        }

        // Block comment /* ... */
        if b == b'/' && i + 1 < len && bytes[i + 1] == b'*' {
            i += 2;
            while i + 1 < len && !(bytes[i] == b'*' && bytes[i + 1] == b'/') {
                i += 1;
            }
            i = (i + 2).min(len);
            out.push(' ');
            continue;
        }

        // Line comment //
        if b == b'/' && i + 1 < len && bytes[i + 1] == b'/' {
            i += 2;
            while i < len && bytes[i] != b'\n' {
                i += 1;
            }
            out.push(' ');
            continue;
        }

        // Line comment #
        if b == b'#' {
            i += 1;
            while i < len && bytes[i] != b'\n' {
                i += 1;
            }
            out.push(' ');
            continue;
        }

        // String literals "..." or '...'
        if b == b'"' || b == b'\'' {
            let quote = b;
            i += 1;
            while i < len {
                if bytes[i] == b'\\' {
                    i += 2; // skip escaped char
                } else if bytes[i] == quote {
                    i += 1;
                    break;
                } else {
                    i += 1;
                }
            }
            out.push_str(" STR ");
            continue;
        }

        // Numbers \b\d+(\.\d+)?\b
        if b.is_ascii_digit() {
            let is_word_boundary_before = i == 0
                || !(bytes[i - 1].is_ascii_alphanumeric()
                    || bytes[i - 1] == b'_'
                    || bytes[i - 1] == b'$');
            if is_word_boundary_before {
                while i < len && bytes[i].is_ascii_digit() {
                    i += 1;
                }
                if i + 1 < len && bytes[i] == b'.' && bytes[i + 1].is_ascii_digit() {
                    i += 1;
                    while i < len && bytes[i].is_ascii_digit() {
                        i += 1;
                    }
                }
                let is_word_boundary_after = i >= len
                    || !(bytes[i].is_ascii_alphanumeric() || bytes[i] == b'_' || bytes[i] == b'$');
                if is_word_boundary_after {
                    out.push_str(" NUM ");
                    continue;
                }
            }
        }

        out.push(b as char);
        i += 1;
    }

    out
}

/// Tokenize cleaned code text into normalized tokens.
pub fn extract_fuzzy_tokens(cleaned: &str) -> Vec<String> {
    let bytes = cleaned.as_bytes();
    let len = bytes.len();
    let mut tokens = Vec::new();
    let mut i = 0;

    while i < len {
        let b = bytes[i];

        if b.is_ascii_whitespace() {
            i += 1;
            continue;
        }

        // Identifiers: [A-Za-z_$][A-Za-z0-9_$]*
        if b.is_ascii_alphabetic() || b == b'_' || b == b'$' {
            let start = i;
            i += 1;
            while i < len
                && (bytes[i].is_ascii_alphanumeric() || bytes[i] == b'_' || bytes[i] == b'$')
            {
                i += 1;
            }
            let word = &cleaned[start..i];
            let lower = word.to_ascii_lowercase();
            if is_fuzzy_keyword(&lower) {
                tokens.push(lower);
            } else {
                tokens.push("ID".to_string());
            }
            continue;
        }

        // Multi-char operators: ===, !==, ==, !=, <=, >=, =>, ++, --, &&, ||, ??
        let rem = &cleaned[i..];
        if rem.starts_with("===") || rem.starts_with("!==") {
            tokens.push(rem[..3].to_string());
            i += 3;
            continue;
        }
        let op2 = ["==", "!=", "<=", ">=", "=>", "++", "--", "&&", "||", "??"]
            .iter()
            .find(|&&op| rem.starts_with(op));
        if let Some(&op) = op2 {
            tokens.push(op.to_string());
            i += 2;
            continue;
        }

        // Single non-whitespace character
        // Extract UTF-8 char
        let ch = cleaned[i..].chars().next().unwrap();
        tokens.push(ch.to_lowercase().to_string());
        i += ch.len_utf8();
    }

    tokens
}

/// Compute 64-bit SimHash from code text.
pub fn compute_fuzzy_simhash(text: &str) -> u64 {
    let cleaned = clean_code_for_fuzzy(text);
    let tokens = extract_fuzzy_tokens(&cleaned);
    if tokens.is_empty() {
        return 0;
    }

    let width = if tokens.len() >= 3 { 3 } else { 1 };
    let mut weights = [0i32; 64];

    // Build n-gram buffer reusing memory
    let mut feature_buf = String::with_capacity(64);

    for i in 0..=(tokens.len() - width) {
        feature_buf.clear();
        for (j, token) in tokens[i..i + width].iter().enumerate() {
            if j > 0 {
                feature_buf.push('\x1f');
            }
            feature_buf.push_str(token);
        }

        let value = blake2b_8_u64(feature_buf.as_bytes());
        for bit in 0..64 {
            if (value & (1u64 << bit)) != 0 {
                weights[bit] += 1;
            } else {
                weights[bit] -= 1;
            }
        }
    }

    let mut fingerprint = 0u64;
    for bit in 0..64 {
        if weights[bit] >= 0 {
            fingerprint |= 1u64 << bit;
        }
    }

    fingerprint
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simhash_basic() {
        let code = "def add(a, b):\n    return a + b\n";
        let fp1 = compute_fuzzy_simhash(code);
        let fp2 = compute_fuzzy_simhash(code);
        assert_eq!(fp1, fp2);
        assert!(fp1 > 0);
    }

    #[test]
    fn test_simhash_identifier_rename() {
        let code1 = "def calculate_sum(val_x, val_y):\n    res = val_x + val_y\n    return res\n";
        let code2 = "def compute_sum(arg_a, arg_b):\n    temp = arg_a + arg_b\n    return temp\n";
        let fp1 = compute_fuzzy_simhash(code1);
        let fp2 = compute_fuzzy_simhash(code2);
        assert_eq!(fp1, fp2);
    }

    #[test]
    fn test_unicode_python_reference_vectors() {
        // Generated from Python extract_fuzzy_tokens and prefer_rust=False.
        // Its identifier regex is ASCII-only: Unicode letters remain tokens,
        // including inside mixed identifiers. Backticks are not string quotes.
        let cases: &[(&str, &str, &[&str], u64)] = &[
            (
                "def add(a, b): return a + b",
                "def add(a, b): return a + b",
                &[
                    "def", "ID", "(", "ID", ",", "ID", ")", ":", "return", "ID", "+", "ID",
                ],
                1999307407177186558,
            ),
            ("ą", "ą", &["ą"], 2684146023269591358),
            (
                "zażółć gęślą jaźń",
                "zażółć gęślą jaźń",
                &[
                    "ID", "ż", "ó", "ł", "ć", "ID", "ę", "ś", "ID", "ą", "ID", "ź", "ń",
                ],
                3173260504582634983,
            ),
            ("😀value", "😀value", &["😀", "ID"], 17867692854670522352),
            (
                "const źródło = `żółć`;",
                "const źródło = `żółć`;",
                &[
                    "const", "ź", "ID", "ó", "ID", "ł", "ID", "=", "`", "ż", "ó", "ł", "ć", "`",
                    ";",
                ],
                16890555981135166839,
            ),
            (
                "fn 変数() {return 1;}",
                "fn 変数() {return  NUM ;}",
                &["ID", "変", "数", "(", ")", "{", "return", "ID", ";", "}"],
                8428574849076232171,
            ),
            (
                "ą/* 😀 */+変数// żółć\n😀# ą\nź",
                "ą +変数 \n😀 \nź",
                &["ą", "+", "変", "数", "😀", "ź"],
                8016116748811581599,
            ),
            (
                "ą\"😀\"+'変数'; return 12.5;",
                "ą STR + STR ; return  NUM ;",
                &["ą", "ID", "+", "ID", ";", "return", "ID", ";"],
                8713030534196668199,
            ),
            (
                "ą\"\\😀\"ź",
                "ą STR ź",
                &["ą", "ID", "ź"],
                13292627870420614445,
            ),
            (
                "RETURN foo_2 + $bar == 12.5; // note",
                "RETURN foo_2 + $bar ==  NUM ;  ",
                &["return", "ID", "+", "ID", "==", "ID", ";"],
                8785272967380082946,
            ),
            (
                "ą===😀!=変数",
                "ą===😀!=変数",
                &["ą", "===", "😀", "!=", "変", "数"],
                8056867025399037722,
            ),
            (
                "aąB_2😀z",
                "aąB_2😀z",
                &["ID", "ą", "ID", "😀", "ID"],
                462200693447372014,
            ),
            (
                "Ąİ変数😀",
                "Ąİ変数😀",
                &["ą", "i\u{307}", "変", "数", "😀"],
                3857494918881161239,
            ),
        ];

        for &(source, cleaned, tokens, fingerprint) in cases {
            assert_eq!(clean_code_for_fuzzy(source), cleaned, "source: {source:?}");
            assert_eq!(extract_fuzzy_tokens(cleaned), tokens, "source: {source:?}");
            assert_eq!(
                compute_fuzzy_simhash(source),
                fingerprint,
                "source: {source:?}"
            );
        }
    }

    #[test]
    fn test_unicode_at_unterminated_construct_boundaries() {
        // Incomplete source is valid UTF-8 too. Preserve the existing stripping
        // behavior while exercising byte scanners at the end of multibyte text.
        for (source, cleaned) in [
            ("ą/*😀", "ą "),
            ("ą//😀", "ą "),
            ("ą#😀", "ą "),
            ("ą\"😀", "ą STR "),
            ("ą'\\😀", "ą STR "),
            ("ą\"😀\\", "ą STR "),
        ] {
            assert_eq!(clean_code_for_fuzzy(source), cleaned);
            compute_fuzzy_simhash(source);
        }
    }
}
