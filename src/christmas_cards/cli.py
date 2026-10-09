"""Root ``xmascards`` command.

Every feature is a subcommand of this single entry point, in the style of
``git`` or ``terraform``. Subcommand groups live in
:mod:`christmas_cards.commands` and are registered here by import path so
that they are only imported when invoked (see ADR 0003).
"""

import sys
from collections.abc import Sequence

from cyclopts import App

from christmas_cards import __version__
from christmas_cards.errors import ChristmasCardsError

app = App(
    name="xmascards",
    help="Christmas card address geocoding and Avery 5160 label printing.",
    version=__version__,
)

# Register subcommand groups lazily as "<module>:<attribute>". Because the module
# is not imported until the command runs, the help text is supplied here.
app.command(
    "christmas_cards.commands.geocode:app",
    name="geocode",
    help="Geocode the address list with OpenStreetMap and Azure Maps.",
)
app.command(
    "christmas_cards.commands.labels:app",
    name="labels",
    help="Prepare and print Avery 5160 mailing and return-address labels.",
)


def main(argv: Sequence[str] | None = None) -> None:
    """Console-script entry point.

    Parameters
    ----------
    argv
        Arguments excluding the program name; defaults to ``sys.argv[1:]``.
    """
    try:
        app(list(sys.argv[1:] if argv is None else argv))
    except ChristmasCardsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
