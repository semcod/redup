# reDUP

Code duplication analyzer and refactoring planner for LLMs

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Code Analysis](#code-analysis)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `redup`
- **version**: `0.4.29`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Taskfile.yml, testql(2), app.doql.less, pyqual.yaml, goal.yaml, .env.example, project/(3 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: redup;
  version: 0.4.29;
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
  step-1: run cmd=PYTHONPATH=src python -m redup quality jscpd;
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

## Interfaces

### CLI Entry Points

- `redup`
- `redup-mcp`

### testql Scenarios

#### `testql-scenarios/generated-cli-tests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-cli-tests.testql.toon.yaml
# SCENARIO: CLI Command Tests
# TYPE: cli
# GENERATED: true

CONFIG[2]{key, value}:
  cli_command, python -m redup
  timeout_ms, 10000

# Test 1: CLI help command
SHELL "python -m redup --help" 5000
ASSERT_EXIT_CODE 0
ASSERT_STDOUT_CONTAINS "usage"

# Test 2: CLI version command
SHELL "python -m redup --version" 5000
ASSERT_EXIT_CODE 0

# Test 3: CLI main workflow (dry-run)
SHELL "python -m redup --help" 10000
ASSERT_EXIT_CODE 0
```

#### `testql-scenarios/generated-from-pytests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-from-pytests.testql.toon.yaml
# SCENARIO: Auto-generated from Python Tests
# TYPE: integration
# GENERATED: true

CONFIG[2]{key, value}:
  base_url, ${api_url:-http://localhost:8101}
  timeout_ms, 10000

# Converted 4 assertions from pytest
ASSERT[4]{field, operator, expected}:
  task.task_id, ==, "GITHUB-123"
  task.task_id, ==, "GITHUB-123"
  task.task_id, ==, "GITHUB-123"
  task.task_id, ==, "GITHUB-123"
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
    - PYTHONPATH=src python -m redup quality jscpd
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

## Configuration

```yaml
project:
  name: redup
  version: 0.4.29
  env: local
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

## Deployment

```bash markpact:run
pip install redup

# development install
pip install -e .[dev]
```

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `*(not set)*` | Required: OpenRouter API key (https://openrouter.ai/keys) |
| `LLM_MODEL` | `openrouter/qwen/qwen3-coder-next` | Model (default: openrouter/qwen/qwen3-coder-next) |
| `PFIX_AUTO_APPLY` | `true` | true = apply fixes without asking |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | true = auto pip/uv install |
| `PFIX_AUTO_RESTART` | `false` | true = os.execv restart after fix |
| `PFIX_MAX_RETRIES` | `3` |  |
| `PFIX_DRY_RUN` | `false` |  |
| `PFIX_ENABLED` | `true` |  |
| `PFIX_GIT_COMMIT` | `false` | true = auto-commit fixes |
| `PFIX_GIT_PREFIX` | `pfix:` | commit message prefix |
| `PFIX_CREATE_BACKUPS` | `false` | false = disable .pfix_backups/ directory |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`redup`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `venv/lib/python3.13/site-packages/cryptography/__init__.py:__version__`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# redup | 115f 14869L | python:108,shell:5,css:1,less:1 | 2026-05-29
# stats: 358 func | 75 cls | 115 mod | CC̄=3.7 | critical:19 | cycles:0
# alerts[5]: CC tasks=14; CC _resolve_changed_files=13; CC _collect_target_files=13; CC _render_dependency_risk=13; CC write_results=12
# hotspots[5]: tasks fan=16; analyze_optimized fan=16; write_results fan=15; scan_command fan=15; detect_communities fan=15
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[115]:
  app.doql.css,74
  app.doql.less,206
  benchmark.py,118
  benchmarks/bench_libraries.py,169
  examples/01_basic_usage.py,61
  project.sh,54
  scripts/jscpd-check.sh,12
  scripts/jscpd-run.sh,12
  scripts/redup-run.sh,30
  src/redup/__init__.py,33
  src/redup/__main__.py,6
  src/redup/analysis_logic.py,28
  src/redup/cli_app/__init__.py,2
  src/redup/cli_app/compare_command.py,356
  src/redup/cli_app/config_builder.py,69
  src/redup/cli_app/fuzzy_similarity.py,172
  src/redup/cli_app/main.py,285
  src/redup/cli_app/output_writer.py,80
  src/redup/cli_app/quality_commands.py,202
  src/redup/cli_app/scan_commands.py,323
  src/redup/cli_app/scan_helpers.py,41
  src/redup/cli_app/tasks_command.py,187
  src/redup/config.py,183
  src/redup/config_handler.py,21
  src/redup/core/__init__.py,2
  src/redup/core/cache.py,287
  src/redup/core/community.py,123
  src/redup/core/comparator.py,313
  src/redup/core/config.py,173
  src/redup/core/decision.py,96
  src/redup/core/differ.py,218
  src/redup/core/fuzzy_similarity.py,431
  src/redup/core/grouper.py,16
  src/redup/core/hash_cache.py,103
  src/redup/core/hasher.py,203
  src/redup/core/lazy_grouper.py,161
  src/redup/core/lsh_matcher.py,233
  src/redup/core/matcher.py,112
  src/redup/core/models.py,296
  src/redup/core/pipeline/__init__.py,293
  src/redup/core/pipeline/duplicate_finder.py,267
  src/redup/core/pipeline/groups.py,100
  src/redup/core/pipeline/phases.py,47
  src/redup/core/pipeline_utils.py,8
  src/redup/core/planner.py,111
  src/redup/core/python_parser.py,187
  src/redup/core/refactor_advisor.py,364
  src/redup/core/scanner/__init__.py,310
  src/redup/core/scanner.py,1
  src/redup/core/scanner_cache.py,93
  src/redup/core/scanner_filters.py,106
  src/redup/core/scanner_loader.py,9
  src/redup/core/scanner_models.py,12
  src/redup/core/scanner_types.py,46
  src/redup/core/scanner_utils.py,100
  src/redup/core/semantic.py,183
  src/redup/core/ts_extractor/__init__.py,50
  src/redup/core/ts_extractor/config.py,144
  src/redup/core/ts_extractor/dispatcher.py,83
  src/redup/core/ts_extractor/extractors/__init__.py,24
  src/redup/core/ts_extractor/extractors/base.py,77
  src/redup/core/ts_extractor/extractors/c_family.py,41
  src/redup/core/ts_extractor/extractors/dotnet.py,56
  src/redup/core/ts_extractor/extractors/markup.py,42
  src/redup/core/ts_extractor/extractors/php.py,51
  src/redup/core/ts_extractor/extractors/query.py,47
  src/redup/core/ts_extractor/extractors/ruby.py,47
  src/redup/core/ts_extractor/extractors/shell.py,32
  src/redup/core/ts_extractor/extractors/stylesheet.py,52
  src/redup/core/ts_extractor/extractors/web.py,71
  src/redup/core/ts_extractor/main.py,115
  src/redup/core/universal_fuzzy.py,472
  src/redup/core/utils/__init__.py,2
  src/redup/core/utils/diff_helpers.py,212
  src/redup/core/utils/duplicate_finders.py,44
  src/redup/core/utils/function_extractor.py,150
  src/redup/core/utils/hash_utils.py,43
  src/redup/core/utils/language_dispatcher.py,77
  src/redup/integrations/__init__.py,6
  src/redup/integrations/planfile_integration.py,312
  src/redup/mcp/__init__.py,43
  src/redup/mcp/handlers.py,345
  src/redup/mcp/schemas.py,146
  src/redup/mcp/server.py,139
  src/redup/mcp/utils.py,29
  src/redup/mcp_server.py,83
  src/redup/mcp_server_clean.py,1
  src/redup/reporters/__init__.py,2
  src/redup/reporters/code2llm_reporter.py,212
  src/redup/reporters/enhanced_reporter.py,261
  src/redup/reporters/json_reporter.py,83
  src/redup/reporters/markdown_reporter.py,97
  src/redup/reporters/toon_reporter.py,269
  src/redup/reporters/yaml_reporter.py,19
  src/redup/reporters.py,1
  src/redup/utils.py,47
  src/sitecustomize.py,5
  test_fuzzy_similarity.py,242
  test_universal_fuzzy.py,337
  tests/__init__.py,1
  tests/test_cli_import_compat.py,26
  tests/test_compare.py,248
  tests/test_e2e.py,559
  tests/test_hasher.py,95
  tests/test_matcher.py,68
  tests/test_mcp_server.py,200
  tests/test_models.py,101
  tests/test_pipeline.py,160
  tests/test_planfile_integration.py,221
  tests/test_planner.py,121
  tests/test_quality_commands.py,140
  tests/test_reporters.py,252
  tests/test_scanner.py,110
  tests/test_ts_extractor.py,226
  tree.sh,2
D:
  benchmark.py:
    e: benchmark_sequential_vs_parallel,benchmark_feature_performance
    benchmark_sequential_vs_parallel()
    benchmark_feature_performance()
  benchmarks/bench_libraries.py:
    e: generate_test_project,benchmark,benchmark_hash_performance,benchmark_fuzzy_performance
    generate_test_project(root;num_files;lines_per_file)
    benchmark()
    benchmark_hash_performance()
    benchmark_fuzzy_performance()
  examples/01_basic_usage.py:
    e: main
    main()
  src/redup/__init__.py:
  src/redup/__main__.py:
  src/redup/analysis_logic.py:
    e: _parse_extensions,_build_scan_config
    _parse_extensions(ext_string)
    _build_scan_config(path;params)
  src/redup/cli_app/__init__.py:
  src/redup/cli_app/compare_command.py:
    e: compare_command,_parse_extensions,_print_summary_table,_detect_communities,_print_recommendation,_print_communities_table,_print_match_details,_generate_llm_plan,_export_json,_short_path,_make_relative_path,_deduplicate_matches,_compact_community,_filter_significant_communities,_build_recommendation_dict,_build_json_report
    compare_command(project_a;project_b;threshold;semantic;extensions;min_lines;no_community;output;refactor_plan;llm_model;env_file)
    _parse_extensions(extensions)
    _print_summary_table(comparison)
    _detect_communities(comparison;threshold;no_community)
    _print_recommendation(comparison;communities)
    _print_communities_table(communities)
    _print_match_details(comparison)
    _generate_llm_plan(report;refactor_plan;env_file;llm_model;comparison)
    _export_json(report;output)
    _short_path(path;max_parts)
    _make_relative_path(path;proj_a;proj_b)
    _deduplicate_matches(matches;proj_a;proj_b)
    _compact_community(c;proj_a;proj_b)
    _filter_significant_communities(communities;proj_a;proj_b)
    _build_recommendation_dict(comparison;communities)
    _build_json_report(comparison;communities)
  src/redup/cli_app/config_builder.py:
    e: build_config,build_config_with_file_support
    build_config(path;extensions;min_lines;min_similarity;include_tests)
    build_config_with_file_support(path;extensions;min_lines;min_similarity;include_tests;parallel;max_workers;incremental;memory_cache;max_cache_mb;functions_only;fuzzy;fuzzy_threshold;target_files)
  src/redup/cli_app/fuzzy_similarity.py:
    e: _apply_fuzzy_similarity,_validate_fuzzy_input,_extract_all_blocks,_separate_blocks_by_type,_analyze_blocks_with_detectors,_analyze_html_css_blocks,_analyze_other_language_blocks,_report_fuzzy_results,_report_similarity_by_groups
    _apply_fuzzy_similarity(dup_map;threshold)
    _validate_fuzzy_input(dup_map;threshold)
    _extract_all_blocks(dup_map)
    _separate_blocks_by_type(all_blocks)
    _analyze_blocks_with_detectors(html_css_blocks;other_blocks;threshold)
    _analyze_html_css_blocks(html_css_blocks;threshold)
    _analyze_other_language_blocks(other_blocks;threshold)
    _report_fuzzy_results(similar_pairs)
    _report_similarity_by_groups(similar_pairs)
  src/redup/cli_app/main.py:
    e: scan,compare,diff,check,config,info
    scan(path;format;output;extensions;min_lines;min_similarity;include_tests;no_functions_only;no_parallel;max_workers;incremental;no_memory_cache;max_cache_mb;changed_only;base_ref;include_untracked;fuzzy;fuzzy_threshold)
    compare(project_a;project_b;threshold;semantic;extensions;min_lines;no_community;output;refactor_plan;llm_model;env_file)
    diff(before;after)
    check(path;max_groups;max_saved_lines;extensions;min_lines;min_similarity;include_tests)
    config(init;show)
    info()
  src/redup/cli_app/output_writer.py:
    e: write_output,write_results
    write_output(content;output;suffix)
    write_results(dup_map;format;output;path)
  src/redup/cli_app/quality_commands.py:
    e: _env_int,_env_path,_repo_root,_jscpd_command,_read_jscpd_stats,_budget_violations,run_jscpd_budget,jscpd_run,jscpd,JscpdStats
    JscpdStats:
    _env_int(name;default)
    _env_path(name;default)
    _repo_root()
    _jscpd_command(cwd)
    _read_jscpd_stats(report_path)
    _budget_violations(stats;max_groups;max_lines)
    run_jscpd_budget(paths;min_lines;max_groups;max_lines;report_dir;silent)
    jscpd_run(ctx)
    jscpd(paths;min_lines;max_groups;max_lines;report_dir;silent)
  src/redup/cli_app/scan_commands.py:
    e: _resolve_changed_files,scan_command,diff_command,check_command,config_command,info_command
    _resolve_changed_files(path;base_ref;include_untracked)
    scan_command(path;format;output;extensions;min_lines;min_similarity;include_tests;functions_only;parallel;max_workers;incremental;memory_cache;max_cache_mb;changed_only;base_ref;include_untracked;fuzzy;fuzzy_threshold)
    diff_command(before;after)
    check_command(path;max_groups;max_saved_lines;extensions;min_lines;min_similarity;include_tests)
    config_command(init;show)
    info_command()
  src/redup/cli_app/scan_helpers.py:
    e: print_scan_header,print_scan_summary,apply_fuzzy_similarity
    print_scan_header(path;ext_list;min_lines;min_similarity)
    print_scan_summary(dup_map)
    apply_fuzzy_similarity(dup_map;threshold)
  src/redup/cli_app/tasks_command.py:
    e: tasks,_preview_tasks
    tasks(ctx;path;output;backend;min_lines;ext;milestone;dry_run)
    _preview_tasks(tasks)
  src/redup/config.py:
    e: get_default_filename,reload_config,RedupConfig
    RedupConfig: _env_name(2),_load_from_env(1),reload(2),get(3),set(3)  # Global configuration container for reDUP settings.
    get_default_filename(suffix)
    reload_config(env_path)
  src/redup/config_handler.py:
  src/redup/core/__init__.py:
  src/redup/core/cache.py:
    e: hash_block_with_cache,build_hash_index_with_cache,HashCache
    HashCache: __init__(1),_init_tables(0),_get_file_hash(2),is_file_unchanged(2),get_cached_block_hashes(2),store_file_hashes(3),cleanup_old_entries(1),get_stats(0)  # SQLite-based cache for file and block hashes.
    hash_block_with_cache(text;file_path;start;end;cache;file_content)
    build_hash_index_with_cache(blocks;min_lines;cache;project_root)
  src/redup/core/community.py:
    e: detect_communities,_longest_common_prefix,CodeCommunity
    CodeCommunity:  # A cluster of similar functions across projects — refactoring
    detect_communities(comparison;min_similarity)
    _longest_common_prefix(names)
  src/redup/core/comparator.py:
    e: compare_projects,_scan_project_blocks,_find_hash_matches,_find_lsh_matches,_is_cross_project_match,_normalize_match_order,_create_cross_project_match,_find_semantic_matches,CrossProjectMatch,CrossProjectComparison
    CrossProjectMatch:  # A pair of similar functions from two different projects.
    CrossProjectComparison: total_matches(0),shared_loc_potential(0)  # Full comparison result between two projects.
    compare_projects(project_a;project_b;similarity_threshold;use_semantic;extensions;min_lines;functions_only)
    _scan_project_blocks(root;extensions;min_lines;functions_only)
    _find_hash_matches(blocks_a;blocks_b;proj_a;proj_b)
    _find_lsh_matches(blocks_a;blocks_b;threshold;proj_a;proj_b)
    _is_cross_project_match(match;a_files;b_files)
    _normalize_match_order(match;a_files)
    _create_cross_project_match(block_a;block_b;similarity;proj_a;proj_b)
    _find_semantic_matches(blocks_a;blocks_b;threshold;proj_a;proj_b)
  src/redup/core/config.py:
    e: _load_toml_file,_get_config_from_pyproject,_get_config_from_redup_toml,load_config,config_to_scan_config,create_sample_redup_toml
    _load_toml_file(file_path)
    _get_config_from_pyproject()
    _get_config_from_redup_toml()
    load_config()
    config_to_scan_config(config;path)
    create_sample_redup_toml()
  src/redup/core/decision.py:
    e: recommend,RefactorDecision,DecisionRecommendation
    RefactorDecision:
    DecisionRecommendation:  # Actionable recommendation produced by the decision engine.
    recommend(comparison;communities)
  src/redup/core/differ.py:
    e: _load_duplication_map,_group_by_id,_groups_match,compare_scans,_format_group_header,_format_group_details,_format_groups_section,_format_assessment,format_diff_result,DiffResult
    DiffResult:  # Result of comparing two reDUP scans.
    _load_duplication_map(file_path)
    _group_by_id(groups)
    _groups_match(group1;group2)
    compare_scans(before_file;after_file)
    _format_group_header(title;width)
    _format_group_details(group;label)
    _format_groups_section(groups;title;width;label)
    _format_assessment(new_lines;resolved_lines)
    format_diff_result(diff)
  src/redup/core/fuzzy_similarity.py:
    e: ComponentSignature,HTMLComponentExtractor,CSSComponentExtractor,FuzzySimilarityDetector
    ComponentSignature:  # Semantic signature of a component for fuzzy matching.
    HTMLComponentExtractor: __init__(0),extract_component_signature(1),_normalize_html(1),_normalize_class_name(1),_detect_component_type(1),_extract_attributes(1),_extract_text_content(1),_compute_structure_hash(1)  # Extract HTML components with semantic normalization for fuzz
    CSSComponentExtractor: __init__(0),extract_component_signature(1),_extract_css_properties(1),_normalize_css_value(1),_detect_css_component_type(1),_compute_css_hash(1)  # Extract CSS components with semantic normalization for fuzzy
    FuzzySimilarityDetector: __init__(1),find_similar_components(1),_extract_signature(1),_compute_similarity(2),_compute_attribute_similarity(2),_compute_css_similarity(2)  # Detect fuzzy similarity between HTML/CSS components.
  src/redup/core/grouper.py:
  src/redup/core/hash_cache.py:
    e: _config_to_hash,HashCache
    HashCache: __init__(1),_load(0),save(0),get_file_hash(1),is_unchanged(2),update(3),invalidate(1),get_cached_results(1),clear(0)  # Cache for file hashes to enable incremental scanning.
    _config_to_hash(config)
  src/redup/core/hasher.py:
    e: _fast_hash,_normalize_text,_ast_to_normalized_string,_normalize_ast_text,_hash_text,hash_block,hash_block_structural,_hashed_block,_blocks_from_different_locations,_find_duplicates,build_hash_index,find_exact_duplicates,find_structural_duplicates,HashedBlock,HashIndex
    HashedBlock:  # A code block with its computed fingerprints.
    HashIndex:  # Index mapping hashes to blocks for fast lookup.
    _fast_hash(data)
    _normalize_text(text)
    _ast_to_normalized_string(tree)
    _normalize_ast_text(text)
    _hash_text(text;normalizer)
    hash_block(text)
    hash_block_structural(text)
    _hashed_block(block)
    _blocks_from_different_locations(blocks)
    _find_duplicates(hash_dict)
    build_hash_index(blocks;min_lines)
    find_exact_duplicates(index)
    find_structural_duplicates(index)
  src/redup/core/lazy_grouper.py:
    e: find_exact_duplicates_lazy,find_structural_duplicates_lazy,_create_duplicate_group,find_all_duplicates_lazy,DuplicateGroupCollector
    DuplicateGroupCollector: __init__(3),collect(1),collect_sorted(1)  # Collector for lazy duplicate groups with optional limits.
    find_exact_duplicates_lazy(index;min_lines)
    find_structural_duplicates_lazy(index;min_lines)
    _create_duplicate_group(hash_val;blocks;duplicate_type)
    find_all_duplicates_lazy(index;min_lines;include_exact;include_structural)
  src/redup/core/lsh_matcher.py:
    e: _create_minhash,_text_to_minhash_features,_create_simple_minhash,build_lsh_index,find_near_duplicates,_SimpleMinHash,LSHIndex
    _SimpleMinHash: __init__(2),jaccard(1)  # Simple MinHash implementation for fallback without datasketc
    LSHIndex: __init__(2),add(1),find_near_duplicates(1),_find_near_duplicates_simple(1),find_all_near_duplicates(1)  # LSH index for efficient near-duplicate detection.
    _create_minhash(text;num_perm)
    _text_to_minhash_features(text;num_features)
    _create_simple_minhash(text;num_perm)
    build_lsh_index(blocks;threshold;min_lines)
    find_near_duplicates(blocks;threshold;min_lines)
  src/redup/core/matcher.py:
    e: sequence_similarity,fuzzy_similarity,_compare_against_reference,match_candidates,refine_structural_matches,MatchResult
    MatchResult:  # Result of comparing two code blocks.
    sequence_similarity(text_a;text_b)
    fuzzy_similarity(text_a;text_b)
    _compare_against_reference(candidates;min_similarity;similarity_fn;method_fn;skip_same_location)
    match_candidates(candidates;min_similarity)
    refine_structural_matches(candidates;min_similarity)
  src/redup/core/models.py:
    e: DuplicateType,RefactorAction,RiskLevel,ScanConfig,DuplicateFragment,DuplicateGroup,RefactorSuggestion,ScanStats,DuplicationMap
    DuplicateType:  # How the duplicate was detected.
    RefactorAction:  # Proposed refactoring action.
    RiskLevel:  # Risk of the proposed refactoring.
    ScanConfig:  # Configuration for project scanning.
    DuplicateFragment: line_count(0)  # A single occurrence of a duplicated code fragment.
    DuplicateGroup: occurrences(0),total_lines(0),saved_lines_potential(0),impact_score(0)  # A cluster of duplicated code fragments.
    RefactorSuggestion:  # A concrete refactoring proposal for a duplicate group.
    ScanStats:  # Statistics from the scanning phase.
    DuplicationMap: total_groups(0),total_fragments(0),total_saved_lines(0),sorted_by_impact(0)  # Complete result of a reDUP analysis run.
  src/redup/core/pipeline/__init__.py:
    e: _build_duplication_map,_empty_duplication_map,analyze,analyze_optimized,analyze_parallel
    _build_duplication_map(config;stats;groups;start_time)
    _empty_duplication_map(config;start_time)
    analyze(config;function_level_only)
    analyze_optimized(config;function_level_only;use_memory_cache;max_cache_mb)
    analyze_parallel(config;function_level_only;max_workers)
  src/redup/core/pipeline/duplicate_finder.py:
    e: _finalize_duplicate_groups,find_exact_groups,find_structural_groups,find_near_duplicate_groups,find_semantic_groups,find_duplicates_phase_optimized,find_duplicates_phase_lazy
    _finalize_duplicate_groups(groups;all_blocks;config;start_time;cache)
    find_exact_groups(index)
    find_structural_groups(index;exact_groups_list)
    find_near_duplicate_groups(all_blocks;config)
    find_semantic_groups(blocks;threshold)
    find_duplicates_phase_optimized(all_blocks;config)
    find_duplicates_phase_lazy(all_blocks;config;cache)
  src/redup/core/pipeline/groups.py:
    e: blocks_to_group,deduplicate_groups,match_results_to_blocks,calculate_similarity
    blocks_to_group(group_id;blocks;dup_type;similarity;normalized_hash)
    deduplicate_groups(groups)
    match_results_to_blocks(matches)
    calculate_similarity(matches)
  src/redup/core/pipeline/phases.py:
    e: ensure_config,scan_phase,scan_phase_parallel,process_blocks
    ensure_config(config)
    scan_phase(config;function_level_only)
    scan_phase_parallel(config;max_workers)
    process_blocks(scanned_files;function_level_only)
  src/redup/core/pipeline_utils.py:
  src/redup/core/planner.py:
    e: _common_prefix,_suggest_module_name,_assess_risk,_choose_action,generate_suggestions
    _common_prefix(paths)
    _suggest_module_name(group)
    _assess_risk(group)
    _choose_action(group)
    generate_suggestions(dup_map)
  src/redup/core/python_parser.py:
    e: _parse_with_libcst,_build_parent_map,_extract_decorators,_extract_function_info,_parse_with_ast,parse_python_functions,parsed_to_code_blocks,ParsedFunction
    ParsedFunction:  # A parsed Python function with metadata.
    _parse_with_libcst(source;filepath)
    _build_parent_map(tree)
    _extract_decorators(node)
    _extract_function_info(node;parent_map;lines)
    _parse_with_ast(source;filepath)
    parse_python_functions(source;filepath)
    parsed_to_code_blocks(parsed;filepath)
  src/redup/core/refactor_advisor.py:
    e: _load_env,_get_model,_resolve_stats,_normalize_match,_build_match_list,_format_communities,_format_matches_section,_build_prompt,_get_prompt_instructions,generate_refactor_plan,_parse_llm_response,format_plan_markdown,format_plan_json,RefactorTask,RefactorPlan
    RefactorTask:  # A single refactoring action item.
    RefactorPlan:  # Complete LLM-generated refactoring plan.
    _load_env(env_path)
    _get_model(model_override)
    _resolve_stats(report)
    _normalize_match(m)
    _build_match_list(report;limit)
    _format_communities(communities)
    _format_matches_section(matches)
    _build_prompt(report)
    _get_prompt_instructions()
    generate_refactor_plan(report;env_path;model)
    _parse_llm_response(raw)
    format_plan_markdown(plan)
    format_plan_json(plan)
  src/redup/core/scanner/__init__.py:
    e: _normalize_scan_config,_extract_function_blocks_python,_extract_sliding_blocks,_read_source_text,_get_source_for_file,_extract_blocks_for_file,_process_single_file,_init_strategy,_init_file_loading,scan_project,scan_project_ultra_fast,scan_project_memory_optimized,scan_project_parallel,scan_project_parallel_memory_optimized
    _normalize_scan_config(config)
    _extract_function_blocks_python(source;filepath)
    _extract_sliding_blocks(source;filepath;min_lines)
    _read_source_text(file_path;cache)
    _get_source_for_file(file_path;preloaded_sources;file_cache)
    _extract_blocks_for_file(source;relative_path;file_ext;function_level_only;min_block_lines)
    _process_single_file(file_path;config;preloaded_sources;file_cache;function_level_only)
    _init_strategy(strategy;function_level_only)
    _init_file_loading(files;strategy)
    scan_project(config;strategy;function_level_only)
    scan_project_ultra_fast(config)
    scan_project_memory_optimized(config;max_cache_mb)
    scan_project_parallel(config;max_workers;function_level_only)
    scan_project_parallel_memory_optimized(config;max_workers;max_cache_mb;function_level_only)
  src/redup/core/scanner.py:
  src/redup/core/scanner_cache.py:
    e: _matches_pattern,_matches_any_exclude,_matches_any_include,_should_exclude,MemoryFileCache
    MemoryFileCache: __init__(1),_estimate_size(1),get_file_content(1),_evict_oldest(1)  # Cache file contents in RAM for faster access during scanning
    _matches_pattern(name;str_path;path_parts;pattern)
    _matches_any_exclude(name;str_path;path_parts;patterns)
    _matches_any_include(name;str_path;path_parts;patterns)
    _should_exclude(path;patterns)
  src/redup/core/scanner_filters.py:
    e: _project_relative_path,_is_test_file,_collect_target_files,_collect_files
    _project_relative_path(file_path;project_root)
    _is_test_file(path)
    _collect_target_files(config)
    _collect_files(config)
  src/redup/core/scanner_loader.py:
  src/redup/core/scanner_models.py:
  src/redup/core/scanner_types.py:
    e: CodeBlock,ScannedFile,ScanStrategy
    CodeBlock: line_count(0)  # A contiguous block of source code lines.
    ScannedFile: line_count(0)  # A file that has been read and split into blocks.
    ScanStrategy:  # Configuration for HOW to scan — not WHAT to scan.
  src/redup/core/scanner_utils.py:
    e: _read_file_with_mmap,_read_file_safe,_load_files_simple,_load_files_with_progress,_load_all_files,_print_load_result,_preload_files
    _read_file_with_mmap(file_path)
    _read_file_safe(file_path)
    _load_files_simple(files)
    _load_files_with_progress(files)
    _load_all_files(files)
    _print_load_result(sources;total_size;load_time)
    _preload_files(files;max_cache_mb)
  src/redup/core/semantic.py:
    e: SemanticMatch,SemanticDetector
    SemanticMatch:  # A pair of semantically similar code blocks.
    SemanticDetector: __init__(2),_ensure_model(0),find_semantic_duplicates(2),find_semantic_duplicates_fast(2),compute_semantic_similarity(2)  # Detects semantically similar code using transformer embeddin
  src/redup/core/ts_extractor/__init__.py:
  src/redup/core/ts_extractor/config.py:
    e: LanguageRegistry
    LanguageRegistry: __init__(0),get_language(1)
  src/redup/core/ts_extractor/dispatcher.py:
    e: initialize_language_dispatcher
    initialize_language_dispatcher()
  src/redup/core/ts_extractor/extractors/__init__.py:
  src/redup/core/ts_extractor/extractors/base.py:
    e: traverse_tree,get_node_text,create_code_block
    traverse_tree(node;source_lines;file_path;matchers;depth;max_depth)
    get_node_text(node)
    create_code_block(node;source_lines;file_path;function_name;class_name)
  src/redup/core/ts_extractor/extractors/c_family.py:
    e: extract_functions_c_cpp
    extract_functions_c_cpp(node;source_lines;file_path)
  src/redup/core/ts_extractor/extractors/dotnet.py:
    e: _extract_class_name,extract_functions_c_sharp
    _extract_class_name(node)
    extract_functions_c_sharp(node;source_lines;file_path)
  src/redup/core/ts_extractor/extractors/markup.py:
    e: extract_blocks_html_xml
    extract_blocks_html_xml(node;source_lines;file_path)
  src/redup/core/ts_extractor/extractors/php.py:
    e: _extract_class_name,extract_functions_php
    _extract_class_name(node)
    extract_functions_php(node;source_lines;file_path)
  src/redup/core/ts_extractor/extractors/query.py:
    e: extract_blocks_sql
    extract_blocks_sql(node;source_lines;file_path)
  src/redup/core/ts_extractor/extractors/ruby.py:
    e: extract_functions_ruby
    extract_functions_ruby(node;source_lines;file_path)
  src/redup/core/ts_extractor/extractors/shell.py:
    e: extract_functions_bash
    extract_functions_bash(node;source_lines;file_path)
  src/redup/core/ts_extractor/extractors/stylesheet.py:
    e: extract_blocks_css
    extract_blocks_css(node;source_lines;file_path)
  src/redup/core/ts_extractor/extractors/web.py:
    e: _extract_function_declaration,_extract_method_definition,_extract_arrow_function,extract_functions_javascript
    _extract_function_declaration(node;source_lines;file_path)
    _extract_method_definition(node;source_lines;file_path)
    _extract_arrow_function(node;source_lines;file_path)
    extract_functions_javascript(node;source_lines;file_path)
  src/redup/core/ts_extractor/main.py:
    e: _get_tree_sitter_language,_get_dispatcher,extract_functions_treesitter,get_supported_languages,is_language_supported
    _get_tree_sitter_language(language_name)
    _get_dispatcher()
    extract_functions_treesitter(source;file_path)
    get_supported_languages()
    is_language_supported(file_path)
  src/redup/core/universal_fuzzy.py:
    e: UniversalSignature,UniversalFuzzyExtractor,UniversalFuzzyDetector
    UniversalSignature:  # Universal semantic signature for any code block.
    UniversalFuzzyExtractor: __init__(0),extract_universal_signature(1),_detect_language(1),_normalize_code(2),_remove_comments(2),_normalize_identifiers(2),_detect_component_type(2),_extract_semantic_patterns(2),_extract_metadata(2),_compute_complexity(2),_compute_structure_hash(1)  # Universal fuzzy extractor for all supported languages and DS
    UniversalFuzzyDetector: __init__(1),find_similar_components(1),_compute_universal_similarity(2),_compute_pattern_similarity(2),_compute_metadata_similarity(2)  # Universal fuzzy similarity detector for all languages and DS
  src/redup/core/utils/__init__.py:
  src/redup/core/utils/diff_helpers.py:
    e: _group_files,_groups_match,_MatchResult,GroupMatcher,DiffCalculator
    _MatchResult:
    GroupMatcher: __init__(2),_match_exact_ids(3),_get_remaining_groups(2),_find_best_match(3),_match_similar_groups(3),_ensure_matches(0),_match_score(2),get_resolved_groups(0),get_new_groups(0),get_unchanged_groups(0)  # Match duplicate groups between two scan results.
    DiffCalculator: calculate_diff_stats(3)  # Aggregate statistics for scan diffs.
    _group_files(group)
    _groups_match(group1;group2)
  src/redup/core/utils/duplicate_finders.py:
    e: create_duplicate_finder
    create_duplicate_finder(hash_type)
  src/redup/core/utils/function_extractor.py:
    e: _extract_java_class_name,FunctionExtractor
    FunctionExtractor: __init__(3),extract_functions(3),_create_function_block(3),_create_method_block(4)  # Generic function extractor that can be configured for differ
    _extract_java_class_name(node)
  src/redup/core/utils/hash_utils.py:
    e: create_hash_function
    create_hash_function(normalizer)
  src/redup/core/utils/language_dispatcher.py:
    e: LanguageDispatcher
    LanguageDispatcher: __init__(0),register_extractor(2),register_group(2),get_extractor(1),extract_functions(4)  # Dispatches function extraction to appropriate language-speci
  src/redup/integrations/__init__.py:
  src/redup/integrations/planfile_integration.py:
    e: export_to_planfile,TaskConfig,DuplicateTask,DuplicateTaskExporter
    TaskConfig:  # Configuration for task export.
    DuplicateTask:  # Represents a task created from a duplicate group.
    DuplicateTaskExporter: __init__(1),export(2),_generate_tasks(1),_create_task_from_group(1),_build_description(3),_render_todo_md(0),_sync_to_backend(0)  # Export duplicate groups as tasks to planfile/TODO.md.
    export_to_planfile(dup_map;output_file;sync_backend)
  src/redup/mcp/__init__.py:
  src/redup/mcp/handlers.py:
    e: _build_scan_config,_run_analysis,_estimate_code2llm_counts,_scan_config_payload,_format_analysis_result,handle_analyze_project,handle_suggest_refactoring,handle_compare_scans,_check_thresholds,_format_top_groups,handle_check_project,_get_optional_deps,handle_project_info
    _build_scan_config(path;params)
    _run_analysis(path;params)
    _estimate_code2llm_counts(dup_map)
    _scan_config_payload(scan_config)
    _format_analysis_result(scan_config;dup_map;fmt;include_snippets)
    handle_analyze_project(params)
    handle_suggest_refactoring(params)
    handle_compare_scans(params)
    _check_thresholds(dup_map;params)
    _format_top_groups(dup_map;max_groups)
    handle_check_project(params)
    _get_optional_deps()
    handle_project_info(_)
  src/redup/mcp/schemas.py:
    e: _make_check_properties
    _make_check_properties()
  src/redup/mcp/server.py:
    e: handle_initialize,handle_tools_list,handle_tools_call,handle_request,run_server
    handle_initialize(request_id)
    handle_tools_list(request_id)
    handle_tools_call(request_id;params)
    handle_request(request)
    run_server()
  src/redup/mcp/utils.py:
    e: json_safe,resolve_path,parse_extensions
    json_safe(value)
    resolve_path(raw)
    parse_extensions(value)
  src/redup/mcp_server.py:
    e: _build_legacy_tool_schema
    _build_legacy_tool_schema()
  src/redup/mcp_server_clean.py:
  src/redup/reporters/__init__.py:
  src/redup/reporters/code2llm_reporter.py:
    e: _calculate_avg_cc,_count_critical_functions,_get_layers,to_code2llm_toon,to_code2llm_context,export_code2llm
    _calculate_avg_cc(dup_map)
    _count_critical_functions(dup_map)
    _get_layers(dup_map)
    to_code2llm_toon(dup_map;files_scanned;total_lines;functions_count;classes_count)
    to_code2llm_context(dup_map;files_scanned;total_lines;functions_count;classes_count;modules)
    export_code2llm(dup_map;output_dir;files_scanned;total_lines;functions_count;classes_count)
  src/redup/reporters/enhanced_reporter.py:
    e: EnhancedReporter
    EnhancedReporter: __init__(1),generate_metrics_report(0),_get_scan_metrics(0),_get_duplication_metrics(0),_get_language_metrics(0),_get_file_metrics(0),_get_complexity_metrics(0),_get_refactoring_metrics(0),_bucket_similarities(1),_bucket_group_sizes(1),_calculate_complexity_score(0),generate_visualization_data(0),_get_duplication_chart_data(0),_get_language_chart_data(0),_get_file_chart_data(0),_get_timeline_data(0),save_enhanced_report(1)  # Enhanced reporter with detailed metrics and visualizations.
  src/redup/reporters/json_reporter.py:
    e: _group_to_dict,_suggestion_to_dict,duplication_map_to_dict,to_json
    _group_to_dict(group;include_snippets)
    _suggestion_to_dict(s)
    duplication_map_to_dict(dup_map)
    to_json(dup_map;indent;include_snippets)
  src/redup/reporters/markdown_reporter.py:
    e: to_markdown
    to_markdown(dup_map)
  src/redup/reporters/toon_reporter.py:
    e: _render_header,_render_summary,_render_duplicates,_render_refactor,_render_hotspots,_render_dependency_risk,_render_quick_wins,_calculate_group_effort,_format_estimate_lines,_render_effort_estimate,_saved_for_suggestion,_render_metrics_target,to_toon
    _render_header(dup_map)
    _render_summary(dup_map)
    _render_duplicates(groups)
    _render_refactor(suggestions)
    _render_hotspots(dup_map)
    _render_dependency_risk(dup_map)
    _render_quick_wins(dup_map)
    _calculate_group_effort(group)
    _format_estimate_lines(estimates;total_minutes)
    _render_effort_estimate(dup_map)
    _saved_for_suggestion(s;dup_map)
    _render_metrics_target(dup_map;groups)
    to_toon(dup_map)
  src/redup/reporters/yaml_reporter.py:
    e: to_yaml
    to_yaml(dup_map)
  src/redup/reporters.py:
  src/redup/utils.py:
    e: _json_safe,_resolve_path,_parse_extensions
    _json_safe(value)
    _resolve_path(raw)
    _parse_extensions(value)
  src/sitecustomize.py:
  test_fuzzy_similarity.py:
    e: test_html_fuzzy_similarity,test_css_fuzzy_similarity,test_mixed_html_css
    test_html_fuzzy_similarity()
    test_css_fuzzy_similarity()
    test_mixed_html_css()
  test_universal_fuzzy.py:
    e: test_programming_languages,test_configuration_files,test_data_formats,test_query_languages,test_cross_language_patterns
    test_programming_languages()
    test_configuration_files()
    test_data_formats()
    test_query_languages()
    test_cross_language_patterns()
  tests/__init__.py:
  tests/test_cli_import_compat.py:
    e: _clear_redup_modules,test_cli_import_restores_click_choice_generics
    _clear_redup_modules()
    test_cli_import_restores_click_choice_generics(monkeypatch)
  tests/test_compare.py:
    e: twin_projects,disjoint_projects,TestFindHashMatches,TestCompareProjects,TestCommunityDetection,TestDecision
    TestFindHashMatches: test_identical_blocks_detected(0),test_different_blocks_no_match(0)
    TestCompareProjects: test_shared_function_detected(1),test_disjoint_projects_no_matches(1)
    TestCommunityDetection: _make_comparison(1),test_detect_communities_requires_networkx(0),test_no_matches_yields_no_communities(0)
    TestDecision: test_keep_separate_when_no_overlap(0),test_merge_when_high_overlap(0),test_extract_shared_lib_moderate_overlap(0)
    twin_projects(tmp_path)
    disjoint_projects(tmp_path)
  tests/test_e2e.py:
    e: project_with_duplicates,empty_project,no_duplicates_project,TestCLIInfo,TestCLIScanToon,TestCLIScanJSON,TestCLIScanYAML,TestCLIScanAll,TestCLIOptions,TestPythonModule,TestFullRoundtrip
    TestCLIInfo: test_info_shows_version(0),test_info_shows_dependencies(0)
    TestCLIScanToon: test_scan_toon_stdout(1),test_scan_toon_to_file(2),test_scan_empty_project(1),test_scan_no_duplicates(1)
    TestCLIScanJSON: test_scan_json_stdout_parseable(1),test_scan_json_to_file(2),test_json_contains_fragment_details(2)
    TestCLIScanYAML: test_scan_yaml_to_file(2)
    TestCLIScanAll: test_format_all_creates_three_files(2),test_format_all_json_valid(2),test_format_all_toon_has_refactor(2),test_all_three_formats_consistent(2)
    TestCLIOptions: test_custom_extensions(1),test_min_lines_filter(1),test_include_tests_flag(1),test_incremental_flag_enables_cache(1),test_changed_only_scans_modified_files(1)
    TestPythonModule: test_python_m_redup_info(0),test_python_m_redup_scan(1)
    TestFullRoundtrip: test_roundtrip_json(2),_verify_json_structure(1),_verify_calculate_tax_group(1),test_roundtrip_all_formats(2),test_roundtrip_self_analysis(0)
    project_with_duplicates(tmp_path)
    empty_project(tmp_path)
    no_duplicates_project(tmp_path)
  tests/test_hasher.py:
    e: test_identical_blocks_same_hash,test_comment_stripping,test_different_blocks_different_hash,test_structural_hash_ignores_literals,test_structural_hash_different_structure,test_build_hash_index_groups_duplicates,test_find_structural_duplicates
    test_identical_blocks_same_hash()
    test_comment_stripping()
    test_different_blocks_different_hash()
    test_structural_hash_ignores_literals()
    test_structural_hash_different_structure()
    test_build_hash_index_groups_duplicates()
    test_find_structural_duplicates()
  tests/test_matcher.py:
    e: _make_hashed,test_sequence_similarity_identical,test_sequence_similarity_different,test_fuzzy_similarity_close,test_match_candidates_above_threshold,test_match_candidates_below_threshold,test_refine_structural_same_location_skipped
    _make_hashed(file;text;func)
    test_sequence_similarity_identical()
    test_sequence_similarity_different()
    test_fuzzy_similarity_close()
    test_match_candidates_above_threshold()
    test_match_candidates_below_threshold()
    test_refine_structural_same_location_skipped()
  tests/test_mcp_server.py:
    e: _create_test_project,_analyze_test_project,test_initialize_and_tools_list,test_analyze_project_returns_json_report,test_compare_scans_returns_summary,test_check_project_detects_threshold_violation,test_unknown_tool_returns_error
    _create_test_project(root)
    _analyze_test_project(root)
    test_initialize_and_tools_list()
    test_analyze_project_returns_json_report()
    test_compare_scans_returns_summary()
    test_check_project_detects_threshold_violation()
    test_unknown_tool_returns_error()
  tests/test_models.py:
    e: test_fragment_line_count,test_group_saved_lines,test_group_single_occurrence_no_savings,test_group_impact_score,test_duplication_map_sorted_by_impact,test_duplication_map_totals,test_scan_config_defaults
    test_fragment_line_count()
    test_group_saved_lines()
    test_group_single_occurrence_no_savings()
    test_group_impact_score()
    test_duplication_map_sorted_by_impact()
    test_duplication_map_totals()
    test_scan_config_defaults()
  tests/test_pipeline.py:
    e: _create_test_project,test_analyze_finds_duplicates,test_analyze_generates_suggestions,test_analyze_empty_project,test_analyze_no_duplicates,test_analyze_optimized_stores_incremental_cache
    _create_test_project(root)
    test_analyze_finds_duplicates()
    test_analyze_generates_suggestions()
    test_analyze_empty_project()
    test_analyze_no_duplicates()
    test_analyze_optimized_stores_incremental_cache()
  tests/test_planfile_integration.py:
    e: create_test_duplication_map,TestDuplicateTaskExporter,TestExportToPlanfile,TestDuplicateTask
    TestDuplicateTaskExporter: test_init_default_config(0),test_init_custom_config(0),test_generate_tasks(1),test_create_task_difficulty_easy(0),test_create_task_difficulty_hard(0),test_export_creates_file(1),test_render_todo_md_structure(1)  # Test the DuplicateTaskExporter class.
    TestExportToPlanfile: test_export_to_planfile_creates_file(1),test_export_to_planfile_with_backend(1)  # Test the export_to_planfile convenience function.
    TestDuplicateTask: test_task_creation(0),test_task_with_external_data(0)  # Test the DuplicateTask dataclass.
    create_test_duplication_map()
  tests/test_planner.py:
    e: test_generate_suggestions_basic,test_no_suggestions_for_single_occurrence,test_priority_ordering,test_large_block_extract_module
    test_generate_suggestions_basic()
    test_no_suggestions_for_single_occurrence()
    test_priority_ordering()
    test_large_block_extract_module()
  tests/test_quality_commands.py:
    e: test_read_jscpd_stats,test_budget_violations,test_run_jscpd_budget_invokes_fallback_and_reads_report,test_quality_jscpd_cli_uses_packaged_command
    test_read_jscpd_stats(tmp_path)
    test_budget_violations()
    test_run_jscpd_budget_invokes_fallback_and_reads_report(tmp_path;monkeypatch)
    test_quality_jscpd_cli_uses_packaged_command(monkeypatch)
  tests/test_reporters.py:
    e: _sample_map,test_json_reporter_valid_json,test_json_reporter_with_suggestions,test_toon_reporter_header,test_toon_reporter_contains_fragments,test_yaml_reporter_valid,test_empty_map_json,test_empty_map_toon,_rich_map,test_toon_hotspots,test_toon_dependency_risk,test_toon_quick_wins,test_toon_effort_estimate,test_toon_empty_map_no_new_sections,test_toon_single_package_no_dependency_risk
    _sample_map()
    test_json_reporter_valid_json()
    test_json_reporter_with_suggestions()
    test_toon_reporter_header()
    test_toon_reporter_contains_fragments()
    test_yaml_reporter_valid()
    test_empty_map_json()
    test_empty_map_toon()
    _rich_map()
    test_toon_hotspots()
    test_toon_dependency_risk()
    test_toon_quick_wins()
    test_toon_effort_estimate()
    test_toon_empty_map_no_new_sections()
    test_toon_single_package_no_dependency_risk()
  tests/test_scanner.py:
    e: test_should_exclude_git,test_should_exclude_venv,test_should_not_exclude_normal,test_is_test_file,test_extract_function_blocks_python,test_extract_function_blocks_syntax_error,test_scan_project_real_dir,test_scan_project_target_files_only,test_scan_project_target_files_does_not_walk_tree
    test_should_exclude_git()
    test_should_exclude_venv()
    test_should_not_exclude_normal()
    test_is_test_file()
    test_extract_function_blocks_python()
    test_extract_function_blocks_syntax_error()
    test_scan_project_real_dir()
    test_scan_project_target_files_only()
    test_scan_project_target_files_does_not_walk_tree(monkeypatch)
  tests/test_ts_extractor.py:
    e: TestLanguageMapping,TestLanguageRegistry,TestLanguageSupportFunctions,TestExtractFunctions,TestHTMLExtraction,TestCSSExtraction,TestSQLExtraction,TestCExtraction,TestLuaExtraction
    TestLanguageMapping: test_language_mapping_has_common_extensions(0),test_language_mapping_has_new_web_languages(0),test_language_mapping_has_data_formats(0),test_language_mapping_has_sql(0),test_language_mapping_has_dsl_languages(0),test_language_mapping_has_additional_programming(0),test_language_mapping_count(0)  # Test language extension mappings.
    TestLanguageRegistry: test_registry_has_core_languages(0),test_registry_has_web_languages(0),test_registry_has_new_languages(0),test_registry_has_dsl_languages(0),test_registry_has_data_formats(0),test_registry_count(0)  # Test language registry for tree-sitter parsers.
    TestLanguageSupportFunctions: test_is_language_supported_python(0),test_is_language_supported_unknown_extension(0),test_is_language_supported_known_languages(0)  # Test language support checking functions.
    TestExtractFunctions: test_extract_python_returns_empty(0),test_extract_unknown_extension_returns_empty(0),test_extract_javascript_no_treesitter(0)  # Test function extraction for different languages.
    TestHTMLExtraction: test_html_extraction_structure(0)  # Test HTML block extraction.
    TestCSSExtraction: test_css_extraction_structure(0)  # Test CSS block extraction.
    TestSQLExtraction: test_sql_extraction_structure(0)  # Test SQL block extraction.
    TestCExtraction: test_c_extraction_structure(0)  # Test C/C++ function extraction.
    TestLuaExtraction: test_lua_extraction_structure(0)  # Test Lua function extraction.
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('redup', '0.4.29', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.css', 74, 'css').
project_file('app.doql.less', 206, 'less').
project_file('benchmark.py', 118, 'python').
project_file('benchmarks/bench_libraries.py', 169, 'python').
project_file('examples/01_basic_usage.py', 61, 'python').
project_file('project.sh', 54, 'shell').
project_file('scripts/jscpd-check.sh', 12, 'shell').
project_file('scripts/jscpd-run.sh', 12, 'shell').
project_file('scripts/redup-run.sh', 30, 'shell').
project_file('src/redup/__init__.py', 33, 'python').
project_file('src/redup/__main__.py', 6, 'python').
project_file('src/redup/analysis_logic.py', 28, 'python').
project_file('src/redup/cli_app/__init__.py', 2, 'python').
project_file('src/redup/cli_app/compare_command.py', 356, 'python').
project_file('src/redup/cli_app/config_builder.py', 69, 'python').
project_file('src/redup/cli_app/fuzzy_similarity.py', 172, 'python').
project_file('src/redup/cli_app/main.py', 285, 'python').
project_file('src/redup/cli_app/output_writer.py', 80, 'python').
project_file('src/redup/cli_app/quality_commands.py', 202, 'python').
project_file('src/redup/cli_app/scan_commands.py', 323, 'python').
project_file('src/redup/cli_app/scan_helpers.py', 41, 'python').
project_file('src/redup/cli_app/tasks_command.py', 187, 'python').
project_file('src/redup/config.py', 183, 'python').
project_file('src/redup/config_handler.py', 21, 'python').
project_file('src/redup/core/__init__.py', 2, 'python').
project_file('src/redup/core/cache.py', 287, 'python').
project_file('src/redup/core/community.py', 123, 'python').
project_file('src/redup/core/comparator.py', 313, 'python').
project_file('src/redup/core/config.py', 173, 'python').
project_file('src/redup/core/decision.py', 96, 'python').
project_file('src/redup/core/differ.py', 218, 'python').
project_file('src/redup/core/fuzzy_similarity.py', 431, 'python').
project_file('src/redup/core/grouper.py', 16, 'python').
project_file('src/redup/core/hash_cache.py', 103, 'python').
project_file('src/redup/core/hasher.py', 203, 'python').
project_file('src/redup/core/lazy_grouper.py', 161, 'python').
project_file('src/redup/core/lsh_matcher.py', 233, 'python').
project_file('src/redup/core/matcher.py', 112, 'python').
project_file('src/redup/core/models.py', 296, 'python').
project_file('src/redup/core/pipeline/__init__.py', 293, 'python').
project_file('src/redup/core/pipeline/duplicate_finder.py', 267, 'python').
project_file('src/redup/core/pipeline/groups.py', 100, 'python').
project_file('src/redup/core/pipeline/phases.py', 47, 'python').
project_file('src/redup/core/pipeline_utils.py', 8, 'python').
project_file('src/redup/core/planner.py', 111, 'python').
project_file('src/redup/core/python_parser.py', 187, 'python').
project_file('src/redup/core/refactor_advisor.py', 364, 'python').
project_file('src/redup/core/scanner/__init__.py', 310, 'python').
project_file('src/redup/core/scanner.py', 1, 'python').
project_file('src/redup/core/scanner_cache.py', 93, 'python').
project_file('src/redup/core/scanner_filters.py', 106, 'python').
project_file('src/redup/core/scanner_loader.py', 9, 'python').
project_file('src/redup/core/scanner_models.py', 12, 'python').
project_file('src/redup/core/scanner_types.py', 46, 'python').
project_file('src/redup/core/scanner_utils.py', 100, 'python').
project_file('src/redup/core/semantic.py', 183, 'python').
project_file('src/redup/core/ts_extractor/__init__.py', 50, 'python').
project_file('src/redup/core/ts_extractor/config.py', 144, 'python').
project_file('src/redup/core/ts_extractor/dispatcher.py', 83, 'python').
project_file('src/redup/core/ts_extractor/extractors/__init__.py', 24, 'python').
project_file('src/redup/core/ts_extractor/extractors/base.py', 77, 'python').
project_file('src/redup/core/ts_extractor/extractors/c_family.py', 41, 'python').
project_file('src/redup/core/ts_extractor/extractors/dotnet.py', 56, 'python').
project_file('src/redup/core/ts_extractor/extractors/markup.py', 42, 'python').
project_file('src/redup/core/ts_extractor/extractors/php.py', 51, 'python').
project_file('src/redup/core/ts_extractor/extractors/query.py', 47, 'python').
project_file('src/redup/core/ts_extractor/extractors/ruby.py', 47, 'python').
project_file('src/redup/core/ts_extractor/extractors/shell.py', 32, 'python').
project_file('src/redup/core/ts_extractor/extractors/stylesheet.py', 52, 'python').
project_file('src/redup/core/ts_extractor/extractors/web.py', 71, 'python').
project_file('src/redup/core/ts_extractor/main.py', 115, 'python').
project_file('src/redup/core/universal_fuzzy.py', 472, 'python').
project_file('src/redup/core/utils/__init__.py', 2, 'python').
project_file('src/redup/core/utils/diff_helpers.py', 212, 'python').
project_file('src/redup/core/utils/duplicate_finders.py', 44, 'python').
project_file('src/redup/core/utils/function_extractor.py', 150, 'python').
project_file('src/redup/core/utils/hash_utils.py', 43, 'python').
project_file('src/redup/core/utils/language_dispatcher.py', 77, 'python').
project_file('src/redup/integrations/__init__.py', 6, 'python').
project_file('src/redup/integrations/planfile_integration.py', 312, 'python').
project_file('src/redup/mcp/__init__.py', 43, 'python').
project_file('src/redup/mcp/handlers.py', 345, 'python').
project_file('src/redup/mcp/schemas.py', 146, 'python').
project_file('src/redup/mcp/server.py', 139, 'python').
project_file('src/redup/mcp/utils.py', 29, 'python').
project_file('src/redup/mcp_server.py', 83, 'python').
project_file('src/redup/mcp_server_clean.py', 1, 'python').
project_file('src/redup/reporters/__init__.py', 2, 'python').
project_file('src/redup/reporters/code2llm_reporter.py', 212, 'python').
project_file('src/redup/reporters/enhanced_reporter.py', 261, 'python').
project_file('src/redup/reporters/json_reporter.py', 83, 'python').
project_file('src/redup/reporters/markdown_reporter.py', 97, 'python').
project_file('src/redup/reporters/toon_reporter.py', 269, 'python').
project_file('src/redup/reporters/yaml_reporter.py', 19, 'python').
project_file('src/redup/reporters.py', 1, 'python').
project_file('src/redup/utils.py', 47, 'python').
project_file('src/sitecustomize.py', 5, 'python').
project_file('test_fuzzy_similarity.py', 242, 'python').
project_file('test_universal_fuzzy.py', 337, 'python').
project_file('tests/__init__.py', 1, 'python').
project_file('tests/test_cli_import_compat.py', 26, 'python').
project_file('tests/test_compare.py', 248, 'python').
project_file('tests/test_e2e.py', 559, 'python').
project_file('tests/test_hasher.py', 95, 'python').
project_file('tests/test_matcher.py', 68, 'python').
project_file('tests/test_mcp_server.py', 200, 'python').
project_file('tests/test_models.py', 101, 'python').
project_file('tests/test_pipeline.py', 160, 'python').
project_file('tests/test_planfile_integration.py', 221, 'python').
project_file('tests/test_planner.py', 121, 'python').
project_file('tests/test_quality_commands.py', 140, 'python').
project_file('tests/test_reporters.py', 252, 'python').
project_file('tests/test_scanner.py', 110, 'python').
project_file('tests/test_ts_extractor.py', 226, 'python').
project_file('tree.sh', 2, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('benchmark.py', 'benchmark_sequential_vs_parallel', 0, 3, 7).
python_function('benchmark.py', 'benchmark_feature_performance', 0, 3, 7).
python_function('benchmarks/bench_libraries.py', 'generate_test_project', 3, 3, 4).
python_function('benchmarks/bench_libraries.py', 'benchmark', 0, 10, 10).
python_function('benchmarks/bench_libraries.py', 'benchmark_hash_performance', 0, 4, 6).
python_function('benchmarks/bench_libraries.py', 'benchmark_fuzzy_performance', 0, 4, 5).
python_function('examples/01_basic_usage.py', 'main', 0, 5, 8).
python_function('src/redup/analysis_logic.py', '_parse_extensions', 1, 4, 2).
python_function('src/redup/analysis_logic.py', '_build_scan_config', 2, 3, 5).
python_function('src/redup/cli_app/compare_command.py', 'compare_command', 11, 1, 10).
python_function('src/redup/cli_app/compare_command.py', '_parse_extensions', 1, 3, 2).
python_function('src/redup/cli_app/compare_command.py', '_print_summary_table', 1, 1, 6).
python_function('src/redup/cli_app/compare_command.py', '_detect_communities', 3, 4, 2).
python_function('src/redup/cli_app/compare_command.py', '_print_recommendation', 2, 4, 3).
python_function('src/redup/cli_app/compare_command.py', '_print_communities_table', 1, 2, 6).
python_function('src/redup/cli_app/compare_command.py', '_print_match_details', 1, 5, 6).
python_function('src/redup/cli_app/compare_command.py', '_generate_llm_plan', 5, 5, 4).
python_function('src/redup/cli_app/compare_command.py', '_export_json', 2, 2, 3).
python_function('src/redup/cli_app/compare_command.py', '_short_path', 2, 2, 3).
python_function('src/redup/cli_app/compare_command.py', '_make_relative_path', 3, 3, 2).
python_function('src/redup/cli_app/compare_command.py', '_deduplicate_matches', 3, 6, 5).
python_function('src/redup/cli_app/compare_command.py', '_compact_community', 3, 5, 5).
python_function('src/redup/cli_app/compare_command.py', '_filter_significant_communities', 3, 4, 1).
python_function('src/redup/cli_app/compare_command.py', '_build_recommendation_dict', 2, 2, 2).
python_function('src/redup/cli_app/compare_command.py', '_build_json_report', 2, 1, 5).
python_function('src/redup/cli_app/config_builder.py', 'build_config', 5, 1, 2).
python_function('src/redup/cli_app/config_builder.py', 'build_config_with_file_support', 14, 10, 4).
python_function('src/redup/cli_app/fuzzy_similarity.py', '_apply_fuzzy_similarity', 2, 3, 7).
python_function('src/redup/cli_app/fuzzy_similarity.py', '_validate_fuzzy_input', 2, 4, 1).
python_function('src/redup/cli_app/fuzzy_similarity.py', '_extract_all_blocks', 1, 3, 2).
python_function('src/redup/cli_app/fuzzy_similarity.py', '_separate_blocks_by_type', 1, 5, 2).
python_function('src/redup/cli_app/fuzzy_similarity.py', '_analyze_blocks_with_detectors', 3, 3, 5).
python_function('src/redup/cli_app/fuzzy_similarity.py', '_analyze_html_css_blocks', 2, 1, 2).
python_function('src/redup/cli_app/fuzzy_similarity.py', '_analyze_other_language_blocks', 2, 1, 2).
python_function('src/redup/cli_app/fuzzy_similarity.py', '_report_fuzzy_results', 1, 5, 4).
python_function('src/redup/cli_app/fuzzy_similarity.py', '_report_similarity_by_groups', 1, 5, 4).
python_function('src/redup/cli_app/main.py', 'scan', 18, 1, 4).
python_function('src/redup/cli_app/main.py', 'compare', 11, 1, 4).
python_function('src/redup/cli_app/main.py', 'diff', 2, 1, 3).
python_function('src/redup/cli_app/main.py', 'check', 7, 1, 5).
python_function('src/redup/cli_app/main.py', 'config', 2, 1, 3).
python_function('src/redup/cli_app/main.py', 'info', 0, 1, 2).
python_function('src/redup/cli_app/output_writer.py', 'write_output', 3, 3, 4).
python_function('src/redup/cli_app/output_writer.py', 'write_results', 4, 12, 15).
python_function('src/redup/cli_app/quality_commands.py', '_env_int', 2, 2, 2).
python_function('src/redup/cli_app/quality_commands.py', '_env_path', 2, 1, 2).
python_function('src/redup/cli_app/quality_commands.py', '_repo_root', 0, 2, 4).
python_function('src/redup/cli_app/quality_commands.py', '_jscpd_command', 1, 4, 3).
python_function('src/redup/cli_app/quality_commands.py', '_read_jscpd_stats', 1, 1, 6).
python_function('src/redup/cli_app/quality_commands.py', '_budget_violations', 3, 3, 1).
python_function('src/redup/cli_app/quality_commands.py', 'run_jscpd_budget', 6, 5, 12).
python_function('src/redup/cli_app/quality_commands.py', 'jscpd_run', 1, 2, 7).
python_function('src/redup/cli_app/quality_commands.py', 'jscpd', 6, 8, 10).
python_function('src/redup/cli_app/scan_commands.py', '_resolve_changed_files', 3, 13, 13).
python_function('src/redup/cli_app/scan_commands.py', 'scan_command', 18, 8, 15).
python_function('src/redup/cli_app/scan_commands.py', 'diff_command', 2, 2, 4).
python_function('src/redup/cli_app/scan_commands.py', 'check_command', 7, 6, 12).
python_function('src/redup/cli_app/scan_commands.py', 'config_command', 2, 5, 11).
python_function('src/redup/cli_app/scan_commands.py', 'info_command', 0, 3, 4).
python_function('src/redup/cli_app/scan_helpers.py', 'print_scan_header', 4, 1, 2).
python_function('src/redup/cli_app/scan_helpers.py', 'print_scan_summary', 1, 1, 1).
python_function('src/redup/cli_app/scan_helpers.py', 'apply_fuzzy_similarity', 2, 1, 1).
python_function('src/redup/cli_app/tasks_command.py', 'tasks', 8, 14, 16).
python_function('src/redup/cli_app/tasks_command.py', '_preview_tasks', 1, 4, 8).
python_function('src/redup/config.py', 'get_default_filename', 1, 3, 1).
python_function('src/redup/config.py', 'reload_config', 1, 1, 1).
python_function('src/redup/core/cache.py', 'hash_block_with_cache', 6, 5, 3).
python_function('src/redup/core/cache.py', 'build_hash_index_with_cache', 4, 9, 8).
python_function('src/redup/core/community.py', 'detect_communities', 2, 11, 15).
python_function('src/redup/core/community.py', '_longest_common_prefix', 1, 7, 3).
python_function('src/redup/core/comparator.py', 'compare_projects', 7, 8, 9).
python_function('src/redup/core/comparator.py', '_scan_project_blocks', 4, 5, 3).
python_function('src/redup/core/comparator.py', '_find_hash_matches', 4, 6, 5).
python_function('src/redup/core/comparator.py', '_find_lsh_matches', 5, 8, 5).
python_function('src/redup/core/comparator.py', '_is_cross_project_match', 3, 4, 0).
python_function('src/redup/core/comparator.py', '_normalize_match_order', 2, 2, 0).
python_function('src/redup/core/comparator.py', '_create_cross_project_match', 5, 3, 1).
python_function('src/redup/core/comparator.py', '_find_semantic_matches', 5, 8, 7).
python_function('src/redup/core/config.py', '_load_toml_file', 1, 4, 3).
python_function('src/redup/core/config.py', '_get_config_from_pyproject', 0, 1, 3).
python_function('src/redup/core/config.py', '_get_config_from_redup_toml', 0, 1, 2).
python_function('src/redup/core/config.py', 'load_config', 0, 5, 7).
python_function('src/redup/core/config.py', 'config_to_scan_config', 2, 4, 6).
python_function('src/redup/core/config.py', 'create_sample_redup_toml', 0, 1, 0).
python_function('src/redup/core/decision.py', 'recommend', 2, 6, 4).
python_function('src/redup/core/differ.py', '_load_duplication_map', 1, 5, 11).
python_function('src/redup/core/differ.py', '_group_by_id', 1, 2, 0).
python_function('src/redup/core/differ.py', '_groups_match', 2, 7, 4).
python_function('src/redup/core/differ.py', 'compare_scans', 2, 1, 8).
python_function('src/redup/core/differ.py', '_format_group_header', 2, 1, 0).
python_function('src/redup/core/differ.py', '_format_group_details', 2, 3, 2).
python_function('src/redup/core/differ.py', '_format_groups_section', 4, 3, 5).
python_function('src/redup/core/differ.py', '_format_assessment', 2, 3, 0).
python_function('src/redup/core/differ.py', 'format_diff_result', 1, 1, 5).
python_function('src/redup/core/hash_cache.py', '_config_to_hash', 1, 1, 4).
python_function('src/redup/core/hasher.py', '_fast_hash', 1, 2, 3).
python_function('src/redup/core/hasher.py', '_normalize_text', 1, 6, 11).
python_function('src/redup/core/hasher.py', '_ast_to_normalized_string', 1, 12, 6).
python_function('src/redup/core/hasher.py', '_normalize_ast_text', 1, 5, 9).
python_function('src/redup/core/hasher.py', '_hash_text', 2, 1, 3).
python_function('src/redup/core/hasher.py', 'hash_block', 1, 1, 1).
python_function('src/redup/core/hasher.py', 'hash_block_structural', 1, 1, 1).
python_function('src/redup/core/hasher.py', '_hashed_block', 1, 1, 3).
python_function('src/redup/core/hasher.py', '_blocks_from_different_locations', 1, 2, 1).
python_function('src/redup/core/hasher.py', '_find_duplicates', 1, 4, 3).
python_function('src/redup/core/hasher.py', 'build_hash_index', 2, 3, 3).
python_function('src/redup/core/hasher.py', 'find_exact_duplicates', 1, 1, 1).
python_function('src/redup/core/hasher.py', 'find_structural_duplicates', 1, 1, 1).
python_function('src/redup/core/lazy_grouper.py', 'find_exact_duplicates_lazy', 2, 5, 4).
python_function('src/redup/core/lazy_grouper.py', 'find_structural_duplicates_lazy', 2, 5, 4).
python_function('src/redup/core/lazy_grouper.py', '_create_duplicate_group', 3, 4, 2).
python_function('src/redup/core/lazy_grouper.py', 'find_all_duplicates_lazy', 4, 3, 2).
python_function('src/redup/core/lsh_matcher.py', '_create_minhash', 2, 3, 5).
python_function('src/redup/core/lsh_matcher.py', '_text_to_minhash_features', 2, 5, 8).
python_function('src/redup/core/lsh_matcher.py', '_create_simple_minhash', 2, 1, 2).
python_function('src/redup/core/lsh_matcher.py', 'build_lsh_index', 3, 3, 2).
python_function('src/redup/core/lsh_matcher.py', 'find_near_duplicates', 3, 10, 2).
python_function('src/redup/core/matcher.py', 'sequence_similarity', 2, 3, 3).
python_function('src/redup/core/matcher.py', 'fuzzy_similarity', 2, 2, 3).
python_function('src/redup/core/matcher.py', '_compare_against_reference', 5, 7, 5).
python_function('src/redup/core/matcher.py', 'match_candidates', 2, 2, 1).
python_function('src/redup/core/matcher.py', 'refine_structural_matches', 2, 1, 1).
python_function('src/redup/core/pipeline/__init__.py', '_build_duplication_map', 4, 2, 5).
python_function('src/redup/core/pipeline/__init__.py', '_empty_duplication_map', 2, 2, 4).
python_function('src/redup/core/pipeline/__init__.py', 'analyze', 2, 2, 5).
python_function('src/redup/core/pipeline/__init__.py', 'analyze_optimized', 4, 11, 16).
python_function('src/redup/core/pipeline/__init__.py', 'analyze_parallel', 3, 2, 10).
python_function('src/redup/core/pipeline/duplicate_finder.py', '_finalize_duplicate_groups', 5, 2, 7).
python_function('src/redup/core/pipeline/duplicate_finder.py', 'find_exact_groups', 1, 6, 6).
python_function('src/redup/core/pipeline/duplicate_finder.py', 'find_structural_groups', 2, 9, 11).
python_function('src/redup/core/pipeline/duplicate_finder.py', 'find_near_duplicate_groups', 2, 11, 8).
python_function('src/redup/core/pipeline/duplicate_finder.py', 'find_semantic_groups', 2, 6, 7).
python_function('src/redup/core/pipeline/duplicate_finder.py', 'find_duplicates_phase_optimized', 2, 1, 5).
python_function('src/redup/core/pipeline/duplicate_finder.py', 'find_duplicates_phase_lazy', 3, 5, 10).
python_function('src/redup/core/pipeline/groups.py', 'blocks_to_group', 5, 5, 6).
python_function('src/redup/core/pipeline/groups.py', 'deduplicate_groups', 1, 6, 5).
python_function('src/redup/core/pipeline/groups.py', 'match_results_to_blocks', 1, 4, 3).
python_function('src/redup/core/pipeline/groups.py', 'calculate_similarity', 1, 3, 2).
python_function('src/redup/core/pipeline/phases.py', 'ensure_config', 1, 2, 1).
python_function('src/redup/core/pipeline/phases.py', 'scan_phase', 2, 2, 1).
python_function('src/redup/core/pipeline/phases.py', 'scan_phase_parallel', 2, 2, 2).
python_function('src/redup/core/pipeline/phases.py', 'process_blocks', 2, 6, 3).
python_function('src/redup/core/planner.py', '_common_prefix', 1, 3, 2).
python_function('src/redup/core/planner.py', '_suggest_module_name', 1, 6, 1).
python_function('src/redup/core/planner.py', '_assess_risk', 1, 7, 2).
python_function('src/redup/core/planner.py', '_choose_action', 1, 7, 2).
python_function('src/redup/core/planner.py', 'generate_suggestions', 1, 6, 9).
python_function('src/redup/core/python_parser.py', '_parse_with_libcst', 2, 4, 11).
python_function('src/redup/core/python_parser.py', '_build_parent_map', 1, 5, 3).
python_function('src/redup/core/python_parser.py', '_extract_decorators', 1, 5, 3).
python_function('src/redup/core/python_parser.py', '_extract_function_info', 3, 4, 9).
python_function('src/redup/core/python_parser.py', '_parse_with_ast', 2, 4, 7).
python_function('src/redup/core/python_parser.py', 'parse_python_functions', 2, 3, 2).
python_function('src/redup/core/python_parser.py', 'parsed_to_code_blocks', 2, 2, 1).
python_function('src/redup/core/refactor_advisor.py', '_load_env', 1, 5, 3).
python_function('src/redup/core/refactor_advisor.py', '_get_model', 1, 2, 1).
python_function('src/redup/core/refactor_advisor.py', '_resolve_stats', 1, 3, 1).
python_function('src/redup/core/refactor_advisor.py', '_normalize_match', 1, 7, 2).
python_function('src/redup/core/refactor_advisor.py', '_build_match_list', 2, 2, 3).
python_function('src/redup/core/refactor_advisor.py', '_format_communities', 1, 6, 4).
python_function('src/redup/core/refactor_advisor.py', '_format_matches_section', 1, 2, 3).
python_function('src/redup/core/refactor_advisor.py', '_build_prompt', 1, 2, 6).
python_function('src/redup/core/refactor_advisor.py', '_get_prompt_instructions', 0, 1, 0).
python_function('src/redup/core/refactor_advisor.py', 'generate_refactor_plan', 3, 6, 9).
python_function('src/redup/core/refactor_advisor.py', '_parse_llm_response', 1, 9, 10).
python_function('src/redup/core/refactor_advisor.py', 'format_plan_markdown', 1, 8, 4).
python_function('src/redup/core/refactor_advisor.py', 'format_plan_json', 1, 2, 0).
python_function('src/redup/core/scanner/__init__.py', '_normalize_scan_config', 1, 2, 4).
python_function('src/redup/core/scanner/__init__.py', '_extract_function_blocks_python', 2, 10, 9).
python_function('src/redup/core/scanner/__init__.py', '_extract_sliding_blocks', 3, 6, 8).
python_function('src/redup/core/scanner/__init__.py', '_read_source_text', 2, 6, 4).
python_function('src/redup/core/scanner/__init__.py', '_get_source_for_file', 3, 2, 2).
python_function('src/redup/core/scanner/__init__.py', '_extract_blocks_for_file', 5, 4, 4).
python_function('src/redup/core/scanner/__init__.py', '_process_single_file', 5, 2, 6).
python_function('src/redup/core/scanner/__init__.py', '_init_strategy', 2, 5, 2).
python_function('src/redup/core/scanner/__init__.py', '_init_file_loading', 2, 3, 2).
python_function('src/redup/core/scanner/__init__.py', 'scan_project', 3, 5, 14).
python_function('src/redup/core/scanner/__init__.py', 'scan_project_ultra_fast', 1, 1, 2).
python_function('src/redup/core/scanner/__init__.py', 'scan_project_memory_optimized', 2, 1, 2).
python_function('src/redup/core/scanner/__init__.py', 'scan_project_parallel', 3, 1, 2).
python_function('src/redup/core/scanner/__init__.py', 'scan_project_parallel_memory_optimized', 4, 1, 2).
python_function('src/redup/core/scanner_cache.py', '_matches_pattern', 4, 4, 2).
python_function('src/redup/core/scanner_cache.py', '_matches_any_exclude', 4, 3, 3).
python_function('src/redup/core/scanner_cache.py', '_matches_any_include', 4, 3, 3).
python_function('src/redup/core/scanner_cache.py', '_should_exclude', 2, 3, 4).
python_function('src/redup/core/scanner_filters.py', '_project_relative_path', 2, 2, 1).
python_function('src/redup/core/scanner_filters.py', '_is_test_file', 1, 8, 2).
python_function('src/redup/core/scanner_filters.py', '_collect_target_files', 1, 13, 14).
python_function('src/redup/core/scanner_filters.py', '_collect_files', 1, 12, 15).
python_function('src/redup/core/scanner_utils.py', '_read_file_with_mmap', 1, 1, 5).
python_function('src/redup/core/scanner_utils.py', '_read_file_safe', 1, 3, 3).
python_function('src/redup/core/scanner_utils.py', '_load_files_simple', 1, 3, 2).
python_function('src/redup/core/scanner_utils.py', '_load_files_with_progress', 1, 3, 8).
python_function('src/redup/core/scanner_utils.py', '_load_all_files', 1, 2, 2).
python_function('src/redup/core/scanner_utils.py', '_print_load_result', 3, 1, 2).
python_function('src/redup/core/scanner_utils.py', '_preload_files', 2, 4, 8).
python_function('src/redup/core/ts_extractor/dispatcher.py', 'initialize_language_dispatcher', 0, 2, 2).
python_function('src/redup/core/ts_extractor/extractors/base.py', 'traverse_tree', 6, 5, 3).
python_function('src/redup/core/ts_extractor/extractors/base.py', 'get_node_text', 1, 3, 2).
python_function('src/redup/core/ts_extractor/extractors/base.py', 'create_code_block', 5, 1, 2).
python_function('src/redup/core/ts_extractor/extractors/c_family.py', 'extract_functions_c_cpp', 3, 1, 6).
python_function('src/redup/core/ts_extractor/extractors/dotnet.py', '_extract_class_name', 1, 5, 2).
python_function('src/redup/core/ts_extractor/extractors/dotnet.py', 'extract_functions_c_sharp', 3, 1, 6).
python_function('src/redup/core/ts_extractor/extractors/markup.py', 'extract_blocks_html_xml', 3, 1, 4).
python_function('src/redup/core/ts_extractor/extractors/php.py', '_extract_class_name', 1, 5, 2).
python_function('src/redup/core/ts_extractor/extractors/php.py', 'extract_functions_php', 3, 1, 6).
python_function('src/redup/core/ts_extractor/extractors/query.py', 'extract_blocks_sql', 3, 1, 4).
python_function('src/redup/core/ts_extractor/extractors/ruby.py', 'extract_functions_ruby', 3, 1, 5).
python_function('src/redup/core/ts_extractor/extractors/shell.py', 'extract_functions_bash', 3, 1, 5).
python_function('src/redup/core/ts_extractor/extractors/stylesheet.py', 'extract_blocks_css', 3, 1, 4).
python_function('src/redup/core/ts_extractor/extractors/web.py', '_extract_function_declaration', 3, 2, 3).
python_function('src/redup/core/ts_extractor/extractors/web.py', '_extract_method_definition', 3, 2, 3).
python_function('src/redup/core/ts_extractor/extractors/web.py', '_extract_arrow_function', 3, 2, 1).
python_function('src/redup/core/ts_extractor/extractors/web.py', 'extract_functions_javascript', 3, 1, 5).
python_function('src/redup/core/ts_extractor/main.py', '_get_tree_sitter_language', 1, 1, 1).
python_function('src/redup/core/ts_extractor/main.py', '_get_dispatcher', 0, 2, 1).
python_function('src/redup/core/ts_extractor/main.py', 'extract_functions_treesitter', 2, 8, 10).
python_function('src/redup/core/ts_extractor/main.py', 'get_supported_languages', 0, 4, 3).
python_function('src/redup/core/ts_extractor/main.py', 'is_language_supported', 1, 5, 4).
python_function('src/redup/core/utils/diff_helpers.py', '_group_files', 1, 2, 0).
python_function('src/redup/core/utils/diff_helpers.py', '_groups_match', 2, 6, 5).
python_function('src/redup/core/utils/duplicate_finders.py', 'create_duplicate_finder', 1, 3, 2).
python_function('src/redup/core/utils/function_extractor.py', '_extract_java_class_name', 1, 5, 2).
python_function('src/redup/core/utils/hash_utils.py', 'create_hash_function', 1, 3, 1).
python_function('src/redup/integrations/planfile_integration.py', 'export_to_planfile', 3, 1, 4).
python_function('src/redup/mcp/handlers.py', '_build_scan_config', 2, 12, 7).
python_function('src/redup/mcp/handlers.py', '_run_analysis', 2, 7, 9).
python_function('src/redup/mcp/handlers.py', '_estimate_code2llm_counts', 1, 5, 3).
python_function('src/redup/mcp/handlers.py', '_scan_config_payload', 1, 1, 1).
python_function('src/redup/mcp/handlers.py', '_format_analysis_result', 4, 7, 14).
python_function('src/redup/mcp/handlers.py', 'handle_analyze_project', 1, 3, 10).
python_function('src/redup/mcp/handlers.py', 'handle_suggest_refactoring', 1, 4, 11).
python_function('src/redup/mcp/handlers.py', 'handle_compare_scans', 1, 1, 5).
python_function('src/redup/mcp/handlers.py', '_check_thresholds', 2, 3, 3).
python_function('src/redup/mcp/handlers.py', '_format_top_groups', 2, 2, 3).
python_function('src/redup/mcp/handlers.py', 'handle_check_project', 1, 3, 10).
python_function('src/redup/mcp/handlers.py', '_get_optional_deps', 0, 3, 2).
python_function('src/redup/mcp/handlers.py', 'handle_project_info', 1, 1, 7).
python_function('src/redup/mcp/schemas.py', '_make_check_properties', 0, 1, 0).
python_function('src/redup/mcp/server.py', 'handle_initialize', 1, 1, 0).
python_function('src/redup/mcp/server.py', 'handle_tools_list', 1, 2, 1).
python_function('src/redup/mcp/server.py', 'handle_tools_call', 2, 4, 1).
python_function('src/redup/mcp/server.py', 'handle_request', 1, 5, 4).
python_function('src/redup/mcp/server.py', 'run_server', 0, 5, 8).
python_function('src/redup/mcp/utils.py', 'json_safe', 1, 6, 4).
python_function('src/redup/mcp/utils.py', 'resolve_path', 1, 3, 7).
python_function('src/redup/mcp/utils.py', 'parse_extensions', 1, 8, 6).
python_function('src/redup/mcp_server.py', '_build_legacy_tool_schema', 0, 2, 1).
python_function('src/redup/reporters/code2llm_reporter.py', '_calculate_avg_cc', 1, 1, 0).
python_function('src/redup/reporters/code2llm_reporter.py', '_count_critical_functions', 1, 1, 0).
python_function('src/redup/reporters/code2llm_reporter.py', '_get_layers', 1, 1, 3).
python_function('src/redup/reporters/code2llm_reporter.py', 'to_code2llm_toon', 5, 5, 8).
python_function('src/redup/reporters/code2llm_reporter.py', 'to_code2llm_context', 6, 11, 4).
python_function('src/redup/reporters/code2llm_reporter.py', 'export_code2llm', 6, 1, 5).
python_function('src/redup/reporters/json_reporter.py', '_group_to_dict', 2, 5, 3).
python_function('src/redup/reporters/json_reporter.py', '_suggestion_to_dict', 1, 1, 0).
python_function('src/redup/reporters/json_reporter.py', 'duplication_map_to_dict', 1, 3, 4).
python_function('src/redup/reporters/json_reporter.py', 'to_json', 3, 1, 2).
python_function('src/redup/reporters/markdown_reporter.py', 'to_markdown', 1, 12, 9).
python_function('src/redup/reporters/toon_reporter.py', '_render_header', 1, 1, 2).
python_function('src/redup/reporters/toon_reporter.py', '_render_summary', 1, 1, 0).
python_function('src/redup/reporters/toon_reporter.py', '_render_duplicates', 1, 8, 3).
python_function('src/redup/reporters/toon_reporter.py', '_render_refactor', 1, 4, 4).
python_function('src/redup/reporters/toon_reporter.py', '_render_hotspots', 1, 6, 8).
python_function('src/redup/reporters/toon_reporter.py', '_render_dependency_risk', 1, 13, 5).
python_function('src/redup/reporters/toon_reporter.py', '_render_quick_wins', 1, 9, 6).
python_function('src/redup/reporters/toon_reporter.py', '_calculate_group_effort', 1, 10, 2).
python_function('src/redup/reporters/toon_reporter.py', '_format_estimate_lines', 2, 4, 3).
python_function('src/redup/reporters/toon_reporter.py', '_render_effort_estimate', 1, 5, 4).
python_function('src/redup/reporters/toon_reporter.py', '_saved_for_suggestion', 2, 3, 0).
python_function('src/redup/reporters/toon_reporter.py', '_render_metrics_target', 2, 2, 1).
python_function('src/redup/reporters/toon_reporter.py', 'to_toon', 1, 3, 11).
python_function('src/redup/reporters/yaml_reporter.py', 'to_yaml', 1, 2, 3).
python_function('src/redup/utils.py', '_json_safe', 1, 10, 4).
python_function('src/redup/utils.py', '_resolve_path', 1, 3, 7).
python_function('src/redup/utils.py', '_parse_extensions', 1, 7, 7).
python_function('test_fuzzy_similarity.py', 'test_html_fuzzy_similarity', 0, 8, 7).
python_function('test_fuzzy_similarity.py', 'test_css_fuzzy_similarity', 0, 7, 7).
python_function('test_fuzzy_similarity.py', 'test_mixed_html_css', 0, 1, 5).
python_function('test_universal_fuzzy.py', 'test_programming_languages', 0, 2, 7).
python_function('test_universal_fuzzy.py', 'test_configuration_files', 0, 2, 7).
python_function('test_universal_fuzzy.py', 'test_data_formats', 0, 2, 7).
python_function('test_universal_fuzzy.py', 'test_query_languages', 0, 2, 7).
python_function('test_universal_fuzzy.py', 'test_cross_language_patterns', 0, 2, 7).
python_function('tests/test_cli_import_compat.py', '_clear_redup_modules', 0, 4, 3).
python_function('tests/test_cli_import_compat.py', 'test_cli_import_restores_click_choice_generics', 1, 3, 4).
python_function('tests/test_compare.py', 'twin_projects', 1, 1, 3).
python_function('tests/test_compare.py', 'disjoint_projects', 1, 1, 3).
python_function('tests/test_e2e.py', 'project_with_duplicates', 1, 1, 1).
python_function('tests/test_e2e.py', 'empty_project', 1, 1, 0).
python_function('tests/test_e2e.py', 'no_duplicates_project', 1, 1, 1).
python_function('tests/test_hasher.py', 'test_identical_blocks_same_hash', 0, 2, 1).
python_function('tests/test_hasher.py', 'test_comment_stripping', 0, 2, 1).
python_function('tests/test_hasher.py', 'test_different_blocks_different_hash', 0, 2, 1).
python_function('tests/test_hasher.py', 'test_structural_hash_ignores_literals', 0, 2, 1).
python_function('tests/test_hasher.py', 'test_structural_hash_different_structure', 0, 2, 1).
python_function('tests/test_hasher.py', 'test_build_hash_index_groups_duplicates', 0, 5, 5).
python_function('tests/test_hasher.py', 'test_find_structural_duplicates', 0, 2, 4).
python_function('tests/test_matcher.py', '_make_hashed', 3, 1, 2).
python_function('tests/test_matcher.py', 'test_sequence_similarity_identical', 0, 2, 1).
python_function('tests/test_matcher.py', 'test_sequence_similarity_different', 0, 2, 1).
python_function('tests/test_matcher.py', 'test_fuzzy_similarity_close', 0, 2, 1).
python_function('tests/test_matcher.py', 'test_match_candidates_above_threshold', 0, 3, 3).
python_function('tests/test_matcher.py', 'test_match_candidates_below_threshold', 0, 2, 3).
python_function('tests/test_matcher.py', 'test_refine_structural_same_location_skipped', 0, 2, 4).
python_function('tests/test_mcp_server.py', '_create_test_project', 1, 1, 1).
python_function('tests/test_mcp_server.py', '_analyze_test_project', 1, 1, 2).
python_function('tests/test_mcp_server.py', 'test_initialize_and_tools_list', 0, 5, 1).
python_function('tests/test_mcp_server.py', 'test_analyze_project_returns_json_report', 0, 4, 6).
python_function('tests/test_mcp_server.py', 'test_compare_scans_returns_summary', 0, 5, 9).
python_function('tests/test_mcp_server.py', 'test_check_project_detects_threshold_violation', 0, 4, 6).
python_function('tests/test_mcp_server.py', 'test_unknown_tool_returns_error', 0, 2, 1).
python_function('tests/test_models.py', 'test_fragment_line_count', 0, 2, 1).
python_function('tests/test_models.py', 'test_group_saved_lines', 0, 4, 2).
python_function('tests/test_models.py', 'test_group_single_occurrence_no_savings', 0, 2, 2).
python_function('tests/test_models.py', 'test_group_impact_score', 0, 2, 2).
python_function('tests/test_models.py', 'test_duplication_map_sorted_by_impact', 0, 3, 4).
python_function('tests/test_models.py', 'test_duplication_map_totals', 0, 4, 3).
python_function('tests/test_models.py', 'test_scan_config_defaults', 0, 5, 1).
python_function('tests/test_pipeline.py', '_create_test_project', 1, 1, 1).
python_function('tests/test_pipeline.py', 'test_analyze_finds_duplicates', 0, 8, 6).
python_function('tests/test_pipeline.py', 'test_analyze_generates_suggestions', 0, 4, 6).
python_function('tests/test_pipeline.py', 'test_analyze_empty_project', 0, 4, 4).
python_function('tests/test_pipeline.py', 'test_analyze_no_duplicates', 0, 2, 5).
python_function('tests/test_pipeline.py', 'test_analyze_optimized_stores_incremental_cache', 0, 3, 10).
python_function('tests/test_planfile_integration.py', 'create_test_duplication_map', 0, 1, 3).
python_function('tests/test_planner.py', 'test_generate_suggestions_basic', 0, 6, 5).
python_function('tests/test_planner.py', 'test_no_suggestions_for_single_occurrence', 0, 2, 5).
python_function('tests/test_planner.py', 'test_priority_ordering', 0, 4, 5).
python_function('tests/test_planner.py', 'test_large_block_extract_module', 0, 2, 4).
python_function('tests/test_quality_commands.py', 'test_read_jscpd_stats', 1, 4, 3).
python_function('tests/test_quality_commands.py', 'test_budget_violations', 0, 3, 2).
python_function('tests/test_quality_commands.py', 'test_run_jscpd_budget_invokes_fallback_and_reads_report', 2, 3, 10).
python_function('tests/test_quality_commands.py', 'test_quality_jscpd_cli_uses_packaged_command', 1, 3, 5).
python_function('tests/test_reporters.py', '_sample_map', 0, 1, 4).
python_function('tests/test_reporters.py', 'test_json_reporter_valid_json', 0, 6, 4).
python_function('tests/test_reporters.py', 'test_json_reporter_with_suggestions', 0, 3, 5).
python_function('tests/test_reporters.py', 'test_toon_reporter_header', 0, 4, 3).
python_function('tests/test_reporters.py', 'test_toon_reporter_contains_fragments', 0, 4, 2).
python_function('tests/test_reporters.py', 'test_yaml_reporter_valid', 0, 4, 2).
python_function('tests/test_reporters.py', 'test_empty_map_json', 0, 3, 3).
python_function('tests/test_reporters.py', 'test_empty_map_toon', 0, 2, 2).
python_function('tests/test_reporters.py', '_rich_map', 0, 1, 5).
python_function('tests/test_reporters.py', 'test_toon_hotspots', 0, 4, 2).
python_function('tests/test_reporters.py', 'test_toon_dependency_risk', 0, 4, 2).
python_function('tests/test_reporters.py', 'test_toon_quick_wins', 0, 3, 2).
python_function('tests/test_reporters.py', 'test_toon_effort_estimate', 0, 4, 2).
python_function('tests/test_reporters.py', 'test_toon_empty_map_no_new_sections', 0, 5, 2).
python_function('tests/test_reporters.py', 'test_toon_single_package_no_dependency_risk', 0, 2, 5).
python_function('tests/test_scanner.py', 'test_should_exclude_git', 0, 2, 2).
python_function('tests/test_scanner.py', 'test_should_exclude_venv', 0, 2, 2).
python_function('tests/test_scanner.py', 'test_should_not_exclude_normal', 0, 2, 2).
python_function('tests/test_scanner.py', 'test_is_test_file', 0, 4, 2).
python_function('tests/test_scanner.py', 'test_extract_function_blocks_python', 0, 5, 1).
python_function('tests/test_scanner.py', 'test_extract_function_blocks_syntax_error', 0, 2, 1).
python_function('tests/test_scanner.py', 'test_scan_project_real_dir', 0, 6, 6).
python_function('tests/test_scanner.py', 'test_scan_project_target_files_only', 0, 5, 5).
python_function('tests/test_scanner.py', 'test_scan_project_target_files_does_not_walk_tree', 1, 3, 7).

% ── Python Classes ───────────────────────────────────────
python_class('src/redup/cli_app/quality_commands.py', 'JscpdStats').
python_class('src/redup/config.py', 'RedupConfig').
python_method('RedupConfig', '_env_name', 2, 1, 0).
python_method('RedupConfig', '_load_from_env', 1, 9, 9).
python_method('RedupConfig', 'reload', 2, 6, 6).
python_method('RedupConfig', 'get', 3, 2, 2).
python_method('RedupConfig', 'set', 3, 2, 3).
python_class('src/redup/core/cache.py', 'HashCache').
python_method('HashCache', '__init__', 1, 1, 4).
python_method('HashCache', '_init_tables', 0, 1, 2).
python_method('HashCache', '_get_file_hash', 2, 1, 3).
python_method('HashCache', 'is_file_unchanged', 2, 4, 5).
python_method('HashCache', 'get_cached_block_hashes', 2, 5, 5).
python_method('HashCache', 'store_file_hashes', 3, 4, 8).
python_method('HashCache', 'cleanup_old_entries', 1, 2, 3).
python_method('HashCache', 'get_stats', 0, 3, 3).
python_class('src/redup/core/community.py', 'CodeCommunity').
python_class('src/redup/core/comparator.py', 'CrossProjectMatch').
python_class('src/redup/core/comparator.py', 'CrossProjectComparison').
python_method('CrossProjectComparison', 'total_matches', 0, 1, 1).
python_method('CrossProjectComparison', 'shared_loc_potential', 0, 2, 2).
python_class('src/redup/core/decision.py', 'RefactorDecision').
python_class('src/redup/core/decision.py', 'DecisionRecommendation').
python_class('src/redup/core/differ.py', 'DiffResult').
python_class('src/redup/core/fuzzy_similarity.py', 'ComponentSignature').
python_class('src/redup/core/fuzzy_similarity.py', 'HTMLComponentExtractor').
python_method('HTMLComponentExtractor', '__init__', 0, 2, 2).
python_method('HTMLComponentExtractor', 'extract_component_signature', 1, 2, 6).
python_method('HTMLComponentExtractor', '_normalize_html', 1, 1, 4).
python_method('HTMLComponentExtractor', '_normalize_class_name', 1, 7, 4).
python_method('HTMLComponentExtractor', '_detect_component_type', 1, 3, 2).
python_method('HTMLComponentExtractor', '_extract_attributes', 1, 4, 7).
python_method('HTMLComponentExtractor', '_extract_text_content', 1, 1, 3).
python_method('HTMLComponentExtractor', '_compute_structure_hash', 1, 2, 4).
python_class('src/redup/core/fuzzy_similarity.py', 'CSSComponentExtractor').
python_method('CSSComponentExtractor', '__init__', 0, 2, 2).
python_method('CSSComponentExtractor', 'extract_component_signature', 1, 2, 4).
python_method('CSSComponentExtractor', '_extract_css_properties', 1, 4, 4).
python_method('CSSComponentExtractor', '_normalize_css_value', 1, 8, 6).
python_method('CSSComponentExtractor', '_detect_css_component_type', 1, 10, 5).
python_method('CSSComponentExtractor', '_compute_css_hash', 1, 2, 5).
python_class('src/redup/core/fuzzy_similarity.py', 'FuzzySimilarityDetector').
python_method('FuzzySimilarityDetector', '__init__', 1, 2, 3).
python_method('FuzzySimilarityDetector', 'find_similar_components', 1, 6, 4).
python_method('FuzzySimilarityDetector', '_extract_signature', 1, 5, 6).
python_method('FuzzySimilarityDetector', '_compute_similarity', 2, 7, 4).
python_method('FuzzySimilarityDetector', '_compute_attribute_similarity', 2, 9, 6).
python_method('FuzzySimilarityDetector', '_compute_css_similarity', 2, 1, 1).
python_class('src/redup/core/hash_cache.py', 'HashCache').
python_method('HashCache', '__init__', 1, 2, 2).
python_method('HashCache', '_load', 0, 3, 3).
python_method('HashCache', 'save', 0, 2, 2).
python_method('HashCache', 'get_file_hash', 1, 2, 4).
python_method('HashCache', 'is_unchanged', 2, 3, 3).
python_method('HashCache', 'update', 3, 2, 4).
python_method('HashCache', 'invalidate', 1, 2, 2).
python_method('HashCache', 'get_cached_results', 1, 2, 2).
python_method('HashCache', 'clear', 0, 2, 2).
python_class('src/redup/core/hasher.py', 'HashedBlock').
python_class('src/redup/core/hasher.py', 'HashIndex').
python_class('src/redup/core/lazy_grouper.py', 'DuplicateGroupCollector').
python_method('DuplicateGroupCollector', '__init__', 3, 1, 0).
python_method('DuplicateGroupCollector', 'collect', 1, 7, 2).
python_method('DuplicateGroupCollector', 'collect_sorted', 1, 1, 2).
python_class('src/redup/core/lsh_matcher.py', '_SimpleMinHash').
python_method('_SimpleMinHash', '__init__', 2, 2, 8).
python_method('_SimpleMinHash', 'jaccard', 1, 4, 3).
python_class('src/redup/core/lsh_matcher.py', 'LSHIndex').
python_method('LSHIndex', '__init__', 2, 2, 1).
python_method('LSHIndex', 'add', 1, 4, 6).
python_method('LSHIndex', 'find_near_duplicates', 1, 10, 8).
python_method('LSHIndex', '_find_near_duplicates_simple', 1, 4, 6).
python_method('LSHIndex', 'find_all_near_duplicates', 1, 8, 5).
python_class('src/redup/core/matcher.py', 'MatchResult').
python_class('src/redup/core/models.py', 'DuplicateType').
python_class('src/redup/core/models.py', 'RefactorAction').
python_class('src/redup/core/models.py', 'RiskLevel').
python_class('src/redup/core/models.py', 'ScanConfig').
python_class('src/redup/core/models.py', 'DuplicateFragment').
python_method('DuplicateFragment', 'line_count', 0, 1, 0).
python_class('src/redup/core/models.py', 'DuplicateGroup').
python_method('DuplicateGroup', 'occurrences', 0, 1, 1).
python_method('DuplicateGroup', 'total_lines', 0, 2, 0).
python_method('DuplicateGroup', 'saved_lines_potential', 0, 2, 0).
python_method('DuplicateGroup', 'impact_score', 0, 1, 1).
python_class('src/redup/core/models.py', 'RefactorSuggestion').
python_class('src/redup/core/models.py', 'ScanStats').
python_class('src/redup/core/models.py', 'DuplicationMap').
python_method('DuplicationMap', 'total_groups', 0, 1, 1).
python_method('DuplicationMap', 'total_fragments', 0, 2, 1).
python_method('DuplicationMap', 'total_saved_lines', 0, 2, 1).
python_method('DuplicationMap', 'sorted_by_impact', 0, 1, 1).
python_class('src/redup/core/python_parser.py', 'ParsedFunction').
python_class('src/redup/core/refactor_advisor.py', 'RefactorTask').
python_class('src/redup/core/refactor_advisor.py', 'RefactorPlan').
python_class('src/redup/core/scanner_cache.py', 'MemoryFileCache').
python_method('MemoryFileCache', '__init__', 1, 1, 0).
python_method('MemoryFileCache', '_estimate_size', 1, 1, 1).
python_method('MemoryFileCache', 'get_file_content', 1, 6, 4).
python_method('MemoryFileCache', '_evict_oldest', 1, 3, 6).
python_class('src/redup/core/scanner_types.py', 'CodeBlock').
python_method('CodeBlock', 'line_count', 0, 1, 0).
python_class('src/redup/core/scanner_types.py', 'ScannedFile').
python_method('ScannedFile', 'line_count', 0, 1, 1).
python_class('src/redup/core/scanner_types.py', 'ScanStrategy').
python_class('src/redup/core/semantic.py', 'SemanticMatch').
python_class('src/redup/core/semantic.py', 'SemanticDetector').
python_method('SemanticDetector', '__init__', 2, 1, 0).
python_method('SemanticDetector', '_ensure_model', 0, 3, 2).
python_method('SemanticDetector', 'find_semantic_duplicates', 2, 9, 13).
python_method('SemanticDetector', 'find_semantic_duplicates_fast', 2, 7, 7).
python_method('SemanticDetector', 'compute_semantic_similarity', 2, 1, 5).
python_class('src/redup/core/ts_extractor/config.py', 'LanguageRegistry').
python_method('LanguageRegistry', '__init__', 0, 1, 0).
python_method('LanguageRegistry', 'get_language', 1, 4, 3).
python_class('src/redup/core/universal_fuzzy.py', 'UniversalSignature').
python_class('src/redup/core/universal_fuzzy.py', 'UniversalFuzzyExtractor').
python_method('UniversalFuzzyExtractor', '__init__', 0, 2, 2).
python_method('UniversalFuzzyExtractor', 'extract_universal_signature', 1, 1, 9).
python_method('UniversalFuzzyExtractor', '_detect_language', 1, 1, 3).
python_method('UniversalFuzzyExtractor', '_normalize_code', 2, 1, 4).
python_method('UniversalFuzzyExtractor', '_remove_comments', 2, 1, 2).
python_method('UniversalFuzzyExtractor', '_normalize_identifiers', 2, 5, 1).
python_method('UniversalFuzzyExtractor', '_detect_component_type', 2, 3, 3).
python_method('UniversalFuzzyExtractor', '_extract_semantic_patterns', 2, 3, 4).
python_method('UniversalFuzzyExtractor', '_extract_metadata', 2, 11, 3).
python_method('UniversalFuzzyExtractor', '_compute_complexity', 2, 1, 5).
python_method('UniversalFuzzyExtractor', '_compute_structure_hash', 1, 1, 2).
python_class('src/redup/core/universal_fuzzy.py', 'UniversalFuzzyDetector').
python_method('UniversalFuzzyDetector', '__init__', 1, 2, 2).
python_method('UniversalFuzzyDetector', 'find_similar_components', 1, 6, 4).
python_method('UniversalFuzzyDetector', '_compute_universal_similarity', 2, 4, 3).
python_method('UniversalFuzzyDetector', '_compute_pattern_similarity', 2, 6, 2).
python_method('UniversalFuzzyDetector', '_compute_metadata_similarity', 2, 9, 6).
python_class('src/redup/core/utils/diff_helpers.py', '_MatchResult').
python_class('src/redup/core/utils/diff_helpers.py', 'GroupMatcher').
python_method('GroupMatcher', '__init__', 2, 1, 0).
python_method('GroupMatcher', '_match_exact_ids', 3, 4, 6).
python_method('GroupMatcher', '_get_remaining_groups', 2, 5, 2).
python_method('GroupMatcher', '_find_best_match', 3, 5, 3).
python_method('GroupMatcher', '_match_similar_groups', 3, 3, 5).
python_method('GroupMatcher', '_ensure_matches', 0, 2, 3).
python_method('GroupMatcher', '_match_score', 2, 6, 6).
python_method('GroupMatcher', 'get_resolved_groups', 0, 5, 2).
python_method('GroupMatcher', 'get_new_groups', 0, 5, 2).
python_method('GroupMatcher', 'get_unchanged_groups', 0, 3, 1).
python_class('src/redup/core/utils/diff_helpers.py', 'DiffCalculator').
python_method('DiffCalculator', 'calculate_diff_stats', 3, 4, 3).
python_class('src/redup/core/utils/function_extractor.py', 'FunctionExtractor').
python_method('FunctionExtractor', '__init__', 3, 1, 0).
python_method('FunctionExtractor', 'extract_functions', 3, 1, 5).
python_method('FunctionExtractor', '_create_function_block', 3, 2, 4).
python_method('FunctionExtractor', '_create_method_block', 4, 2, 4).
python_class('src/redup/core/utils/language_dispatcher.py', 'LanguageDispatcher').
python_method('LanguageDispatcher', '__init__', 0, 1, 0).
python_method('LanguageDispatcher', 'register_extractor', 2, 1, 0).
python_method('LanguageDispatcher', 'register_group', 2, 1, 0).
python_method('LanguageDispatcher', 'get_extractor', 1, 4, 2).
python_method('LanguageDispatcher', 'extract_functions', 4, 2, 2).
python_class('src/redup/integrations/planfile_integration.py', 'TaskConfig').
python_class('src/redup/integrations/planfile_integration.py', 'DuplicateTask').
python_class('src/redup/integrations/planfile_integration.py', 'DuplicateTaskExporter').
python_method('DuplicateTaskExporter', '__init__', 1, 2, 1).
python_method('DuplicateTaskExporter', 'export', 2, 4, 4).
python_method('DuplicateTaskExporter', '_generate_tasks', 1, 3, 3).
python_method('DuplicateTaskExporter', '_create_task_from_group', 1, 12, 5).
python_method('DuplicateTaskExporter', '_build_description', 3, 7, 3).
python_method('DuplicateTaskExporter', '_render_todo_md', 0, 11, 11).
python_method('DuplicateTaskExporter', '_sync_to_backend', 0, 6, 3).
python_class('src/redup/reporters/enhanced_reporter.py', 'EnhancedReporter').
python_method('EnhancedReporter', '__init__', 1, 1, 0).
python_method('EnhancedReporter', 'generate_metrics_report', 0, 1, 6).
python_method('EnhancedReporter', '_get_scan_metrics', 0, 1, 1).
python_method('EnhancedReporter', '_get_duplication_metrics', 0, 7, 6).
python_method('EnhancedReporter', '_get_language_metrics', 0, 7, 7).
python_method('EnhancedReporter', '_get_file_metrics', 0, 4, 7).
python_method('EnhancedReporter', '_get_complexity_metrics', 0, 5, 5).
python_method('EnhancedReporter', '_get_refactoring_metrics', 0, 8, 4).
python_method('EnhancedReporter', '_bucket_similarities', 1, 6, 2).
python_method('EnhancedReporter', '_bucket_group_sizes', 1, 5, 2).
python_method('EnhancedReporter', '_calculate_complexity_score', 0, 4, 1).
python_method('EnhancedReporter', 'generate_visualization_data', 0, 1, 4).
python_method('EnhancedReporter', '_get_duplication_chart_data', 0, 2, 4).
python_method('EnhancedReporter', '_get_language_chart_data', 0, 2, 4).
python_method('EnhancedReporter', '_get_file_chart_data', 0, 3, 2).
python_method('EnhancedReporter', '_get_timeline_data', 0, 1, 0).
python_method('EnhancedReporter', 'save_enhanced_report', 1, 2, 6).
python_class('tests/test_compare.py', 'TestFindHashMatches').
python_method('TestFindHashMatches', 'test_identical_blocks_detected', 0, 4, 3).
python_method('TestFindHashMatches', 'test_different_blocks_no_match', 0, 2, 3).
python_class('tests/test_compare.py', 'TestCompareProjects').
python_method('TestCompareProjects', 'test_shared_function_detected', 1, 8, 3).
python_method('TestCompareProjects', 'test_disjoint_projects_no_matches', 1, 2, 1).
python_class('tests/test_compare.py', 'TestCommunityDetection').
python_method('TestCommunityDetection', '_make_comparison', 1, 2, 5).
python_method('TestCommunityDetection', 'test_detect_communities_requires_networkx', 0, 3, 4).
python_method('TestCommunityDetection', 'test_no_matches_yields_no_communities', 0, 3, 4).
python_class('tests/test_compare.py', 'TestDecision').
python_method('TestDecision', 'test_keep_separate_when_no_overlap', 0, 3, 3).
python_method('TestDecision', 'test_merge_when_high_overlap', 0, 2, 4).
python_method('TestDecision', 'test_extract_shared_lib_moderate_overlap', 0, 2, 4).
python_class('tests/test_e2e.py', 'TestCLIInfo').
python_method('TestCLIInfo', 'test_info_shows_version', 0, 3, 1).
python_method('TestCLIInfo', 'test_info_shows_dependencies', 0, 2, 2).
python_class('tests/test_e2e.py', 'TestCLIScanToon').
python_method('TestCLIScanToon', 'test_scan_toon_stdout', 1, 5, 2).
python_method('TestCLIScanToon', 'test_scan_toon_to_file', 2, 5, 4).
python_method('TestCLIScanToon', 'test_scan_empty_project', 1, 3, 2).
python_method('TestCLIScanToon', 'test_scan_no_duplicates', 1, 3, 2).
python_class('tests/test_e2e.py', 'TestCLIScanJSON').
python_method('TestCLIScanJSON', 'test_scan_json_stdout_parseable', 1, 7, 10).
python_method('TestCLIScanJSON', 'test_scan_json_to_file', 2, 6, 5).
python_method('TestCLIScanJSON', 'test_json_contains_fragment_details', 2, 5, 4).
python_class('tests/test_e2e.py', 'TestCLIScanYAML').
python_method('TestCLIScanYAML', 'test_scan_yaml_to_file', 2, 5, 4).
python_class('tests/test_e2e.py', 'TestCLIScanAll').
python_method('TestCLIScanAll', 'test_format_all_creates_three_files', 2, 5, 3).
python_method('TestCLIScanAll', 'test_format_all_json_valid', 2, 2, 4).
python_method('TestCLIScanAll', 'test_format_all_toon_has_refactor', 2, 2, 3).
python_method('TestCLIScanAll', 'test_all_three_formats_consistent', 2, 3, 4).
python_class('tests/test_e2e.py', 'TestCLIOptions').
python_method('TestCLIOptions', 'test_custom_extensions', 1, 3, 4).
python_method('TestCLIOptions', 'test_min_lines_filter', 1, 3, 2).
python_method('TestCLIOptions', 'test_include_tests_flag', 1, 3, 4).
python_method('TestCLIOptions', 'test_incremental_flag_enables_cache', 1, 2, 1).
python_method('TestCLIOptions', 'test_changed_only_scans_modified_files', 1, 7, 12).
python_class('tests/test_e2e.py', 'TestPythonModule').
python_method('TestPythonModule', 'test_python_m_redup_info', 0, 3, 1).
python_method('TestPythonModule', 'test_python_m_redup_scan', 1, 3, 2).
python_class('tests/test_e2e.py', 'TestFullRoundtrip').
python_method('TestFullRoundtrip', 'test_roundtrip_json', 2, 6, 13).
python_method('TestFullRoundtrip', '_verify_json_structure', 1, 9, 0).
python_method('TestFullRoundtrip', '_verify_calculate_tax_group', 1, 15, 3).
python_method('TestFullRoundtrip', 'test_roundtrip_all_formats', 2, 8, 6).
python_method('TestFullRoundtrip', 'test_roundtrip_self_analysis', 0, 6, 9).
python_class('tests/test_planfile_integration.py', 'TestDuplicateTaskExporter').
python_method('TestDuplicateTaskExporter', 'test_init_default_config', 0, 4, 2).
python_method('TestDuplicateTaskExporter', 'test_init_custom_config', 0, 3, 3).
python_method('TestDuplicateTaskExporter', 'test_generate_tasks', 1, 6, 4).
python_method('TestDuplicateTaskExporter', 'test_create_task_difficulty_easy', 0, 2, 3).
python_method('TestDuplicateTaskExporter', 'test_create_task_difficulty_hard', 0, 2, 3).
python_method('TestDuplicateTaskExporter', 'test_export_creates_file', 1, 5, 6).
python_method('TestDuplicateTaskExporter', 'test_render_todo_md_structure', 1, 7, 4).
python_class('tests/test_planfile_integration.py', 'TestExportToPlanfile').
python_method('TestExportToPlanfile', 'test_export_to_planfile_creates_file', 1, 3, 3).
python_method('TestExportToPlanfile', 'test_export_to_planfile_with_backend', 1, 2, 2).
python_class('tests/test_planfile_integration.py', 'TestDuplicateTask').
python_method('TestDuplicateTask', 'test_task_creation', 0, 5, 1).
python_method('TestDuplicateTask', 'test_task_with_external_data', 0, 3, 1).
python_class('tests/test_ts_extractor.py', 'TestLanguageMapping').
python_method('TestLanguageMapping', 'test_language_mapping_has_common_extensions', 0, 7, 0).
python_method('TestLanguageMapping', 'test_language_mapping_has_new_web_languages', 0, 5, 0).
python_method('TestLanguageMapping', 'test_language_mapping_has_data_formats', 0, 7, 0).
python_method('TestLanguageMapping', 'test_language_mapping_has_sql', 0, 4, 0).
python_method('TestLanguageMapping', 'test_language_mapping_has_dsl_languages', 0, 11, 0).
python_method('TestLanguageMapping', 'test_language_mapping_has_additional_programming', 0, 10, 0).
python_method('TestLanguageMapping', 'test_language_mapping_count', 0, 2, 1).
python_class('tests/test_ts_extractor.py', 'TestLanguageRegistry').
python_method('TestLanguageRegistry', 'test_registry_has_core_languages', 0, 6, 0).
python_method('TestLanguageRegistry', 'test_registry_has_web_languages', 0, 5, 0).
python_method('TestLanguageRegistry', 'test_registry_has_new_languages', 0, 11, 0).
python_method('TestLanguageRegistry', 'test_registry_has_dsl_languages', 0, 6, 0).
python_method('TestLanguageRegistry', 'test_registry_has_data_formats', 0, 6, 0).
python_method('TestLanguageRegistry', 'test_registry_count', 0, 2, 1).
python_class('tests/test_ts_extractor.py', 'TestLanguageSupportFunctions').
python_method('TestLanguageSupportFunctions', 'test_is_language_supported_python', 0, 2, 1).
python_method('TestLanguageSupportFunctions', 'test_is_language_supported_unknown_extension', 0, 2, 1).
python_method('TestLanguageSupportFunctions', 'test_is_language_supported_known_languages', 0, 2, 1).
python_class('tests/test_ts_extractor.py', 'TestExtractFunctions').
python_method('TestExtractFunctions', 'test_extract_python_returns_empty', 0, 2, 1).
python_method('TestExtractFunctions', 'test_extract_unknown_extension_returns_empty', 0, 2, 1).
python_method('TestExtractFunctions', 'test_extract_javascript_no_treesitter', 0, 2, 2).
python_class('tests/test_ts_extractor.py', 'TestHTMLExtraction').
python_method('TestHTMLExtraction', 'test_html_extraction_structure', 0, 2, 1).
python_class('tests/test_ts_extractor.py', 'TestCSSExtraction').
python_method('TestCSSExtraction', 'test_css_extraction_structure', 0, 2, 1).
python_class('tests/test_ts_extractor.py', 'TestSQLExtraction').
python_method('TestSQLExtraction', 'test_sql_extraction_structure', 0, 2, 1).
python_class('tests/test_ts_extractor.py', 'TestCExtraction').
python_method('TestCExtraction', 'test_c_extraction_structure', 0, 2, 1).
python_class('tests/test_ts_extractor.py', 'TestLuaExtraction').
python_method('TestLuaExtraction', 'test_lua_extraction_structure', 0, 2, 1).

% ── Dependencies ─────────────────────────────────────────

% ── Makefile Targets ─────────────────────────────────────

% ── Taskfile Tasks ───────────────────────────────────────
taskfile_task('', 'Install Python dependencies (editable)').
taskfile_task('', 'Run pytest suite').
taskfile_task('', 'Run ruff lint check').
taskfile_task('', 'Run jscpd duplicate-code budget').
taskfile_task('', 'Run lint and duplicate-code gates').
taskfile_task('', 'Auto-format with ruff').
taskfile_task('', 'Build wheel + sdist').
taskfile_task('', 'Remove build artefacts').
taskfile_task('', '[from doql] workflow: health').
taskfile_task('', 'Run install, lint, test').
taskfile_task('', 'Show available tasks').
taskfile_task('', 'Auto-format with ruff (alias of fmt)').
taskfile_task('', 'Generate SUMD (Structured Unified Markdown Descriptor) for AI-aware project description').
taskfile_task('', 'Generate SUMR (Summary Report) with project metrics and health status').

% ── Environment Variables ────────────────────────────────
env_variable('OPENROUTER_API_KEY', '*(not set)*', 'Required: OpenRouter API key (https://openrouter.ai/keys)').
env_variable('LLM_MODEL', 'openrouter/qwen/qwen3-coder-next', 'Model (default: openrouter/qwen/qwen3-coder-next)').
env_variable('PFIX_AUTO_APPLY', 'true', 'true = apply fixes without asking').
env_variable('PFIX_AUTO_INSTALL_DEPS', 'true', 'true = auto pip/uv install').
env_variable('PFIX_AUTO_RESTART', 'false', 'true = os.execv restart after fix').
env_variable('PFIX_MAX_RETRIES', '3', '').
env_variable('PFIX_DRY_RUN', 'false', '').
env_variable('PFIX_ENABLED', 'true', '').
env_variable('PFIX_GIT_COMMIT', 'false', 'true = auto-commit fixes').
env_variable('PFIX_GIT_PREFIX', 'pfix:', 'commit message prefix').
env_variable('PFIX_CREATE_BACKUPS', 'false', 'false = disable .pfix_backups/ directory').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-cli-tests.testql.toon.yaml', 'cli').
testql_scenario('generated-from-pytests.testql.toon.yaml', 'integration').

% ── Semantic Facts from SUMD.md ──────────────────────────
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-cli-tests.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-from-pytests.testql.toon.yaml', 'testql').
sumd_declared_file('Taskfile.yml', 'taskfile').
sumd_declared_file('pyqual.yaml', 'pyqual').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
sumd_interface('cli', 'argparse').
sumd_interface('cli', '').
sumd_workflow('install', 'manual').
sumd_workflow_step('install', 1, 'pip install -e .[dev]').
sumd_workflow('test', 'manual').
sumd_workflow_step('test', 1, 'pytest -q').
sumd_workflow('lint', 'manual').
sumd_workflow_step('lint', 1, 'ruff check .').
sumd_workflow('jscpd', 'manual').
sumd_workflow_step('jscpd', 1, 'PYTHONPATH=src python -m redup quality jscpd').
sumd_workflow('quality', 'manual').
sumd_workflow_step('quality', 1, 'taskfile run lint').
sumd_workflow_step('quality', 2, 'taskfile run jscpd').
sumd_workflow('fmt', 'manual').
sumd_workflow_step('fmt', 1, 'ruff format .').
sumd_workflow('build', 'manual').
sumd_workflow_step('build', 1, 'python -m build').
sumd_workflow('clean', 'manual').
sumd_workflow_step('clean', 1, 'rm -rf build/ dist/ *.egg-info').
sumd_workflow('health', 'manual').
sumd_workflow_step('health', 1, 'docker compose ps').
sumd_workflow_step('health', 2, 'docker compose exec app echo "Health check passed"').
sumd_workflow('all', 'manual').
sumd_workflow_step('all', 1, 'taskfile run install').
sumd_workflow_step('all', 2, 'taskfile run lint').
sumd_workflow_step('all', 3, 'taskfile run test').
sumd_workflow('help', 'manual').
sumd_workflow_step('help', 1, 'echo "redup — available tasks:"').
sumd_workflow_step('help', 2, 'echo ""').
sumd_workflow_step('help', 3, 'taskfile list').
sumd_workflow('format', 'manual').
sumd_workflow_step('format', 1, 'ruff format .').
sumd_workflow('sumd', 'manual').
sumd_workflow('sumr', 'manual').
```

## Call Graph

*260 nodes · 307 edges · 62 modules · CC̄=3.8*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `to_markdown` *(in src.redup.reporters.markdown_reporter)* | 12 ⚠ | 3 | 54 | **57** |
| `to_code2llm_context` *(in src.redup.reporters.code2llm_reporter)* | 11 ⚠ | 3 | 36 | **39** |
| `tasks` *(in src.redup.cli_app.tasks_command)* | 14 ⚠ | 0 | 35 | **35** |
| `initialize_language_dispatcher` *(in src.redup.core.ts_extractor.dispatcher)* | 2 | 1 | 31 | **32** |
| `scan_project` *(in src.redup.core.scanner)* | 5 | 11 | 20 | **31** |
| `set` *(in src.redup.config.RedupConfig)* | 2 | 27 | 3 | **30** |
| `benchmark` *(in benchmarks.bench_libraries)* | 10 ⚠ | 0 | 27 | **27** |
| `benchmark_sequential_vs_parallel` *(in benchmark)* | 3 | 0 | 26 | **26** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/redup
# generated in 0.28s
# nodes: 260 | edges: 307 | modules: 62
# CC̄=3.8

HUBS[20]:
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
  src.redup.config.RedupConfig.set
    CC=2  in:27  out:3  total:30
  benchmarks.bench_libraries.benchmark
    CC=10  in:0  out:27  total:27
  benchmark.benchmark_sequential_vs_parallel
    CC=3  in:0  out:26  total:26
  src.redup.cli_app.output_writer.write_results
    CC=12  in:1  out:25  total:26
  src.redup.core.pipeline.analyze_optimized
    CC=11  in:2  out:23  total:25
  src.redup.mcp.handlers._build_scan_config
    CC=12  in:1  out:24  total:25
  src.redup.cli_app.scan_commands.config_command
    CC=5  in:1  out:23  total:24
  src.redup.core.config.config_to_scan_config
    CC=4  in:5  out:18  total:23
  src.redup.core.differ._load_duplication_map
    CC=5  in:2  out:21  total:23
  examples.01_basic_usage.main
    CC=5  in:0  out:23  total:23
  src.redup.core.refactor_advisor._parse_llm_response
    CC=9  in:1  out:21  total:22
  src.redup.core.community.detect_communities
    CC=11  in:1  out:20  total:21
  src.redup.core.refactor_advisor.format_plan_markdown
    CC=8  in:1  out:20  total:21
  src.redup.cli_app.compare_command._print_summary_table
    CC=1  in:1  out:20  total:21
  src.redup.cli_app.scan_commands.check_command
    CC=6  in:1  out:19  total:20

MODULES:
  benchmark  [2 funcs]
    benchmark_feature_performance  CC=3  out:15
    benchmark_sequential_vs_parallel  CC=3  out:26
  benchmarks.bench_libraries  [2 funcs]
    benchmark  CC=10  out:27
    generate_test_project  CC=3  out:5
  examples.01_basic_usage  [1 funcs]
    main  CC=5  out:23
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
    build_config_with_file_support  CC=10  out:4
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
  src.redup.cli_app.quality_commands  [7 funcs]
    _budget_violations  CC=3  out:2
    _jscpd_command  CC=4  out:4
    _read_jscpd_stats  CC=1  out:11
    _repo_root  CC=2  out:4
    jscpd  CC=8  out:16
    jscpd_run  CC=2  out:8
    run_jscpd_budget  CC=5  out:16
  src.redup.cli_app.scan_commands  [4 funcs]
    check_command  CC=6  out:19
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
    build_hash_index_with_cache  CC=9  out:9
    hash_block_with_cache  CC=5  out:5
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
  src.redup.core.differ  [8 funcs]
    _format_assessment  CC=3  out:0
    _format_group_details  CC=3  out:2
    _format_group_header  CC=1  out:0
    _format_groups_section  CC=3  out:5
    _group_by_id  CC=2  out:0
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
  src.redup.core.pipeline  [4 funcs]
    _build_duplication_map  CC=2  out:5
    analyze  CC=2  out:5
    analyze_optimized  CC=11  out:23
    analyze_parallel  CC=2  out:12
  src.redup.core.pipeline.duplicate_finder  [6 funcs]
    _finalize_duplicate_groups  CC=2  out:7
    find_duplicates_phase_lazy  CC=5  out:10
    find_duplicates_phase_optimized  CC=1  out:5
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
    _collect_files  CC=12  out:15
    _collect_target_files  CC=13  out:17
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
  src.redup.mcp.handlers  [12 funcs]
    _build_scan_config  CC=12  out:24
    _check_thresholds  CC=3  out:7
    _estimate_code2llm_counts  CC=5  out:6
    _format_analysis_result  CC=7  out:15
    _get_optional_deps  CC=3  out:2
    _run_analysis  CC=7  out:17
    _scan_config_payload  CC=1  out:1
    handle_analyze_project  CC=3  out:12
    handle_check_project  CC=3  out:14
    handle_compare_scans  CC=1  out:7
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
  src.redup.reporters.json_reporter  [4 funcs]
    _group_to_dict  CC=5  out:4
    _suggestion_to_dict  CC=1  out:0
    duplication_map_to_dict  CC=3  out:4
    to_json  CC=1  out:2
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
    to_yaml  CC=2  out:3

EDGES:
  benchmark.benchmark_sequential_vs_parallel → src.redup.core.pipeline.analyze
  benchmark.benchmark_feature_performance → src.redup.core.pipeline.analyze_parallel
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
  src.redup.core.lazy_grouper.find_exact_duplicates_lazy → src.redup.core.lazy_grouper._create_duplicate_group
  src.redup.core.lazy_grouper.find_exact_duplicates_lazy → src.redup.core.hasher._blocks_from_different_locations
  src.redup.core.lazy_grouper.find_structural_duplicates_lazy → src.redup.core.lazy_grouper._create_duplicate_group
  src.redup.core.lazy_grouper.find_structural_duplicates_lazy → src.redup.core.hasher._blocks_from_different_locations
  src.redup.core.lazy_grouper.find_all_duplicates_lazy → src.redup.core.lazy_grouper.find_exact_duplicates_lazy
  src.redup.core.lazy_grouper.find_all_duplicates_lazy → src.redup.core.lazy_grouper.find_structural_duplicates_lazy
  src.redup.core.config._get_config_from_pyproject → src.redup.core.config._load_toml_file
  src.redup.core.config._get_config_from_redup_toml → src.redup.core.config._load_toml_file
  src.redup.core.config.load_config → src.redup.core.config._get_config_from_redup_toml
  src.redup.core.config.load_config → src.redup.core.config._get_config_from_pyproject
  src.redup.core.planner._suggest_module_name → src.redup.core.planner._common_prefix
  src.redup.core.planner.generate_suggestions → src.redup.core.planner._choose_action
  src.redup.core.planner.generate_suggestions → src.redup.core.planner._suggest_module_name
  src.redup.core.planner.generate_suggestions → src.redup.core.planner._assess_risk
  src.redup.core.scanner_utils._read_file_safe → src.redup.core.scanner_utils._read_file_with_mmap
  src.redup.core.scanner_utils._load_files_simple → src.redup.core.scanner_utils._read_file_safe
  src.redup.core.scanner_utils._load_files_with_progress → src.redup.core.scanner_utils._read_file_safe
  src.redup.core.scanner_utils._load_all_files → src.redup.core.scanner_utils._load_files_with_progress
  src.redup.core.scanner_utils._load_all_files → src.redup.core.scanner_utils._load_files_simple
  src.redup.core.scanner_utils._preload_files → src.redup.core.scanner_utils._print_load_result
  src.redup.core.scanner_utils._preload_files → src.redup.core.scanner_utils._load_all_files
  src.redup.core.scanner_utils._preload_files → src.redup.core.scanner_utils._load_files_simple
  examples.01_basic_usage.main → src.redup.core.pipeline.analyze
  src.redup.core.hasher._normalize_ast_text → src.redup.core.hasher._ast_to_normalized_string
  src.redup.core.hasher._normalize_ast_text → src.redup.core.hasher._normalize_text
  src.redup.core.hasher._hash_text → src.redup.core.hasher._fast_hash
  src.redup.core.hasher.hash_block → src.redup.core.hasher._hash_text
  src.redup.core.hasher.hash_block_structural → src.redup.core.hasher._hash_text
  src.redup.core.hasher._hashed_block → src.redup.core.hasher.hash_block
  src.redup.core.hasher._hashed_block → src.redup.core.hasher.hash_block_structural
  src.redup.core.hasher._find_duplicates → src.redup.core.hasher._blocks_from_different_locations
  src.redup.core.hasher.build_hash_index → src.redup.core.hasher._hashed_block
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

### Integration (1)

**`Auto-generated from Python Tests`**

## Intent

Code duplication analyzer and refactoring planner for LLMs
