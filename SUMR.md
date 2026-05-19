# reDUP

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Dependencies](#dependencies)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `redup`
- **version**: `0.4.25`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Taskfile.yml, testql(2), app.doql.less, pyqual.yaml, goal.yaml, .env.example, project/(6 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: redup;
  version: 0.4.25;
}

dependencies {
  runtime: "pyyaml>=6.0, typer>=0.12.0, rich>=13.0, pydantic>=2.0, tomli>=2.0; python_version<'3.11', python-dotenv>=1.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
  dev: "pytest>=7.0, pytest-cov>=4.0, ruff>=0.4, mypy>=1.8, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
}

interface[type="cli"] {
  framework: argparse;
}
interface[type="cli"] page[name="redup"] {

}

workflow[name="install"] {
  trigger: manual;
  step-1: run cmd=pip install -e .[dev];
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=pytest -q;
}

workflow[name="lint"] {
  trigger: manual;
  step-1: run cmd=ruff check .;
}

workflow[name="jscpd"] {
  trigger: manual;
  step-1: run cmd=scripts/jscpd-check.sh;
}

workflow[name="quality"] {
  trigger: manual;
  step-1: run cmd=taskfile run lint;
  step-2: run cmd=taskfile run jscpd;
}

workflow[name="fmt"] {
  trigger: manual;
  step-1: run cmd=ruff format .;
}

workflow[name="build"] {
  trigger: manual;
  step-1: run cmd=python -m build;
}

workflow[name="clean"] {
  trigger: manual;
  step-1: run cmd=rm -rf build/ dist/ *.egg-info;
}

workflow[name="health"] {
  trigger: manual;
  step-1: run cmd=docker compose ps;
  step-2: run cmd=docker compose exec app echo "Health check passed";
}

workflow[name="all"] {
  trigger: manual;
  step-1: run cmd=taskfile run install;
  step-2: run cmd=taskfile run lint;
  step-3: run cmd=taskfile run test;
}

workflow[name="help"] {
  trigger: manual;
  step-1: run cmd=echo "redup — available tasks:";
  step-2: run cmd=echo "";
  step-3: run cmd=taskfile list;
}

workflow[name="format"] {
  trigger: manual;
  step-1: run cmd=ruff format .;
}

workflow[name="sumd"] {
  trigger: manual;
  step-1: run cmd=echo "# $(basename $(pwd))" > SUMD.md
echo "" >> SUMD.md
echo "$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('description','Project description'))" 2>/dev/null || echo 'Project description')" >> SUMD.md
echo "" >> SUMD.md
echo "## Contents" >> SUMD.md
echo "" >> SUMD.md
echo "- [Metadata](#metadata)" >> SUMD.md
echo "- [Architecture](#architecture)" >> SUMD.md
echo "- [Dependencies](#dependencies)" >> SUMD.md
echo "- [Source Map](#source-map)" >> SUMD.md
echo "- [Intent](#intent)" >> SUMD.md
echo "" >> SUMD.md
echo "## Metadata" >> SUMD.md
echo "" >> SUMD.md
echo "- **name**: \`$(basename $(pwd))\`" >> SUMD.md
echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMD.md
echo "- **python_requires**: \`>=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d. -f1,2)\`" >> SUMD.md
echo "- **license**: $(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('license',{}).get('text','MIT'))" 2>/dev/null || echo 'MIT')" >> SUMD.md
echo "- **ecosystem**: SUMD + DOQL + testql + taskfile" >> SUMD.md
echo "- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, src/" >> SUMD.md
echo "" >> SUMD.md
echo "## Architecture" >> SUMD.md
echo "" >> SUMD.md
echo '```' >> SUMD.md
echo "SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)" >> SUMD.md
echo '```' >> SUMD.md
echo "" >> SUMD.md
echo "## Source Map" >> SUMD.md
echo "" >> SUMD.md
find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -not -path './__pycache__/*' -not -path './.git/*' | head -50 | sed 's|^./||' | sed 's|^|- |' >> SUMD.md
echo "Generated SUMD.md";
  step-2: run cmd=python3 -c "
import json, os, subprocess
from pathlib import Path
project_name = Path.cwd().name
py_files = list(Path('.').rglob('*.py'))
py_files = [f for f in py_files if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])]
data = {
    'project_name': project_name,
    'description': 'SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization',
    'files': [{'path': str(f), 'type': 'python'} for f in py_files[:100]]
}
with open('sumd.json', 'w') as f:
    json.dump(data, f, indent=2)
print('Generated sumd.json')
" 2>/dev/null || echo 'Python generation failed, using fallback';
}

workflow[name="sumr"] {
  trigger: manual;
  step-1: run cmd=echo "# $(basename $(pwd)) - Summary Report" > SUMR.md
echo "" >> SUMR.md
echo "SUMR - Summary Report for project analysis" >> SUMR.md
echo "" >> SUMR.md
echo "## Contents" >> SUMR.md
echo "" >> SUMR.md
echo "- [Metadata](#metadata)" >> SUMR.md
echo "- [Quality Status](#quality-status)" >> SUMR.md
echo "- [Metrics](#metrics)" >> SUMR.md
echo "- [Refactoring Analysis](#refactoring-analysis)" >> SUMR.md
echo "- [Intent](#intent)" >> SUMR.md
echo "" >> SUMR.md
echo "## Metadata" >> SUMR.md
echo "" >> SUMR.md
echo "- **name**: \`$(basename $(pwd))\`" >> SUMR.md
echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMR.md
echo "- **generated_at**: \`$(date -Iseconds)\`" >> SUMR.md
echo "" >> SUMR.md
echo "## Quality Status" >> SUMR.md
echo "" >> SUMR.md
if [ -f pyqual.yaml ]; then
  echo "- **pyqual_config**: ✅ Present" >> SUMR.md
  echo "- **last_run**: $(stat -c %y .pyqual/pipeline.db 2>/dev/null | cut -d' ' -f1 || echo 'N/A')" >> SUMR.md
else
  echo "- **pyqual_config**: ❌ Missing" >> SUMR.md
fi
echo "" >> SUMR.md
echo "## Metrics" >> SUMR.md
echo "" >> SUMR.md
py_files=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' | wc -l)
echo "- **python_files**: $py_files" >> SUMR.md
lines=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -exec cat {} \; 2>/dev/null | wc -l)
echo "- **total_lines**: $lines" >> SUMR.md
echo "" >> SUMR.md
echo "## Refactoring Analysis" >> SUMR.md
echo "" >> SUMR.md
echo "Run \`code2llm ./ -f evolution\` for detailed refactoring queue." >> SUMR.md
echo "Generated SUMR.md";
  step-2: run cmd=python3 -c "
import json, os, subprocess
from pathlib import Path
from datetime import datetime
project_name = Path.cwd().name
py_files = len([f for f in Path('.').rglob('*.py') if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])])
data = {
    'project_name': project_name,
    'report_type': 'SUMR',
    'generated_at': datetime.now().isoformat(),
    'metrics': {
        'python_files': py_files,
        'has_pyqual_config': Path('pyqual.yaml').exists()
    }
}
with open('SUMR.json', 'w') as f:
    json.dump(data, f, indent=2)
print('Generated SUMR.json')
" 2>/dev/null || echo 'Python generation failed, using fallback';
}

deploy {
  target: pip;
}

environment[name="local"] {
  runtime: python;
  env_file: .env;
  python_version: >=3.10;
}
```

## Workflows

### Taskfile Tasks (`Taskfile.yml`)

```yaml markpact:taskfile path=Taskfile.yml
version: '1'
name: redup
description: Minimal Taskfile
variables:
  APP_NAME: redup
environments:
  local:
    container_runtime: docker
    compose_command: docker compose
pipeline:
  python_version: "3.12"
  runner_image: ubuntu-latest
  branches: [main]
  cache: [~/.cache/pip]
  artifacts: [dist/]

  stages:
    - name: lint
      tasks: [lint]

    - name: test
      tasks: [test]

    - name: build
      tasks: [build]
      when: "branch:main"

tasks:
  install:
    desc: Install Python dependencies (editable)
    cmds:
    - pip install -e .[dev]
  test:
    desc: Run pytest suite
    cmds:
    - pytest -q
  lint:
    desc: Run ruff lint check
    cmds:
    - ruff check .
  jscpd:
    desc: Run jscpd duplicate-code budget
    cmds:
    - scripts/jscpd-check.sh
  quality:
    desc: Run lint and duplicate-code gates
    cmds:
    - taskfile run lint
    - taskfile run jscpd
  fmt:
    desc: Auto-format with ruff
    cmds:
    - ruff format .
  build:
    desc: Build wheel + sdist
    cmds:
    - python -m build
  clean:
    desc: Remove build artefacts
    cmds:
    - rm -rf build/ dist/ *.egg-info
  health:
    desc: '[from doql] workflow: health'
    cmds:
    - docker compose ps
    - docker compose exec app echo "Health check passed"
  all:
    desc: Run install, lint, test
    cmds:
    - taskfile run install
    - taskfile run lint
    - taskfile run test
  help:
    desc: Show available tasks
    cmds:
    - echo "redup — available tasks:"
    - echo ""
    - taskfile list
  format:
    desc: Auto-format with ruff (alias of fmt)
    cmds:
    - ruff format .
  sumd:
    desc: Generate SUMD (Structured Unified Markdown Descriptor) for AI-aware project description
    cmds:
    - |
      echo "# $(basename $(pwd))" > SUMD.md
      echo "" >> SUMD.md
      echo "$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('description','Project description'))" 2>/dev/null || echo 'Project description')" >> SUMD.md
      echo "" >> SUMD.md
      echo "## Contents" >> SUMD.md
      echo "" >> SUMD.md
      echo "- [Metadata](#metadata)" >> SUMD.md
      echo "- [Architecture](#architecture)" >> SUMD.md
      echo "- [Dependencies](#dependencies)" >> SUMD.md
      echo "- [Source Map](#source-map)" >> SUMD.md
      echo "- [Intent](#intent)" >> SUMD.md
      echo "" >> SUMD.md
      echo "## Metadata" >> SUMD.md
      echo "" >> SUMD.md
      echo "- **name**: \`$(basename $(pwd))\`" >> SUMD.md
      echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMD.md
      echo "- **python_requires**: \`>=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d. -f1,2)\`" >> SUMD.md
      echo "- **license**: $(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('license',{}).get('text','MIT'))" 2>/dev/null || echo 'MIT')" >> SUMD.md
      echo "- **ecosystem**: SUMD + DOQL + testql + taskfile" >> SUMD.md
      echo "- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, src/" >> SUMD.md
      echo "" >> SUMD.md
      echo "## Architecture" >> SUMD.md
      echo "" >> SUMD.md
      echo '```' >> SUMD.md
      echo "SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)" >> SUMD.md
      echo '```' >> SUMD.md
      echo "" >> SUMD.md
      echo "## Source Map" >> SUMD.md
      echo "" >> SUMD.md
      find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -not -path './__pycache__/*' -not -path './.git/*' | head -50 | sed 's|^./||' | sed 's|^|- |' >> SUMD.md
      echo "Generated SUMD.md"
    - |
      python3 -c "
      import json, os, subprocess
      from pathlib import Path
      project_name = Path.cwd().name
      py_files = list(Path('.').rglob('*.py'))
      py_files = [f for f in py_files if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])]
      data = {
          'project_name': project_name,
          'description': 'SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization',
          'files': [{'path': str(f), 'type': 'python'} for f in py_files[:100]]
      }
      with open('sumd.json', 'w') as f:
          json.dump(data, f, indent=2)
      print('Generated sumd.json')
      " 2>/dev/null || echo 'Python generation failed, using fallback'
  sumr:
    desc: Generate SUMR (Summary Report) with project metrics and health status
    cmds:
    - |
      echo "# $(basename $(pwd)) - Summary Report" > SUMR.md
      echo "" >> SUMR.md
      echo "SUMR - Summary Report for project analysis" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Contents" >> SUMR.md
      echo "" >> SUMR.md
      echo "- [Metadata](#metadata)" >> SUMR.md
      echo "- [Quality Status](#quality-status)" >> SUMR.md
      echo "- [Metrics](#metrics)" >> SUMR.md
      echo "- [Refactoring Analysis](#refactoring-analysis)" >> SUMR.md
      echo "- [Intent](#intent)" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Metadata" >> SUMR.md
      echo "" >> SUMR.md
      echo "- **name**: \`$(basename $(pwd))\`" >> SUMR.md
      echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMR.md
      echo "- **generated_at**: \`$(date -Iseconds)\`" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Quality Status" >> SUMR.md
      echo "" >> SUMR.md
      if [ -f pyqual.yaml ]; then
        echo "- **pyqual_config**: ✅ Present" >> SUMR.md
        echo "- **last_run**: $(stat -c %y .pyqual/pipeline.db 2>/dev/null | cut -d' ' -f1 || echo 'N/A')" >> SUMR.md
      else
        echo "- **pyqual_config**: ❌ Missing" >> SUMR.md
      fi
      echo "" >> SUMR.md
      echo "## Metrics" >> SUMR.md
      echo "" >> SUMR.md
      py_files=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' | wc -l)
      echo "- **python_files**: $py_files" >> SUMR.md
      lines=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -exec cat {} \; 2>/dev/null | wc -l)
      echo "- **total_lines**: $lines" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Refactoring Analysis" >> SUMR.md
      echo "" >> SUMR.md
      echo "Run \`code2llm ./ -f evolution\` for detailed refactoring queue." >> SUMR.md
      echo "Generated SUMR.md"
    - |
      python3 -c "
      import json, os, subprocess
      from pathlib import Path
      from datetime import datetime
      project_name = Path.cwd().name
      py_files = len([f for f in Path('.').rglob('*.py') if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])])
      data = {
          'project_name': project_name,
          'report_type': 'SUMR',
          'generated_at': datetime.now().isoformat(),
          'metrics': {
              'python_files': py_files,
              'has_pyqual_config': Path('pyqual.yaml').exists()
          }
      }
      with open('SUMR.json', 'w') as f:
          json.dump(data, f, indent=2)
      print('Generated SUMR.json')
      " 2>/dev/null || echo 'Python generation failed, using fallback'
```

## Quality Pipeline (`pyqual.yaml`)

```yaml markpact:pyqual path=pyqual.yaml
pipeline:
  name: redup-quality-loop
  profile: python-minimal

  metrics:
    cc_max: 15
    coverage_min: 40     # current: ~44%
    critical_max: 0

  stages:
    - name: test
      run: .venv/bin/pytest tests/ --cov=src/redup --cov-report=json:.pyqual/coverage.json -q
      when: always

  env:
    LLM_MODEL: openrouter/qwen/qwen3-coder-next
    LLX_DEFAULT_TIER: balanced
    LLX_VERBOSE: true
```

## Dependencies

### Runtime

```text markpact:deps python
pyyaml>=6.0
typer>=0.12.0
rich>=13.0
pydantic>=2.0
tomli>=2.0; python_version<'3.11'
python-dotenv>=1.0
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

### Development

```text markpact:deps python scope=dev
pytest>=7.0
pytest-cov>=4.0
ruff>=0.4
mypy>=1.8
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

## Call Graph

*253 nodes · 305 edges · 62 modules · CC̄=3.7*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `print` *(in scripts.jscpd-check)* | 0 | 66 | 0 | **66** |
| `to_markdown` *(in src.redup.reporters.markdown_reporter)* | 12 ⚠ | 3 | 54 | **57** |
| `to_code2llm_context` *(in src.redup.reporters.code2llm_reporter)* | 11 ⚠ | 3 | 36 | **39** |
| `tasks` *(in src.redup.cli_app.tasks_command)* | 14 ⚠ | 0 | 35 | **35** |
| `initialize_language_dispatcher` *(in src.redup.core.ts_extractor.dispatcher)* | 2 | 1 | 31 | **32** |
| `scan_project` *(in src.redup.core.scanner)* | 5 | 11 | 20 | **31** |
| `analyze_optimized` *(in src.redup.core.pipeline)* | 14 ⚠ | 2 | 29 | **31** |
| `set` *(in src.redup.config.RedupConfig)* | 2 | 25 | 3 | **28** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/redup
# generated in 0.24s
# nodes: 253 | edges: 305 | modules: 62
# CC̄=3.7

HUBS[20]:
  scripts.jscpd-check.print
    CC=0  in:66  out:0  total:66
  src.redup.reporters.markdown_reporter.to_markdown
    CC=12  in:3  out:54  total:57
  src.redup.reporters.code2llm_reporter.to_code2llm_context
    CC=11  in:3  out:36  total:39
  src.redup.cli_app.tasks_command.tasks
    CC=14  in:0  out:35  total:35
  src.redup.core.ts_extractor.dispatcher.initialize_language_dispatcher
    CC=2  in:1  out:31  total:32
  src.redup.core.scanner.scan_project
    CC=5  in:11  out:20  total:31
  src.redup.core.pipeline.analyze_optimized
    CC=14  in:2  out:29  total:31
  src.redup.config.RedupConfig.set
    CC=2  in:25  out:3  total:28
  benchmarks.bench_libraries.benchmark
    CC=10  in:0  out:27  total:27
  src.redup.cli_app.output_writer.write_results
    CC=12  in:1  out:25  total:26
  benchmark.benchmark_sequential_vs_parallel
    CC=3  in:0  out:26  total:26
  src.redup.mcp.handlers._build_scan_config
    CC=12  in:1  out:24  total:25
  src.redup.cli_app.scan_commands.config_command
    CC=5  in:1  out:23  total:24
  examples.01_basic_usage.main
    CC=5  in:0  out:23  total:23
  src.redup.core.differ._load_duplication_map
    CC=5  in:2  out:21  total:23
  src.redup.core.pipeline.analyze_parallel
    CC=3  in:4  out:19  total:23
  src.redup.core.config.config_to_scan_config
    CC=4  in:5  out:18  total:23
  src.redup.core.refactor_advisor._parse_llm_response
    CC=9  in:1  out:21  total:22
  src.redup.cli_app.compare_command._print_summary_table
    CC=1  in:1  out:20  total:21
  src.redup.core.community.detect_communities
    CC=11  in:1  out:20  total:21

MODULES:
  benchmark  [2 funcs]
    benchmark_feature_performance  CC=3  out:15
    benchmark_sequential_vs_parallel  CC=3  out:26
  benchmarks.bench_libraries  [4 funcs]
    benchmark  CC=10  out:27
    benchmark_fuzzy_performance  CC=4  out:12
    benchmark_hash_performance  CC=4  out:13
    generate_test_project  CC=3  out:5
  examples.01_basic_usage  [1 funcs]
    main  CC=5  out:23
  scripts.jscpd-check  [1 funcs]
    print  CC=0  out:0
  src.redup.analysis_logic  [2 funcs]
    _build_scan_config  CC=3  out:6
    _parse_extensions  CC=4  out:3
  src.redup.cli_app.compare_command  [15 funcs]
    _build_json_report  CC=1  out:6
    _build_recommendation_dict  CC=2  out:2
    _compact_community  CC=5  out:6
    _deduplicate_matches  CC=6  out:6
    _detect_communities  CC=4  out:2
    _export_json  CC=2  out:3
    _filter_significant_communities  CC=4  out:1
    _generate_llm_plan  CC=5  out:8
    _make_relative_path  CC=3  out:2
    _parse_extensions  CC=3  out:2
  src.redup.cli_app.config_builder  [2 funcs]
    build_config  CC=1  out:2
    build_config_with_file_support  CC=7  out:4
  src.redup.cli_app.fuzzy_similarity  [8 funcs]
    _analyze_blocks_with_detectors  CC=3  out:12
    _analyze_html_css_blocks  CC=1  out:2
    _analyze_other_language_blocks  CC=1  out:2
    _apply_fuzzy_similarity  CC=3  out:9
    _extract_all_blocks  CC=3  out:2
    _report_fuzzy_results  CC=5  out:12
    _separate_blocks_by_type  CC=5  out:2
    _validate_fuzzy_input  CC=4  out:3
  src.redup.cli_app.main  [4 funcs]
    check  CC=1  out:10
    config  CC=1  out:4
    diff  CC=1  out:4
    info  CC=1  out:2
  src.redup.cli_app.output_writer  [2 funcs]
    write_output  CC=3  out:5
    write_results  CC=12  out:25
  src.redup.cli_app.scan_commands  [4 funcs]
    check_command  CC=4  out:19
    config_command  CC=5  out:23
    diff_command  CC=2  out:5
    info_command  CC=3  out:9
  src.redup.cli_app.scan_helpers  [2 funcs]
    apply_fuzzy_similarity  CC=1  out:1
    print_scan_header  CC=1  out:6
  src.redup.cli_app.tasks_command  [1 funcs]
    tasks  CC=14  out:35
  src.redup.config  [2 funcs]
    set  CC=2  out:3
    get_default_filename  CC=3  out:1
  src.redup.core.cache  [2 funcs]
    build_hash_index_with_cache  CC=4  out:6
    hash_block_with_cache  CC=4  out:5
  src.redup.core.community  [1 funcs]
    detect_communities  CC=11  out:20
  src.redup.core.comparator  [8 funcs]
    _create_cross_project_match  CC=3  out:1
    _find_hash_matches  CC=6  out:7
    _find_lsh_matches  CC=8  out:5
    _find_semantic_matches  CC=8  out:7
    _is_cross_project_match  CC=4  out:0
    _normalize_match_order  CC=2  out:0
    _scan_project_blocks  CC=5  out:3
    compare_projects  CC=8  out:13
  src.redup.core.config  [6 funcs]
    _get_config_from_pyproject  CC=1  out:4
    _get_config_from_redup_toml  CC=1  out:2
    _load_toml_file  CC=4  out:3
    config_to_scan_config  CC=4  out:18
    create_sample_redup_toml  CC=1  out:0
    load_config  CC=5  out:8
  src.redup.core.decision  [1 funcs]
    recommend  CC=6  out:6
  src.redup.core.differ  [9 funcs]
    _format_assessment  CC=3  out:0
    _format_group_details  CC=3  out:2
    _format_group_header  CC=1  out:0
    _format_groups_section  CC=3  out:5
    _group_by_id  CC=2  out:0
    _groups_match  CC=7  out:5
    _load_duplication_map  CC=5  out:21
    compare_scans  CC=1  out:10
    format_diff_result  CC=1  out:9
  src.redup.core.fuzzy_similarity  [2 funcs]
    _compute_attribute_similarity  CC=9  out:11
    _extract_attributes  CC=4  out:11
  src.redup.core.hasher  [13 funcs]
    _ast_to_normalized_string  CC=12  out:18
    _blocks_from_different_locations  CC=2  out:1
    _fast_hash  CC=2  out:4
    _find_duplicates  CC=4  out:3
    _hash_text  CC=1  out:3
    _hashed_block  CC=1  out:3
    _normalize_ast_text  CC=5  out:11
    _normalize_text  CC=6  out:11
    build_hash_index  CC=3  out:4
    find_exact_duplicates  CC=1  out:1
  src.redup.core.lazy_grouper  [4 funcs]
    _create_duplicate_group  CC=4  out:2
    find_all_duplicates_lazy  CC=3  out:2
    find_exact_duplicates_lazy  CC=5  out:4
    find_structural_duplicates_lazy  CC=5  out:4
  src.redup.core.lsh_matcher  [9 funcs]
    _find_near_duplicates_simple  CC=4  out:6
    add  CC=4  out:8
    find_all_near_duplicates  CC=8  out:7
    find_near_duplicates  CC=10  out:9
    _create_minhash  CC=3  out:5
    _create_simple_minhash  CC=1  out:2
    _text_to_minhash_features  CC=5  out:14
    build_lsh_index  CC=3  out:2
    find_near_duplicates  CC=2  out:2
  src.redup.core.matcher  [5 funcs]
    _compare_against_reference  CC=7  out:5
    fuzzy_similarity  CC=2  out:4
    match_candidates  CC=2  out:1
    refine_structural_matches  CC=1  out:1
    sequence_similarity  CC=3  out:4
  src.redup.core.pipeline  [3 funcs]
    analyze  CC=2  out:8
    analyze_optimized  CC=14  out:29
    analyze_parallel  CC=3  out:19
  src.redup.core.pipeline.duplicate_finder  [5 funcs]
    find_duplicates_phase_lazy  CC=6  out:17
    find_duplicates_phase_optimized  CC=1  out:9
    find_exact_groups  CC=6  out:6
    find_near_duplicate_groups  CC=11  out:13
    find_structural_groups  CC=9  out:12
  src.redup.core.pipeline.groups  [3 funcs]
    blocks_to_group  CC=5  out:7
    deduplicate_groups  CC=6  out:5
    match_results_to_blocks  CC=4  out:3
  src.redup.core.pipeline.phases  [4 funcs]
    ensure_config  CC=2  out:1
    process_blocks  CC=6  out:3
    scan_phase  CC=2  out:1
    scan_phase_parallel  CC=2  out:2
  src.redup.core.planner  [5 funcs]
    _assess_risk  CC=7  out:3
    _choose_action  CC=7  out:2
    _common_prefix  CC=3  out:2
    _suggest_module_name  CC=6  out:1
    generate_suggestions  CC=6  out:9
  src.redup.core.python_parser  [6 funcs]
    _build_parent_map  CC=5  out:5
    _extract_decorators  CC=5  out:5
    _extract_function_info  CC=4  out:9
    _parse_with_ast  CC=4  out:7
    _parse_with_libcst  CC=4  out:15
    parse_python_functions  CC=3  out:2
  src.redup.core.refactor_advisor  [13 funcs]
    _build_match_list  CC=2  out:3
    _build_prompt  CC=2  out:15
    _format_communities  CC=6  out:10
    _format_matches_section  CC=2  out:3
    _get_model  CC=2  out:1
    _get_prompt_instructions  CC=1  out:0
    _load_env  CC=5  out:5
    _normalize_match  CC=7  out:11
    _parse_llm_response  CC=9  out:21
    _resolve_stats  CC=3  out:5
  src.redup.core.scanner  [14 funcs]
    _extract_blocks_for_file  CC=4  out:4
    _extract_function_blocks_python  CC=10  out:13
    _extract_sliding_blocks  CC=6  out:9
    _get_source_for_file  CC=2  out:2
    _init_file_loading  CC=3  out:2
    _init_strategy  CC=5  out:2
    _normalize_scan_config  CC=2  out:4
    _process_single_file  CC=2  out:6
    _read_source_text  CC=6  out:4
    scan_project  CC=5  out:20
  src.redup.core.scanner_cache  [4 funcs]
    _matches_any_exclude  CC=3  out:3
    _matches_any_include  CC=3  out:3
    _matches_pattern  CC=4  out:4
    _should_exclude  CC=3  out:4
  src.redup.core.scanner_filters  [3 funcs]
    _collect_files  CC=11  out:12
    _is_test_file  CC=8  out:5
    _project_relative_path  CC=2  out:1
  src.redup.core.scanner_utils  [7 funcs]
    _load_all_files  CC=2  out:2
    _load_files_simple  CC=3  out:2
    _load_files_with_progress  CC=3  out:10
    _preload_files  CC=4  out:9
    _print_load_result  CC=1  out:2
    _read_file_safe  CC=3  out:3
    _read_file_with_mmap  CC=1  out:5
  src.redup.core.semantic  [1 funcs]
    find_semantic_duplicates  CC=9  out:16
  src.redup.core.ts_extractor.dispatcher  [1 funcs]
    initialize_language_dispatcher  CC=2  out:31
  src.redup.core.ts_extractor.extractors.base  [2 funcs]
    create_code_block  CC=1  out:2
    get_node_text  CC=3  out:2
  src.redup.core.ts_extractor.extractors.c_family  [1 funcs]
    extract_functions_c_cpp  CC=1  out:8
  src.redup.core.ts_extractor.extractors.dotnet  [2 funcs]
    _extract_class_name  CC=5  out:2
    extract_functions_c_sharp  CC=1  out:11
  src.redup.core.ts_extractor.extractors.markup  [1 funcs]
    extract_blocks_html_xml  CC=1  out:5
  src.redup.core.ts_extractor.extractors.php  [2 funcs]
    _extract_class_name  CC=5  out:2
    extract_functions_php  CC=1  out:9
  src.redup.core.ts_extractor.extractors.query  [1 funcs]
    extract_blocks_sql  CC=1  out:5
  src.redup.core.ts_extractor.extractors.ruby  [1 funcs]
    extract_functions_ruby  CC=1  out:10
  src.redup.core.ts_extractor.extractors.shell  [1 funcs]
    extract_functions_bash  CC=1  out:6
  src.redup.core.ts_extractor.extractors.stylesheet  [1 funcs]
    extract_blocks_css  CC=1  out:5
  src.redup.core.ts_extractor.extractors.web  [4 funcs]
    _extract_arrow_function  CC=2  out:1
    _extract_function_declaration  CC=2  out:3
    _extract_method_definition  CC=2  out:3
    extract_functions_javascript  CC=1  out:8
  src.redup.core.ts_extractor.main  [5 funcs]
    _get_dispatcher  CC=2  out:1
    _get_tree_sitter_language  CC=1  out:1
    extract_functions_treesitter  CC=8  out:10
    get_supported_languages  CC=4  out:3
    is_language_supported  CC=5  out:4
  src.redup.core.universal_fuzzy  [2 funcs]
    _compute_metadata_similarity  CC=9  out:11
    _compute_pattern_similarity  CC=6  out:4
  src.redup.core.utils.diff_helpers  [6 funcs]
    _ensure_matches  CC=2  out:4
    _find_best_match  CC=5  out:3
    _match_exact_ids  CC=4  out:7
    _match_score  CC=6  out:8
    _group_files  CC=2  out:0
    _groups_match  CC=6  out:7
  src.redup.core.utils.duplicate_finders  [1 funcs]
    create_duplicate_finder  CC=3  out:2
  src.redup.core.utils.hash_utils  [1 funcs]
    create_hash_function  CC=3  out:1
  src.redup.mcp.handlers  [11 funcs]
    _build_scan_config  CC=12  out:24
    _check_thresholds  CC=3  out:7
    _estimate_code2llm_counts  CC=5  out:6
    _format_analysis_result  CC=7  out:15
    _get_optional_deps  CC=3  out:2
    _run_analysis  CC=7  out:17
    handle_analyze_project  CC=3  out:12
    handle_check_project  CC=3  out:14
    handle_compare_scans  CC=1  out:7
    handle_project_info  CC=1  out:7
  src.redup.mcp.server  [5 funcs]
    handle_initialize  CC=1  out:0
    handle_request  CC=5  out:6
    handle_tools_call  CC=4  out:2
    handle_tools_list  CC=2  out:1
    run_server  CC=5  out:14
  src.redup.mcp.utils  [3 funcs]
    json_safe  CC=6  out:8
    parse_extensions  CC=8  out:8
    resolve_path  CC=3  out:8
  src.redup.reporters.code2llm_reporter  [6 funcs]
    _calculate_avg_cc  CC=1  out:0
    _count_critical_functions  CC=1  out:0
    _get_layers  CC=1  out:3
    export_code2llm  CC=1  out:6
    to_code2llm_context  CC=11  out:36
    to_code2llm_toon  CC=5  out:17
  src.redup.reporters.enhanced_reporter  [1 funcs]
    _get_language_metrics  CC=7  out:9
  src.redup.reporters.json_reporter  [3 funcs]
    _group_to_dict  CC=5  out:4
    _suggestion_to_dict  CC=1  out:0
    to_json  CC=3  out:5
  src.redup.reporters.markdown_reporter  [1 funcs]
    to_markdown  CC=12  out:54
  src.redup.reporters.toon_reporter  [12 funcs]
    _calculate_group_effort  CC=10  out:2
    _format_estimate_lines  CC=4  out:6
    _render_dependency_risk  CC=13  out:14
    _render_duplicates  CC=8  out:6
    _render_effort_estimate  CC=5  out:4
    _render_header  CC=1  out:2
    _render_hotspots  CC=6  out:9
    _render_quick_wins  CC=9  out:12
    _render_refactor  CC=4  out:10
    _render_summary  CC=1  out:0
  src.redup.reporters.yaml_reporter  [1 funcs]
    to_yaml  CC=4  out:6

EDGES:
  benchmark.benchmark_sequential_vs_parallel → scripts.jscpd-check.print
  benchmark.benchmark_sequential_vs_parallel → src.redup.core.pipeline.analyze
  benchmark.benchmark_feature_performance → scripts.jscpd-check.print
  benchmark.benchmark_feature_performance → src.redup.core.pipeline.analyze_parallel
  examples.01_basic_usage.main → src.redup.core.pipeline.analyze
  examples.01_basic_usage.main → scripts.jscpd-check.print
  benchmarks.bench_libraries.benchmark → benchmarks.bench_libraries.generate_test_project
  benchmarks.bench_libraries.benchmark → src.redup.core.pipeline.analyze
  benchmarks.bench_libraries.benchmark → scripts.jscpd-check.print
  benchmarks.bench_libraries.benchmark_hash_performance → scripts.jscpd-check.print
  benchmarks.bench_libraries.benchmark_fuzzy_performance → scripts.jscpd-check.print
  src.redup.analysis_logic._build_scan_config → src.redup.core.config.config_to_scan_config
  src.redup.analysis_logic._build_scan_config → src.redup.analysis_logic._parse_extensions
  src.redup.analysis_logic._build_scan_config → src.redup.core.config.load_config
  src.redup.core.config._get_config_from_pyproject → src.redup.core.config._load_toml_file
  src.redup.core.config._get_config_from_redup_toml → src.redup.core.config._load_toml_file
  src.redup.core.config.load_config → src.redup.core.config._get_config_from_redup_toml
  src.redup.core.config.load_config → src.redup.core.config._get_config_from_pyproject
  src.redup.core.refactor_advisor._build_match_list → src.redup.core.refactor_advisor._normalize_match
  src.redup.core.refactor_advisor._build_prompt → src.redup.core.refactor_advisor._resolve_stats
  src.redup.core.refactor_advisor._build_prompt → src.redup.core.refactor_advisor._build_match_list
  src.redup.core.refactor_advisor._build_prompt → src.redup.core.refactor_advisor._format_matches_section
  src.redup.core.refactor_advisor._build_prompt → src.redup.core.refactor_advisor._format_communities
  src.redup.core.refactor_advisor._build_prompt → src.redup.core.refactor_advisor._get_prompt_instructions
  src.redup.core.refactor_advisor.generate_refactor_plan → src.redup.core.refactor_advisor._load_env
  src.redup.core.refactor_advisor.generate_refactor_plan → src.redup.core.refactor_advisor._get_model
  src.redup.core.refactor_advisor.generate_refactor_plan → src.redup.core.refactor_advisor._build_prompt
  src.redup.core.refactor_advisor.generate_refactor_plan → src.redup.core.refactor_advisor._parse_llm_response
  src.redup.core.universal_fuzzy.UniversalFuzzyDetector._compute_pattern_similarity → src.redup.config.RedupConfig.set
  src.redup.core.universal_fuzzy.UniversalFuzzyDetector._compute_metadata_similarity → src.redup.config.RedupConfig.set
  src.redup.core.scanner_cache._matches_any_exclude → src.redup.core.scanner_cache._matches_pattern
  src.redup.core.scanner_cache._matches_any_include → src.redup.core.scanner_cache._matches_pattern
  src.redup.core.scanner_cache._should_exclude → src.redup.core.scanner_cache._matches_any_exclude
  src.redup.core.scanner_cache._should_exclude → src.redup.core.scanner_cache._matches_any_include
  src.redup.core.matcher.sequence_similarity → src.redup.core.hasher._normalize_text
  src.redup.core.matcher.fuzzy_similarity → src.redup.core.hasher._normalize_text
  src.redup.core.matcher.fuzzy_similarity → src.redup.core.matcher.sequence_similarity
  src.redup.core.matcher.match_candidates → src.redup.core.matcher._compare_against_reference
  src.redup.core.matcher.refine_structural_matches → src.redup.core.matcher._compare_against_reference
  src.redup.core.lazy_grouper.find_exact_duplicates_lazy → src.redup.core.lazy_grouper._create_duplicate_group
  src.redup.core.lazy_grouper.find_exact_duplicates_lazy → src.redup.core.hasher._blocks_from_different_locations
  src.redup.core.lazy_grouper.find_structural_duplicates_lazy → src.redup.core.lazy_grouper._create_duplicate_group
  src.redup.core.lazy_grouper.find_structural_duplicates_lazy → src.redup.core.hasher._blocks_from_different_locations
  src.redup.core.lazy_grouper.find_all_duplicates_lazy → src.redup.core.lazy_grouper.find_exact_duplicates_lazy
  src.redup.core.lazy_grouper.find_all_duplicates_lazy → src.redup.core.lazy_grouper.find_structural_duplicates_lazy
  src.redup.core.hasher._normalize_ast_text → src.redup.core.hasher._ast_to_normalized_string
  src.redup.core.hasher._normalize_ast_text → src.redup.core.hasher._normalize_text
  src.redup.core.hasher._hash_text → src.redup.core.hasher._fast_hash
  src.redup.core.hasher.hash_block → src.redup.core.hasher._hash_text
  src.redup.core.hasher.hash_block_structural → src.redup.core.hasher._hash_text
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

### Integration (1)

**`Auto-generated from Python Tests`**

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/redup
# generated in 0.24s
# nodes: 253 | edges: 305 | modules: 62
# CC̄=3.7

HUBS[20]:
  scripts.jscpd-check.print
    CC=0  in:66  out:0  total:66
  src.redup.reporters.markdown_reporter.to_markdown
    CC=12  in:3  out:54  total:57
  src.redup.reporters.code2llm_reporter.to_code2llm_context
    CC=11  in:3  out:36  total:39
  src.redup.cli_app.tasks_command.tasks
    CC=14  in:0  out:35  total:35
  src.redup.core.ts_extractor.dispatcher.initialize_language_dispatcher
    CC=2  in:1  out:31  total:32
  src.redup.core.scanner.scan_project
    CC=5  in:11  out:20  total:31
  src.redup.core.pipeline.analyze_optimized
    CC=14  in:2  out:29  total:31
  src.redup.config.RedupConfig.set
    CC=2  in:25  out:3  total:28
  benchmarks.bench_libraries.benchmark
    CC=10  in:0  out:27  total:27
  src.redup.cli_app.output_writer.write_results
    CC=12  in:1  out:25  total:26
  benchmark.benchmark_sequential_vs_parallel
    CC=3  in:0  out:26  total:26
  src.redup.mcp.handlers._build_scan_config
    CC=12  in:1  out:24  total:25
  src.redup.cli_app.scan_commands.config_command
    CC=5  in:1  out:23  total:24
  examples.01_basic_usage.main
    CC=5  in:0  out:23  total:23
  src.redup.core.differ._load_duplication_map
    CC=5  in:2  out:21  total:23
  src.redup.core.pipeline.analyze_parallel
    CC=3  in:4  out:19  total:23
  src.redup.core.config.config_to_scan_config
    CC=4  in:5  out:18  total:23
  src.redup.core.refactor_advisor._parse_llm_response
    CC=9  in:1  out:21  total:22
  src.redup.cli_app.compare_command._print_summary_table
    CC=1  in:1  out:20  total:21
  src.redup.core.community.detect_communities
    CC=11  in:1  out:20  total:21

MODULES:
  benchmark  [2 funcs]
    benchmark_feature_performance  CC=3  out:15
    benchmark_sequential_vs_parallel  CC=3  out:26
  benchmarks.bench_libraries  [4 funcs]
    benchmark  CC=10  out:27
    benchmark_fuzzy_performance  CC=4  out:12
    benchmark_hash_performance  CC=4  out:13
    generate_test_project  CC=3  out:5
  examples.01_basic_usage  [1 funcs]
    main  CC=5  out:23
  scripts.jscpd-check  [1 funcs]
    print  CC=0  out:0
  src.redup.analysis_logic  [2 funcs]
    _build_scan_config  CC=3  out:6
    _parse_extensions  CC=4  out:3
  src.redup.cli_app.compare_command  [15 funcs]
    _build_json_report  CC=1  out:6
    _build_recommendation_dict  CC=2  out:2
    _compact_community  CC=5  out:6
    _deduplicate_matches  CC=6  out:6
    _detect_communities  CC=4  out:2
    _export_json  CC=2  out:3
    _filter_significant_communities  CC=4  out:1
    _generate_llm_plan  CC=5  out:8
    _make_relative_path  CC=3  out:2
    _parse_extensions  CC=3  out:2
  src.redup.cli_app.config_builder  [2 funcs]
    build_config  CC=1  out:2
    build_config_with_file_support  CC=7  out:4
  src.redup.cli_app.fuzzy_similarity  [8 funcs]
    _analyze_blocks_with_detectors  CC=3  out:12
    _analyze_html_css_blocks  CC=1  out:2
    _analyze_other_language_blocks  CC=1  out:2
    _apply_fuzzy_similarity  CC=3  out:9
    _extract_all_blocks  CC=3  out:2
    _report_fuzzy_results  CC=5  out:12
    _separate_blocks_by_type  CC=5  out:2
    _validate_fuzzy_input  CC=4  out:3
  src.redup.cli_app.main  [4 funcs]
    check  CC=1  out:10
    config  CC=1  out:4
    diff  CC=1  out:4
    info  CC=1  out:2
  src.redup.cli_app.output_writer  [2 funcs]
    write_output  CC=3  out:5
    write_results  CC=12  out:25
  src.redup.cli_app.scan_commands  [4 funcs]
    check_command  CC=4  out:19
    config_command  CC=5  out:23
    diff_command  CC=2  out:5
    info_command  CC=3  out:9
  src.redup.cli_app.scan_helpers  [2 funcs]
    apply_fuzzy_similarity  CC=1  out:1
    print_scan_header  CC=1  out:6
  src.redup.cli_app.tasks_command  [1 funcs]
    tasks  CC=14  out:35
  src.redup.config  [2 funcs]
    set  CC=2  out:3
    get_default_filename  CC=3  out:1
  src.redup.core.cache  [2 funcs]
    build_hash_index_with_cache  CC=4  out:6
    hash_block_with_cache  CC=4  out:5
  src.redup.core.community  [1 funcs]
    detect_communities  CC=11  out:20
  src.redup.core.comparator  [8 funcs]
    _create_cross_project_match  CC=3  out:1
    _find_hash_matches  CC=6  out:7
    _find_lsh_matches  CC=8  out:5
    _find_semantic_matches  CC=8  out:7
    _is_cross_project_match  CC=4  out:0
    _normalize_match_order  CC=2  out:0
    _scan_project_blocks  CC=5  out:3
    compare_projects  CC=8  out:13
  src.redup.core.config  [6 funcs]
    _get_config_from_pyproject  CC=1  out:4
    _get_config_from_redup_toml  CC=1  out:2
    _load_toml_file  CC=4  out:3
    config_to_scan_config  CC=4  out:18
    create_sample_redup_toml  CC=1  out:0
    load_config  CC=5  out:8
  src.redup.core.decision  [1 funcs]
    recommend  CC=6  out:6
  src.redup.core.differ  [9 funcs]
    _format_assessment  CC=3  out:0
    _format_group_details  CC=3  out:2
    _format_group_header  CC=1  out:0
    _format_groups_section  CC=3  out:5
    _group_by_id  CC=2  out:0
    _groups_match  CC=7  out:5
    _load_duplication_map  CC=5  out:21
    compare_scans  CC=1  out:10
    format_diff_result  CC=1  out:9
  src.redup.core.fuzzy_similarity  [2 funcs]
    _compute_attribute_similarity  CC=9  out:11
    _extract_attributes  CC=4  out:11
  src.redup.core.hasher  [13 funcs]
    _ast_to_normalized_string  CC=12  out:18
    _blocks_from_different_locations  CC=2  out:1
    _fast_hash  CC=2  out:4
    _find_duplicates  CC=4  out:3
    _hash_text  CC=1  out:3
    _hashed_block  CC=1  out:3
    _normalize_ast_text  CC=5  out:11
    _normalize_text  CC=6  out:11
    build_hash_index  CC=3  out:4
    find_exact_duplicates  CC=1  out:1
  src.redup.core.lazy_grouper  [4 funcs]
    _create_duplicate_group  CC=4  out:2
    find_all_duplicates_lazy  CC=3  out:2
    find_exact_duplicates_lazy  CC=5  out:4
    find_structural_duplicates_lazy  CC=5  out:4
  src.redup.core.lsh_matcher  [9 funcs]
    _find_near_duplicates_simple  CC=4  out:6
    add  CC=4  out:8
    find_all_near_duplicates  CC=8  out:7
    find_near_duplicates  CC=10  out:9
    _create_minhash  CC=3  out:5
    _create_simple_minhash  CC=1  out:2
    _text_to_minhash_features  CC=5  out:14
    build_lsh_index  CC=3  out:2
    find_near_duplicates  CC=2  out:2
  src.redup.core.matcher  [5 funcs]
    _compare_against_reference  CC=7  out:5
    fuzzy_similarity  CC=2  out:4
    match_candidates  CC=2  out:1
    refine_structural_matches  CC=1  out:1
    sequence_similarity  CC=3  out:4
  src.redup.core.pipeline  [3 funcs]
    analyze  CC=2  out:8
    analyze_optimized  CC=14  out:29
    analyze_parallel  CC=3  out:19
  src.redup.core.pipeline.duplicate_finder  [5 funcs]
    find_duplicates_phase_lazy  CC=6  out:17
    find_duplicates_phase_optimized  CC=1  out:9
    find_exact_groups  CC=6  out:6
    find_near_duplicate_groups  CC=11  out:13
    find_structural_groups  CC=9  out:12
  src.redup.core.pipeline.groups  [3 funcs]
    blocks_to_group  CC=5  out:7
    deduplicate_groups  CC=6  out:5
    match_results_to_blocks  CC=4  out:3
  src.redup.core.pipeline.phases  [4 funcs]
    ensure_config  CC=2  out:1
    process_blocks  CC=6  out:3
    scan_phase  CC=2  out:1
    scan_phase_parallel  CC=2  out:2
  src.redup.core.planner  [5 funcs]
    _assess_risk  CC=7  out:3
    _choose_action  CC=7  out:2
    _common_prefix  CC=3  out:2
    _suggest_module_name  CC=6  out:1
    generate_suggestions  CC=6  out:9
  src.redup.core.python_parser  [6 funcs]
    _build_parent_map  CC=5  out:5
    _extract_decorators  CC=5  out:5
    _extract_function_info  CC=4  out:9
    _parse_with_ast  CC=4  out:7
    _parse_with_libcst  CC=4  out:15
    parse_python_functions  CC=3  out:2
  src.redup.core.refactor_advisor  [13 funcs]
    _build_match_list  CC=2  out:3
    _build_prompt  CC=2  out:15
    _format_communities  CC=6  out:10
    _format_matches_section  CC=2  out:3
    _get_model  CC=2  out:1
    _get_prompt_instructions  CC=1  out:0
    _load_env  CC=5  out:5
    _normalize_match  CC=7  out:11
    _parse_llm_response  CC=9  out:21
    _resolve_stats  CC=3  out:5
  src.redup.core.scanner  [14 funcs]
    _extract_blocks_for_file  CC=4  out:4
    _extract_function_blocks_python  CC=10  out:13
    _extract_sliding_blocks  CC=6  out:9
    _get_source_for_file  CC=2  out:2
    _init_file_loading  CC=3  out:2
    _init_strategy  CC=5  out:2
    _normalize_scan_config  CC=2  out:4
    _process_single_file  CC=2  out:6
    _read_source_text  CC=6  out:4
    scan_project  CC=5  out:20
  src.redup.core.scanner_cache  [4 funcs]
    _matches_any_exclude  CC=3  out:3
    _matches_any_include  CC=3  out:3
    _matches_pattern  CC=4  out:4
    _should_exclude  CC=3  out:4
  src.redup.core.scanner_filters  [3 funcs]
    _collect_files  CC=11  out:12
    _is_test_file  CC=8  out:5
    _project_relative_path  CC=2  out:1
  src.redup.core.scanner_utils  [7 funcs]
    _load_all_files  CC=2  out:2
    _load_files_simple  CC=3  out:2
    _load_files_with_progress  CC=3  out:10
    _preload_files  CC=4  out:9
    _print_load_result  CC=1  out:2
    _read_file_safe  CC=3  out:3
    _read_file_with_mmap  CC=1  out:5
  src.redup.core.semantic  [1 funcs]
    find_semantic_duplicates  CC=9  out:16
  src.redup.core.ts_extractor.dispatcher  [1 funcs]
    initialize_language_dispatcher  CC=2  out:31
  src.redup.core.ts_extractor.extractors.base  [2 funcs]
    create_code_block  CC=1  out:2
    get_node_text  CC=3  out:2
  src.redup.core.ts_extractor.extractors.c_family  [1 funcs]
    extract_functions_c_cpp  CC=1  out:8
  src.redup.core.ts_extractor.extractors.dotnet  [2 funcs]
    _extract_class_name  CC=5  out:2
    extract_functions_c_sharp  CC=1  out:11
  src.redup.core.ts_extractor.extractors.markup  [1 funcs]
    extract_blocks_html_xml  CC=1  out:5
  src.redup.core.ts_extractor.extractors.php  [2 funcs]
    _extract_class_name  CC=5  out:2
    extract_functions_php  CC=1  out:9
  src.redup.core.ts_extractor.extractors.query  [1 funcs]
    extract_blocks_sql  CC=1  out:5
  src.redup.core.ts_extractor.extractors.ruby  [1 funcs]
    extract_functions_ruby  CC=1  out:10
  src.redup.core.ts_extractor.extractors.shell  [1 funcs]
    extract_functions_bash  CC=1  out:6
  src.redup.core.ts_extractor.extractors.stylesheet  [1 funcs]
    extract_blocks_css  CC=1  out:5
  src.redup.core.ts_extractor.extractors.web  [4 funcs]
    _extract_arrow_function  CC=2  out:1
    _extract_function_declaration  CC=2  out:3
    _extract_method_definition  CC=2  out:3
    extract_functions_javascript  CC=1  out:8
  src.redup.core.ts_extractor.main  [5 funcs]
    _get_dispatcher  CC=2  out:1
    _get_tree_sitter_language  CC=1  out:1
    extract_functions_treesitter  CC=8  out:10
    get_supported_languages  CC=4  out:3
    is_language_supported  CC=5  out:4
  src.redup.core.universal_fuzzy  [2 funcs]
    _compute_metadata_similarity  CC=9  out:11
    _compute_pattern_similarity  CC=6  out:4
  src.redup.core.utils.diff_helpers  [6 funcs]
    _ensure_matches  CC=2  out:4
    _find_best_match  CC=5  out:3
    _match_exact_ids  CC=4  out:7
    _match_score  CC=6  out:8
    _group_files  CC=2  out:0
    _groups_match  CC=6  out:7
  src.redup.core.utils.duplicate_finders  [1 funcs]
    create_duplicate_finder  CC=3  out:2
  src.redup.core.utils.hash_utils  [1 funcs]
    create_hash_function  CC=3  out:1
  src.redup.mcp.handlers  [11 funcs]
    _build_scan_config  CC=12  out:24
    _check_thresholds  CC=3  out:7
    _estimate_code2llm_counts  CC=5  out:6
    _format_analysis_result  CC=7  out:15
    _get_optional_deps  CC=3  out:2
    _run_analysis  CC=7  out:17
    handle_analyze_project  CC=3  out:12
    handle_check_project  CC=3  out:14
    handle_compare_scans  CC=1  out:7
    handle_project_info  CC=1  out:7
  src.redup.mcp.server  [5 funcs]
    handle_initialize  CC=1  out:0
    handle_request  CC=5  out:6
    handle_tools_call  CC=4  out:2
    handle_tools_list  CC=2  out:1
    run_server  CC=5  out:14
  src.redup.mcp.utils  [3 funcs]
    json_safe  CC=6  out:8
    parse_extensions  CC=8  out:8
    resolve_path  CC=3  out:8
  src.redup.reporters.code2llm_reporter  [6 funcs]
    _calculate_avg_cc  CC=1  out:0
    _count_critical_functions  CC=1  out:0
    _get_layers  CC=1  out:3
    export_code2llm  CC=1  out:6
    to_code2llm_context  CC=11  out:36
    to_code2llm_toon  CC=5  out:17
  src.redup.reporters.enhanced_reporter  [1 funcs]
    _get_language_metrics  CC=7  out:9
  src.redup.reporters.json_reporter  [3 funcs]
    _group_to_dict  CC=5  out:4
    _suggestion_to_dict  CC=1  out:0
    to_json  CC=3  out:5
  src.redup.reporters.markdown_reporter  [1 funcs]
    to_markdown  CC=12  out:54
  src.redup.reporters.toon_reporter  [12 funcs]
    _calculate_group_effort  CC=10  out:2
    _format_estimate_lines  CC=4  out:6
    _render_dependency_risk  CC=13  out:14
    _render_duplicates  CC=8  out:6
    _render_effort_estimate  CC=5  out:4
    _render_header  CC=1  out:2
    _render_hotspots  CC=6  out:9
    _render_quick_wins  CC=9  out:12
    _render_refactor  CC=4  out:10
    _render_summary  CC=1  out:0
  src.redup.reporters.yaml_reporter  [1 funcs]
    to_yaml  CC=4  out:6

EDGES:
  benchmark.benchmark_sequential_vs_parallel → scripts.jscpd-check.print
  benchmark.benchmark_sequential_vs_parallel → src.redup.core.pipeline.analyze
  benchmark.benchmark_feature_performance → scripts.jscpd-check.print
  benchmark.benchmark_feature_performance → src.redup.core.pipeline.analyze_parallel
  examples.01_basic_usage.main → src.redup.core.pipeline.analyze
  examples.01_basic_usage.main → scripts.jscpd-check.print
  benchmarks.bench_libraries.benchmark → benchmarks.bench_libraries.generate_test_project
  benchmarks.bench_libraries.benchmark → src.redup.core.pipeline.analyze
  benchmarks.bench_libraries.benchmark → scripts.jscpd-check.print
  benchmarks.bench_libraries.benchmark_hash_performance → scripts.jscpd-check.print
  benchmarks.bench_libraries.benchmark_fuzzy_performance → scripts.jscpd-check.print
  src.redup.analysis_logic._build_scan_config → src.redup.core.config.config_to_scan_config
  src.redup.analysis_logic._build_scan_config → src.redup.analysis_logic._parse_extensions
  src.redup.analysis_logic._build_scan_config → src.redup.core.config.load_config
  src.redup.core.config._get_config_from_pyproject → src.redup.core.config._load_toml_file
  src.redup.core.config._get_config_from_redup_toml → src.redup.core.config._load_toml_file
  src.redup.core.config.load_config → src.redup.core.config._get_config_from_redup_toml
  src.redup.core.config.load_config → src.redup.core.config._get_config_from_pyproject
  src.redup.core.refactor_advisor._build_match_list → src.redup.core.refactor_advisor._normalize_match
  src.redup.core.refactor_advisor._build_prompt → src.redup.core.refactor_advisor._resolve_stats
  src.redup.core.refactor_advisor._build_prompt → src.redup.core.refactor_advisor._build_match_list
  src.redup.core.refactor_advisor._build_prompt → src.redup.core.refactor_advisor._format_matches_section
  src.redup.core.refactor_advisor._build_prompt → src.redup.core.refactor_advisor._format_communities
  src.redup.core.refactor_advisor._build_prompt → src.redup.core.refactor_advisor._get_prompt_instructions
  src.redup.core.refactor_advisor.generate_refactor_plan → src.redup.core.refactor_advisor._load_env
  src.redup.core.refactor_advisor.generate_refactor_plan → src.redup.core.refactor_advisor._get_model
  src.redup.core.refactor_advisor.generate_refactor_plan → src.redup.core.refactor_advisor._build_prompt
  src.redup.core.refactor_advisor.generate_refactor_plan → src.redup.core.refactor_advisor._parse_llm_response
  src.redup.core.universal_fuzzy.UniversalFuzzyDetector._compute_pattern_similarity → src.redup.config.RedupConfig.set
  src.redup.core.universal_fuzzy.UniversalFuzzyDetector._compute_metadata_similarity → src.redup.config.RedupConfig.set
  src.redup.core.scanner_cache._matches_any_exclude → src.redup.core.scanner_cache._matches_pattern
  src.redup.core.scanner_cache._matches_any_include → src.redup.core.scanner_cache._matches_pattern
  src.redup.core.scanner_cache._should_exclude → src.redup.core.scanner_cache._matches_any_exclude
  src.redup.core.scanner_cache._should_exclude → src.redup.core.scanner_cache._matches_any_include
  src.redup.core.matcher.sequence_similarity → src.redup.core.hasher._normalize_text
  src.redup.core.matcher.fuzzy_similarity → src.redup.core.hasher._normalize_text
  src.redup.core.matcher.fuzzy_similarity → src.redup.core.matcher.sequence_similarity
  src.redup.core.matcher.match_candidates → src.redup.core.matcher._compare_against_reference
  src.redup.core.matcher.refine_structural_matches → src.redup.core.matcher._compare_against_reference
  src.redup.core.lazy_grouper.find_exact_duplicates_lazy → src.redup.core.lazy_grouper._create_duplicate_group
  src.redup.core.lazy_grouper.find_exact_duplicates_lazy → src.redup.core.hasher._blocks_from_different_locations
  src.redup.core.lazy_grouper.find_structural_duplicates_lazy → src.redup.core.lazy_grouper._create_duplicate_group
  src.redup.core.lazy_grouper.find_structural_duplicates_lazy → src.redup.core.hasher._blocks_from_different_locations
  src.redup.core.lazy_grouper.find_all_duplicates_lazy → src.redup.core.lazy_grouper.find_exact_duplicates_lazy
  src.redup.core.lazy_grouper.find_all_duplicates_lazy → src.redup.core.lazy_grouper.find_structural_duplicates_lazy
  src.redup.core.hasher._normalize_ast_text → src.redup.core.hasher._ast_to_normalized_string
  src.redup.core.hasher._normalize_ast_text → src.redup.core.hasher._normalize_text
  src.redup.core.hasher._hash_text → src.redup.core.hasher._fast_hash
  src.redup.core.hasher.hash_block → src.redup.core.hasher._hash_text
  src.redup.core.hasher.hash_block_structural → src.redup.core.hasher._hash_text
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 106f 16795L | python:87,json:6,shell:5,yaml:4,toml:2,yml:1,txt:1 | 2026-05-19
# generated in 0.04s
# CC̄=3.7 | critical:0/385 | dups:0 | cycles:3

HEALTH[0]: ok

REFACTOR[1]:
  1. break 3 circular dependencies

PIPELINES[166]:
  [1] Src [benchmark_sequential_vs_parallel]: benchmark_sequential_vs_parallel → print
      PURITY: 100% pure
  [2] Src [benchmark_feature_performance]: benchmark_feature_performance → print
      PURITY: 100% pure
  [3] Src [main]: main → analyze → ensure_config
      PURITY: 100% pure
  [4] Src [benchmark]: benchmark → generate_test_project
      PURITY: 100% pure
  [5] Src [benchmark_hash_performance]: benchmark_hash_performance → print
      PURITY: 100% pure

LAYERS:
  benchmarks/                     CC̄=5.2    ←in:0  →out:16  !! split
  │ bench_libraries            168L  0C    4m  CC=10     ←0
  │
  examples/                       CC̄=5.0    ←in:0  →out:18  !! split
  │ 01_basic_usage              60L  0C    1m  CC=5      ←0
  │
  src/                            CC̄=3.7    ←in:0  →out:0
  │ universal_fuzzy            471L  3C   16m  CC=11     ←0
  │ fuzzy_similarity           430L  4C   20m  CC=10     ←0
  │ refactor_advisor           363L  2C   13m  CC=9      ←1
  │ compare_command            355L  0C   16m  CC=6      ←1
  │ handlers                   346L  0C   12m  CC=12     ←0
  │ __init__                   313L  0C    3m  CC=14     ←6
  │ comparator                 312L  2C    8m  CC=8      ←1
  │ planfile_integration       311L  3C    8m  CC=12     ←0
  │ __init__                   309L  0C   14m  CC=10     ←3
  │ models                     294L  9C    1m  CC=1      ←0
  │ duplicate_finder           271L  0C    6m  CC=11     ←1
  │ toon_reporter              268L  0C   13m  CC=13     ←3
  │ main                       264L  0C    6m  CC=1      ←0
  │ enhanced_reporter          260L  1C   17m  CC=8      ←0
  │ cache                      259L  1C   10m  CC=5      ←1
  │ scan_commands              243L  0C    5m  CC=7      ←1
  │ lsh_matcher                232L  2C   12m  CC=10     ←1
  │ differ                     217L  1C    9m  CC=7      ←3
  │ diff_helpers               211L  3C   13m  CC=6      ←0
  │ code2llm_reporter          211L  0C    6m  CC=11     ←2
  │ hasher                     202L  2C   13m  CC=12     ←8
  │ python_parser              186L  1C    7m  CC=5      ←0
  │ tasks_command              186L  0C    2m  CC=14     ←0
  │ config                     182L  1C    7m  CC=9      ←14
  │ semantic                   182L  2C    5m  CC=9      ←0
  │ config                     172L  0C    6m  CC=5      ←5
  │ fuzzy_similarity           171L  0C    9m  CC=5      ←1
  │ lazy_grouper               160L  1C    7m  CC=7      ←1
  │ function_extractor         149L  1C    5m  CC=5      ←0
  │ schemas                    145L  0C    1m  CC=1      ←0
  │ config                     143L  1C    2m  CC=4      ←0
  │ server                     138L  0C    5m  CC=5      ←0
  │ community                  122L  1C    2m  CC=11     ←1
  │ main                       114L  0C    5m  CC=8      ←1
  │ matcher                    111L  1C    5m  CC=7      ←1
  │ planner                    110L  0C    5m  CC=7      ←1
  │ hash_cache                 102L  1C   10m  CC=3      ←0
  │ groups                      99L  0C    4m  CC=6      ←2
  │ scanner_utils               99L  0C    7m  CC=4      ←1
  │ markdown_reporter           96L  0C    1m  CC=12     ←2
  │ decision                    95L  2C    1m  CC=6      ←1
  │ scanner_cache               92L  1C    8m  CC=6      ←1
  │ mcp_server                  82L  0C    1m  CC=2      ←0
  │ dispatcher                  82L  0C    1m  CC=2      ←1
  │ output_writer               79L  0C    2m  CC=12     ←1
  │ base                        76L  0C    3m  CC=5      ←9
  │ language_dispatcher         76L  1C    5m  CC=4      ←0
  │ json_reporter               73L  0C    3m  CC=5      ←4
  │ web                         70L  0C    4m  CC=2      ←0
  │ scanner_filters             61L  0C    3m  CC=11     ←1
  │ dotnet                      55L  0C    2m  CC=5      ←0
  │ config_builder              53L  0C    2m  CC=7      ←1
  │ stylesheet                  51L  0C    1m  CC=1      ←0
  │ php                         50L  0C    2m  CC=5      ←0
  │ __init__                    49L  0C    0m  CC=0.0    ←0
  │ utils                       46L  0C    3m  CC=10     ←0
  │ ruby                        46L  0C    1m  CC=1      ←0
  │ query                       46L  0C    1m  CC=1      ←0
  │ phases                      46L  0C    4m  CC=6      ←1
  │ scanner_types               45L  3C    0m  CC=0.0    ←0
  │ duplicate_finders           43L  0C    1m  CC=3      ←0
  │ hash_utils                  42L  0C    1m  CC=3      ←0
  │ __init__                    42L  0C    0m  CC=0.0    ←0
  │ markup                      41L  0C    1m  CC=1      ←0
  │ scan_helpers                40L  0C    3m  CC=1      ←1
  │ c_family                    40L  0C    1m  CC=1      ←0
  │ yaml_reporter               34L  0C    1m  CC=4      ←2
  │ __init__                    32L  0C    0m  CC=0.0    ←0
  │ shell                       31L  0C    1m  CC=1      ←0
  │ utils                       28L  0C    3m  CC=8      ←1
  │ analysis_logic              27L  0C    2m  CC=4      ←0
  │ __init__                    23L  0C    0m  CC=0.0    ←0
  │ config_handler              20L  0C    0m  CC=0.0    ←0
  │ grouper                     15L  0C    0m  CC=0.0    ←0
  │ scanner_models              11L  0C    0m  CC=0.0    ←0
  │ scanner_loader               8L  0C    0m  CC=0.0    ←0
  │ pipeline_utils               7L  0C    0m  CC=0.0    ←0
  │ __main__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ sitecustomize                4L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=3.0    ←in:0  →out:0
  │ !! planfile.yaml             1670L  0C    0m  CC=0.0    ←0
  │ !! compare_report.json        792L  0C    0m  CC=0.0    ←0
  │ !! compare_report_test.json   687L  0C    0m  CC=0.0    ←0
  │ goal.yaml                  428L  0C    0m  CC=0.0    ←0
  │ Taskfile.yml               195L  0C    0m  CC=0.0    ←0
  │ pyproject.toml             162L  0C    0m  CC=0.0    ←0
  │ benchmark                  117L  0C    2m  CC=3      ←0
  │ prefact.yaml                82L  0C    0m  CC=0.0    ←0
  │ project.sh                  54L  0C    0m  CC=0.0    ←0
  │ redup.toml                  29L  0C    0m  CC=0.0    ←0
  │ .jscpd.json                 23L  0C    0m  CC=0.0    ←0
  │ pyqual.yaml                 18L  0C    0m  CC=0.0    ←0
  │ coverage.json                1L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │
  scripts/                        CC̄=0.0    ←in:66  →out:0
  │ jscpd-check.sh              69L  0C    1m  CC=0.0    ←7
  │ redup-run.sh                29L  0C    0m  CC=0.0    ←0
  │ jscpd-run.sh                27L  0C    0m  CC=0.0    ←0
  │
  redup_self_analysis/            CC̄=0.0    ←in:0  →out:0
  │ duplication.json            96L  0C    0m  CC=0.0    ←0
  │
  proxy_analysis/                 CC̄=0.0    ←in:0  →out:0
  │ !! duplication.json          1436L  0C    0m  CC=0.0    ←0
  │
  toon/                           CC̄=0.0    ←in:0  →out:0
  │ validation.txt              67L  0C    0m  CC=0.0    ←0
  │

COUPLING:
                 scripts   benchmark   src.redup    examples  benchmarks
     scripts          ──         ←23         ←13         ←15         ←15  hub
   benchmark          23          ──           4                          !! fan-out
   src.redup          13          ←4          ──          ←3          ←1  hub
    examples          15                       3          ──              !! fan-out
  benchmarks          15                       1                      ──  !! fan-out
  CYCLES: 3
  HUB: scripts/ (fan-in=66)
  HUB: src.redup/ (fan-in=8)
  SMELL: examples/ fan-out=18 → split needed
  SMELL: benchmark/ fan-out=27 → split needed
  SMELL: benchmarks/ fan-out=16 → split needed
  SMELL: src.redup/ fan-out=13 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 15 groups | 84f 10217L | 2026-04-16

SUMMARY:
  files_scanned: 84
  total_lines:   10217
  dup_groups:    15
  dup_fragments: 36
  saved_lines:   217
  scan_ms:       382

HOTSPOTS[7] (files with most duplication):
  redup/core/ts_extractor.py  dup=74L  groups=4  frags=11  (0.7%)
  redup/core/scanner_utils.py  dup=70L  groups=3  frags=3  (0.7%)
  redup/core/scanner_loader.py  dup=52L  groups=1  frags=1  (0.5%)
  redup/core/lazy_grouper.py  dup=43L  groups=1  frags=2  (0.4%)
  redup/core/scanner_filters.py  dup=38L  groups=3  frags=3  (0.4%)
  redup/core/ts_extractor/config.py  dup=36L  groups=1  frags=1  (0.4%)
  redup/core/scanner_cache.py  dup=20L  groups=1  frags=1  (0.2%)

DUPLICATES[15] (ranked by impact):
  [13e2207f2235bb42] ! EXAC  _preload_files  L=52 N=2 saved=52 sim=1.00
      redup/core/scanner_loader.py:9-60  (_preload_files)
      redup/core/scanner_utils.py:53-104  (_preload_files)
  [564d795253a4d77e] ! EXAC  __init__  L=36 N=2 saved=36 sim=1.00
      redup/core/ts_extractor/config.py:29-64  (__init__)
      redup/core/ts_extractor.py:183-218  (__init__)
  [f9993352566057e2]   STRU  find_exact_duplicates_lazy  L=26 N=2 saved=26 sim=1.00
      redup/core/lazy_grouper.py:12-37  (find_exact_duplicates_lazy)
      redup/core/lazy_grouper.py:40-56  (find_structural_duplicates_lazy)
  [aceed17801fd5eab]   STRU  _extract_functions_go  L=3 N=8 saved=21 sim=1.00
      redup/core/ts_extractor.py:317-319  (_extract_functions_go)
      redup/core/ts_extractor.py:322-324  (_extract_functions_rust)
      redup/core/ts_extractor.py:327-329  (_extract_functions_java)
      redup/core/ts_extractor.py:530-532  (_extract_functions_lua)
      redup/core/ts_extractor.py:595-597  (_extract_functions_scala)
      redup/core/ts_extractor.py:600-602  (_extract_functions_kotlin)
      redup/core/ts_extractor.py:605-607  (_extract_functions_swift)
      redup/core/ts_extractor.py:610-612  (_extract_functions_objc)
  [f48205bef036490c]   EXAC  _should_exclude  L=20 N=2 saved=20 sim=1.00
      redup/core/scanner_cache.py:54-73  (_should_exclude)
      redup/core/scanner_filters.py:12-31  (_should_exclude)
  [942f4d9ca24ea6c6]   EXAC  _is_test_file  L=12 N=2 saved=12 sim=1.00
      redup/core/scanner_filters.py:42-53  (_is_test_file)
      redup/core/scanner_utils.py:18-29  (_is_test_file)
  [a1f05b27526f854f]   STRU  get_supported_languages  L=11 N=2 saved=11 sim=1.00
      redup/core/ts_extractor/main.py:84-94  (get_supported_languages)
      redup/core/ts_extractor.py:761-771  (get_supported_languages)
  [4f911264caf89b59]   EXAC  _extract_class_name  L=9 N=2 saved=9 sim=1.00
      redup/core/ts_extractor/extractors/dotnet.py:11-19  (_extract_class_name)
      redup/core/ts_extractor/extractors/php.py:11-19  (_extract_class_name)
  [5c98c3b290cc964f]   EXAC  _project_relative_path  L=6 N=2 saved=6 sim=1.00
      redup/core/scanner_filters.py:34-39  (_project_relative_path)
      redup/core/scanner_utils.py:10-15  (_project_relative_path)
  [e3dc4781be464665]   STRU  _analyze_html_css_blocks  L=6 N=2 saved=6 sim=1.00
      redup/cli_app/fuzzy_similarity.py:99-104  (_analyze_html_css_blocks)
      redup/cli_app/fuzzy_similarity.py:107-112  (_analyze_other_language_blocks)
  [03ae9c9486552925]   STRU  _extract_function_declaration  L=5 N=2 saved=5 sim=1.00
      redup/core/ts_extractor/extractors/web.py:11-15  (_extract_function_declaration)
      redup/core/ts_extractor/extractors/web.py:18-22  (_extract_method_definition)
  [6ffbb36246294349]   EXAC  handle_interrupt  L=4 N=2 saved=4 sim=1.00
      redup/core/pipeline/__init__.py:123-126  (handle_interrupt)
      redup/core/pipeline/__init__.py:220-223  (handle_interrupt)
  [b7ae77230bef684c]   STRU  hash_block  L=3 N=2 saved=3 sim=1.00
      redup/core/hasher.py:114-116  (hash_block)
      redup/core/hasher.py:119-121  (hash_block_structural)
  [05dfc46abe0918b4]   STRU  find_exact_duplicates  L=3 N=2 saved=3 sim=1.00
      redup/core/hasher.py:179-181  (find_exact_duplicates)
      redup/core/hasher.py:184-186  (find_structural_duplicates)
  [010e49186ddfd823]   STRU  _get_tree_sitter_language  L=3 N=2 saved=3 sim=1.00
      redup/core/ts_extractor/main.py:17-19  (_get_tree_sitter_language)
      redup/core/ts_extractor.py:244-246  (_get_tree_sitter_language)

REFACTOR[15] (ranked by priority):
  [1] ◐ extract_module     → redup/core/utils/_preload_files.py
      WHY: 2 occurrences of 52-line block across 2 files — saves 52 lines
      FILES: redup/core/scanner_loader.py, redup/core/scanner_utils.py
  [2] ◐ extract_function   → redup/core/utils/__init__.py
      WHY: 2 occurrences of 36-line block across 2 files — saves 36 lines
      FILES: redup/core/ts_extractor.py, redup/core/ts_extractor/config.py
  [3] ○ extract_function   → redup/core/utils/find_exact_duplicates_lazy.py
      WHY: 2 occurrences of 26-line block across 1 files — saves 26 lines
      FILES: redup/core/lazy_grouper.py
  [4] ○ extract_function   → redup/core/utils/_extract_functions_go.py
      WHY: 8 occurrences of 3-line block across 1 files — saves 21 lines
      FILES: redup/core/ts_extractor.py
  [5] ○ extract_function   → redup/core/utils/_should_exclude.py
      WHY: 2 occurrences of 20-line block across 2 files — saves 20 lines
      FILES: redup/core/scanner_cache.py, redup/core/scanner_filters.py
  [6] ○ extract_function   → redup/core/utils/_is_test_file.py
      WHY: 2 occurrences of 12-line block across 2 files — saves 12 lines
      FILES: redup/core/scanner_filters.py, redup/core/scanner_utils.py
  [7] ○ extract_function   → redup/core/utils/get_supported_languages.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: redup/core/ts_extractor.py, redup/core/ts_extractor/main.py
  [8] ○ extract_function   → redup/core/ts_extractor/extractors/utils/_extract_class_name.py
      WHY: 2 occurrences of 9-line block across 2 files — saves 9 lines
      FILES: redup/core/ts_extractor/extractors/dotnet.py, redup/core/ts_extractor/extractors/php.py
  [9] ○ extract_function   → redup/core/utils/_project_relative_path.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: redup/core/scanner_filters.py, redup/core/scanner_utils.py
  [10] ○ extract_function   → redup/cli_app/utils/_analyze_html_css_blocks.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: redup/cli_app/fuzzy_similarity.py
  [11] ○ extract_function   → redup/core/ts_extractor/extractors/utils/_extract_function_declaration.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: redup/core/ts_extractor/extractors/web.py
  [12] ○ extract_function   → redup/core/pipeline/utils/handle_interrupt.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: redup/core/pipeline/__init__.py
  [13] ○ extract_function   → redup/core/utils/hash_block.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: redup/core/hasher.py
  [14] ○ extract_function   → redup/core/utils/find_exact_duplicates.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: redup/core/hasher.py
  [15] ○ extract_function   → redup/core/utils/_get_tree_sitter_language.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: redup/core/ts_extractor.py, redup/core/ts_extractor/main.py

QUICK_WINS[8] (low risk, high savings — do first):
  [3] extract_function   saved=26L  → redup/core/utils/find_exact_duplicates_lazy.py
      FILES: lazy_grouper.py
  [4] extract_function   saved=21L  → redup/core/utils/_extract_functions_go.py
      FILES: ts_extractor.py
  [5] extract_function   saved=20L  → redup/core/utils/_should_exclude.py
      FILES: scanner_cache.py, scanner_filters.py
  [6] extract_function   saved=12L  → redup/core/utils/_is_test_file.py
      FILES: scanner_filters.py, scanner_utils.py
  [7] extract_function   saved=11L  → redup/core/utils/get_supported_languages.py
      FILES: ts_extractor.py, main.py
  [8] extract_function   saved=9L  → redup/core/ts_extractor/extractors/utils/_extract_class_name.py
      FILES: dotnet.py, php.py
  [9] extract_function   saved=6L  → redup/core/utils/_project_relative_path.py
      FILES: scanner_filters.py, scanner_utils.py
  [10] extract_function   saved=6L  → redup/cli_app/utils/_analyze_html_css_blocks.py
      FILES: fuzzy_similarity.py

EFFORT_ESTIMATE (total ≈ 8.7h):
  hard   _preload_files                      saved=52L  ~156min
  hard   __init__                            saved=36L  ~108min
  medium find_exact_duplicates_lazy          saved=26L  ~52min
  medium _extract_functions_go               saved=21L  ~42min
  medium _should_exclude                     saved=20L  ~40min
  easy   _is_test_file                       saved=12L  ~24min
  easy   get_supported_languages             saved=11L  ~22min
  easy   _extract_class_name                 saved=9L  ~18min
  easy   _project_relative_path              saved=6L  ~12min
  easy   _analyze_html_css_blocks            saved=6L  ~12min
  ... +5 more (~36min)

METRICS-TARGET:
  dup_groups:  15 → 0
  saved_lines: 217 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 379 func | 68f | 2026-05-19
# generated in 0.01s

NEXT[3] (ranked by impact):
  [1] !! SPLIT           planfile.yaml
      WHY: 1670L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0

  [2] !! SPLIT           proxy_analysis/duplication.json
      WHY: 1436L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0

  [3] !! SPLIT           compare_report.json
      WHY: 792L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[3]:
  ⚠ Splitting planfile.yaml may break 0 import paths
  ⚠ Splitting proxy_analysis/duplication.json may break 0 import paths
  ⚠ Splitting compare_report.json may break 0 import paths

METRICS-TARGET:
  CC̄:          3.7 → ≤2.6
  max-CC:      14 → ≤7
  god-modules: 4 → 0
  high-CC(≥15): 0 → ≤0
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=3.6 → now CC̄=3.7
```

### Validation (`project/validation.toon.yaml`)

```toon markpact:analysis path=project/validation.toon.yaml
# vallm batch | 147f | 116✓ 2⚠ 1✗ | 2026-04-16

SUMMARY:
  scanned: 147  passed: 116 (78.9%)  warnings: 2  errors: 1  unsupported: 30

WARNINGS[2]{path,score}:
  src/redup/core/refactor_advisor.py,0.97
    issues[2]{rule,severity,message,line}:
      complexity.cyclomatic,warning,_build_prompt has cyclomatic complexity 16 (max: 15),64
      complexity.lizard_cc,warning,_build_prompt: CC=16 exceeds limit 15,64
  src/redup/reporters/toon_reporter.py,0.97
    issues[2]{rule,severity,message,line}:
      complexity.cyclomatic,warning,_render_effort_estimate has cyclomatic complexity 17 (max: 15),168
      complexity.lizard_cc,warning,_render_effort_estimate: CC=17 exceeds limit 15,168

ERRORS[1]{path,score}:
  src/redup/core/semantic.py,0.79
    issues[4]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'sentence_transformers' not found,64
      python.import.resolvable,error,Module 'torch' not found,65
      python.import.resolvable,error,Module 'sentence_transformers' not found,126
      python.import.resolvable,error,Module 'sentence_transformers' not found,170

UNSUPPORTED[3]{bucket,count}:
  *.md,17
  *.txt,2
  other,11
```

## Intent

Code duplication analyzer and refactoring planner for LLMs
