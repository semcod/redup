"""CLI command for exporting duplication findings as tasks to TODO.md.

Provides integration with planfile for task management and synchronization
with GitHub, GitLab, and Jira.
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from redup.core import analyze

app = typer.Typer(help="Export duplication findings as tasks to TODO.md")
console = Console()


@app.callback(invoke_without_command=True)
def tasks(
    ctx: typer.Context,
    path: Path = typer.Argument(
        default=".",
        help="Path to analyze for duplications",
    ),
    output: Path = typer.Option(
        Path("TODO.md"),
        "--output", "-o",
        help="Output TODO.md file path",
    ),
    backend: str | None = typer.Option(
        None,
        "--backend", "-b",
        help="Sync backend: github, gitlab, jira",
    ),
    min_lines: int = typer.Option(
        3,
        "--min-lines", "-l",
        help="Minimum lines for duplication detection",
    ),
    ext: list[str] | None = typer.Option(
        None,
        "--ext", "-e",
        help="File extensions to include (default: .py)",
    ),
    milestone: str | None = typer.Option(
        None,
        "--milestone", "-m",
        help="Milestone for synced tasks",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-n",
        help="Preview without writing files",
    ),
) -> None:
    """Export duplication findings as tasks to TODO.md.

    Creates a TODO.md file with refactoring tasks based on found duplications.
    Optionally syncs with GitHub, GitLab, or Jira when --backend is specified.

    Examples:
        redup tasks ./my-project
        redup tasks ./my-project --output refactoring.md --backend github
        redup tasks ./my-project -b gitlab -m "Sprint 1" --dry-run
    """
    if ctx.invoked_subcommand is not None:
        return

    # Validate backend
    valid_backends = {"github", "gitlab", "jira", None}
    if backend not in valid_backends:
        console.print(f"[red]Error: Invalid backend '{backend}'. Use: github, gitlab, or jira[/red]")
        raise typer.Exit(1)

    # Check if planfile is installed for sync
    if backend:
        try:
            import planfile  # noqa: F401
        except ImportError:
            console.print(
                "[yellow]Warning: planfile not installed. "
                "Install with: pip install redup[tasks][/yellow]"
            )
            backend = None

    # Analyze project
    console.print(f"[blue]Analyzing {path} for duplications...[/blue]")

    extensions = tuple(ext) if ext else (".py",)
    result = analyze(
        str(path),
        min_block_lines=min_lines,
        extensions=extensions,
    )

    if not result or not result.groups:
        console.print("[green]No duplications found! Nothing to export.[/green]")
        raise typer.Exit(0)

    # Show summary
    total_savings = sum(g.saved_lines_potential for g in result.groups)
    console.print(f"[green]Found {len(result.groups)} duplicate groups[/green]")
    console.print(f"[green]Potential savings: {total_savings} lines[/green]")

    # Generate tasks
    try:
        from redup.integrations.planfile_integration import (
            DuplicateTaskExporter,
            TaskConfig,
        )

        config = TaskConfig(
            todo_file=output,
            sync_backend=backend,
            sync_enabled=backend is not None,
            milestone=milestone,
        )

        exporter = DuplicateTaskExporter(config)

        if dry_run:
            # Just preview
            tasks_list = exporter._generate_tasks(result)
            _preview_tasks(tasks_list)
        else:
            # Export to file
            result_path = exporter.export(result)
            console.print(f"[green]✓ Exported {len(exporter.tasks)} tasks to {result_path}[/green]")

            if backend:
                console.print(f"[blue]Syncing with {backend}...[/blue]")
                synced = sum(1 for t in exporter.tasks if t.task_id)
                console.print(f"[green]✓ Synced {synced} tasks to {backend}[/green]")

    except ImportError as e:
        console.print(f"[red]Error: Required module not available: {e}[/red]")
        console.print("[yellow]Install with: pip install redup[tasks][/yellow]")
        raise typer.Exit(1)


def _preview_tasks(tasks: list) -> None:
    """Preview tasks in a table without exporting."""
    if not tasks:
        console.print("[yellow]No tasks to display[/yellow]")
        return

    table = Table(title="Tasks Preview")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Priority", style="bold")
    table.add_column("Title", style="white", no_wrap=False)
    table.add_column("Difficulty", style="yellow")
    table.add_column("Savings", style="green", justify="right")

    for i, task in enumerate(tasks[:20], 1):
        difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(
            task.difficulty, "⚪"
        )

        priority_style = {
            "critical": "red",
            "major": "yellow",
            "minor": "dim",
        }.get(task.priority, "white")

        table.add_row(
            str(i),
            f"[{priority_style}]{task.priority}[/{priority_style}]",
            task.title,
            f"{difficulty_emoji} {task.difficulty}",
            f"{task.lines_saved}L",
        )

    if len(tasks) > 20:
        table.add_row("", "", f"... and {len(tasks) - 20} more", "", "")

    console.print(table)
    console.print(f"\n[dim]Total: {len(tasks)} tasks[/dim]")
