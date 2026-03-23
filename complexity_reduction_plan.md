# Pipeline Complexity Reduction Plan

## 🎯 Target Functions
Based on code2llm analysis, we need to reduce complexity in:

1. **analyze()** - CC=20 (target: ≤15)
2. **_ast_to_normalized_string()** - CC=17 (target: ≤15)

## 🔧 Refactoring Strategy

### 1. Break Down analyze() Function

Current structure (CC=20):
```python
def analyze(config=None, function_level_only=False):
    # 20+ lines of complex logic
    # Multiple phases mixed together
    # Complex conditional logic
```

Proposed structure:
```python
def analyze(config=None, function_level_only=False):
    """Main analysis orchestrator."""
    config = _ensure_config(config)
    
    # Phase 1: Scan
    scanned_files, stats = _scan_phase(config)
    
    # Phase 2: Process blocks
    all_blocks = _process_blocks(scanned_files, function_level_only)
    
    # Phase 3: Hash and find duplicates
    groups = _find_duplicates_phase(all_blocks, config)
    
    # Phase 4: Deduplicate and suggest
    final_groups = _deduplicate_phase(groups)
    suggestions = generate_suggestions(final_groups)
    
    return DuplicationMap(
        project_path=config.root.as_posix(),
        config=config,
        stats=stats,
        groups=final_groups,
        suggestions=suggestions,
    )


def _ensure_config(config: ScanConfig | None) -> ScanConfig:
    """Ensure we have a valid configuration."""
    return config or ScanConfig()


def _scan_phase(config: ScanConfig) -> tuple[list[ScannedFile], ScanStats]:
    """Phase 1: Scan project files."""
    return scan_project(config)


def _process_blocks(
    scanned_files: list[ScannedFile], 
    function_level_only: bool
) -> list[CodeBlock]:
    """Phase 2: Extract and filter code blocks."""
    all_blocks: list[CodeBlock] = []
    for sf in scanned_files:
        for block in sf.blocks:
            if function_level_only and block.function_name is None:
                continue
            all_blocks.append(block)
    return all_blocks


def _find_duplicates_phase(
    all_blocks: list[CodeBlock], 
    config: ScanConfig
) -> list[DuplicateGroup]:
    """Phase 3: Hash and find duplicate groups."""
    index = build_hash_index(all_blocks, min_lines=config.min_block_lines)
    
    # Find exact duplicates
    exact_groups = _find_exact_groups(index)
    
    # Find structural duplicates
    structural_groups = _find_structural_groups(index, exact_groups)
    
    return exact_groups + structural_groups


def _find_exact_groups(index: HashIndex) -> list[DuplicateGroup]:
    """Find exact duplicate groups."""
    groups = []
    exact_groups = find_exact_duplicates(index)
    
    for i, (h, blocks) in enumerate(exact_groups.items(), 1):
        func_blocks = [b for b in blocks if b.block.function_name]
        if len(func_blocks) >= 2:
            g = _blocks_to_group(
                group_id=f"E{i:04d}",
                blocks=func_blocks,
                dup_type=DuplicateType.EXACT,
                normalized_hash=h,
            )
            if g.occurrences >= 2:
                groups.append(g)
    
    return groups


def _find_structural_groups(
    index: HashIndex, 
    exact_groups: dict[str, list[HashedBlock]]
) -> list[DuplicateGroup]:
    """Find structural duplicate groups."""
    groups = []
    exact_hashes = set(exact_groups.keys())
    structural_groups = find_structural_duplicates(index)
    
    for i, (h, blocks) in enumerate(structural_groups.items(), 1):
        if h in exact_hashes:
            continue
            
        func_blocks = [b for b in blocks if b.block.function_name]
        if len(func_blocks) >= 2:
            refined = refine_structural_matches(func_blocks)
            if len(refined) >= 2:
                g = _blocks_to_group(
                    group_id=f"S{i:04d}",
                    blocks=refined,
                    dup_type=DuplicateType.STRUCTURAL,
                    normalized_hash=h,
                    similarity=_calculate_similarity(refined),
                )
                if g.occurrences >= 2:
                    groups.append(g)
    
    return groups


def _deduplicate_phase(groups: list[DuplicateGroup]) -> list[DuplicateGroup]:
    """Phase 4: Remove overlapping groups."""
    return _deduplicate_groups(groups)
```

### 2. Simplify _ast_to_normalized_string()

Current structure (CC=17):
```python
def _ast_to_normalized_string(tree):
    # Complex AST walking with many conditionals
    # Multiple node types handled in one function
```

Proposed structure:
```python
def _ast_to_normalized_string(tree) -> str:
    """Convert AST to normalized string with placeholders."""
    name_map: dict[str, str] = {}
    counter = [0]
    parts: list[str] = []
    
    for node in ast.walk(tree):
        part = _process_ast_node(node, name_map, counter)
        if part:
            parts.append(part)
    
    return " ".join(parts)


def _process_ast_node(
    node, 
    name_map: dict[str, str], 
    counter: list[int]
) -> str | None:
    """Process a single AST node and return its normalized representation."""
    if isinstance(node, ast.Name):
        return _get_placeholder(node.id, name_map, counter)
    elif isinstance(node, ast.arg):
        return _get_placeholder(node.arg, name_map, counter)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return f"DEF({_get_placeholder(node.name, name_map, counter)})"
    elif isinstance(node, ast.ClassDef):
        return f"CLASS({_get_placeholder(node.name, name_map, counter)})"
    elif isinstance(node, ast.Constant):
        return _normalize_constant(node.value)
    elif isinstance(node, ast.If):
        return "IF"
    elif isinstance(node, ast.For):
        return "FOR"
    elif isinstance(node, ast.While):
        return "WHILE"
    elif isinstance(node, ast.Return):
        return "RETURN"
    elif isinstance(node, ast.Compare):
        ops = [type(op).__name__ for op in node.ops]
        return f"CMP({','.join(ops)})"
    elif isinstance(node, ast.BinOp):
        return f"BINOP({type(node.op).__name__})"
    elif isinstance(node, ast.Call):
        return "CALL"
    return None


def _get_placeholder(
    name: str, 
    name_map: dict[str, str], 
    counter: list[int]
) -> str:
    """Get or create a placeholder for a name."""
    if name in BUILTINS or (name.startswith("__") and name.endswith("__")):
        return name
    
    if name not in name_map:
        name_map[name] = f"_V{counter[0]}"
        counter[0] += 1
    
    return name_map[name]


def _normalize_constant(value) -> str:
    """Normalize constant values."""
    if isinstance(value, str):
        return "__STR__"
    elif isinstance(value, (int, float)):
        return "__NUM__"
    else:
        return str(type(value).__name__)
```

## 📈 Expected Results

### Complexity Reduction
- **analyze()**: CC=20 → CC=8 (60% reduction)
- **_ast_to_normalized_string()**: CC=17 → CC=6 (65% reduction)

### Benefits
1. **Better testability**: Each function can be tested independently
2. **Improved readability**: Clear phase separation
3. **Easier maintenance**: Smaller, focused functions
4. **Better documentation**: Each function has a single responsibility

### Implementation Steps
1. **Phase 1**: Extract helper functions from analyze()
2. **Phase 2**: Refactor _ast_to_normalized_string()
3. **Phase 3**: Add comprehensive tests for new functions
4. **Phase 4**: Update documentation

## 🧪 Testing Strategy

```python
def test_analyze_phases():
    """Test that analyze phases work correctly."""
    config = ScanConfig(root=Path("tests/fixtures"))
    
    # Test each phase independently
    scanned_files, stats = _scan_phase(config)
    assert len(scanned_files) > 0
    
    blocks = _process_blocks(scanned_files, function_level_only=True)
    assert len(blocks) > 0
    
    groups = _find_duplicates_phase(blocks, config)
    assert isinstance(groups, list)
    
    final_groups = _deduplicate_phase(groups)
    assert len(final_groups) <= len(groups)


def test_ast_node_processing():
    """Test AST node processing individually."""
    # Test each node type separately
    assert _process_ast_node(ast.Name(id="test"), {}, [0]) == "_V0"
    assert _process_ast_node(ast.Constant(value=42), {}, [0]) == "__NUM__"
    assert _process_ast_node(ast.If(), {}, [0]) == "IF"
```

This refactoring will significantly improve code maintainability while preserving all existing functionality.
