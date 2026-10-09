"""Read and write the address list in a Google Sheet.

See ADR 0015 for how the Google credentials are found and kept out of the repository.
"""

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import google.auth
import gspread
import requests
from google.auth.credentials import Credentials
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account
from gspread.utils import rowcol_to_a1

from christmas_cards.config import get_settings
from christmas_cards.errors import ChristmasCardsError
from christmas_cards.geocoding import (
    ADDRESS_HASH_COLUMN,
    GEOCODE_COLUMNS,
    address_hash,
    geocode_row,
    has_address,
)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class Worksheet(Protocol):
    """The parts of :class:`gspread.Worksheet` the geocoder uses."""

    @property
    def col_count(self) -> int: ...

    def get_all_values(self) -> list[list[str]]: ...

    def add_cols(self, cols: int) -> Any: ...

    def update(self, values: list[list[str]], range_name: str | None = None) -> Any: ...

    def batch_update(self, data: list[dict[str, Any]]) -> Any: ...


def _require_private(path: Path) -> None:
    """Refuse a key file that other users on this machine can read."""
    if os.name == "posix" and path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise ChristmasCardsError(
            f"{path} can be read by other users. Restrict it with: chmod 600 '{path}'"
        )


def load_credentials() -> Credentials:
    """Find Google credentials, in order:

    1. ``google_service_account_info``: a service-account key as JSON, normally from the
       ``DYNACONF_GOOGLE_SERVICE_ACCOUNT_INFO`` environment variable or a secret store;
    2. ``google_service_account_file``: the path to a service-account key file, which must
       be readable only by its owner;
    3. Application Default Credentials (``GOOGLE_APPLICATION_CREDENTIALS``, or
       ``gcloud auth application-default login``).
    """
    settings = get_settings()
    info = settings.get("google_service_account_info")
    if info:
        data = json.loads(info) if isinstance(info, str) else dict(info)
        creds: Credentials = service_account.Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
            data, scopes=SCOPES
        )
        return creds

    key_file = settings.get("google_service_account_file")
    if key_file:
        path = Path(key_file).expanduser()
        if not path.is_file():
            raise ChristmasCardsError(f"google_service_account_file {path} does not exist.")
        _require_private(path)
        creds = service_account.Credentials.from_service_account_file(  # type: ignore[no-untyped-call]
            str(path), scopes=SCOPES
        )
        return creds

    try:
        creds, _project = google.auth.default(scopes=SCOPES)
    except DefaultCredentialsError as exc:
        raise ChristmasCardsError(
            "No Google credentials found. Set google_service_account_file in .secrets.toml, "
            "or run: gcloud auth application-default login "
            f"--scopes=https://www.googleapis.com/auth/cloud-platform,{SCOPES[0]}"
        ) from exc
    return creds


def open_worksheet(spreadsheet: str, worksheet: str | None = None) -> gspread.Worksheet:
    """Open ``worksheet`` (default: the first one) of a spreadsheet given by URL or key."""
    client = gspread.authorize(load_credentials())
    try:
        if spreadsheet.startswith("https://"):
            book = client.open_by_url(spreadsheet)
        else:
            book = client.open_by_key(spreadsheet)
        return book.worksheet(worksheet) if worksheet else book.sheet1
    except gspread.SpreadsheetNotFound as exc:
        raise ChristmasCardsError(
            f"Spreadsheet {spreadsheet} not found. If you use a service account, share the "
            "sheet with its client_email."
        ) from exc
    except gspread.WorksheetNotFound as exc:
        raise ChristmasCardsError(f"Worksheet {worksheet!r} not found in {spreadsheet}.") from exc


@dataclass
class GeocodeSummary:
    """How many rows :func:`geocode_worksheet` geocoded, left alone, or skipped."""

    geocoded: int = 0
    unchanged: int = 0
    blank: int = 0


def _ensure_columns(ws: Worksheet, header: list[str]) -> list[str]:
    """Append any missing geocoding columns to the header row; return the new header."""
    missing = [column for column in GEOCODE_COLUMNS if column not in header]
    if not missing:
        return header
    header = header + missing
    if len(header) > ws.col_count:
        ws.add_cols(len(header) - ws.col_count)
    ws.update([header], "A1")
    return header


def geocode_worksheet(
    ws: Worksheet,
    azure_key: str,
    *,
    regeocode_all: bool = False,
    osm_delay: float = 1.0,
    batch_size: int = 10,
) -> GeocodeSummary:
    """Geocode the rows of ``ws`` in place.

    By default only rows whose ``Address Hash`` is missing or no longer matches their
    ``Address`` (new or edited addresses) are geocoded. ``regeocode_all`` redoes every row.
    Results are written back every ``batch_size`` rows, so an interrupted run keeps its
    progress.
    """
    values = ws.get_all_values()
    if not values or "Address" not in values[0]:
        raise ChristmasCardsError("The worksheet has no 'Address' column in its first row.")
    # Rows come back padded to the sheet's width, so drop the header's trailing blanks.
    header = list(values[0])
    while header and not header[-1]:
        header.pop()
    header = _ensure_columns(ws, header)
    column_numbers = {name: index + 1 for index, name in enumerate(header)}

    summary = GeocodeSummary()
    pending: list[dict[str, Any]] = []

    def flush() -> None:
        if pending:
            ws.batch_update(pending)
            pending.clear()

    with requests.Session() as session:
        for row_number, cells in enumerate(values[1:], start=2):
            row = dict(zip(header, cells + [""] * (len(header) - len(cells)), strict=False))
            if not has_address(row):
                summary.blank += 1
                continue
            if not regeocode_all and row[ADDRESS_HASH_COLUMN] == address_hash(row["Address"]):
                summary.unchanged += 1
                continue

            result = geocode_row(session, row, azure_key, osm_delay=osm_delay)
            pending.extend(
                {
                    "range": rowcol_to_a1(row_number, column_numbers[column]),
                    "values": [[result[column]]],
                }
                for column in GEOCODE_COLUMNS
            )
            summary.geocoded += 1
            if summary.geocoded % batch_size == 0:
                flush()
        flush()
    return summary
