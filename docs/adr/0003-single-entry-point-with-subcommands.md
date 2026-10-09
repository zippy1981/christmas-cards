# 0003. Expose every command as a subcommand of a single `xmascards` entry point

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

The project will grow into a series of related commands. Installing each one as a
separate console script fills users' `PATH` with names and makes the commands hard to
discover. Tools like `git`, `terraform` and `kubectl` show a better pattern: one
executable, with features grouped as subcommands.

## Decision

- The project installs exactly one console script, **`xmascards`** (*Christmas cards*),
  defined in `pyproject.toml` as `xmascards = "christmas_cards.cli:main"`. Running
  `python -m christmas_cards` is equivalent.
- The root `cyclopts.App` lives in `src/christmas_cards/cli.py`. It owns global
  behavior (`--help`, `--version`).
- Each subcommand group is its own module in `src/christmas_cards/commands/` and
  exposes a `cyclopts.App` named `app`. The groups nest naturally:
  `xmascards <group> <command> [args]`.
- Groups are registered on the root app **by import path**
  (`app.command("christmas_cards.commands.geocode:app", name="geocode", help=...)`).
  The module is only imported when that command runs, so `xmascards --help` and unrelated
  commands stay fast as heavy dependencies are added. Because the module isn't imported,
  the group's one-line help is passed at registration.
- The original scripts map onto two groups: `xmascards geocode csv` (was `geocode_csv.py`)
  and `xmascards labels prepare|print|return-address` (were `create_address_csv.py`,
  `print_labels.py` and `return+address.py`). The reusable logic lives in plain modules
  (`geocoding.py`, `labels.py`) so the command modules stay thin.

## Alternatives considered

- **One console script per command.** Simpler per command, but scatters the UX and
  clutters the `PATH`.
- **Eager imports of every group.** Simpler registration, but startup time grows with
  every dependency any command uses.
- **Plugin discovery via entry points.** Lets third parties add commands, which we don't
  need. It can be added later without changing the user-facing shape.

## Consequences

- Adding a command group means creating one module, adding one `app.command(...)` line
  in `cli.py`, and writing its tests.
- A typo in a lazy import path only shows up when that command runs. Tests must invoke
  every registered group at least once. The coverage gate in
  [ADR 0008](0008-testing-and-code-coverage.md) enforces this in practice.
