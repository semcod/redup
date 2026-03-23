# 🚀 Performance Guide

## Quick Wins (największy efekt z najmniejszym wysiłkiem)

### 1. Parallel Scanning (dla projektów >10 plików)
```bash
# Użyj wszystkich rdzeni CPU
redup scan . --parallel

# Ogranicz liczbę workerów
redup scan . --parallel --max-workers 4
```

### 2. Functions Only (2-3x szybsze)
```bash
# Pomija sliding-window analizę linii
redup scan . --functions-only
```

### 3. Incremental Scanning (10-100x szybsze na 2+ uruchomienie)
```bash
# Pierwsze skanowanie - pełne + zapis cache
redup scan . --incremental

# Kolejne skanowanie - tylko zmienione pliki
redup scan . --incremental
```

### 4. Połączenie wszystkich optymalizacji
```bash
redup scan . --parallel --functions-only --incremental --min-lines 5
```

## Konfiguracja w redup.toml

```toml
[scan]
extensions = ".py"           # Tylko Python
min_lines = 5                # Wyższy próg = mniej bloków
min_similarity = 0.90        # Wyższy próg = mniej porównań
include_tests = false

[lsh]
enabled = false              # Wyłącz LSH (jest wolny)
```

## Current Performance Characteristics (v0.3.7)

| Strategia | Projekt 100 plików | Projekt 1000 plików |
|-----------|-------------------|---------------------|
| Domyślnie | 2-5s | 30-60s |
| --functions-only | 1-2s | 10-20s |
| --parallel | 1-2s | 5-15s |
| --functions-only --parallel | 0.5-1s | 3-8s |
| --incremental (2nd run) | 0.1-0.5s | 0.5-2s |

### Baseline Metrics
- **Scan Rate**: ~3,000 lines/sec for Python projects (domyślnie)
- **Scan Rate**: ~10,000 lines/sec (z optymalizacjami)
- **Memory Usage**: Efficient block processing

### Identified Bottlenecks

1. **String Operations** (2.2s total)
   - `str.join()` calls: 2.18s (145K calls)
   - Line processing in sliding window extraction

2. **AST Walking** (1.5s total)
   - `ast.walk()`: 1.52s (352K calls)

3. **LSH Near-Duplicate Detection** (slow with datasketch)
   - Wyłącz jeśli niepotrzebne: `enabled = false` w [lsh]

## Implementation Status

- ✅ Parallel scanning (`--parallel`)
- ✅ Incremental scanning (`--incremental`) - nowość v0.3.7
- ✅ Hash cache module (`HashCache` class)
- ✅ Lazy tree-sitter loading
- ✅ Optimized file filtering with `lru_cache`

## CI/CD Optimization

```yaml
# GitHub Actions example
- name: Cache reDUP
  uses: actions/cache@v3
  with:
    path: .redup_cache.json
    key: redup-${{ github.sha }}
    restore-keys: redup-

- name: Run reDUP
  run: |
    pip install redup
    redup scan . --incremental --functions-only --max-groups 10
```
