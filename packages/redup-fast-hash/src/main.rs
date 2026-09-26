use std::env;
use std::fs;
use std::io::{self, BufRead};
use redup_fast_hash::simhash::compute_fuzzy_simhash;
use redup_fast_hash::similarity::sequence_ratio;

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage:");
        eprintln!("  redup-fast-hash --simhash <text>");
        eprintln!("  redup-fast-hash --file <path>");
        eprintln!("  redup-fast-hash --similarity <text_a> <text_b>");
        eprintln!("  redup-fast-hash --stdin-lines");
        std::process::exit(1);
    }

    match args[1].as_str() {
        "--simhash" => {
            if args.len() < 3 {
                eprintln!("Error: missing text argument");
                std::process::exit(1);
            }
            let text = &args[2];
            let hash = compute_fuzzy_simhash(text);
            println!("{}", hash);
        }
        "--similarity" => {
            if args.len() < 4 {
                eprintln!("Error: missing text_a or text_b argument");
                std::process::exit(1);
            }
            let text_a = &args[2];
            let text_b = &args[3];
            let ratio = sequence_ratio(text_a, text_b);
            println!("{:.6}", ratio);
        }
        "--file" => {
            if args.len() < 3 {
                eprintln!("Error: missing file path");
                std::process::exit(1);
            }
            match fs::read_to_string(&args[2]) {
                Ok(content) => {
                    let hash = compute_fuzzy_simhash(&content);
                    println!("{}", hash);
                }
                Err(err) => {
                    eprintln!("Error reading file {}: {}", args[2], err);
                    std::process::exit(1);
                }
            }
        }
        "--stdin-lines" => {
            let stdin = io::stdin();
            for line in stdin.lock().lines() {
                match line {
                    Ok(text) => {
                        let hash = compute_fuzzy_simhash(&text);
                        println!("{}", hash);
                    }
                    Err(_) => break,
                }
            }
        }
        "--stdin-pairs" => {
            let stdin = io::stdin();
            for line in stdin.lock().lines() {
                match line {
                    Ok(text) => {
                        if let Some((a, b)) = text.split_once('\t') {
                            let ratio = sequence_ratio(a, b);
                            println!("{:.6}", ratio);
                        }
                    }
                    Err(_) => break,
                }
            }
        }
        _ => {
            eprintln!("Unknown command: {}", args[1]);
            std::process::exit(1);
        }
    }
}
