#!/usr/bin/env python3
"""Simple performance benchmark for reDUP."""

import time
from pathlib import Path

import sys
sys.path.insert(0, 'src')

from redup.core.pipeline import analyze, analyze_parallel
from redup.core.models import ScanConfig


def benchmark_sequential_vs_parallel():
    """Compare sequential vs parallel scanning performance."""
    
    print("🚀 reDUP Performance Benchmark")
    print("=" * 50)
    
    # Test configuration
    config = ScanConfig(
        root=Path("src"),
        extensions=[".py"],
        min_block_lines=3,
        min_similarity=0.85,
        include_tests=False,
    )
    
    # Sequential scan
    print("\n📊 Sequential Scanning...")
    start_time = time.time()
    result_seq = analyze(config=config, function_level_only=True)
    seq_time = time.time() - start_time
    
    print(f"  Time: {seq_time:.3f}s")
    print(f"  Files: {result_seq.stats.files_scanned}")
    print(f"  Lines: {result_seq.stats.total_lines}")
    print(f"  Groups: {result_seq.total_groups}")
    
    # Parallel scan
    print("\n⚡ Parallel Scanning...")
    start_time = time.time()
    result_par = analyze_parallel(config=config, function_level_only=True, max_workers=4)
    par_time = time.time() - start_time
    
    print(f"  Time: {par_time:.3f}s")
    print(f"  Files: {result_par.stats.files_scanned}")
    print(f"  Lines: {result_par.stats.total_lines}")
    print(f"  Groups: {result_par.total_groups}")
    
    # Performance comparison
    print("\n📈 Performance Comparison:")
    if par_time > 0:
        speedup = seq_time / par_time
        print(f"  Speedup: {speedup:.2f}x")
        print(f"  Time saved: {((seq_time - par_time) / seq_time * 100):.1f}%")
    
    # Verify results are similar
    groups_diff = abs(result_seq.total_groups - result_par.total_groups)
    if groups_diff == 0:
        print("  ✅ Results identical")
    else:
        print(f"  ⚠️  Groups differ by {groups_diff}")


def benchmark_feature_performance():
    """Test performance of different features."""
    
    print("\n🔬 Feature Performance Test")
    print("=" * 50)
    
    configs = [
        ("Basic (exact + structural)", ScanConfig(
            root=Path("src"),
            extensions=[".py"],
            min_block_lines=3,
            min_similarity=0.85,
            lsh_enabled=False,
        )),
        ("With LSH enabled", ScanConfig(
            root=Path("src"),
            extensions=[".py"],
            min_block_lines=3,
            min_similarity=0.85,
            lsh_enabled=True,
            lsh_min_lines=30,  # Lower threshold for testing
            lsh_threshold=0.7,
        )),
    ]
    
    for name, config in configs:
        print(f"\n📋 {name}:")
        start_time = time.time()
        result = analyze_parallel(config=config, function_level_only=True)
        elapsed = time.time() - start_time
        
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Groups: {result.total_groups}")
        print(f"  Types: {len(set(g.duplicate_type for g in result.groups))}")


if __name__ == "__main__":
    benchmark_sequential_vs_parallel()
    benchmark_feature_performance()
    
    print("\n✅ Benchmark complete!")
    print("\n💡 Tips:")
    print("  - Use --parallel for large projects (>50 files)")
    print("  - Enable LSH for projects with large functions (>50 lines)")
    print("  - Use --functions-only for fastest analysis")
    print("  - Configure thresholds appropriately for your codebase")
