"""Tests for the root ``xmascards`` command."""

import runpy
import sys

import pytest

from christmas_cards import __version__
from christmas_cards.cli import app, main


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    app(["--version"], result_action="return_value")
    assert capsys.readouterr().out.strip() == __version__


def test_help_lists_subcommands(capsys: pytest.CaptureFixture[str]) -> None:
    app(["--help"], result_action="return_value")
    out = capsys.readouterr().out
    assert "geocode" in out
    assert "labels" in out


def test_main_prints_result_and_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["labels", "return-address", "out.pdf", "--address", "Me"])
    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == "Wrote return-address labels to out.pdf"


def test_main_reports_errors_without_traceback(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["geocode", "csv"])
    assert exc_info.value.code == 1
    assert capsys.readouterr().err.startswith("Error: azure_map_key is not set")


def test_python_dash_m(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["xmascards", "--version"])
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("christmas_cards", run_name="__main__")
    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == __version__


def test_unknown_command_fails() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["no-such-command"])
    assert exc_info.value.code != 0
