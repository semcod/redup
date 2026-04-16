# System Architecture Analysis

## Overview

- **Project**: /home/tom/github/semcod/redup
- **Primary Language**: python
- **Languages**: python: 84, shell: 1
- **Analysis Mode**: static
- **Total Functions**: 379
- **Total Classes**: 51
- **Modules**: 85
- **Entry Points**: 196

## Architecture by Module

### src.redup.core.fuzzy_similarity
- **Functions**: 20
- **Classes**: 4
- **File**: `fuzzy_similarity.py`

### src.redup.reporters.enhanced_reporter
- **Functions**: 17
- **Classes**: 1
- **File**: `enhanced_reporter.py`

### src.redup.core.universal_fuzzy
- **Functions**: 16
- **Classes**: 3
- **File**: `universal_fuzzy.py`

### src.redup.cli_app.compare_command
- **Functions**: 16
- **File**: `compare_command.py`

### src.redup.core.scanner
- **Functions**: 14
- **File**: `__init__.py`

### src.redup.core.hasher
- **Functions**: 13
- **Classes**: 2
- **File**: `hasher.py`

### src.redup.core.utils.diff_helpers
- **Functions**: 13
- **Classes**: 3
- **File**: `diff_helpers.py`

### src.redup.core.lsh_matcher
- **Functions**: 12
- **Classes**: 2
- **File**: `lsh_matcher.py`

### src.redup.mcp.handlers
- **Functions**: 12
- **File**: `handlers.py`

### src.redup.reporters.toon_reporter
- **Functions**: 11
- **File**: `toon_reporter.py`

### src.redup.core.hash_cache
- **Functions**: 10
- **Classes**: 1
- **File**: `hash_cache.py`

### src.redup.core.cache
- **Functions**: 10
- **Classes**: 1
- **File**: `cache.py`

### src.redup.cli_app.fuzzy_similarity
- **Functions**: 9
- **File**: `fuzzy_similarity.py`

### src.redup.config
- **Functions**: 7
- **Classes**: 1
- **File**: `config.py`

### src.redup.core.refactor_advisor
- **Functions**: 7
- **Classes**: 2
- **File**: `refactor_advisor.py`

### src.redup.core.lazy_grouper
- **Functions**: 7
- **Classes**: 1
- **File**: `lazy_grouper.py`

### src.redup.core.python_parser
- **Functions**: 7
- **Classes**: 1
- **File**: `python_parser.py`

### src.redup.core.config
- **Functions**: 6
- **File**: `config.py`

### src.redup.core.pipeline.duplicate_finder
- **Functions**: 6
- **File**: `duplicate_finder.py`

### src.redup.reporters.code2llm_reporter
- **Functions**: 6
- **File**: `code2llm_reporter.py`

## Key Entry Points

Main execution flows into the system:

### src.redup.core.scanner_loader._preload_files
> Load ALL files into RAM at once for maximum speed.
- **Calls**: time.time, files.sort, len, print, time.time, Progress, progress.add_task, progress.console.print

### benchmarks.bench_libraries.benchmark
> Run benchmark with current library configuration.
- **Calls**: tempfile.TemporaryDirectory, Path, benchmarks.bench_libraries.generate_test_project, ScanConfig, time.perf_counter, src.redup.core.pipeline.analyze, print, print

### benchmark.benchmark_sequential_vs_parallel
> Compare sequential vs parallel scanning performance.
- **Calls**: print, print, ScanConfig, print, time.time, src.redup.core.pipeline.analyze, print, print

### examples.01_basic_usage.main
- **Calls**: ScanConfig, src.redup.core.pipeline.analyze, print, print, print, print, print, print

### src.redup.cli_app.main.scan
> Scan a project for code duplicates.
- **Calls**: app.command, typer.Argument, typer.Option, typer.Option, typer.Option, typer.Option, typer.Option, typer.Option

### src.redup.core.semantic.SemanticDetector.find_semantic_duplicates
> Find semantically similar code blocks using embeddings.

Pipeline:
1. Encode all blocks to vectors (batched, GPU if available)
2. Compute cosine simil
- **Calls**: self._ensure_model, self._model.encode, util.cos_sim, src.redup.config.RedupConfig.set, range, matches.sort, len, len

### benchmark.benchmark_feature_performance
> Test performance of different features.
- **Calls**: print, print, print, time.time, src.redup.core.pipeline.analyze_parallel, print, print, print

### src.redup.reporters.enhanced_reporter.EnhancedReporter._get_duplication_metrics
> Get duplication analysis metrics.
- **Calls**: sum, sum, Counter, len, dict, self._bucket_similarities, max, len

### src.redup.core.ts_extractor._extract_functions_javascript
> Extract functions from JavaScript/TypeScript using tree-sitter.
- **Calls**: node.child_by_field_name, blocks.append, traverse, name_node.text.decode, CodeBlock, node.child_by_field_name, blocks.append, name_node.text.decode

### src.redup.mcp.server.run_server
> Run the MCP server (entry point).
- **Calls**: print, None.join, print, sorted, line.strip, TOOL_SCHEMA_REDUP.keys, json.loads, src.redup.mcp.server.handle_request

### src.redup.mcp.handlers.handle_check_project
> Check project against quality gates.
- **Calls**: src.redup.mcp.utils.resolve_path, src.redup.mcp.handlers._run_analysis, int, int, src.redup.mcp.handlers._check_thresholds, json.dumps, params.get, FileNotFoundError

### benchmarks.bench_libraries.benchmark_hash_performance
> Benchmark hash performance specifically.
- **Calls**: print, time.perf_counter, range, time.perf_counter, time.perf_counter, range, print, None.hexdigest

### src.redup.core.ts_extractor._extract_functions_c_sharp
> Extract functions from C# using tree-sitter.
- **Calls**: node.child_by_field_name, blocks.append, traverse, name_node.text.decode, CodeBlock, node.child_by_field_name, blocks.append, parent.child_by_field_name

### src.redup.core.fuzzy_similarity.CSSComponentExtractor._normalize_css_value
> Normalize CSS property values for fuzzy comparison.
- **Calls**: None.lower, re.search, re.search, re.sub, re.sub, size_match.groups, float, value.strip

### src.redup.cli_app.main.compare
> Compare two projects and recommend refactoring strategy (merge / extract / keep separate).
- **Calls**: app.command, typer.Argument, typer.Argument, typer.Option, typer.Option, typer.Option, typer.Option, typer.Option

### benchmarks.bench_libraries.benchmark_fuzzy_performance
> Benchmark fuzzy matching performance.
- **Calls**: print, time.perf_counter, range, None.ratio, time.perf_counter, time.perf_counter, range, print

### src.redup.core.fuzzy_similarity.HTMLComponentExtractor._normalize_class_name
> Normalize class names to patterns.
- **Calls**: class_str.split, None.join, cls.startswith, normalized.append, cls.startswith, normalized.append, cls.startswith, normalized.append

### src.redup.core.pipeline.duplicate_finder.find_structural_groups
> Find structural duplicate groups.
- **Calls**: src.redup.config.RedupConfig.set, src.redup.core.hasher.find_structural_duplicates, enumerate, exact_hashes.add, structural_groups.items, len, src.redup.core.matcher.refine_structural_matches, src.redup.core.pipeline.groups.match_results_to_blocks

### src.redup.mcp.handlers.handle_analyze_project
> Analyze a project and return formatted results.
- **Calls**: src.redup.mcp.utils.resolve_path, src.redup.mcp.handlers._run_analysis, None.lower, src.redup.mcp.handlers._format_analysis_result, params.get, FileNotFoundError, path.exists, path.is_dir

### src.redup.config.RedupConfig._load_from_env
> Load configuration from environment variables.
- **Calls**: dir, attr_name.startswith, cls._env_name, os.getenv, getattr, isinstance, isinstance, value.lower

### src.redup.core.universal_fuzzy.UniversalFuzzyExtractor._extract_metadata
> Extract language-specific metadata.
- **Calls**: re.findall, re.findall, re.findall, re.findall, re.findall, None.join, None.join, None.join

### src.redup.core.universal_fuzzy.UniversalFuzzyDetector._compute_metadata_similarity
> Compute similarity between metadata dictionaries.
- **Calls**: src.redup.config.RedupConfig.set, src.redup.config.RedupConfig.set, len, len, meta1.keys, meta2.keys, value_similarities.append, value_similarities.append

### src.redup.core.hasher._normalize_ast_text
> Deeper normalization: replace variable names and literals with placeholders.
- **Calls**: _normalize_cache.get, ast.parse, src.redup.core.hasher._ast_to_normalized_string, len, _normalize_cache.pop, src.redup.core.hasher._normalize_text, re.sub, re.sub

### src.redup.core.ts_extractor._extract_functions_ruby
> Extract functions from Ruby using tree-sitter.
- **Calls**: node.child_by_field_name, blocks.append, traverse, name_node.text.decode, CodeBlock, node.child_by_field_name, blocks.append, name_node.text.decode

### src.redup.core.ts_extractor._extract_functions_php
> Extract functions from PHP using tree-sitter.
- **Calls**: node.child_by_field_name, blocks.append, traverse, name_node.text.decode, CodeBlock, blocks.append, parent.child_by_field_name, CodeBlock

### src.redup.core.cache.HashCache.store_file_hashes
> Store file and block hashes in cache.
- **Calls**: self._get_file_hash, time.time, self.db.execute, self.db.execute, self.db.commit, file_path.stat, self.db.executemany, str

### src.redup.core.fuzzy_similarity.HTMLComponentExtractor._extract_attributes
> Extract key attributes for comparison.
- **Calls**: re.findall, re.search, re.findall, None.join, None.lower, None.join, sorted, sorted

### src.redup.core.fuzzy_similarity.CSSComponentExtractor._detect_css_component_type
> Detect component type from CSS selector and properties.
- **Calls**: re.search, None.strip, any, any, selector_match.group, any, selector.lower, any

### src.redup.core.fuzzy_similarity.FuzzySimilarityDetector._compute_attribute_similarity
> Compute similarity between attribute dictionaries.
- **Calls**: src.redup.config.RedupConfig.set, src.redup.config.RedupConfig.set, attrs1.keys, attrs2.keys, len, len, value_similarities.append, value_similarities.append

### src.redup.core.ts_extractor.extractors.dotnet.extract_functions_c_sharp
> Extract functions from C# using tree-sitter.
- **Calls**: traverse, node.child_by_field_name, blocks.append, traverse, src.redup.core.ts_extractor.extractors.base.get_node_text, src.redup.core.ts_extractor.extractors.dotnet._extract_class_name, src.redup.core.ts_extractor.extractors.base.create_code_block, node.child_by_field_name

## Process Flows

Key execution flows identified:

### Flow 1: _preload_files
```
_preload_files [src.redup.core.scanner_loader]
```

### Flow 2: benchmark
```
benchmark [benchmarks.bench_libraries]
  └─> generate_test_project
```

### Flow 3: benchmark_sequential_vs_parallel
```
benchmark_sequential_vs_parallel [benchmark]
```

### Flow 4: main
```
main [examples.01_basic_usage]
  └─ →> analyze
      └─ →> ensure_config
      └─ →> scan_phase
          └─ →> scan_project
```

### Flow 5: scan
```
scan [src.redup.cli_app.main]
```

### Flow 6: find_semantic_duplicates
```
find_semantic_duplicates [src.redup.core.semantic.SemanticDetector]
  └─ →> set
```

### Flow 7: benchmark_feature_performance
```
benchmark_feature_performance [benchmark]
  └─ →> analyze_parallel
      └─ →> ensure_config
```

### Flow 8: _get_duplication_metrics
```
_get_duplication_metrics [src.redup.reporters.enhanced_reporter.EnhancedReporter]
```

### Flow 9: _extract_functions_javascript
```
_extract_functions_javascript [src.redup.core.ts_extractor]
```

### Flow 10: run_server
```
run_server [src.redup.mcp.server]
```

## Key Classes

### src.redup.reporters.enhanced_reporter.EnhancedReporter
> Enhanced reporter with detailed metrics and visualizations.
- **Methods**: 17
- **Key Methods**: src.redup.reporters.enhanced_reporter.EnhancedReporter.__init__, src.redup.reporters.enhanced_reporter.EnhancedReporter.generate_metrics_report, src.redup.reporters.enhanced_reporter.EnhancedReporter._get_scan_metrics, src.redup.reporters.enhanced_reporter.EnhancedReporter._get_duplication_metrics, src.redup.reporters.enhanced_reporter.EnhancedReporter._get_language_metrics, src.redup.reporters.enhanced_reporter.EnhancedReporter._get_file_metrics, src.redup.reporters.enhanced_reporter.EnhancedReporter._get_complexity_metrics, src.redup.reporters.enhanced_reporter.EnhancedReporter._get_refactoring_metrics, src.redup.reporters.enhanced_reporter.EnhancedReporter._bucket_similarities, src.redup.reporters.enhanced_reporter.EnhancedReporter._bucket_group_sizes

### src.redup.core.universal_fuzzy.UniversalFuzzyExtractor
> Universal fuzzy extractor for all supported languages and DSLs.
- **Methods**: 11
- **Key Methods**: src.redup.core.universal_fuzzy.UniversalFuzzyExtractor.__init__, src.redup.core.universal_fuzzy.UniversalFuzzyExtractor.extract_universal_signature, src.redup.core.universal_fuzzy.UniversalFuzzyExtractor._detect_language, src.redup.core.universal_fuzzy.UniversalFuzzyExtractor._normalize_code, src.redup.core.universal_fuzzy.UniversalFuzzyExtractor._remove_comments, src.redup.core.universal_fuzzy.UniversalFuzzyExtractor._normalize_identifiers, src.redup.core.universal_fuzzy.UniversalFuzzyExtractor._detect_component_type, src.redup.core.universal_fuzzy.UniversalFuzzyExtractor._extract_semantic_patterns, src.redup.core.universal_fuzzy.UniversalFuzzyExtractor._extract_metadata, src.redup.core.universal_fuzzy.UniversalFuzzyExtractor._compute_complexity

### src.redup.core.utils.diff_helpers.GroupMatcher
> Match duplicate groups between two scan results.
- **Methods**: 10
- **Key Methods**: src.redup.core.utils.diff_helpers.GroupMatcher.__init__, src.redup.core.utils.diff_helpers.GroupMatcher._match_exact_ids, src.redup.core.utils.diff_helpers.GroupMatcher._get_remaining_groups, src.redup.core.utils.diff_helpers.GroupMatcher._find_best_match, src.redup.core.utils.diff_helpers.GroupMatcher._match_similar_groups, src.redup.core.utils.diff_helpers.GroupMatcher._ensure_matches, src.redup.core.utils.diff_helpers.GroupMatcher._match_score, src.redup.core.utils.diff_helpers.GroupMatcher.get_resolved_groups, src.redup.core.utils.diff_helpers.GroupMatcher.get_new_groups, src.redup.core.utils.diff_helpers.GroupMatcher.get_unchanged_groups

### src.redup.core.hash_cache.HashCache
> Cache for file hashes to enable incremental scanning.
- **Methods**: 9
- **Key Methods**: src.redup.core.hash_cache.HashCache.__init__, src.redup.core.hash_cache.HashCache._load, src.redup.core.hash_cache.HashCache.save, src.redup.core.hash_cache.HashCache.get_file_hash, src.redup.core.hash_cache.HashCache.is_unchanged, src.redup.core.hash_cache.HashCache.update, src.redup.core.hash_cache.HashCache.invalidate, src.redup.core.hash_cache.HashCache.get_cached_results, src.redup.core.hash_cache.HashCache.clear

### src.redup.core.cache.HashCache
> SQLite-based cache for file and block hashes.

Provides ~10x speedup for incremental scans by cachin
- **Methods**: 8
- **Key Methods**: src.redup.core.cache.HashCache.__init__, src.redup.core.cache.HashCache._init_tables, src.redup.core.cache.HashCache._get_file_hash, src.redup.core.cache.HashCache.is_file_unchanged, src.redup.core.cache.HashCache.get_cached_block_hashes, src.redup.core.cache.HashCache.store_file_hashes, src.redup.core.cache.HashCache.cleanup_old_entries, src.redup.core.cache.HashCache.get_stats

### src.redup.core.fuzzy_similarity.HTMLComponentExtractor
> Extract HTML components with semantic normalization for fuzzy matching.
- **Methods**: 8
- **Key Methods**: src.redup.core.fuzzy_similarity.HTMLComponentExtractor.__init__, src.redup.core.fuzzy_similarity.HTMLComponentExtractor.extract_component_signature, src.redup.core.fuzzy_similarity.HTMLComponentExtractor._normalize_html, src.redup.core.fuzzy_similarity.HTMLComponentExtractor._normalize_class_name, src.redup.core.fuzzy_similarity.HTMLComponentExtractor._detect_component_type, src.redup.core.fuzzy_similarity.HTMLComponentExtractor._extract_attributes, src.redup.core.fuzzy_similarity.HTMLComponentExtractor._extract_text_content, src.redup.core.fuzzy_similarity.HTMLComponentExtractor._compute_structure_hash

### src.redup.core.fuzzy_similarity.CSSComponentExtractor
> Extract CSS components with semantic normalization for fuzzy matching.
- **Methods**: 6
- **Key Methods**: src.redup.core.fuzzy_similarity.CSSComponentExtractor.__init__, src.redup.core.fuzzy_similarity.CSSComponentExtractor.extract_component_signature, src.redup.core.fuzzy_similarity.CSSComponentExtractor._extract_css_properties, src.redup.core.fuzzy_similarity.CSSComponentExtractor._normalize_css_value, src.redup.core.fuzzy_similarity.CSSComponentExtractor._detect_css_component_type, src.redup.core.fuzzy_similarity.CSSComponentExtractor._compute_css_hash

### src.redup.core.fuzzy_similarity.FuzzySimilarityDetector
> Detect fuzzy similarity between HTML/CSS components.
- **Methods**: 6
- **Key Methods**: src.redup.core.fuzzy_similarity.FuzzySimilarityDetector.__init__, src.redup.core.fuzzy_similarity.FuzzySimilarityDetector.find_similar_components, src.redup.core.fuzzy_similarity.FuzzySimilarityDetector._extract_signature, src.redup.core.fuzzy_similarity.FuzzySimilarityDetector._compute_similarity, src.redup.core.fuzzy_similarity.FuzzySimilarityDetector._compute_attribute_similarity, src.redup.core.fuzzy_similarity.FuzzySimilarityDetector._compute_css_similarity

### src.redup.config.RedupConfig
> Global configuration container for reDUP settings.

Attributes can be set via:
- Environment variabl
- **Methods**: 5
- **Key Methods**: src.redup.config.RedupConfig._env_name, src.redup.config.RedupConfig._load_from_env, src.redup.config.RedupConfig.reload, src.redup.config.RedupConfig.get, src.redup.config.RedupConfig.set

### src.redup.core.universal_fuzzy.UniversalFuzzyDetector
> Universal fuzzy similarity detector for all languages and DSLs.
- **Methods**: 5
- **Key Methods**: src.redup.core.universal_fuzzy.UniversalFuzzyDetector.__init__, src.redup.core.universal_fuzzy.UniversalFuzzyDetector.find_similar_components, src.redup.core.universal_fuzzy.UniversalFuzzyDetector._compute_universal_similarity, src.redup.core.universal_fuzzy.UniversalFuzzyDetector._compute_pattern_similarity, src.redup.core.universal_fuzzy.UniversalFuzzyDetector._compute_metadata_similarity

### src.redup.core.semantic.SemanticDetector
> Detects semantically similar code using transformer embeddings.
- **Methods**: 5
- **Key Methods**: src.redup.core.semantic.SemanticDetector.__init__, src.redup.core.semantic.SemanticDetector._ensure_model, src.redup.core.semantic.SemanticDetector.find_semantic_duplicates, src.redup.core.semantic.SemanticDetector.find_semantic_duplicates_fast, src.redup.core.semantic.SemanticDetector.compute_semantic_similarity

### src.redup.core.lsh_matcher.LSHIndex
> LSH index for efficient near-duplicate detection.
- **Methods**: 5
- **Key Methods**: src.redup.core.lsh_matcher.LSHIndex.__init__, src.redup.core.lsh_matcher.LSHIndex.add, src.redup.core.lsh_matcher.LSHIndex.find_near_duplicates, src.redup.core.lsh_matcher.LSHIndex._find_near_duplicates_simple, src.redup.core.lsh_matcher.LSHIndex.find_all_near_duplicates

### src.redup.core.utils.language_dispatcher.LanguageDispatcher
> Dispatches function extraction to appropriate language-specific extractors.
- **Methods**: 5
- **Key Methods**: src.redup.core.utils.language_dispatcher.LanguageDispatcher.__init__, src.redup.core.utils.language_dispatcher.LanguageDispatcher.register_extractor, src.redup.core.utils.language_dispatcher.LanguageDispatcher.register_group, src.redup.core.utils.language_dispatcher.LanguageDispatcher.get_extractor, src.redup.core.utils.language_dispatcher.LanguageDispatcher.extract_functions

### src.redup.core.scanner_cache.MemoryFileCache
> Cache file contents in RAM for faster access during scanning.
- **Methods**: 4
- **Key Methods**: src.redup.core.scanner_cache.MemoryFileCache.__init__, src.redup.core.scanner_cache.MemoryFileCache._estimate_size, src.redup.core.scanner_cache.MemoryFileCache.get_file_content, src.redup.core.scanner_cache.MemoryFileCache._evict_oldest

### src.redup.core.models.DuplicateGroup
> A cluster of duplicated code fragments.
- **Methods**: 4
- **Key Methods**: src.redup.core.models.DuplicateGroup.occurrences, src.redup.core.models.DuplicateGroup.total_lines, src.redup.core.models.DuplicateGroup.saved_lines_potential, src.redup.core.models.DuplicateGroup.impact_score

### src.redup.core.models.DuplicationMap
> Complete result of a reDUP analysis run.
- **Methods**: 4
- **Key Methods**: src.redup.core.models.DuplicationMap.total_groups, src.redup.core.models.DuplicationMap.total_fragments, src.redup.core.models.DuplicationMap.total_saved_lines, src.redup.core.models.DuplicationMap.sorted_by_impact

### src.redup.core.utils.function_extractor.FunctionExtractor
> Generic function extractor that can be configured for different languages.
- **Methods**: 4
- **Key Methods**: src.redup.core.utils.function_extractor.FunctionExtractor.__init__, src.redup.core.utils.function_extractor.FunctionExtractor.extract_functions, src.redup.core.utils.function_extractor.FunctionExtractor._create_function_block, src.redup.core.utils.function_extractor.FunctionExtractor._create_method_block

### src.redup.core.lazy_grouper.DuplicateGroupCollector
> Collector for lazy duplicate groups with optional limits.

Allows collecting lazy groups with limits
- **Methods**: 3
- **Key Methods**: src.redup.core.lazy_grouper.DuplicateGroupCollector.__init__, src.redup.core.lazy_grouper.DuplicateGroupCollector.collect, src.redup.core.lazy_grouper.DuplicateGroupCollector.collect_sorted

### src.redup.core.comparator.CrossProjectComparison
> Full comparison result between two projects.
- **Methods**: 2
- **Key Methods**: src.redup.core.comparator.CrossProjectComparison.total_matches, src.redup.core.comparator.CrossProjectComparison.shared_loc_potential

### src.redup.core.lsh_matcher._SimpleMinHash
> Simple MinHash implementation for fallback without datasketch.
- **Methods**: 2
- **Key Methods**: src.redup.core.lsh_matcher._SimpleMinHash.__init__, src.redup.core.lsh_matcher._SimpleMinHash.jaccard

## Data Transformation Functions

Key functions that process and transform data:

### src.redup.utils._parse_extensions
- **Output to**: isinstance, value.split, list, None.strip, extensions.append

### src.redup.core.hash_cache.HashCache.invalidate
> Invalidate cache for a file or entire cache.
- **Output to**: str, self._cache.pop

### src.redup.core.refactor_advisor._parse_llm_response
> Parse LLM response into structured tasks.
- **Output to**: raw.strip, text.startswith, data.get, data.get, text.split

### src.redup.core.refactor_advisor.format_plan_markdown
> Format a RefactorPlan as a markdown TODO list.
- **Output to**: lines.append, lines.append, lines.append, lines.append, lines.append

### src.redup.core.refactor_advisor.format_plan_json
> Format a RefactorPlan as a JSON-serialisable dict.

### src.redup.core.python_parser._parse_with_libcst
> Fast path — libcst CST parsing.
- **Output to**: cst.parse_module, tree.visit, self._class_stack.append, self._class_stack.pop, len

### src.redup.core.python_parser._parse_with_ast
> Fallback — stdlib ast parsing.
- **Output to**: source.splitlines, src.redup.core.python_parser._build_parent_map, ast.walk, ast.parse, isinstance

### src.redup.core.python_parser.parse_python_functions
> Parse Python source — uses libcst if available, falls back to ast.
- **Output to**: src.redup.core.python_parser._parse_with_ast, src.redup.core.python_parser._parse_with_libcst

### src.redup.core.python_parser.parsed_to_code_blocks
> Convert ParsedFunction list to CodeBlock list for pipeline compatibility.
- **Output to**: CodeBlock

### src.redup.analysis_logic._parse_extensions
> Parse comma-separated extension string into list.
- **Output to**: e.strip, ext_string.split, e.strip

### src.redup.core.scanner._process_single_file
> Process a single file and return ScannedFile or None if skipped.
- **Output to**: src.redup.core.scanner._get_source_for_file, source.splitlines, str, src.redup.core.scanner._extract_blocks_for_file, ScannedFile

### src.redup.core.pipeline.phases.process_blocks
> Phase 2: Extract and filter code blocks with memory optimization.
- **Output to**: range, len, all_blocks.append

### src.redup.core.differ.format_diff_result
> Format a DiffResult as a human-readable string.
- **Output to**: lines.append, lines.append, lines.append, lines.append, lines.append

### src.redup.cli_app.fuzzy_similarity._validate_fuzzy_input
> Validate input parameters for fuzzy similarity analysis.
- **Output to**: FuzzyValidationResult, FuzzyValidationResult, FuzzyValidationResult

### src.redup.cli_app.compare_command._parse_extensions
> Parse comma-separated extensions string into list.
- **Output to**: e.strip, extensions.split

### src.redup.mcp.utils.parse_extensions
- **Output to**: isinstance, value.split, list, None.strip, None.strip

### src.redup.mcp.handlers._format_analysis_result
> Format analysis result based on output format.
- **Output to**: ValueError, src.redup.reporters.json_reporter.to_json, src.redup.reporters.yaml_reporter.to_yaml, src.redup.reporters.toon_reporter.to_toon, src.redup.reporters.markdown_reporter.to_markdown

### src.redup.mcp.handlers._format_top_groups
> Format top groups by impact for response.
- **Output to**: round, dup_map.sorted_by_impact, min

## Behavioral Patterns

### recursion__json_safe
- **Type**: recursion
- **Confidence**: 0.90
- **Functions**: src.redup.utils._json_safe

### recursion_traverse_tree
- **Type**: recursion
- **Confidence**: 0.90
- **Functions**: src.redup.core.ts_extractor.extractors.base.traverse_tree

### recursion_json_safe
- **Type**: recursion
- **Confidence**: 0.90
- **Functions**: src.redup.mcp.utils.json_safe

### state_machine_EnhancedReporter
- **Type**: state_machine
- **Confidence**: 0.70
- **Functions**: src.redup.reporters.enhanced_reporter.EnhancedReporter.__init__, src.redup.reporters.enhanced_reporter.EnhancedReporter.generate_metrics_report, src.redup.reporters.enhanced_reporter.EnhancedReporter._get_scan_metrics, src.redup.reporters.enhanced_reporter.EnhancedReporter._get_duplication_metrics, src.redup.reporters.enhanced_reporter.EnhancedReporter._get_language_metrics

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `src.redup.reporters.markdown_reporter.to_markdown` - 54 calls
- `src.redup.reporters.code2llm_reporter.to_code2llm_context` - 36 calls
- `src.redup.core.differ.format_diff_result` - 35 calls
- `src.redup.core.ts_extractor.dispatcher.initialize_language_dispatcher` - 31 calls
- `src.redup.core.pipeline.analyze_optimized` - 29 calls
- `benchmarks.bench_libraries.benchmark` - 27 calls
- `benchmark.benchmark_sequential_vs_parallel` - 26 calls
- `src.redup.cli_app.scan_commands.scan_command` - 26 calls
- `src.redup.cli_app.output_writer.write_results` - 25 calls
- `examples.01_basic_usage.main` - 23 calls
- `src.redup.cli_app.scan_commands.config_command` - 23 calls
- `src.redup.core.refactor_advisor.format_plan_markdown` - 20 calls
- `src.redup.core.community.detect_communities` - 20 calls
- `src.redup.core.scanner.scan_project` - 20 calls
- `src.redup.cli_app.scan_commands.check_command` - 19 calls
- `src.redup.core.pipeline.analyze_parallel` - 19 calls
- `src.redup.core.config.config_to_scan_config` - 18 calls
- `src.redup.core.pipeline.duplicate_finder.find_duplicates_phase_lazy` - 17 calls
- `src.redup.reporters.code2llm_reporter.to_code2llm_toon` - 17 calls
- `src.redup.cli_app.main.scan` - 17 calls
- `src.redup.core.semantic.SemanticDetector.find_semantic_duplicates` - 16 calls
- `benchmark.benchmark_feature_performance` - 15 calls
- `src.redup.mcp.server.run_server` - 14 calls
- `src.redup.mcp.handlers.handle_check_project` - 14 calls
- `benchmarks.bench_libraries.benchmark_hash_performance` - 13 calls
- `src.redup.core.comparator.compare_projects` - 13 calls
- `src.redup.core.pipeline.duplicate_finder.find_near_duplicate_groups` - 13 calls
- `src.redup.cli_app.main.compare` - 13 calls
- `benchmarks.bench_libraries.benchmark_fuzzy_performance` - 12 calls
- `src.redup.core.pipeline.duplicate_finder.find_structural_groups` - 12 calls
- `src.redup.mcp.handlers.handle_analyze_project` - 12 calls
- `src.redup.core.cache.HashCache.store_file_hashes` - 11 calls
- `src.redup.core.ts_extractor.extractors.dotnet.extract_functions_c_sharp` - 11 calls
- `src.redup.reporters.toon_reporter.to_toon` - 11 calls
- `src.redup.mcp.handlers.handle_suggest_refactoring` - 11 calls
- `src.redup.core.refactor_advisor.generate_refactor_plan` - 10 calls
- `src.redup.core.ts_extractor.extract_functions_treesitter` - 10 calls
- `src.redup.core.ts_extractor.main.extract_functions_treesitter` - 10 calls
- `src.redup.core.ts_extractor.extractors.ruby.extract_functions_ruby` - 10 calls
- `src.redup.core.differ.compare_scans` - 10 calls

## System Interactions

How components interact:

```mermaid
graph TD
    _preload_files --> time
    _preload_files --> sort
    _preload_files --> len
    _preload_files --> print
    benchmark --> TemporaryDirectory
    benchmark --> Path
    benchmark --> generate_test_projec
    benchmark --> ScanConfig
    benchmark --> perf_counter
    benchmark_sequential --> print
    benchmark_sequential --> ScanConfig
    benchmark_sequential --> time
    main --> ScanConfig
    main --> analyze
    main --> print
    scan --> command
    scan --> Argument
    scan --> Option
    find_semantic_duplic --> _ensure_model
    find_semantic_duplic --> encode
    find_semantic_duplic --> cos_sim
    find_semantic_duplic --> set
    find_semantic_duplic --> range
    benchmark_feature_pe --> print
    benchmark_feature_pe --> time
    benchmark_feature_pe --> analyze_parallel
    _get_duplication_met --> sum
    _get_duplication_met --> Counter
    _get_duplication_met --> len
    _get_duplication_met --> dict
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.