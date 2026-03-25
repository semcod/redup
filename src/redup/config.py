"""Centralized configuration for reDUP with .env file support.

This module provides global configuration settings that can be customized via:
1. Environment variables (REDUP_* prefix)
2. .env files in the project directory
3. redup.toml configuration file
4. Programmatic overrides

Example .env file:
    REDUP_DEFAULT_OUTPUT_FILENAME=duplication.toon.yaml
    REDUP_DEFAULT_FORMAT=toon
    REDUP_MIN_LINES=5
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv

    # Load .env from current working directory if it exists
    _env_path = Path.cwd() / ".env"
    if _env_path.exists():
        load_dotenv(_env_path, override=True)
except ImportError:
    load_dotenv = None  # type: ignore


class RedupConfig:
    """Global configuration container for reDUP settings.

    Attributes can be set via:
    - Environment variables (REDUP_* prefix, e.g., REDUP_DEFAULT_OUTPUT_FILENAME)
    - .env files in the project directory (loaded automatically)
    - Direct attribute assignment (e.g., config.DEFAULT_OUTPUT_FILENAME = "...")
    """

    # Output settings
    DEFAULT_OUTPUT_FILENAME: str = "duplication.toon.yaml"
    DEFAULT_FORMAT: str = "toon"
    DEFAULT_OUTPUT_DIR: str = "."

    # Scan settings
    DEFAULT_MIN_LINES: int = 3
    DEFAULT_MIN_SIMILARITY: float = 0.85
    DEFAULT_EXTENSIONS: str = ".py"
    DEFAULT_INCLUDE_TESTS: bool = False

    # Performance settings
    DEFAULT_PARALLEL: bool = False
    DEFAULT_MAX_WORKERS: int | None = None
    DEFAULT_INCREMENTAL: bool = False
    DEFAULT_MEMORY_CACHE: bool = True
    DEFAULT_MAX_CACHE_MB: int = 512

    # Fuzzy settings
    DEFAULT_FUZZY: bool = False
    DEFAULT_FUZZY_THRESHOLD: float = 0.8

    # LSH settings
    DEFAULT_LSH_ENABLED: bool = True
    DEFAULT_LSH_MIN_LINES: int = 50
    DEFAULT_LSH_THRESHOLD: float = 0.8

    # Cache settings
    DEFAULT_CACHE_DIR: str = ".redup/cache"

    @classmethod
    def _env_name(cls, attr_name: str) -> str:
        """Convert attribute name to environment variable name."""
        return f"REDUP_{attr_name}"

    @classmethod
    def _load_from_env(cls) -> dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}
        for attr_name in dir(cls):
            if attr_name.startswith("DEFAULT_"):
                env_name = cls._env_name(attr_name)
                value = os.getenv(env_name)
                if value is not None:
                    # Convert to appropriate type based on default
                    default_value = getattr(cls, attr_name)
                    if isinstance(default_value, bool):
                        config[attr_name] = value.lower() in ("true", "1", "yes", "on")
                    elif isinstance(default_value, int):
                        try:
                            config[attr_name] = int(value)
                        except ValueError:
                            pass
                    elif isinstance(default_value, float):
                        try:
                            config[attr_name] = float(value)
                        except ValueError:
                            pass
                    else:
                        config[attr_name] = value
        return config

    @classmethod
    def reload(cls, env_path: Path | None = None) -> None:
        """Reload configuration from .env file and environment variables.

        Args:
            env_path: Optional path to .env file. If None, looks for .env in current directory.
        """
        # Load from .env file if specified or found
        if load_dotenv is not None:
            if env_path is not None:
                if env_path.exists():
                    load_dotenv(env_path, override=True)
            else:
                cwd_env = Path.cwd() / ".env"
                if cwd_env.exists():
                    load_dotenv(cwd_env, override=True)

        # Update class attributes from environment variables
        for attr_name, value in cls._load_from_env().items():
            setattr(cls, attr_name, value)

    @classmethod
    def get(cls, attr_name: str, default: Any = None) -> Any:
        """Get configuration value by name."""
        if hasattr(cls, attr_name):
            return getattr(cls, attr_name)
        return default

    @classmethod
    def set(cls, attr_name: str, value: Any) -> None:
        """Set configuration value by name."""
        if hasattr(cls, attr_name):
            setattr(cls, attr_name, value)
        else:
            raise AttributeError(f"No such config attribute: {attr_name}")


# Global config instance
config = RedupConfig()

# Load initial configuration from .env if present
config.reload()


def get_default_filename(suffix: str | None = None) -> str:
    """Get default output filename.

    Args:
        suffix: Optional file suffix. If None, uses the full DEFAULT_OUTPUT_FILENAME.
            If provided, constructs appropriate filename with that suffix.

    Returns:
        Default filename string.
    """
    if suffix is None:
        return config.DEFAULT_OUTPUT_FILENAME
    
    # Get the base name without any extensions (e.g., "duplication.toon.yaml" -> "duplication")
    # Split on all dots and take the first part as base
    full_name = config.DEFAULT_OUTPUT_FILENAME
    base = full_name.split(".")[0]
    
    # For "toon" format, use the full default filename (duplication.toonyaml)
    if suffix == "toon":
        return config.DEFAULT_OUTPUT_FILENAME
    
    # For other formats, use simple extension (duplication.json, duplication.yaml, etc.)
    return f"{base}.{suffix}"


def reload_config(env_path: Path | None = None) -> None:
    """Reload configuration from .env file.

    This function can be called to reload settings when .env file changes.

    Args:
        env_path: Optional path to .env file. If None, looks for .env in current directory.
    """
    config.reload(env_path)
