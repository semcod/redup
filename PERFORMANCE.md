# 🚀 Performance Guide

## Current Performance Characteristics

### Baseline Metrics (v0.3.6)
- **Scan Rate**: ~3,000 lines/sec for Python projects
- **Memory Usage**: Efficient block processing
- **Overhead**: 16M function calls for full project scan

### Identified Bottlenecks

1. **String Operations** (2.2s total)
   - `str.join()` calls: 2.18s (145K calls)
   - Line processing in sliding window extraction

2. **AST Walking** (1.5s total)
   - `ast.walk()`: 1.52s (352K calls)
   - `ast.iter_child_nodes()`: 1.01s (704K calls)

3. **File Filtering** (1.2s total)
   - Path exclusion checks: 1.22s (8.7K calls)

## Optimization Strategies

### 1. Reduce String Operations
```python
# Current (slow)
text = "\n".join(line.strip() for _, line in chunk)

# Optimized (faster)
lines = [line.strip() for _, line in chunk]
text = "\n".join(lines)
```

### 2. AST Walking Optimization
```python
# Current (walks entire tree)
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

# Optimized (targeted traversal)
for node in tree.body:
    if isinstance(node, ast.ClassDef):
        for method in node.body:
            if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
```

### 3. Caching File Filters
```python
# Cache exclusion decisions
@functools.lru_cache(maxsize=1000)
def _should_exclude_cached(path: str, is_dir: bool) -> bool:
    return _should_exclude(Path(path), is_dir)
```

## Performance Targets

### Short-term (v0.4.0)
- **50% faster** scanning through string optimization
- **30% less memory** usage via block streaming
- **10,000 lines/sec** processing rate

### Long-term (v1.0.0)
- **50,000 lines/sec** processing rate
- **Parallel AST parsing** for large files
- **Incremental scanning** for changed files only

## Benchmark Suite

```python
def benchmark_scan_performance():
    """Run comprehensive performance benchmarks."""
    
    # Small project (<1000 lines)
    run_benchmark("small", Path("test_data/small_project"))
    
    # Medium project (1000-10000 lines)
    run_benchmark("medium", Path("test_data/medium_project"))
    
    # Large project (>10000 lines)
    run_benchmark("large", Path("test_data/large_project"))
```

## Memory Profiling

### Current Usage Patterns
- Block storage: ~50MB for 10K line project
- AST trees: ~100MB for complex Python files
- Hash indexes: ~20MB for duplicate detection

### Optimization Opportunities
1. **Streaming blocks** instead of storing all in memory
2. **AST pruning** after extraction
3. **Compressed hash storage** for large projects

## Parallel Processing

### Current Implementation
- File-level parallelism available
- `--parallel` flag with `--max-workers`

### Future Enhancements
1. **Intra-file parallelism** for large files
2. **Pipeline parallelism** (scan → hash → match)
3. **Distributed scanning** for massive projects

## Monitoring

### Performance Metrics
```python
@dataclass
class PerformanceMetrics:
    scan_time_ms: float
    files_scanned: int
    lines_processed: int
    blocks_extracted: int
    memory_peak_mb: float
    cpu_usage_percent: float
```

### Alerts
- Scan time > 30s for medium projects
- Memory usage > 500MB
- CPU usage > 90% for > 10s
