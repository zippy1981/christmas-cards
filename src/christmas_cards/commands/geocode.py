"""``xmascards geocode``: geocode the Christmas card address list."""

import csv
from pathlib import Path
from typing import Annotated

from cyclopts import App, Parameter

from christmas_cards.config import get_settings
from christmas_cards.errors import ChristmasCardsError
from christmas_cards.geocoding import GEOCODE_COLUMNS, geocode_rows

app = App(name="geocode", help="Geocode the address list with OpenStreetMap and Azure Maps.")


def azure_map_key() -> str:
    """Return the Azure Maps key from the settings, failing if it isn't set."""
    key: str | None = get_settings().get("azure_map_key")
    if not key:
        raise ChristmasCardsError(
            "azure_map_key is not set. Put it in .secrets.toml or set DYNACONF_AZURE_MAP_KEY."
        )
    return key


@app.command(name="csv")
def geocode_csv(
    input_csv: Path = Path("Christmas Card List - Addresses.csv"),
    output_csv: Path = Path("Geocoded_Addresses.csv"),
    *,
    osm_delay: float = 1.0,
) -> str:
    """Geocode a CSV address list into a new CSV.

    The input needs at least **First Name**, **Last Name** and **Address** columns.
    Rows with a blank address are dropped.

    Parameters
    ----------
    input_csv
        Address list to read.
    output_csv
        Where to write the input columns plus the geocoding results.
    osm_delay
        Seconds to wait after each OpenStreetMap request (its usage policy allows one per second).
    """
    key = azure_map_key()
    with input_csv.open(newline="", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames or [])
        if "Address" not in fieldnames:
            raise ChristmasCardsError(f"{input_csv} has no 'Address' column.")
        rows = list(geocode_rows(reader, key, osm_delay=osm_delay))

    columns = fieldnames + [c for c in GEOCODE_COLUMNS if c not in fieldnames]
    with output_csv.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, columns)
        writer.writeheader()
        writer.writerows(rows)
    return f"Geocoded addresses saved to {output_csv}"


@app.command
def sheet(
    spreadsheet: str | None = None,
    *,
    worksheet: str | None = None,
    regeocode_all: Annotated[bool, Parameter(name="--all")] = False,
    osm_delay: float = 1.0,
) -> str:
    """Geocode a Google Sheet in place.

    The sheet needs at least **First Name**, **Last Name** and **Address** columns. The
    geocoding columns, including an **Address Hash** of each geocoded address, are added
    if they are missing. Only new and changed addresses are geocoded unless ``--all`` is given.

    Parameters
    ----------
    spreadsheet
        Spreadsheet URL or key. Defaults to ``google_sheet_id`` in the settings.
    worksheet
        Worksheet (tab) name. Defaults to ``google_worksheet`` in the settings, then the first tab.
    regeocode_all
        Re-geocode every address, even ones that haven't changed.
    osm_delay
        Seconds to wait after each OpenStreetMap request (its usage policy allows one per second).
    """
    settings = get_settings()
    spreadsheet = spreadsheet or settings.get("google_sheet_id")
    if not spreadsheet:
        raise ChristmasCardsError(
            "No spreadsheet. Pass one, or set google_sheet_id in settings.toml or .secrets.toml."
        )
    key = azure_map_key()
    # Imported here so the Google libraries only load for this command.
    from christmas_cards import google_sheets

    ws = google_sheets.open_worksheet(spreadsheet, worksheet or settings.get("google_worksheet"))
    summary = google_sheets.geocode_worksheet(
        ws, key, regeocode_all=regeocode_all, osm_delay=osm_delay
    )
    return (
        f"Geocoded {summary.geocoded} addresses; {summary.unchanged} unchanged, "
        f"{summary.blank} without an address."
    )
