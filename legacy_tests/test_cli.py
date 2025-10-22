"""Placeholder tests asserting CLI module removal."""

import importlib

import pytest


def test_cli_module_removed() -> None:
    with pytest.raises(ImportError):
        importlib.import_module("canvas_code_correction.cli")
