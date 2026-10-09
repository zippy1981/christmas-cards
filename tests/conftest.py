"""Shared pytest fixtures."""

from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any

import pytest
import requests

from christmas_cards.cli import app
from christmas_cards.config import get_settings

type RunCli = Callable[[Sequence[str]], Any]


@pytest.fixture
def run_cli() -> RunCli:
    """Invoke the CLI in-process and return the command's return value."""

    def _run(argv: Sequence[str]) -> Any:
        return app(list(argv), result_action="return_value", exit_on_error=False)

    return _run


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Run each test in an empty directory, so no real settings or secrets are loaded."""
    monkeypatch.chdir(tmp_path)
    for name in (
        "DYNACONF_AZURE_MAP_KEY",
        "DYNACONF_RETURN_ADDRESS",
        "DYNACONF_GOOGLE_SHEET_ID",
        "DYNACONF_GOOGLE_WORKSHEET",
        "DYNACONF_GOOGLE_SERVICE_ACCOUNT_INFO",
        "DYNACONF_GOOGLE_SERVICE_ACCOUNT_FILE",
        "GOOGLE_APPLICATION_CREDENTIALS",
    ):
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()


class FakeResponse:
    """The parts of :class:`requests.Response` the geocoder uses."""

    def __init__(self, payload: Any, status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise requests.HTTPError(f"{self.status} error")

    def json(self) -> Any:
        return self.payload


type Responder = Callable[[str], FakeResponse]


@pytest.fixture
def fake_http(monkeypatch: pytest.MonkeyPatch) -> Callable[[Responder], list[str]]:
    """Route ``requests.Session.get`` to a responder; returns the list of requested URLs."""

    def _install(responder: Responder) -> list[str]:
        urls: list[str] = []

        def fake_get(self: requests.Session, url: str, **kwargs: Any) -> FakeResponse:
            urls.append(url)
            return responder(url)

        monkeypatch.setattr(requests.Session, "get", fake_get)
        return urls

    return _install
