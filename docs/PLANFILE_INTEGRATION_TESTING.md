# Planfile Integration Testing Guide

This guide explains how to test the redup + planfile integration for creating tasks from code duplications.

## Prerequisites

### Option 1: Local Testing Only (No Sync)
```bash
# Just redup is enough
pip install -e ".[dev]"
```

### Option 2: With GitHub/GitLab/Jira Sync
```bash
# Install with planfile support
pip install -e ".[tasks]"

# Or install planfile separately
pip install planfile>=0.4.0
```

## Quick Test - Local Export Only

### 1. Basic TODO.md Generation

```bash
# Analyze current directory and export to TODO.md
cd /path/to/your/project
redup tasks . --output TODO.md
```

**Expected Output:**
```
Analyzing /path/to/your/project for duplications...
✓ Found 9 duplicate groups
✓ Potential savings: 158 lines
✓ Exported 9 tasks to TODO.md
```

### 2. Preview Without Creating Files (Dry Run)

```bash
redup tasks . --dry-run
```

**Expected Output:**
```
Tasks Preview
┏━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┓
┃ # ┃ Priority ┃ Title                           ┃ Difficulty ┃ Savings ┃
┡━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━┩
│ 1 │ critical ┃ Refactor: process_file (2x dup) ┃ 🟡 medium  │   47L   │
│ 2 │ major    ┃ Refactor: validate (3x dup)     ┃ 🟢 easy    │   23L   │
└───┴──────────┴─────────────────────────────────┴────────────┴─────────┘

Total: 9 tasks
```

## Testing with GitHub Sync

### 1. Configure Environment Variables

Create `.env` file or export directly:

```bash
# GitHub Configuration
export GITHUB_TOKEN="ghp_your_personal_access_token"
export GITHUB_REPO="your-username/your-repo"
export GITHUB_MILESTONE="Sprint 1"  # optional
```

**How to get GitHub Token:**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `write:issues`, `write:discussions`
4. Generate and copy token

### 2. Run with GitHub Sync

```bash
redup tasks . \
  --backend github \
  --milestone "Code Quality Sprint" \
  --output TODO.md
```

**Expected Output:**
```
Analyzing . for duplications...
✓ Found 9 duplicate groups
✓ Exported 9 tasks to TODO.md
✓ Syncing with github...
✓ Synced 9 tasks to github
```

### 3. Verify in GitHub

- Go to: `https://github.com/your-username/your-repo/issues`
- You should see new issues created for each duplication
- Issues will have labels: `refactoring`, `duplication`
- Milestone will be set if configured

## Testing with GitLab Sync

### 1. Configure Environment Variables

```bash
# GitLab Configuration
export GITLAB_TOKEN="glpat-your-personal-access-token"
export GITLAB_URL="https://gitlab.com/api/v4"  # or your self-hosted URL
export GITLAB_PROJECT_ID="12345678"  # or "namespace/project-name"
```

**How to get GitLab Token:**
1. Go to: https://gitlab.com/-/profile/personal_access_tokens
2. Create token with scopes: `api`, `write_repository`
3. Copy the token

### 2. Run with GitLab Sync

```bash
redup tasks . \
  --backend gitlab \
  --milestone "Sprint 42" \
  --output TODO.md
```

### 3. Verify in GitLab

- Go to: `https://gitlab.com/your-namespace/your-project/-/issues`
- New issues should be created for each duplication

## Testing with Jira Sync

### 1. Configure Environment Variables

```bash
# Jira Configuration
export JIRA_SERVER="https://your-domain.atlassian.net"
export JIRA_USERNAME="your-email@company.com"
export JIRA_API_TOKEN="your-api-token"
export JIRA_PROJECT_KEY="PROJ"
```

**How to get Jira API Token:**
1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Create API token
3. Copy the token

### 2. Run with Jira Sync

```bash
redup tasks . \
  --backend jira \
  --milestone "Q1 Technical Debt" \
  --output TODO.md
```

## Python API Testing

### Test 1: Basic Export

```python
from pathlib import Path
import redup
from redup.integrations.planfile_integration import (
    DuplicateTaskExporter,
    TaskConfig,
)

# Analyze project
config = redup.ScanConfig(
    root=Path("./my-project"),
    extensions=(".py",),
    min_block_lines=5,
)
result = redup.analyze(config)

# Export to TODO.md
exporter_config = TaskConfig(todo_file=Path("TODO.md"))
exporter = DuplicateTaskExporter(exporter_config)
output_path = exporter.export(result)

print(f"✓ Created: {output_path}")
print(f"✓ Tasks: {len(exporter.tasks)}")
print(f"✓ Total savings: {sum(t.lines_saved for t in exporter.tasks)} lines")
```

### Test 2: With Custom Labels

```python
exporter_config = TaskConfig(
    todo_file=Path("TODO.md"),
    sync_backend="github",
    sync_enabled=True,
    milestone="Sprint 1",
    labels=["technical-debt", "refactoring", "duplicate"],
)
```

### Test 3: Access Task Details

```python
for task in exporter.tasks:
    print(f"Title: {task.title}")
    print(f"Priority: {task.priority}")  # critical/major/minor
    print(f"Difficulty: {task.difficulty}")  # easy/medium/hard
    print(f"Files: {len(task.files)}")
    print(f"Savings: {task.lines_saved} lines")
    print(f"Description: {task.description[:100]}...")
    print()
```

## Testing Different Scenarios

### Scenario 1: Large Project (50+ files)

```bash
# Use parallel scanning for large projects
redup tasks ./large-project \
  --parallel \
  --max-workers 4 \
  --output TODO.md
```

### Scenario 2: Multiple Languages

```bash
# Scan Python + JavaScript + TypeScript
redup tasks ./project \
  --ext ".py,.js,.ts" \
  --min-lines 3 \
  --output TODO.md
```

### Scenario 3: Function-Level Only (Faster)

```bash
# Skip sliding-window detection, only functions
redup tasks . --functions-only --output TODO.md
```

### Scenario 4: CI/CD Integration

```yaml
# .github/workflows/redup-tasks.yml
name: Create Refactoring Tasks

on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday
  workflow_dispatch:

jobs:
  create-tasks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install redup
        run: pip install "redup[tasks]"
      
      - name: Create tasks
        run: redup tasks . --backend github --milestone "Weekly Tech Debt"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Verifying TODO.md Content

### Check File Structure

```bash
head -50 TODO.md
```

Expected sections:
- `# TODO - Duplication Refactoring Tasks`
- `## CRITICAL (N tasks)`
- `## MAJOR (N tasks)`
- `## MINOR (N tasks)`
- `## Planfile Export Configuration`

### Check Individual Task

```bash
grep -A 10 "CRITICAL" TODO.md | head -15
```

Expected format:
```markdown
- [ ] **Refactor: function_name (2x duplication)** 🟡
   Priority: critical | Savings: 47L
   <details>
   <summary>Details</summary>
   ## Duplication Analysis
   ...
```

## Troubleshooting

### Issue: "planfile not installed"

```bash
pip install planfile>=0.4.0
# Or:
pip install -e ".[tasks]"
```

### Issue: "GITHUB_TOKEN not set"

```bash
export GITHUB_TOKEN="your-token"
# Or create .env file
echo "GITHUB_TOKEN=your-token" > .env
```

### Issue: "No duplications found"

```bash
# Lower the threshold
redup tasks . --min-lines 2 --min-sim 0.7
```

### Issue: Sync fails but TODO.md created

Check network connectivity and token permissions:
```bash
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

## Validation Checklist

- [ ] Local export creates TODO.md
- [ ] Dry-run shows task preview table
- [ ] TODO.md has all sections (CRITICAL, MAJOR, MINOR)
- [ ] Each task has checkbox, priority, difficulty emoji
- [ ] Task details include file list and description
- [ ] Planfile config section present at bottom
- [ ] With GitHub token, issues are created
- [ ] With GitLab token, issues are created
- [ ] Milestones are assigned correctly
- [ ] Labels are applied to issues

## Example Output Files

### TODO.md (Local)
```markdown
# TODO - Duplication Refactoring Tasks

Generated by [redup](https://github.com/semcod/redup)
Total tasks: 9
Total potential savings: 158 lines

## CRITICAL (2 tasks)

- [ ] **Refactor: process_file (2x duplication)** 🟡
   Priority: critical | Savings: 47L
   <details>
   <summary>Details</summary>
   ## Duplication Analysis
   
   - **Occurrences**: 2
   - **Lines per block**: 47
   - **Potential savings**: 47 lines
   - **Files affected**: 2
   - **Packages**: src
   
   ### Files
   - `src/core/scanner.py`
   - `src/core/planner.py`
   
   ### Suggested Action
   Extract function to a shared utility module.
   </details>

## Planfile Export Configuration

```yaml
tasks:
  - id: refactor_process_file_2x_duplication
    title: Refactor: process_file (2x duplication)
    priority: critical
    labels: ['refactoring', 'duplication']
    description: |
      ## Duplication Analysis
      ...
```
```

## Next Steps

After successful testing:

1. **Review tasks**: Open TODO.md and prioritize
2. **Create issues**: Use `--backend github` or `--backend gitlab`
3. **Assign work**: Add assignees in your issue tracker
4. **Track progress**: Update checkboxes as you complete tasks
5. **Re-run weekly**: Schedule in CI/CD to catch new duplications

For more info:
- [redup documentation](https://github.com/semcod/redup)
- [planfile documentation](https://github.com/semcod/planfile)
