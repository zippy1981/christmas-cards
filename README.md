# Justin Dearing's Christmas card Python scripts

[![CI](https://github.com/zippy1981/christmas-cards/actions/workflows/ci.yml/badge.svg)](https://github.com/zippy1981/christmas-cards/actions/workflows/ci.yml)
[![CodeQL](https://github.com/zippy1981/christmas-cards/actions/workflows/codeql.yml/badge.svg)](https://github.com/zippy1981/christmas-cards/actions/workflows/codeql.yml)
[![Lint Markdown](https://github.com/zippy1981/christmas-cards/actions/workflows/markdown-lint.yml/badge.svg)](https://github.com/zippy1981/christmas-cards/actions/workflows/markdown-lint.yml)

These are the scripts I use to cleanse my address book and print Avery 5160 mailing labels.
They are packaged as subcommands of one executable, **`xmascards`**, built with
[Cyclopts](https://cyclopts.readthedocs.io/), in the same way as `git` or `terraform`.

```console
$ xmascards --help
Usage: xmascards COMMAND

Christmas card address geocoding and Avery 5160 label printing.

╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ geocode      Geocode the address list with OpenStreetMap and Azure Maps.     │
│ labels       Prepare and print Avery 5160 mailing and return-address labels. │
│ --help (-h)  Display this message and exit.                                  │
│ --version    Display application version.                                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## History

In 2010 I got married. This lead to the creation of a Google spreadsheet of wedding
invitation mailing addresses which became a Christmas card list. I used the MapQuest API
to geocode them, and this lasted until 2024 when my API key failed.

So then I geocoded them in Python. Then I could not correctly print Avery 5160 labels
because Windows kept scaling them. In previous years I borrowed my parents' printer. In
2023 it just worked. In 2025 the scaling issue reappeared. After much wailing and gnashing
of teeth I realized it worked in 2023 because I printed from Linux.

## How to use

1. Set up a virtual environment (see [Development setup](#development-setup)), or open the
   repository in the dev container.

2. Make a file called `Christmas Card List - Addresses.csv` with at least **First Name**,
   **Last Name** and **Address** columns:

   ```csv
   First Name,Last Name,Address
   George,Washington,1600 Pennsylvania Ave NW Washington DC
   ```

3. Create an Azure Maps account and put the key in `.secrets.toml` (git-ignored), or set
   the `DYNACONF_AZURE_MAP_KEY` environment variable
   ([ADR 0013](docs/adr/0013-configuration-and-secrets-with-dynaconf.md)):

   ```toml
   azure_map_key = "KEY_GOES_HERE"
   ```

4. Run `xmascards geocode csv` to create `Geocoded_Addresses.csv`.

5. Run `xmascards labels prepare` to make `For Labels.csv`.

6. Run `xmascards labels print` to make `avery_5160_labels.pdf`.

7. Optionally, run `xmascards labels return-address` to make a page of return-address
   labels. The address comes from `return_address` in `settings.toml`, or `--address`.

8. Print the PDF at 100% scale. See [Printing from Linux](PrintingFromLinux.md).

Every command takes its input and output paths as optional arguments; run any command with
`--help` for details.

## Development setup

You need Python 3.12 or newer (3.13 is the default; see `.python-version`). Always
work inside a virtual environment ([ADR 0005](docs/adr/0005-virtual-environments-for-development.md)).

```sh
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt -e .
```

`requirements.txt` pins every runtime and dev dependency and is generated from
`pyproject.toml`, so don't edit it by hand. After changing dependencies in `pyproject.toml`,
regenerate it (CI fails if it is out of date;
[ADR 0012](docs/adr/0012-pinned-requirements-txt.md)):

```sh
pip install uv
uv pip compile pyproject.toml --group dev --universal --python-version 3.12 -o requirements.txt
```

The dev container (`.devcontainer/`) has Python 3.13 and PowerShell, and runs the venv
setup above automatically ([ADR 0014](docs/adr/0014-dev-container-with-powershell.md)).

Common tasks (the same commands CI runs):

```sh
pytest                  # tests + coverage (terminal, coverage.xml, htmlcov/)
ruff check .            # lint
ruff format .           # format
mypy                    # strict type-check
xmascards --help        # try the CLI
```

## Project layout

```text
src/christmas_cards/
├── cli.py              # root `xmascards` app; registers subcommand groups
├── config.py           # Dynaconf settings (settings.toml, .secrets.toml, DYNACONF_*)
├── geocoding.py        # OpenStreetMap and Azure Maps lookups
├── labels.py           # Avery 5160 layout and PDF rendering
└── commands/
    ├── geocode.py      # `xmascards geocode ...`
    └── labels.py       # `xmascards labels ...`
tests/                  # pytest suite (coverage gate: 90%)
docs/adr/               # architecture decision records
```

## Adding a subcommand group

1. Create `src/christmas_cards/commands/<name>.py` with an `app = App(name="<name>", help=...)`
   and `@app.command` functions that **return** their result.
2. Register it in `cli.py`:
   `app.command("christmas_cards.commands.<name>:app", name="<name>", help="...")`.
3. Add tests in `tests/test_<name>.py` using the `run_cli` fixture.

See [ADR 0003](docs/adr/0003-single-entry-point-with-subcommands.md) for the reasoning.

## Architecture decisions

Significant decisions are recorded as ADRs in [`docs/adr/`](docs/adr/README.md).
