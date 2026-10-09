"""Tests for label layout and the ``xmascards labels`` subcommand group."""

import csv
import json
from itertools import islice
from pathlib import Path

import pytest

from christmas_cards import labels
from christmas_cards.errors import ChristmasCardsError
from tests.conftest import RunCli


def write_geocoded(path: Path, count: int) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, ["First Name", "Last Name", "Azure Address"])
        writer.writeheader()
        for i in range(count):
            address = {
                "streetNumber": str(i),
                "streetName": "Main St",
                "municipality": "Cranford",
                "countrySubdivision": "NJ",
                "extendedPostalCode": "07016-1234",
            }
            if i == 0:
                address["unexpected"] = "only on one row"
            writer.writerow(
                {
                    "First Name": f"Person{i}",
                    "Last Name": "Smith",
                    "Azure Address": json.dumps(address),
                }
            )


def test_label_positions_wrap_rows_and_pages() -> None:
    positions = list(islice(labels.label_positions(), 31))
    first_x, first_y, first_new = positions[0]
    assert first_x == labels.MARGIN_X
    assert first_y == labels.PAGE_HEIGHT - labels.MARGIN_Y - labels.LABEL_HEIGHT
    assert not first_new
    assert positions[1][0] == labels.MARGIN_X + labels.LABEL_WIDTH + labels.SPACING_X
    assert positions[3][:2] == (labels.MARGIN_X, first_y - labels.LABEL_HEIGHT)
    assert [new for *_, new in positions].count(True) == 1
    assert positions[30] == (first_x, first_y, True)


def test_prepare_and_print(run_cli: RunCli, tmp_path: Path) -> None:
    write_geocoded(tmp_path / "Geocoded_Addresses.csv", 31)

    assert run_cli(["labels", "prepare"]) == "Wrote 31 addresses to For Labels.csv"
    with (tmp_path / "For Labels.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["unexpected"] == "only on one row"
    assert rows[1]["unexpected"] == ""
    assert labels.address_lines(rows[1]) == [
        "Person1 Smith",
        "1 Main St",
        "Cranford, NJ 07016-1234",
    ]

    assert run_cli(["labels", "print"]) == "Wrote 31 labels to avery_5160_labels.pdf"
    pdf = (tmp_path / "avery_5160_labels.pdf").read_bytes()
    assert pdf.startswith(b"%PDF")
    assert b"/Count 2" in pdf


def test_prepare_handles_failed_geocode() -> None:
    [row] = labels.prepare_label_rows([{"First Name": "A", "Last Name": "B", "Azure Address": ""}])
    assert row == {"First Name": "A", "Last Name": "B"}
    assert labels.address_lines(row) == ["A B", " ", ",  "]


def test_return_address_from_settings(run_cli: RunCli, tmp_path: Path) -> None:
    (tmp_path / "settings.toml").write_text('return_address = "Me\\n1 Main St"\n')
    result = run_cli(["labels", "return-address"])
    assert result == "Wrote return-address labels to avery_5160_return_addresses.pdf"
    assert (tmp_path / "avery_5160_return_addresses.pdf").read_bytes().startswith(b"%PDF")


def test_return_address_option(run_cli: RunCli, tmp_path: Path) -> None:
    run_cli(["labels", "return-address", "r.pdf", "--address", "Me"])
    assert (tmp_path / "r.pdf").exists()


def test_return_address_required(run_cli: RunCli) -> None:
    with pytest.raises(ChristmasCardsError, match="No return address"):
        run_cli(["labels", "return-address"])
