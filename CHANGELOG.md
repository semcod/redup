# Changelog

## [Unreleased]

## [0.1.4] - 2026-03-23

### Docs
- Update COMPLEXITY_REDUCTION_COMPLETE.md
- Update CONTINUATION_PLAN.md
- Update code2llm_output/README.md
- Update code2llm_output/context.md
- Update complexity_reduction_plan.md
- Update docs/README.md
- Update project/README.md
- Update project/context.md

### Other
- Update VERSION
- Update code2llm_output/analysis.toon
- Update project.sh
- Update project/analysis.toon
- Update project/calls.mmd
- Update project/calls.png
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- Update project/dashboard.html
- Update project/duplication.json
- ... and 11 more files

## [0.1.2] - 2026-03-23

### Docs
- Update REFACTORING_SUMMARY.md
- Update TODO.md
- Update proxy_refactoring_plan.md

### Other
- Update .idea/misc.xml
- Update .idea/redup.iml
- Update cli_utilities_demo.py
- Update project.sh
- Update proxy_analysis/duplication.json
- Update proxy_analysis/duplication.toon
- Update proxy_analysis/duplication.yaml
- Update redup_self_analysis/duplication.json
- Update refactored_frontend_demo.py

## [0.1.1] - 2026-03-22

### Docs
- Update CHANGELOG.md
- Update README.md

### Test
- Update tests/__init__.py
- Update tests/test_e2e.py
- Update tests/test_hasher.py
- Update tests/test_matcher.py
- Update tests/test_models.py
- Update tests/test_pipeline.py
- Update tests/test_planner.py
- Update tests/test_reporters.py
- Update tests/test_scanner.py

### Other
- Update .gitignore
- Update .idea/.gitignore
- Update .idea/inspectionProfiles/Project_Default.xml
- Update .idea/inspectionProfiles/profiles_settings.xml
- Update .idea/misc.xml
- Update .idea/modules.xml
- Update .idea/redup.iml
- Update .idea/vcs.xml
- Update LICENSE
- Update examples/01_basic_usage.py


All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-22

### Added

- **Core pipeline**: scan → hash → match → group → plan → report
- **Scanner**: file discovery with glob/fnmatch, Python AST function extraction, sliding-window block extraction
- **Hasher**: SHA-256 exact hashing, structural hashing with variable/literal normalization
- **Matcher**: SequenceMatcher fuzzy similarity, rapidfuzz support (optional)
- **Planner**: refactoring suggestion generator with impact scoring and risk assessment
- **JSON reporter**: machine-readable duplication map
- **YAML reporter**: human-readable duplication report
- **TOON reporter**: LLM-optimized compact diagnostic format
- **CLI**: `redup scan` and `redup info` commands via Typer
- **Tests**: 35+ tests covering models, scanner, hasher, matcher, planner, pipeline, reporters
- **Example**: basic usage script

### Architecture

```
src/redup/
├── core/          # scanner, hasher, matcher, planner, pipeline, models
├── reporters/     # json, yaml, toon output formats
└── cli_app/       # typer CLI
```
