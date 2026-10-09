"""``xmascards labels``: prepare and print Avery 5160 labels."""

from pathlib import Path

from cyclopts import App

from christmas_cards import labels
from christmas_cards.config import get_settings
from christmas_cards.errors import ChristmasCardsError

app = App(name="labels", help="Prepare and print Avery 5160 mailing and return-address labels.")


@app.command
def prepare(
    geocoded_csv: Path = Path("Geocoded_Addresses.csv"),
    labels_csv: Path = Path("For Labels.csv"),
) -> str:
    """Turn the geocoded address list into one row of label fields per recipient.

    Parameters
    ----------
    geocoded_csv
        Output of ``xmascards geocode csv``.
    labels_csv
        Where to write the label fields.
    """
    count = labels.prepare_label_csv(geocoded_csv, labels_csv)
    return f"Wrote {count} addresses to {labels_csv}"


@app.command(name="print")
def print_labels(
    labels_csv: Path = Path("For Labels.csv"),
    output_pdf: Path = Path("avery_5160_labels.pdf"),
) -> str:
    """Render the mailing labels as a PDF.

    Parameters
    ----------
    labels_csv
        Output of ``xmascards labels prepare``.
    output_pdf
        PDF to write. Print it at 100% scale (see PrintingFromLinux.md).
    """
    count = labels.create_address_labels(labels_csv, output_pdf)
    return f"Wrote {count} labels to {output_pdf}"


@app.command
def return_address(
    output_pdf: Path = Path("avery_5160_return_addresses.pdf"),
    *,
    address: str | None = None,
) -> str:
    """Render a page of return-address labels as a PDF.

    Parameters
    ----------
    output_pdf
        PDF to write.
    address
        Return address, one line per label line. Defaults to ``return_address`` in the settings.
    """
    address = address or get_settings().get("return_address")
    if not address:
        raise ChristmasCardsError(
            "No return address. Pass --address or set return_address in settings.toml."
        )
    labels.create_return_address_labels(address, output_pdf)
    return f"Wrote return-address labels to {output_pdf}"
