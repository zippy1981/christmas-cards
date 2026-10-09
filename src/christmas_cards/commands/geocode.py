"""``xmascards geocode``: geocode the Christmas card address list."""

import csv
from pathlib import Path

from cyclopts import App

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
