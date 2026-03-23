"""Benchmark: library speedups vs stdlib fallbacks.

This script measures the performance improvements from the optional
fast libraries (xxhash, rapidfuzz, libcst, pybloom-live) compared
to their stdlib fallbacks.
"""

import time
import tempfile
from pathlib import Path

# Test with proper PYTHONPATH
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from redup.core.models import ScanConfig
from redup.core.pipeline import analyze


def generate_test_project(root: Path, num_files: int = 50, lines_per_file: int = 200):
    """Generate project with known duplicates for benchmarking."""
    for i in range(num_files):
        funcs = []
        for j in range(10):
            funcs.append(f'''
def func_{j}(x_{j}, y_{j}):
    """Docstring for func_{j}."""
    if x_{j} <= 0:
        return 0.0
    result = x_{j} * y_{j}
    if result > 1000:
        result = 1000
    return round(result, 2)
''')
        (root / f"module_{i}.py").write_text("\n".join(funcs))


def benchmark():
    """Run benchmark with current library configuration."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        generate_test_project(root, num_files=50)
        config = ScanConfig(root=root, min_block_lines=3)

        t0 = time.perf_counter()
        result = analyze(config=config, function_level_only=True)
        elapsed = time.perf_counter() - t0

        print(f"Files:    {result.stats.files_scanned}")
        print(f"Lines:    {result.stats.total_lines}")
        print(f"Groups:   {result.total_groups}")
        print(f"Saved:    {result.total_saved_lines} lines")
        print(f"Time:     {elapsed:.2f}s")

        # Check which fast libraries are available
        libs = {}
        for name, pkg in [("xxhash", "xxhash"), ("rapidfuzz", "rapidfuzz"),
                          ("libcst", "libcst"), ("pybloom", "pybloom_live"),
                          ("sentence-transformers", "sentence_transformers")]:
            try:
                __import__(pkg)
                libs[name] = "✓"
            except ImportError:
                libs[name] = "✗"

        print(f"\nLibraries: {libs}")
        
        # Performance tips
        tips = []
        if libs.get("xxhash") == "✗":
            tips.append("Install xxhash for 20x faster hashing")
        if libs.get("rapidfuzz") == "✗":
            tips.append("Install rapidfuzz for 70x faster fuzzy matching")
        if libs.get("libcst") == "✗":
            tips.append("Install libcst for 2-10x faster Python parsing")
        if libs.get("pybloom") == "✗":
            tips.append("Install pybloom-live to eliminate 90% of non-duplicates")
        if libs.get("sentence-transformers") == "✗":
            tips.append("Install sentence-transformers for semantic duplicate detection")
            
        if tips:
            print("\nPerformance tips:")
            for tip in tips:
                print(f"  • {tip}")
        else:
            print("\n✓ All fast libraries available!")


def benchmark_hash_performance():
    """Benchmark hash performance specifically."""
    print("\n=== Hash Performance Benchmark ===")
    
    import hashlib
    
    text = b"def foo():\n    return 42\n" * 100
    
    # Test SHA-256
    t0 = time.perf_counter()
    for _ in range(100_000):
        hashlib.sha256(text).hexdigest()[:16]
    sha_time = time.perf_counter() - t0
    
    # Test xxhash if available
    try:
        import xxhash
        t0 = time.perf_counter()
        for _ in range(100_000):
            xxhash.xxh64(text).hexdigest()[:16]
        xx_time = time.perf_counter() - t0
        speedup = sha_time / xx_time
        print(f"SHA-256: {sha_time:.2f}s  xxhash: {xx_time:.2f}s  speedup: {speedup:.0f}x")
    except ImportError:
        print(f"SHA-256: {sha_time:.2f}s  xxhash: not available (install for 20x speedup)")


def benchmark_fuzzy_performance():
    """Benchmark fuzzy matching performance."""
    print("\n=== Fuzzy Matching Performance Benchmark ===")
    
    from difflib import SequenceMatcher
    
    text1 = "def calculate_tax(amount, rate):"
    text2 = "def calculate_tax(rate, amount):"
    
    # Test difflib
    t0 = time.perf_counter()
    for _ in range(10_000):
        SequenceMatcher(None, text1, text2).ratio()
    difflib_time = time.perf_counter() - t0
    
    # Test rapidfuzz if available
    try:
        from rapidfuzz import fuzz
        t0 = time.perf_counter()
        for _ in range(10_000):
            fuzz.ratio(text1, text2) / 100.0
        rapidfuzz_time = time.perf_counter() - t0
        speedup = difflib_time / rapidfuzz_time
        print(f"difflib: {difflib_time:.3f}s  rapidfuzz: {rapidfuzz_time:.3f}s  speedup: {speedup:.1f}x")
    except ImportError:
        print(f"difflib: {difflib_time:.3f}s  rapidfuzz: not available (install for 70x speedup)")


if __name__ == "__main__":
    print("reDUP Library Performance Benchmark")
    print("=" * 40)
    
    # Run individual benchmarks
    benchmark_hash_performance()
    benchmark_fuzzy_performance()
    
    # Run full pipeline benchmark
    print("\n=== Full Pipeline Benchmark ===")
    benchmark()
    
    print("\nInstall fast libraries:")
    print("  pip install redup[fast]     # xxhash + libcst + pybloom-live")
    print("  pip install redup[fuzzy]    # rapidfuzz")
    print("  pip install redup[semantic] # sentence-transformers")
    print("  pip install redup[all]      # everything")
