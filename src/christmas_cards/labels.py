"""Lay out Avery 5160 address labels (30 per US Letter page) as a PDF."""

import csv
import json
from collections.abc import Iterable, Iterator
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

PAGE_WIDTH, PAGE_HEIGHT = letter
LABEL_WIDTH = 2.625 * inch
LABEL_HEIGHT = 1.0 * inch
MARGIN_X = 0.1875 * inch
MARGIN_Y = 0.5 * inch
SPACING_X = 0.125 * inch
SPACING_Y = 0.0 * inch
COLUMNS = 3
LABELS_PER_PAGE = 30
FONT_NAME = "Helvetica"
FONT_SIZE = 10

type Row = dict[str, str]


def label_positions() -> Iterator[tuple[float, float, bool]]:
    """Yield ``(x, y, new_page)`` for the bottom-left corner of each label, forever.

    ``new_page`` is true for the first label of every page after the first.
    """
    count = 0
    while True:
        index = count % LABELS_PER_PAGE
        row, column = divmod(index, COLUMNS)
        x = MARGIN_X + column * (LABEL_WIDTH + SPACING_X)
        y = PAGE_HEIGHT - MARGIN_Y - LABEL_HEIGHT - row * (LABEL_HEIGHT + SPACING_Y)
        yield x, y, count > 0 and index == 0
        count += 1


def prepare_label_rows(geocoded_rows: Iterable[Row]) -> list[Row]:
    """Flatten each row's ``Azure Address`` JSON, keeping the names alongside it."""
    data: list[Row] = []
    for row in geocoded_rows:
        address: Row = {k: str(v) for k, v in json.loads(row["Azure Address"] or "{}").items()}
        address["First Name"] = row["First Name"]
        address["Last Name"] = row["Last Name"]
        data.append(address)
    return data


def prepare_label_csv(geocoded_csv: Path, labels_csv: Path) -> int:
    """Write the label data for ``geocoded_csv`` to ``labels_csv``; return the row count."""
    with geocoded_csv.open(newline="", encoding="utf-8") as infile:
        data = prepare_label_rows(csv.DictReader(infile))

    # Not every address has every field, so collect the columns from all rows.
    columns = sorted({column for row in data for column in row})
    with labels_csv.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, columns)
        writer.writeheader()
        writer.writerows(data)
    return len(data)


def address_lines(row: Row) -> list[str]:
    """The three lines printed on a mailing label for ``row``."""
    return [
        f"{row['First Name']} {row['Last Name']}",
        f"{row.get('streetNumber', '')} {row.get('streetName', '')}",
        f"{row.get('municipality', '')}, {row.get('countrySubdivision', '')} "
        f"{row.get('extendedPostalCode', '')}",
    ]


def create_address_labels(labels_csv: Path, output_pdf: Path) -> int:
    """Render one mailing label per row of ``labels_csv``; return the label count."""
    c = canvas.Canvas(str(output_pdf), pagesize=letter)

    # A border around the first page helps check the printer isn't scaling the page.
    border_thickness = 2  # px
    c.setLineWidth(border_thickness / 72 * inch)
    c.rect(0, 0, PAGE_WIDTH - 2, PAGE_HEIGHT - 2, stroke=1, fill=0)

    count = 0
    with labels_csv.open(newline="", encoding="utf-8") as infile:
        for row, (x, y, new_page) in zip(csv.DictReader(infile), label_positions(), strict=False):
            if new_page:
                c.showPage()
            c.setFont(FONT_NAME, FONT_SIZE)
            text = c.beginText(x + 0.1 * inch, y + 0.6 * inch)
            for line in address_lines(row):
                text.textLine(line)
            c.drawText(text)
            count += 1
    c.save()
    return count


def create_return_address_labels(return_address: str, output_pdf: Path) -> None:
    """Render a full page of ``return_address`` labels."""
    c = canvas.Canvas(str(output_pdf), pagesize=letter)
    for _, (x, y, _new_page) in zip(range(LABELS_PER_PAGE), label_positions(), strict=False):
        c.setFont(FONT_NAME, FONT_SIZE)
        text_y = y + 0.8 * inch
        for line in return_address.splitlines():
            c.drawString(x + 0.1 * inch, text_y, line)
            text_y -= 0.13 * inch
    c.save()
