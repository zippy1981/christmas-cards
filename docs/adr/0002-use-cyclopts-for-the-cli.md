# 0002. Use Cyclopts for the command-line interface

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

The project is a collection of Python commands. We need a CLI framework that:

- supports nested subcommands (see [ADR 0003](0003-single-entry-point-with-subcommands.md)),
- derives arguments, options and help text from ordinary type-hinted functions and
  their docstrings, so commands stay plain, testable Python,
- produces good help and error output, and
- is actively maintained and fully typed.

## Decision

We will use [Cyclopts](https://cyclopts.readthedocs.io/), pinned to the 5.x series
(`cyclopts>=5.1,<6`).

Commands are plain functions that **return** their result rather than printing it.
Cyclopts' default result action prints a non-integer return value and exits 0. Tests
call the app with `result_action="return_value"` and assert on the return value
directly.

## Alternatives considered

- **argparse (stdlib).** No dependency, but very verbose. Types and help are declared
  twice (in the parser and the function), and nested subcommands need a lot of boilerplate.
- **Click.** Mature, but decorator-heavy. Parameters are declared in decorators instead of
  being inferred from type hints, and the typing story is weaker.
- **Typer.** Type-hint driven like Cyclopts, but built on Click, and it relies on
  `Annotated[..., typer.Option()]` for many common cases. Cyclopts handles more
  types natively (unions, literals, dataclasses, lists), parses docstrings for parameter
  help, and supports lazy loading of subcommands by import path.

## Consequences

- Command functions are easy to unit-test without a CLI runner.
- Cyclopts is younger and has a smaller community than Click, and major versions have
  made breaking changes (v3→v4→v5). The upper bound on the pin, together with
  Dependabot ([ADR 0011](0011-dependency-management-with-dependabot.md)), turns major
  upgrades into deliberate, reviewed changes.
