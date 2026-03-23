# 🚀 **Sprint 2 Plan - New Features & Extensions**

## **Cel Sprint 2: v0.2.1**
**Rozszerzenie funkcjonalności o nowe komendy i formaty przy zachowaniu jakości kodu**

---

## **📋 Feature List & Priority**

### **HIGH Priority (Core Features)**

#### **1. Multi-language Support**
- **Cel**: Dodaj wsparcie dla JavaScript, TypeScript, Go, Rust
- **Wysiłek**: ~4h
- **Plik**: `src/redup/core/ts_extractor.py`
- **Zależność**: `tree-sitter` (już w optional deps)

**Plan implementacji:**
```python
# Nowy moduł ts_extractor.py
def extract_functions_treesitter(source: str, language: str) -> list[CodeBlock]:
    """Extract functions using tree-sitter for multi-language support."""
    
# Rozszerzenie scanner.py
def _extract_functions_by_language(file_path: Path, content: str) -> list[CodeBlock]:
    """Route to appropriate extractor based on file extension."""
    
# Rozszerzenie ScanConfig
@dataclass
class ScanConfig:
    languages: list[str] = field(default_factory=lambda: ["python"])
```

#### **2. redup diff Command**
- **Cel**: Porównaj dwa skany i pokaż zmiany
- **Wysiłek**: ~3h
- **Plik**: `src/redup/core/differ.py`

**Użycie:**
```bash
redup diff --before duplication_v1.json --after duplication_v2.json
```

**Output:**
```
# RESOLVED: 3 groups eliminated (saved 45 lines)
# NEW: 1 group added (billing.py + shipping.py, 12 lines)
# UNCHANGED: 2 groups remain
```

#### **3. redup check Command**
- **Cel**: CI gate - exit code 1 jeśli duplikaty przekraczają próg
- **Wysiłek**: ~2h
- **Plik**: `src/redup/cli_app/main.py`

**Użycie w CI:**
```bash
redup check . --max-groups 5 --max-saved-lines 100
# Exit codes: 0=OK, 1=threshold exceeded, 2=scan error
```

### **MEDIUM Priority (Enhancements)**

#### **4. TOML Configuration**
- **Cel**: Konfiguracja w pliku TOML
- **Wysiłek**: ~2h
- **Plik**: `src/redup/config.py`

**Opcje konfiguracyjne:**
```toml
# redup.toml
[redup]
min_lines = 3
min_similarity = 0.85
include_tests = false
languages = ["python", "javascript"]

[redup.exclude_patterns]
"__pycache__" = true
"node_modules" = true
".git" = true

# Lub w pyproject.toml
[tool.redup]
min_lines = 3
min_similarity = 0.85
```

#### **5. Markdown Reporter**
- **Cel**: Generuj raporty w formacie Markdown
- **Wysiłek**: ~1h
- **Plik**: `src/redup/reporters/markdown_reporter.py`

**Format output:**
```markdown
# Duplication Analysis Report

## Summary
- **Files scanned**: 17
- **Duplicate groups**: 2
- **Lines recoverable**: 6

## Duplicate Groups

### Group S0401: hash_block
- **Type**: Structural
- **Lines**: 3
- **Occurrences**: 2
- **Similarity**: 0.91
- **Files affected**:
  - `src/redup/core/hasher.py:153-155`
  - `src/redup/core/hasher.py:158-160`
```

#### **6. LSH Near-Duplicate Detection**
- **Cel**: MinHash/LSH dla dużych bloków (>50 linii)
- **Wysiłek**: ~3h
- **Zależność**: `datasketch` (już w optional deps)

### **LOW Priority (Nice to Have)**

#### **7. Code Snippet in JSON**
- **Cel**: Opcjonalne dołączenie tekstu fragmentu
- **Wysiłek**: ~1h
- **Flag**: `--include-snippets`

#### **8. Git Blame Integration**
- **Cel**: Informacje o autorze i czasie duplikacji
- **Wysiłek**: ~3h
- **Zależność**: `gitpython`

---

## **🏗️ Architektura Sprint 2**

### **Nowe Moduły:**
```
src/redup/
├── core/
│   ├── ts_extractor.py      # Multi-language AST extraction
│   ├── differ.py            # Scan comparison
│   └── config.py            # TOML configuration
├── reporters/
│   └── markdown_reporter.py # Markdown output
└── cli_app/
    └── main.py              # New commands: diff, check
```

### **Rozszerzenia istniejących:**
```
src/redup/core/
├── scanner.py              # Multi-language routing
├── models.py               # New config fields
└── pipeline.py             # Configuration loading
```

---

## **📝 Plan Implementacji**

### **Tydzień 1: Core Features**
1. **Day 1**: Multi-language support (tree-sitter integration)
2. **Day 2**: redup diff command implementation
3. **Day 3**: redup check CI gate
4. **Day 4**: Testing and integration

### **Tydzień 2: Enhancements**
1. **Day 1**: TOML configuration support
2. **Day 2**: Markdown reporter
3. **Day 3**: LSH near-duplicate detection
4. **Day 4**: Testing and documentation

### **Tydzień 3: Polish & Release**
1. **Day 1**: Code snippets in JSON
2. **Day 2**: Git blame integration (if time permits)
3. **Day 3**: Comprehensive testing
4. **Day 4**: Documentation and release v0.2.1

---

## **🧪 Test Strategy**

### **Unit Tests**
- **ts_extractor.py**: Test dla każdego języka
- **differ.py**: Test porównania scanów
- **config.py**: Test ładowania konfiguracji
- **markdown_reporter.py**: Test formatowania

### **Integration Tests**
- **CLI commands**: Test `redup diff` i `redup check`
- **Multi-language**: Test skanowania projektów JS/TS
- **Configuration**: Test ładowania TOML

### **E2E Tests**
- **CI pipeline**: Test `redup check` w środowisku CI
- **Real projects**: Test na projektach wielojęzycznych
- **Diff workflow**: Test pełnego workflow diff

---

## **📊 Success Metrics**

### **Quality Gates**
- **CC̄ ≤ 3.5** (maintain Sprint 1 achievement)
- **No critical functions** (CC > 10)
- **100% test coverage** for new features
- **Performance**: < 2s scan for 1000+ lines

### **Feature Completeness**
- **Multi-language**: 4 languages supported
- **New commands**: `diff` i `check` working
- **Configuration**: TOML support functional
- **Reporters**: Markdown format available

### **User Experience**
- **CLI consistency**: New commands follow existing patterns
- **Documentation**: All features documented
- **Error handling**: Clear error messages
- **Performance**: No regression in scan speed

---

## **🚦 Definition of Done**

### **For Each Feature:**
- [ ] Code implemented with proper type hints
- [ ] Unit tests written and passing
- [ ] Integration tests covering main workflows
- [ ] Documentation updated (README, CLI help)
- [ ] Error handling implemented
- [ ] Performance impact measured (< 10% regression)

### **For Sprint 2:**
- [ ] All HIGH priority features complete
- [ ] At least 2 MEDIUM priority features complete
- [ ] Quality gates met (CC̄ ≤ 3.5, no critical functions)
- [ ] All tests passing (including new ones)
- [ ] Documentation comprehensive
- [ ] Version 0.2.1 released

---

## **⚠️ Risks & Mitigations**

### **Risk 1: Tree-sitter Complexity**
- **Mitigation**: Start with Python fallback, add languages incrementally
- **Backup**: Use existing AST for Python, tree-sitter for others

### **Risk 2: Performance Regression**
- **Mitigation**: Profile each new feature, optimize bottlenecks
- **Backup**: Make new features optional/opt-in

### **Risk 3: Configuration Complexity**
- **Mitigation**: Keep defaults unchanged, make TOML optional
- **Backup**: CLI options override config file

### **Risk 4: Test Coverage**
- **Mitigation**: Write tests alongside code, use TDD for new features
- **Backup**: Focus on integration tests over unit tests for complex features

---

## **🎯 Sprint Goals**

### **Primary Goal**
**Rozszerz reDUP o nowe funkcjonalności przy zachowaniu jakości kodu osiągniętej w Sprint 1**

### **Secondary Goals**
- Ustanów podstawy dla wsparcia wielojęzycznego
- Wprowadź reDUP do pipeline'ów CI/CD
- Popraw doświadczenie deweloperskie (konfiguracja, nowe formaty)

### **Stretch Goals**
- Eksperymentalne funkcje (LSH, Git blame)
- Integracja z zewnętrznymi narzędziami
- Przygotowanie podkładu pod Sprint 3

---

*Ready to start Sprint 2 implementation!* 🚀
