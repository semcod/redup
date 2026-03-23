"""Refactored frontend.py - demonstrating dashboard endpoint consolidation."""

import os
from typing import Dict, Tuple

import structlog
from fastapi import APIRouter
from fastapi.responses import Response

from proxym.config import get_settings

logger = structlog.get_logger()

router = APIRouter()

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC_ROOT = os.path.dirname(_HERE)  # src/proxym/
_MIME_JS = "text/javascript"
_MIME_JS_UTF8 = "text/javascript; charset=utf-8"


def _serve_file(paths: list[str], media_type: str, charset_header: str | None = None) -> Response:
    """Try paths in order; return content from first found file."""
    for file_path in paths:
        try:
            with open(file_path, "r") as f:
                content = f.read()
            headers = {"Content-Type": charset_header} if charset_header else {}
            return Response(content=content, media_type=media_type, headers=headers)
        except FileNotFoundError:
            continue
    
    # Return 404 if no file found
    return Response(content="File not found", status_code=404, media_type="text/plain")


def _create_dashboard_endpoint(route: str, file_path: str, description: str):
    """Generic factory for dashboard JS/JSX endpoints.
    
    Args:
        route: The URL route pattern
        file_path: Relative path from _SRC_ROOT to the file
        description: Endpoint description for documentation
        
    Returns:
        FastAPI endpoint function
    """
    @router.get(route)
    async def endpoint():
        """Serve dashboard component."""
        return _serve_file(
            [os.path.join(_SRC_ROOT, file_path)],
            _MIME_JS, _MIME_JS_UTF8,
        )
    
    # Set the docstring dynamically
    endpoint.__doc__ = description
    return endpoint


# Dashboard endpoint configuration
# Maps route -> (file_path, description)
DASHBOARD_ENDPOINTS: Dict[str, Tuple[str, str]] = {
    "/dashboard-hook.js": (
        "dashboard/hooks/useDashboardData.js", 
        "Serve the useDashboardData hook (plain JS, no Babel needed)."
    ),
    "/dashboard-api.js": (
        "dashboard/api.js",
        "Serve the dashboard API client (plain JS, no Babel needed)."
    ),
    "/dashboard-formatters.js": (
        "dashboard/utils/formatters.js",
        "Serve formatters utility (plain JS, no Babel needed)."
    ),
    "/dashboard-ui-components.jsx": (
        "dashboard/components/ui.jsx",
        "Serve UI primitives: StatusBadge, CostBar, Card, StateBadge."
    ),
    "/dashboard-models.jsx": (
        "dashboard/components/models.jsx",
        "Serve data models and types."
    ),
    "/dashboard-accounts.jsx": (
        "dashboard/components/accounts.jsx",
        "Serve account management components."
    ),
    "/dashboard-layout.jsx": (
        "dashboard/components/layout.jsx",
        "Serve layout components."
    ),
    "/dashboard-overview.jsx": (
        "dashboard/components/overview.jsx",
        "Serve overview dashboard."
    ),
    "/dashboard-vms.jsx": (
        "dashboard/components/vms.jsx",
        "Serve VM management components."
    ),
    "/dashboard-logs.jsx": (
        "dashboard/components/logs.jsx",
        "Serve log viewing components."
    ),
    "/dashboard-voice-schemas.jsx": (
        "dashboard/components/voice/schemas.jsx",
        "Serve voice schema components."
    ),
    "/dashboard-voice-engine.jsx": (
        "dashboard/components/voice/engine.jsx",
        "Serve voice engine components."
    ),
    "/dashboard-voice.jsx": (
        "dashboard/components/voice/main.jsx",
        "Serve main voice components."
    ),
    "/dashboard-projects.jsx": (
        "dashboard/components/projects.jsx",
        "Serve project management components."
    ),
    "/dashboard-tickets.jsx": (
        "dashboard/components/tickets.jsx",
        "Serve ticket management components."
    ),
    "/dashboard-tools.jsx": (
        "dashboard/components/tools.jsx",
        "Serve tool management components."
    ),
    "/dashboard-home.jsx": (
        "dashboard/components/home.jsx",
        "Serve home dashboard."
    ),
    "/dashboard-tasks.jsx": (
        "dashboard/components/tasks.jsx",
        "Serve task management components."
    ),
    "/dashboard-system.jsx": (
        "dashboard/components/system.jsx",
        "Serve system information."
    ),
    "/dashboard-setup.jsx": (
        "dashboard/components/setup.jsx",
        "Serve setup wizard."
    ),
    "/dashboard-users.jsx": (
        "dashboard/components/users.jsx",
        "Serve user management."
    ),
}


# Register all dashboard endpoints dynamically
for route, (file_path, description) in DASHBOARD_ENDPOINTS.items():
    # Create a unique function name for each endpoint
    endpoint_name = f"dashboard_{route.replace('/', '_').replace('.', '_').replace('-', '_')}"
    
    # Create the endpoint using the factory function
    endpoint_func = _create_dashboard_endpoint(route, file_path, description)
    
    # Add to module globals so it can be discovered by FastAPI
    globals()[endpoint_name] = endpoint_func


# Additional diagnostic endpoints (different pattern)
@router.get("/dashboard-diag-helpers.jsx")
async def dashboard_diag_helpers_jsx():
    """Serve diagnostic helper components."""
    return _serve_file(
        [os.path.join(_SRC_ROOT, "dashboard", "diag", "helpers.jsx")],
        _MIME_JS, _MIME_JS_UTF8,
    )


@router.get("/dashboard-diag-infrastructure.jsx")
async def dashboard_diag_infrastructure_jsx():
    """Serve infrastructure diagnostic components."""
    return _serve_file(
        [os.path.join(_SRC_ROOT, "dashboard", "diag", "infrastructure.jsx")],
        _MIME_JS, _MIME_JS_UTF8,
    )


@router.get("/dashboard-diag-config.jsx")
async def dashboard_diag_config_jsx():
    """Serve configuration diagnostic components."""
    return _serve_file(
        [os.path.join(_SRC_ROOT, "dashboard", "diag", "config.jsx")],
        _MIME_JS, _MIME_JS_UTF8,
    )


@router.get("/dashboard-diag-extensions.jsx")
async def dashboard_diag_extensions_jsx():
    """Serve extensions diagnostic components."""
    return _serve_file(
        [os.path.join(_SRC_ROOT, "dashboard", "diag", "extensions.jsx")],
        _MIME_JS, _MIME_JS_UTF8,
    )


@router.get("/dashboard-diag-agent.jsx")
async def dashboard_diag_agent_jsx():
    """Serve agent diagnostic components."""
    return _serve_file(
        [os.path.join(_SRC_ROOT, "dashboard", "diag", "agent.jsx")],
        _MIME_JS, _MIME_JS_UTF8,
    )


# Legacy endpoints that don't follow the pattern
@router.get("/favicon.ico")
async def favicon():
    """Serve favicon."""
    return _serve_file(
        [os.path.join(_SRC_ROOT, "static", "favicon.ico")],
        "image/x-icon", None,
    )


@router.get("/")
async def index():
    """Serve main dashboard HTML."""
    return _serve_file(
        [os.path.join(_SRC_ROOT, "static", "index.html")],
        "text/html", "text/html; charset=utf-8",
    )


# Configuration endpoint
@router.get("/config.json")
async def config_json():
    """Serve configuration as JSON."""
    settings = get_settings()
    import json
    config_data = {
        "api_base": settings.api_base_url,
        "ws_url": settings.ws_url,
        "debug": settings.debug,
    }
    return Response(
        content=json.dumps(config_data, indent=2),
        media_type="application/json",
        headers={"Content-Type": "application/json; charset=utf-8"}
    )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return Response(
        content='{"status": "healthy", "service": "proxy-frontend"}',
        media_type="application/json",
        headers={"Content-Type": "application/json; charset=utf-8"}
    )


print(f"Registered {len(DASHBOARD_ENDPOINTS)} dashboard endpoints")
print(f"Total endpoints: {len(router.routes)}")
