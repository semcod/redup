"""Pipeline phases: scan, process, deduplicate."""

from __future__ import annotations

from redup.core.models import ScanConfig, ScanStats
from redup.core.scanner import ScanStrategy, scan_project
from redup.core.scanner_types import CodeBlock, ScannedFile


def ensure_config(config: ScanConfig | None) -> ScanConfig:
    """Ensure we have a valid configuration."""
    return config or ScanConfig()


def scan_phase(
    config: ScanConfig, function_level_only: bool | None = None
) -> tuple[list[ScannedFile], ScanStats]:
    """Phase 1: Scan project files."""
    if function_level_only is None:
        function_level_only = config.functions_only
    return scan_project(config, function_level_only=function_level_only)


def scan_phase_parallel(
    config: ScanConfig, max_workers: int | None = None
) -> tuple[list[ScannedFile], ScanStats]:
    """Phase 1: Scan project files in parallel."""
    strategy = ScanStrategy(parallel=True, max_workers=max_workers or 4)
    return scan_project(config, strategy, function_level_only=True)


def process_blocks(
    scanned_files: list[ScannedFile], function_level_only: bool
) -> list[CodeBlock]:
    """Phase 2: Extract and filter code blocks with memory optimization."""
    all_blocks: list[CodeBlock] = []

    # Batch process files to reduce memory overhead
    batch_size = 100
    for i in range(0, len(scanned_files), batch_size):
        batch = scanned_files[i:i + batch_size]
        for sf in batch:
            for block in sf.blocks:
                if function_level_only and block.function_name is None:
                    continue
                all_blocks.append(block)

    return all_blocks
