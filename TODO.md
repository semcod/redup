# TODO - reDUP Analysis & Refactoring Plan

## 📊 Analysis Summary

### reDUP Self-Analysis Results
- **Files scanned**: 16 Python files
- **Total lines**: 1,361 lines  
- **Duplicate groups found**: 2 groups
- **Recoverable lines**: 11 lines (0.8% of codebase)
- **Scan performance**: ~370ms for self-analysis

### Proxy Project Analysis Results
- **Files scanned**: 113 Python files
- **Total lines**: 18,353 lines
- **Duplicate groups found**: 21 groups (13 with min_lines=5)
- **Recoverable lines**: 465 lines (2.5% of codebase)
- **Scan performance**: ~4.3 seconds

---

## 🎯 Priority Action Items

### High Priority (ROI > 50 lines)

#### 1. Fix reDUP Internal Duplicates
- **File**: `src/redup/core/hasher.py`
- **Issue**: 2 structural duplicate groups (11 lines recoverable)
- **Action**: Refactor `hash_block()` and `find_*_duplicates()` functions
- **Impact**: Improve code quality, reduce maintenance burden
- **Estimated effort**: 2-3 hours

#### 2. Proxy Project - Frontend Dashboard Refactoring
- **File**: `src/proxym/api/frontend.py`
- **Issue**: 20 nearly identical 6-line dashboard functions (114 lines recoverable)
- **Action**: Extract common dashboard JS/JSX generation logic
- **Target**: `utils/dashboard_hook_js.py`
- **Impact**: Largest single refactoring opportunity
- **Estimated effort**: 4-6 hours

### Medium Priority (ROI 10-50 lines)

#### 3. Proxy Project - CLI Pattern Consolidation
- **Files**: 6 CLI controller files
- **Issue**: Repeated test patterns and status reporting (72 lines total)
- **Action**: Create shared utility functions
- **Targets**: 
  - `utils/tests_vscode.py` (test patterns)
  - `utils/status.py` (status reporting)
- **Estimated effort**: 3-4 hours

#### 4. Proxy Project - Tool Management Refactoring
- **File**: `src/proxym/cli/_groups/tools_ctl.py`
- **Issue**: 3 similar 7-line functions (cancel/retry/repair, start/stop, show/job)
- **Action**: Extract common tool management patterns
- **Estimated effort**: 2-3 hours

---

## 🔧 reDUP Improvements

### Code Quality Issues
1. **Syntax Warnings**: Fix invalid escape sequences in regex patterns
2. **Linting Issues**: Resolve remaining 6 ruff warnings (Typer defaults, unused imports)
3. **Type Annotations**: Update Optional[T] to T | None for Python 3.10+
4. **Exception Handling**: Add proper exception chaining with `from err`

### Performance Optimizations
1. **Memory Usage**: Large projects generate 600K+ blocks - consider streaming processing
2. **Scan Speed**: 4.3s for 18K lines could be improved with:
   - Parallel file processing
   - Early termination for exact duplicates
   - Cached AST parsing
3. **Algorithm Efficiency**: 
   - LSH for large codebases (datasketch integration)
   - Progressive similarity checking

### Feature Enhancements
1. **Language Support**: Add tree-sitter for multi-language analysis
2. **Better Filtering**: 
   - Exclude test files by default
   - Ignore generated code
   - Custom ignore patterns
3. **Improved Reporting**:
   - HTML report with syntax highlighting
   - Interactive web interface
   - Integration with IDE plugins

### User Experience
1. **CLI Improvements**:
   - Progress bars for large scans
   - Better error messages
   - Configuration file support
2. **Output Formats**:
   - SARIF output for CI/CD integration
   - CodeClimate format
   - SonarQube plugin

---

## 📋 Detailed Refactoring Tasks

### reDUP Internal Refactoring

#### Task 1.1: Hash Function Consolidation
```python
# Current duplicate pattern in hasher.py:
def hash_block(text: str) -> str:
    normalized = _normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

def hash_block_structural(text: str) -> str:
    normalized = _normalize_ast_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
```
**Solution**: Create generic `_hash_text(text: str, normalizer: callable) -> str`

#### Task 1.2: Duplicate Finder Consolidation
```python
# Current duplicate pattern:
def find_exact_duplicates(index: HashIndex) -> dict[str, list[HashedBlock]]:
    return {h: blocks for h, blocks in index.exact.items() 
            if len(blocks) > 1 and _blocks_from_different_locations(blocks)}

def find_structural_duplicates(index: HashIndex) -> dict[str, list[HashedBlock]]:
    return {h: blocks for h, blocks in index.structural.items() 
            if len(blocks) > 1 and _blocks_from_different_locations(blocks)}
```
**Solution**: Create generic `_find_duplicates(hash_dict: dict, index: HashIndex) -> dict`

### Proxy Project Refactoring

#### Task 2.1: Dashboard Function Extraction
**Pattern**: 20 similar functions in `frontend.py`
```python
def dashboard_hook_js():
    return js_file("dashboard/hook.js")

def dashboard_formatters_js():
    return js_file("dashboard/formatters.js")
# ... 18 more similar functions
```
**Solution**: Create generic `dashboard_jsx_component(name: str) -> js_file`

#### Task 2.2: CLI Utility Functions
**Pattern**: Repeated across 6 CLI files
```python
# Test pattern
tests = vscode_tests(config)
print(f"Found {len(tests)} tests")

# Status pattern  
status = get_status(config)
print(f"Status: {status}")
```
**Solution**: Create shared utility functions in common module

---

## 🚀 Implementation Plan

### Phase 1: reDUP Internal Fixes (Week 1)
1. Fix syntax warnings and linting issues
2. Refactor internal duplicates (hasher.py)
3. Add better error handling
4. Improve test coverage

### Phase 2: Proxy Project High-ROI (Week 2)
1. Dashboard frontend refactoring (114 lines)
2. CLI pattern consolidation (72 lines)
3. Tool management improvements (28 lines)

### Phase 3: reDUP Enhancements (Week 3-4)
1. Performance optimizations
2. Multi-language support
3. Better reporting formats
4. CLI UX improvements

### Phase 4: Advanced Features (Month 2)
1. Web interface
2. IDE integrations
3. CI/CD pipeline integration
4. Advanced filtering options

---

## 📈 Success Metrics

### Code Quality Metrics
- **reDUP**: Reduce internal duplicates from 2 groups to 0
- **Proxy**: Reduce duplicates from 21 groups to <10 groups
- **Coverage**: Maintain >95% test coverage
- **Linting**: Zero ruff warnings

### Performance Metrics
- **reDUP self-scan**: <200ms (target: 50% improvement)
- **Proxy scan**: <2s (target: 50% improvement)
- **Memory usage**: <100MB for Proxy project

### User Experience Metrics
- **CLI**: Add progress bars for >1000 file scans
- **Reports**: HTML output with interactive features
- **Integration**: Support for 3+ CI/CD platforms

---

## 🔍 Technical Debt Analysis

### Immediate Concerns
1. **Regex Escape Sequences**: Multiple syntax warnings in output
2. **Unused Imports**: 4 modules with unused imports
3. **Type Annotations**: Inconsistent Optional vs Union usage

### Medium-term Concerns
1. **Memory Scaling**: Large projects may exceed available RAM
2. **Single-threaded Processing**: Missing parallelization opportunities
3. **Limited Language Support**: Python-only analysis currently

### Long-term Considerations
1. **Architecture**: Consider plugin system for language support
2. **Storage**: Persistent cache for repeated analyses
3. **Distribution**: Package size and dependency management

---

## 📝 Notes & Observations

### reDUP Strengths
- Excellent detection accuracy (found meaningful duplicates)
- Good performance for small-to-medium projects
- Clean, well-structured codebase
- Comprehensive output formats

### reDUP Limitations
- Python-only analysis (missing tree-sitter integration)
- Memory intensive for large projects
- Limited customization options
- No incremental analysis support

### Proxy Project Patterns
- **Frontend**: Repetitive dashboard component generation
- **CLI**: Similar command patterns across modules
- **Tools**: Repeated VM/container management logic
- **Dashboard**: Duplicate helper functions across modules

---

## 🎯 Next Steps

1. **This Week**: Complete reDUP internal refactoring
2. **Next Week**: Begin Proxy project dashboard refactoring
3. **Following Week**: Implement performance improvements
4. **Monthly Review**: Assess progress and adjust priorities

---

*Generated by reDUP v0.1.1 on 2026-03-23*
*Analysis time: ~15 minutes total*
