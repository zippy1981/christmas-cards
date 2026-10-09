"""Geocode addresses with OpenStreetMap Nominatim and Azure Maps."""

import hashlib
import json
import time
from collections.abc import Iterable, Iterator
from typing import Any
from urllib.parse import quote

import requests

USER_AGENT = "Justin Dearing Cristmas Card GeoCoder/1.0 (zippy1981@gmail.com)"
OSM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
AZURE_SEARCH_URL = "https://atlas.microsoft.com/search/address/json"
TIMEOUT_SECONDS = 30

#: Columns added to each row by :func:`geocode_rows`, in output order.
GEOCODE_COLUMNS = [
    "OSM_URL",
    "BINGMAPS_URL",
    "OSM Address",
    "OSM DisplayAddress",
    "Azure Address",
    "Azure Score",
    "Address Hash",
]
ADDRESS_HASH_COLUMN = "Address Hash"

type Row = dict[str, str]


def address_hash(address: str) -> str:
    """Fingerprint ``address`` so a later run can tell whether it has changed.

    Differences in case and whitespace don't count as changes.
    """
    normalized = " ".join(address.split()).casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def osm_url(address: str) -> str:
    """Return the Nominatim search URL for ``address``."""
    return f"{OSM_SEARCH_URL}?q={quote(address)}&format=json&addressdetails=1&limit=1"


def azure_url(address: str, key: str) -> str:
    """Return the Azure Maps address search URL for ``address``."""
    return f"{AZURE_SEARCH_URL}?api-version=1.0&query={quote(address)}&subscription-key={key}"


def _get_json(session: requests.Session, url: str) -> Any:
    response = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def geocode_osm(session: requests.Session, address: str) -> tuple[dict[str, Any], str]:
    """Look up ``address`` with Nominatim.

    Returns the structured address and the display name; both are empty if the lookup fails.
    """
    try:
        results = _get_json(session, osm_url(address))
    except (requests.RequestException, ValueError) as exc:
        print(f"Error geocoding address '{address}' with OpenStreetMap: {exc}")
        return {}, ""
    if not results:
        return {}, ""
    return results[0].get("address", {}), results[0].get("display_name", "")


def geocode_azure(
    session: requests.Session, address: str, key: str
) -> tuple[dict[str, Any], float]:
    """Look up ``address`` with Azure Maps.

    Returns the structured address and the match score; both are empty if the lookup fails.
    """
    try:
        results = _get_json(session, azure_url(address, key)).get("results", [])
    except (requests.RequestException, ValueError) as exc:
        print(f"Error geocoding address '{address}' with Azure Maps: {exc}")
        return {}, 0
    if not results:
        return {}, 0
    return results[0].get("address", {}), results[0].get("score", 0)


def geocode_row(
    session: requests.Session, row: Row, azure_key: str, *, osm_delay: float = 1.0
) -> Row:
    """Return ``row`` with the :data:`GEOCODE_COLUMNS` filled in from its ``Address``."""
    address = row["Address"]
    osm_address, osm_display = geocode_osm(session, address)
    # Nominatim's usage policy allows at most one request per second.
    time.sleep(osm_delay)
    azure_address, azure_score = geocode_azure(session, address, azure_key)
    return {
        **row,
        "OSM_URL": osm_url(address),
        "BINGMAPS_URL": azure_url(address, "___KEY_HERE___"),
        "OSM Address": json.dumps(osm_address),
        "OSM DisplayAddress": osm_display,
        "Azure Address": json.dumps(azure_address),
        "Azure Score": str(azure_score),
        ADDRESS_HASH_COLUMN: address_hash(address),
    }


def has_address(row: Row) -> bool:
    """Whether ``row`` has a non-blank ``Address``."""
    return bool((row.get("Address") or "").strip())


def geocode_rows(rows: Iterable[Row], azure_key: str, *, osm_delay: float = 1.0) -> Iterator[Row]:
    """Geocode every row that has an address, skipping the rest."""
    with requests.Session() as session:
        for row in rows:
            if has_address(row):
                yield geocode_row(session, row, azure_key, osm_delay=osm_delay)
