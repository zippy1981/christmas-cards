# 0007. Use Ruff for linting/formatting and mypy (strict) for type checking

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

Consistent style and static checking catch bugs early and keep reviews focused on
behavior. Cyclopts derives the CLI from type hints, so accurate annotations are
functional, not just documentation.

## Decision

- **Ruff** is both linter and formatter. It is configured in `pyproject.toml`
  (line length 100, rule sets E/W/F/I/B/UP/SIM/RUF/PT).
- **mypy** in `strict` mode checks `src/` and `tests/`.
- CI runs `ruff check`, `ruff format --check` and `mypy` in a dedicated `lint` job.
  Ruff uses `--output-format=github`, so violations appear as inline annotations on
  pull requests.

## Alternatives considered

- **Black + isort + flake8.** Three tools and three configurations to do what Ruff
  does alone, much faster.
- **Pyright / basedpyright.** Excellent, but distributed via npm or a wrapper. mypy is
  the reference checker and installs with pip. Either could be adopted later.
- **pre-commit hooks.** These complement CI rather than replacing it. Left optional for
  now so contributors aren't forced to install another tool.

## Consequences

- All code must be fully annotated. Untyped third-party libraries will need stubs or a
  targeted `ignore_missing_imports` override.
