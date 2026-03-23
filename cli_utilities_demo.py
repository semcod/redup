"""CLI utilities refactoring - demonstration of shared helper functions."""

from typing import List, Optional, Any
import structlog

logger = structlog.get_logger()


def show_vscode_tests(config: Any, label: str = "tests") -> List[Any]:
    """Display VSCode tests for a configuration.
    
    Args:
        config: Configuration object containing test settings
        label: Descriptive label for output
        
    Returns:
        List of discovered tests
    """
    # This would be the actual test discovery logic
    tests = []  # vscode_tests(config) - placeholder
    
    print(f"Found {len(tests)} {label}")
    
    if tests and len(tests) <= 5:
        for i, test in enumerate(tests, 1):
            print(f"  {i}. {test}")
    elif tests and len(tests) > 5:
        print(f"  Showing first 5 of {len(tests)} tests:")
        for i, test in enumerate(tests[:5], 1):
            print(f"  {i}. {test}")
        print(f"  ... and {len(tests) - 5} more")
    
    return tests


def show_status(config: Any, label: str = "Status") -> Any:
    """Display status for a configuration.
    
    Args:
        config: Configuration object containing status information
        label: Descriptive label for output
        
    Returns:
        Status information
    """
    # This would be the actual status retrieval logic
    status = None  # get_status(config) - placeholder
    
    print(f"{label}: {status}")
    
    # Add additional context if available
    if hasattr(status, 'state') and status.state:
        print(f"  State: {status.state}")
    if hasattr(status, 'last_updated') and status.last_updated:
        print(f"  Last updated: {status.last_updated}")
    
    return status


def make_args_from_config(config: Any, required_args: Optional[List[str]] = None) -> List[str]:
    """Generate command arguments from configuration.
    
    Args:
        config: Configuration object
        required_args: List of required argument names
        
    Returns:
        List of command-line arguments
    """
    args = []
    
    if required_args:
        for arg in required_args:
            if hasattr(config, arg):
                value = getattr(config, arg)
                if value is not None:
                    # Handle different value types
                    if isinstance(value, bool) and value:
                        args.append(f"--{arg}")
                    elif isinstance(value, list):
                        for item in value:
                            args.extend([f"--{arg}", str(item)])
                    elif not isinstance(value, bool):
                        args.extend([f"--{arg}", str(value)])
    
    return args


def confirm_action(message: str, default: bool = False) -> bool:
    """Get user confirmation for an action.
    
    Args:
        message: Confirmation message
        default: Default response if user just presses Enter
        
    Returns:
        True if user confirms, False otherwise
    """
    prompt = f"{message} ({'Y/n' if default else 'y/N'}): "
    
    try:
        response = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled.")
        return False
    
    if not response:
        return default
    
    return response in ['y', 'yes', 'true', '1'] if default else response in ['y', 'yes', 'true', '1']


def format_output(data: Any, format_type: str = "table") -> str:
    """Format data for CLI output.
    
    Args:
        data: Data to format
        format_type: Output format (table, json, yaml)
        
    Returns:
        Formatted string
    """
    if format_type == "json":
        import json
        return json.dumps(data, indent=2, default=str)
    elif format_type == "yaml":
        try:
            import yaml
            return yaml.dump(data, default_flow_style=False)
        except ImportError:
            return "YAML output requires PyYAML: pip install pyyaml"
    else:
        # Default table format
        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                # List of dictionaries - create table
                headers = list(data[0].keys())
                rows = [[str(item.get(header, "")) for header in headers] for item in data]
                return format_table(headers, rows)
            else:
                # Simple list
                return "\\n".join(f"  {i}. {item}" for i, item in enumerate(data, 1))
        elif isinstance(data, dict):
            # Single dictionary
            return "\\n".join(f"  {key}: {value}" for key, value in data.items())
        else:
            return str(data)


def format_table(headers: List[str], rows: List[List[str]]) -> str:
    """Format data as a table.
    
    Args:
        headers: Column headers
        rows: Table rows
        
    Returns:
        Formatted table string
    """
    if not headers or not rows:
        return ""
    
    # Calculate column widths
    col_widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Format header row
    header_line = " | ".join(header.ljust(width) for header, width in zip(headers, col_widths))
    separator = "-+-".join("-" * width for width in col_widths)
    
    # Format data rows
    data_lines = []
    for row in rows:
        row_cells = []
        for i, cell in enumerate(row):
            if i < len(col_widths):
                row_cells.append(str(cell).ljust(col_widths[i]))
            else:
                row_cells.append(str(cell))
        data_lines.append(" | ".join(row_cells))
    
    return "\\n".join([header_line, separator] + data_lines)


def handle_error(error: Exception, context: str = "operation") -> None:
    """Handle and log errors consistently.
    
    Args:
        error: Exception that occurred
        context: Context where error occurred
    """
    logger.error(f"Error during {context}: {error}")
    
    if isinstance(error, FileNotFoundError):
        print(f"Error: File not found during {context}")
    elif isinstance(error, PermissionError):
        print(f"Error: Permission denied during {context}")
    elif isinstance(error, ValueError):
        print(f"Error: Invalid value during {context}: {error}")
    else:
        print(f"Error: Unexpected error during {context}: {error}")


# Example usage in CLI controllers:

"""
# Before refactoring (repeated pattern):
def cmd_accounts_show(config):
    tests = vscode_tests(config)
    print(f"Found {len(tests)} tests")
    
    status = get_status(config)
    print(f"Status: {status}")
    
    args = []
    if hasattr(config, 'verbose') and config.verbose:
        args.append('--verbose')
    if hasattr(config, 'format') and config.format:
        args.extend(['--format', config.format])

# After refactoring:
from proxym.utils.cli_helpers import show_vscode_tests, show_status, make_args_from_config

def cmd_accounts_show(config):
    tests = show_vscode_tests(config, "account tests")
    status = show_status(config, "Account status")
    args = make_args_from_config(config, ['verbose', 'format'])
"""
