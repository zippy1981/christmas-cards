"""Tests for geocoding and the ``xmascards geocode`` subcommand group."""

import csv
import json
from collections.abc import Callable
from pathlib import Path

import pytest

from christmas_cards.errors import ChristmasCardsError
from christmas_cards.geocoding import address_hash
from tests.conftest import FakeResponse, Responder, RunCli

type FakeHttp = Callable[[Responder], list[str]]

OSM_HIT = [
    {
        "address": {"house_number": "1600", "road": "Pennsylvania Avenue NW"},
        "display_name": "White House, Washington, DC",
    }
]
AZURE_HIT = {
    "results": [
        {
            "address": {"streetNumber": "1600", "streetName": "Pennsylvania Avenue NW"},
            "score": 0.98,
        }
    ]
}


def found(url: str) -> FakeResponse:
    return FakeResponse(OSM_HIT if "openstreetmap" in url else AZURE_HIT)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.fixture
def azure_key(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("DYNACONF_AZURE_MAP_KEY", "secret-key")
    return "secret-key"


@pytest.mark.usefixtures("azure_key")
def test_geocode_csv(run_cli: RunCli, fake_http: FakeHttp, tmp_path: Path) -> None:
    write_csv(
        tmp_path / "in.csv",
        [
            {"First Name": "George", "Last Name": "Washington", "Address": "1600 Penn Ave"},
            {"First Name": "No", "Last Name": "Address", "Address": "  "},
        ],
    )
    urls = fake_http(found)

    result = run_cli(["geocode", "csv", "in.csv", "out.csv", "--osm-delay", "0"])

    assert result == "Geocoded addresses saved to out.csv"
    [row] = read_csv(tmp_path / "out.csv")
    assert row["First Name"] == "George"
    assert json.loads(row["OSM Address"])["road"] == "Pennsylvania Avenue NW"
    assert row["OSM DisplayAddress"] == "White House, Washington, DC"
    assert json.loads(row["Azure Address"])["streetNumber"] == "1600"
    assert row["Azure Score"] == "0.98"
    assert "subscription-key=___KEY_HERE___" in row["BINGMAPS_URL"]
    assert row["OSM_URL"] == urls[0]
    assert row["Address Hash"] == address_hash("1600 Penn Ave")
    assert "subscription-key=secret-key" in urls[1]


@pytest.mark.usefixtures("azure_key")
@pytest.mark.parametrize(
    "responder",
    [
        lambda url: FakeResponse([] if "openstreetmap" in url else {"results": []}),
        lambda url: FakeResponse(None, status=500),
    ],
    ids=["no-match", "http-error"],
)
def test_geocode_csv_failed_lookups_leave_blanks(
    run_cli: RunCli, fake_http: FakeHttp, tmp_path: Path, responder: Responder
) -> None:
    write_csv(tmp_path / "in.csv", [{"First Name": "A", "Last Name": "B", "Address": "Nowhere"}])
    fake_http(responder)

    run_cli(["geocode", "csv", "in.csv", "out.csv", "--osm-delay", "0"])

    [row] = read_csv(tmp_path / "out.csv")
    assert row["OSM Address"] == "{}"
    assert row["OSM DisplayAddress"] == ""
    assert row["Azure Address"] == "{}"
    assert row["Azure Score"] == "0"


@pytest.mark.usefixtures("azure_key")
def test_geocode_csv_requires_address_column(run_cli: RunCli, tmp_path: Path) -> None:
    write_csv(tmp_path / "in.csv", [{"First Name": "A", "Last Name": "B"}])
    with pytest.raises(ChristmasCardsError, match="no 'Address' column"):
        run_cli(["geocode", "csv", "in.csv", "out.csv"])


def test_geocode_csv_requires_azure_key(run_cli: RunCli) -> None:
    with pytest.raises(ChristmasCardsError, match="azure_map_key is not set"):
        run_cli(["geocode", "csv"])


def test_azure_key_from_secrets_file(run_cli: RunCli, fake_http: FakeHttp, tmp_path: Path) -> None:
    (tmp_path / ".secrets.toml").write_text('azure_map_key = "from-file"\n')
    write_csv(tmp_path / "in.csv", [{"First Name": "A", "Last Name": "B", "Address": "X"}])
    urls = fake_http(found)

    run_cli(["geocode", "csv", "in.csv", "out.csv", "--osm-delay", "0"])

    assert "subscription-key=from-file" in urls[1]
