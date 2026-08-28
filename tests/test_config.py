"""Tests for project-local configuration loading."""

from pathlib import Path

from redup.cli_app.config_builder import build_config_with_file_support


def test_config_is_loaded_from_scanned_project_not_process_cwd(
    tmp_path: Path, monkeypatch
) -> None:
    project = tmp_path / "project"
    server_cwd = tmp_path / "server"
    project.mkdir()
    server_cwd.mkdir()
    (project / "pyproject.toml").write_text(
        """[tool.redup.scan]
extensions = ".py,.js"
min_lines = 9
include_tests = true
""",
        encoding="utf-8",
    )
    (server_cwd / "redup.toml").write_text(
        """[scan]
extensions = ".rs"
min_lines = 99
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(server_cwd)

    config = build_config_with_file_support(
        project,
        extensions=None,
        min_lines=None,
        min_similarity=None,
        include_tests=None,
    )

    assert config.extensions == [".py", ".js"]
    assert config.min_block_lines == 9
    assert config.include_tests is True
