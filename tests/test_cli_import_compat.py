"""Regression tests for CLI import compatibility shims."""

from __future__ import annotations

import importlib
import sys

import click


def _clear_redup_modules() -> None:
    for name in list(sys.modules):
        if name == "redup" or name.startswith("redup."):
            sys.modules.pop(name, None)


def test_cli_import_restores_click_choice_generics(monkeypatch):
    monkeypatch.setattr(click.Choice, "__class_getitem__", None, raising=False)

    _clear_redup_modules()

    module = importlib.import_module("redup.cli_app.main")

    assert module.app is not None
    assert callable(click.Choice.__class_getitem__)
