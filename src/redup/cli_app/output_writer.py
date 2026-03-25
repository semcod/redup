"""Output writers for reDUP CLI results."""

from pathlib import Path
from typing import Any

from redup.config import config, get_default_filename
from redup.core.models import DuplicationMap
from redup.reporters.json_reporter import to_json
from redup.reporters.markdown_reporter import to_markdown
from redup.reporters.toon_reporter import to_toon
from redup.reporters.yaml_reporter import to_yaml
from redup.reporters.code2llm_reporter import export_code2llm, to_code2llm_context, to_code2llm_toon
from redup.reporters.enhanced_reporter import EnhancedReporter


def write_output(content: str, output: Path | None, suffix: str) -> None:
    """Write content to file or stdout."""
    import typer

    if output:
        target = output if output.suffix else output / get_default_filename(suffix)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        typer.echo(f"  → {target}")
    else:
        typer.echo(content)


def write_results(dup_map: DuplicationMap, format: str, output: Any, path: Path) -> None:
    """Write analysis results in specified format."""
    import typer
    
    if format == "json":
        content = to_json(dup_map)
        write_output(content, output, "json")
    elif format == "yaml":
        content = to_yaml(dup_map)
        write_output(content, output, "yaml")
    elif format == "toon":
        content = to_toon(dup_map)
        write_output(content, output, "toon")
    elif format == "markdown":
        content = to_markdown(dup_map)
        write_output(content, output, "md")
    elif format == "enhanced":
        reporter = EnhancedReporter(dup_map)
        content = reporter.generate_report()
        write_output(content, output, "html")
    elif format == "code2llm":
        if output:
            content = to_code2llm_context(dup_map)
            write_output(content, output, "md")
        else:
            # For code2llm, create a directory with multiple files
            export_code2llm(dup_map, output or path / "code2llm")
    elif format == "all":
        # Generate all formats
        formats = {
            "json": to_json(dup_map),
            "yaml": to_yaml(dup_map),
            "toon": to_toon(dup_map),
            "markdown": to_markdown(dup_map),
        }
        
        # Determine and create output directory
        if output:
            # Create output directory if it doesn't exist
            output.mkdir(parents=True, exist_ok=True)
            base_dir = output
        else:
            base_dir = path
        
        for fmt, content in formats.items():
            target = base_dir / get_default_filename(fmt)
            target.write_text(content, encoding="utf-8")
            typer.echo(f"  → {target}")
    else:
        typer.echo(f"❌ Unknown format: {format}", err=True)
        raise typer.Exit(1)
