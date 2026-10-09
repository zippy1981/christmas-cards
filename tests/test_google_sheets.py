"""Tests for geocoding a Google Sheet (``xmascards geocode sheet``)."""

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import google.auth
import gspread
import pytest
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account
from gspread.utils import a1_to_rowcol

from christmas_cards import google_sheets
from christmas_cards.errors import ChristmasCardsError
from christmas_cards.geocoding import ADDRESS_HASH_COLUMN, GEOCODE_COLUMNS, address_hash
from tests.conftest import FakeResponse, Responder, RunCli

type FakeHttp = Callable[[Responder], list[str]]


def found(url: str) -> FakeResponse:
    if "openstreetmap" in url:
        return FakeResponse([{"address": {"road": "Main St"}, "display_name": "Main St"}])
    return FakeResponse({"results": [{"address": {"streetName": "Main St"}, "score": 0.9}]})


class FakeWorksheet:
    """An in-memory stand-in for :class:`gspread.Worksheet`."""

    def __init__(self, rows: list[list[str]], col_count: int | None = None) -> None:
        self.col_count = col_count or max(len(r) for r in rows)
        self.rows = [r + [""] * (self.col_count - len(r)) for r in rows]
        self.batch_updates = 0

    def get_all_values(self) -> list[list[str]]:
        return [list(r) for r in self.rows]

    def add_cols(self, cols: int) -> None:
        self.col_count += cols
        self.rows = [r + [""] * cols for r in self.rows]

    def _set(self, a1: str, values: list[list[str]]) -> None:
        row, col = a1_to_rowcol(a1)
        for r, line in enumerate(values, start=row - 1):
            for c, value in enumerate(line, start=col - 1):
                assert c < self.col_count, "wrote past the last column"
                self.rows[r][c] = value

    def update(self, values: list[list[str]], range_name: str | None = None) -> None:
        self._set(range_name or "A1", values)

    def batch_update(self, data: list[dict[str, Any]]) -> None:
        self.batch_updates += 1
        for item in data:
            self._set(item["range"], item["values"])

    def records(self) -> list[dict[str, str]]:
        header, *rows = self.rows
        return [dict(zip(header, row, strict=True)) for row in rows]


@pytest.fixture
def azure_key(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("DYNACONF_AZURE_MAP_KEY", "secret-key")
    return "secret-key"


def test_address_hash_ignores_case_and_whitespace() -> None:
    assert address_hash(" 1 Main  St\n") == address_hash("1 main st")
    assert address_hash("1 Main St") != address_hash("2 Main St")


def test_new_sheet_gets_columns_and_hashes(fake_http: FakeHttp) -> None:
    ws = FakeWorksheet(
        [
            ["First Name", "Last Name", "Address", ""],
            ["Ada", "Lovelace", "1 Main St"],
            ["No", "Address", ""],
        ]
    )
    urls = fake_http(found)

    summary = google_sheets.geocode_worksheet(ws, "k", osm_delay=0)

    assert summary == google_sheets.GeocodeSummary(geocoded=1, unchanged=0, blank=1)
    assert ws.rows[0] == ["First Name", "Last Name", "Address", *GEOCODE_COLUMNS]
    ada, blank = ws.records()
    assert ada[ADDRESS_HASH_COLUMN] == address_hash("1 Main St")
    assert json.loads(ada["Azure Address"]) == {"streetName": "Main St"}
    assert ada["Azure Score"] == "0.9"
    assert blank[ADDRESS_HASH_COLUMN] == ""
    assert len(urls) == 2


def test_only_new_and_changed_addresses_are_geocoded(fake_http: FakeHttp) -> None:
    header = ["First Name", "Last Name", "Address", *GEOCODE_COLUMNS]
    stale = ["old"] * (len(GEOCODE_COLUMNS) - 1)
    ws = FakeWorksheet(
        [
            header,
            ["Same", "Person", "1 Main St", *stale, address_hash("1 Main St")],
            ["Moved", "Person", "2 New Rd", *stale, address_hash("2 Old Rd")],
            ["New", "Person", "3 Main St"],
        ]
    )
    urls = fake_http(found)

    summary = google_sheets.geocode_worksheet(ws, "k", osm_delay=0, batch_size=1)

    assert summary == google_sheets.GeocodeSummary(geocoded=2, unchanged=1, blank=0)
    same, moved, new = ws.records()
    assert same["Azure Address"] == "old"
    assert moved["Azure Address"] != "old"
    assert moved[ADDRESS_HASH_COLUMN] == address_hash("2 New Rd")
    assert new[ADDRESS_HASH_COLUMN] == address_hash("3 Main St")
    assert len(urls) == 4
    assert ws.batch_updates == 2


def test_regeocode_all(fake_http: FakeHttp) -> None:
    header = ["Address", *GEOCODE_COLUMNS]
    stale = ["old"] * (len(GEOCODE_COLUMNS) - 1)
    ws = FakeWorksheet([header, ["1 Main St", *stale, address_hash("1 Main St")]])
    fake_http(found)

    summary = google_sheets.geocode_worksheet(ws, "k", regeocode_all=True, osm_delay=0)

    assert summary.geocoded == 1
    assert ws.records()[0]["Azure Address"] != "old"


def test_sheet_without_address_column() -> None:
    with pytest.raises(ChristmasCardsError, match="no 'Address' column"):
        google_sheets.geocode_worksheet(FakeWorksheet([["Name"]]), "k")


# --- the CLI command ------------------------------------------------------------------


@pytest.fixture
def fake_client(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Replace gspread with a client that serves one FakeWorksheet; returns call records."""
    calls: dict[str, Any] = {
        "ws": FakeWorksheet([["First Name", "Last Name", "Address"], ["A", "B", "1 Main St"]])
    }

    class Book:
        sheet1 = calls["ws"]

        def worksheet(self, name: str) -> FakeWorksheet:
            if name != "Addresses":
                raise gspread.WorksheetNotFound(name)
            calls["worksheet"] = name
            return calls["ws"]  # type: ignore[no-any-return]

    class Client:
        def open_by_key(self, key: str) -> Book:
            if key == "missing":
                raise gspread.SpreadsheetNotFound
            calls["key"] = key
            return Book()

        def open_by_url(self, url: str) -> Book:
            calls["url"] = url
            return Book()

    monkeypatch.setattr(google_sheets, "load_credentials", lambda: "creds")
    monkeypatch.setattr(gspread, "authorize", lambda creds: Client())
    return calls


@pytest.mark.usefixtures("azure_key")
def test_geocode_sheet_command(
    run_cli: RunCli, fake_http: FakeHttp, fake_client: dict[str, Any], tmp_path: Path
) -> None:
    (tmp_path / ".secrets.toml").write_text('google_sheet_id = "sheet-key"\n')
    fake_http(found)

    result = run_cli(["geocode", "sheet", "--osm-delay", "0"])
    assert result == "Geocoded 1 addresses; 0 unchanged, 0 without an address."
    assert fake_client["key"] == "sheet-key"

    result = run_cli(["geocode", "sheet", "--osm-delay", "0"])
    assert result == "Geocoded 0 addresses; 1 unchanged, 0 without an address."

    result = run_cli(["geocode", "sheet", "--all", "--osm-delay", "0"])
    assert result == "Geocoded 1 addresses; 0 unchanged, 0 without an address."


@pytest.mark.usefixtures("azure_key")
def test_geocode_sheet_by_url_and_worksheet(
    run_cli: RunCli, fake_http: FakeHttp, fake_client: dict[str, Any]
) -> None:
    fake_http(found)
    url = "https://docs.google.com/spreadsheets/d/abc/edit"
    run_cli(["geocode", "sheet", url, "--worksheet", "Addresses", "--osm-delay", "0"])
    assert fake_client["url"] == url
    assert fake_client["worksheet"] == "Addresses"


@pytest.mark.usefixtures("azure_key", "fake_client")
@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["missing"], "Spreadsheet missing not found"),
        (["k", "--worksheet", "Nope"], "Worksheet 'Nope' not found"),
    ],
)
def test_geocode_sheet_not_found(run_cli: RunCli, args: list[str], message: str) -> None:
    with pytest.raises(ChristmasCardsError, match=message):
        run_cli(["geocode", "sheet", *args])


def test_geocode_sheet_requires_spreadsheet(run_cli: RunCli) -> None:
    with pytest.raises(ChristmasCardsError, match="No spreadsheet"):
        run_cli(["geocode", "sheet"])


# --- credentials ------------------------------------------------------------------------


@pytest.fixture
def fake_service_account(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    calls: dict[str, Any] = {}

    def from_info(info: dict[str, Any], scopes: list[str]) -> str:
        calls["info"] = info
        return "info-creds"

    def from_file(path: str, scopes: list[str]) -> str:
        calls["file"] = path
        return "file-creds"

    monkeypatch.setattr(service_account.Credentials, "from_service_account_info", from_info)
    monkeypatch.setattr(service_account.Credentials, "from_service_account_file", from_file)
    return calls


def test_credentials_from_env_json(
    monkeypatch: pytest.MonkeyPatch, fake_service_account: dict[str, Any]
) -> None:
    monkeypatch.setenv("DYNACONF_GOOGLE_SERVICE_ACCOUNT_INFO", '{"type": "service_account"}')
    creds: object = google_sheets.load_credentials()
    assert creds == "info-creds"
    assert fake_service_account["info"] == {"type": "service_account"}


def test_credentials_from_private_file(
    tmp_path: Path, fake_service_account: dict[str, Any]
) -> None:
    key = tmp_path / "key.json"
    key.write_text("{}")
    key.chmod(0o600)
    (tmp_path / ".secrets.toml").write_text(f"google_service_account_file = '{key}'\n")
    creds: object = google_sheets.load_credentials()
    assert creds == "file-creds"
    assert fake_service_account["file"] == str(key)


@pytest.mark.skipif(os.name != "posix", reason="POSIX file permissions")
@pytest.mark.usefixtures("fake_service_account")
def test_credentials_file_must_be_private(tmp_path: Path) -> None:
    key = tmp_path / "key.json"
    key.write_text("{}")
    key.chmod(0o644)
    (tmp_path / ".secrets.toml").write_text(f"google_service_account_file = '{key}'\n")
    with pytest.raises(ChristmasCardsError, match="chmod 600"):
        google_sheets.load_credentials()


def test_credentials_file_must_exist(tmp_path: Path) -> None:
    (tmp_path / ".secrets.toml").write_text("google_service_account_file = 'nope.json'\n")
    with pytest.raises(ChristmasCardsError, match="does not exist"):
        google_sheets.load_credentials()


def test_application_default_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(google.auth, "default", lambda scopes: ("adc-creds", "project"))
    creds: object = google_sheets.load_credentials()
    assert creds == "adc-creds"


def test_no_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_default(scopes: list[str]) -> None:
        raise DefaultCredentialsError("none")  # type: ignore[no-untyped-call]

    monkeypatch.setattr(google.auth, "default", no_default)
    with pytest.raises(ChristmasCardsError, match="application-default login"):
        google_sheets.load_credentials()
