# Proxy Project Refactoring Plan

## 🎯 Dashboard Functions Refactoring (114 lines recoverable)

### Current Pattern Analysis
The proxy project has 20 nearly identical dashboard endpoint functions in `src/proxym/api/frontend.py`:

```python
# Current duplicate pattern:
@router.get("/dashboard-hook.js")
async def dashboard_hook_js():
    """Serve the useDashboardData hook (plain JS, no Babel needed)."""
    return _serve_file(
        [os.path.join(_SRC_ROOT, "dashboard", "hooks", "useDashboardData.js")],
        _MIME_JS, _MIME_JS_UTF8,
    )

@router.get("/dashboard-formatters.js") 
async def dashboard_formatters_js():
    """Serve formatters utility (plain JS, no Babel needed)."""
    return _serve_file(
        [os.path.join(_SRC_ROOT, "dashboard", "utils", "formatters.js")],
        _MIME_JS, _MIME_JS_UTF8,
    )

# ... 18 more similar functions
```

### Refactored Solution

#### 1. Create Generic Dashboard Endpoint Function
```python
def _create_dashboard_endpoint(route: str, file_path: str, description: str):
    """Generic factory for dashboard JS/JSX endpoints."""
    @router.get(route)
    async def endpoint():
        """Serve dashboard component."""
        return _serve_file(
            [os.path.join(_SRC_ROOT, file_path)],
            _MIME_JS, _MIME_JS_UTF8,
        )
    endpoint.__doc__ = description
    return endpoint
```

#### 2. Configuration-Driven Registration
```python
# Dashboard endpoint configuration
DASHBOARD_ENDPOINTS = {
    "/dashboard-hook.js": ("dashboard/hooks/useDashboardData.js", "Serve the useDashboardData hook (plain JS, no Babel needed)."),
    "/dashboard-formatters.js": ("dashboard/utils/formatters.js", "Serve formatters utility (plain JS, no Babel needed)."),
    "/dashboard-ui-components.jsx": ("dashboard/components/ui.jsx", "Serve UI primitives: StatusBadge, CostBar, Card, StateBadge."),
    "/dashboard-models.jsx": ("dashboard/components/models.jsx", "Serve data models and types."),
    "/dashboard-accounts.jsx": ("dashboard/components/accounts.jsx", "Serve account management components."),
    "/dashboard-layout.jsx": ("dashboard/components/layout.jsx", "Serve layout components."),
    "/dashboard-overview.jsx": ("dashboard/components/overview.jsx", "Serve overview dashboard."),
    "/dashboard-vms.jsx": ("dashboard/components/vms.jsx", "Serve VM management components."),
    "/dashboard-logs.jsx": ("dashboard/components/logs.jsx", "Serve log viewing components."),
    "/dashboard-voice-schemas.jsx": ("dashboard/components/voice/schemas.jsx", "Serve voice schema components."),
    "/dashboard-voice-engine.jsx": ("dashboard/components/voice/engine.jsx", "Serve voice engine components."),
    "/dashboard-voice.jsx": ("dashboard/components/voice/main.jsx", "Serve main voice components."),
    "/dashboard-projects.jsx": ("dashboard/components/projects.jsx", "Serve project management components."),
    "/dashboard-tickets.jsx": ("dashboard/components/tickets.jsx", "Serve ticket management components."),
    "/dashboard-tools.jsx": ("dashboard/components/tools.jsx", "Serve tool management components."),
    "/dashboard-home.jsx": ("dashboard/components/home.jsx", "Serve home dashboard."),
    "/dashboard-tasks.jsx": ("dashboard/components/tasks.jsx", "Serve task management components."),
    "/dashboard-system.jsx": ("dashboard/components/system.jsx", "Serve system information."),
    "/dashboard-setup.jsx": ("dashboard/components/setup.jsx", "Serve setup wizard."),
    "/dashboard-users.jsx": ("dashboard/components/users.jsx", "Serve user management."),
}

# Register all endpoints
for route, (file_path, description) in DASHBOARD_ENDPOINTS.items():
    endpoint_name = route.replace("/", "_").replace(".", "_").replace("-", "_")
    globals()[endpoint_name] = _create_dashboard_endpoint(route, file_path, description)
```

### Benefits
- **Lines saved**: 114 lines (from ~120 lines to ~6 lines)
- **Maintainability**: Single point of change for all dashboard endpoints
- **Consistency**: Uniform error handling and response structure
- **Extensibility**: Easy to add new dashboard components

---

## 🔧 CLI Pattern Consolidation (72 lines recoverable)

### Current Pattern
Repeated CLI patterns across 6 files:
```python
# Test pattern (repeated 19 times)
tests = vscode_tests(config)
print(f"Found {len(tests)} tests")

# Status pattern (repeated 19 times)  
status = get_status(config)
print(f"Status: {status}")
```

### Refactored Solution

#### 1. Create Shared CLI Utilities
```python
# src/proxym/utils/cli_helpers.py

def show_vscode_tests(config, label="tests"):
    """Display VSCode tests for a configuration."""
    tests = vscode_tests(config)
    print(f"Found {len(tests)} {label}")
    return tests

def show_status(config, label="Status"):
    """Display status for a configuration."""
    status = get_status(config)
    print(f"{label}: {status}")
    return status

def make_args_from_config(config, required_args=None):
    """Generate command arguments from configuration."""
    args = []
    if required_args:
        for arg in required_args:
            if hasattr(config, arg):
                args.extend([f"--{arg}", getattr(config, arg)])
    return args
```

#### 2. Update CLI Controllers
Replace repeated patterns with shared utilities:
```python
# Before (in each CLI file)
tests = vscode_tests(config)
print(f"Found {len(tests)} tests")

# After
from proxym.utils.cli_helpers import show_vscode_tests
tests = show_vscode_tests(config)
```

### Benefits
- **Lines saved**: 72 lines across 6 files
- **Consistency**: Standardized output format
- **Maintainability**: Single location for CLI logic updates

---

## 🛠️ Tool Management Refactoring (28 lines recoverable)

### Current Pattern
Similar tool management functions:
```python
async def tools_cancel():
    # cancel logic
    
async def tools_retry(): 
    # retry logic (similar to cancel)
    
async def tools_repair():
    # repair logic (similar to cancel)
```

### Refactored Solution
```python
def _create_tool_action(action: str):
    """Generic tool action factory."""
    @router.post(f"/tools/{action}")
    async def tool_action():
        return await _execute_tool_action(action)
    return tool_action

# Register all tool actions
for action in ["cancel", "retry", "repair", "start", "stop"]:
    globals()[f"tools_{action}"] = _create_tool_action(action)
```

---

## 📊 Implementation Priority

### Phase 1: Dashboard Refactoring (Highest ROI)
1. Create `_create_dashboard_endpoint` function
2. Define `DASHBOARD_ENDPOINTS` configuration
3. Replace all 20 duplicate functions
4. Test all dashboard endpoints still work

### Phase 2: CLI Utilities (Medium ROI)
1. Create `src/proxym/utils/cli_helpers.py`
2. Update 6 CLI controller files
3. Test CLI commands maintain same behavior

### Phase 3: Tool Management (Low ROI)
1. Create generic tool action factory
2. Consolidate tool management functions
3. Test tool operations remain functional

---

## 🎯 Expected Results

### Code Metrics
- **Total lines saved**: 214 lines
- **Functions eliminated**: 20 dashboard + 19 CLI patterns + 6 tool functions
- **Files affected**: 1 main file + 6 CLI files

### Quality Improvements
- **DRY compliance**: Eliminate all identified duplicates
- **Maintainability**: Centralized logic for common operations
- **Consistency**: Standardized patterns across the codebase
- **Extensibility**: Easy to add new endpoints and CLI commands

### Testing Strategy
1. **Dashboard endpoints**: Verify all routes return correct content
2. **CLI commands**: Ensure output format remains unchanged
3. **Tool operations**: Confirm all tool actions work as expected
4. **Integration tests**: Run full proxy test suite

---

## 🔄 Rollback Plan

If issues arise during refactoring:

1. **Dashboard**: Keep original functions commented out during transition
2. **CLI**: Gradually migrate files one at a time
3. **Tools**: Maintain backward compatibility during refactoring

---

*Generated by reDUP v0.1.1 analysis*
*Target completion: Phase 1 (1-2 days), Full implementation (1 week)*
