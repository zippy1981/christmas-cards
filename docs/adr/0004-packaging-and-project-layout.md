# 0004. Use a `src` layout, `pyproject.toml`, Hatchling and PEP 735 dependency groups

- **Status:** Accepted. Amended by [0012](0012-pinned-requirements-txt.md), which adds a generated `requirements.txt`
- **Date:** 2026-10-09

## Context

We need a standard way to declare metadata and dependencies, build distributions, and
configure tools. We also want tests to run against the *installed* package, not whatever
happens to be importable from the repository root.

## Decision

- **`src` layout:** code lives in `src/christmas_cards/`. It can only be imported
  once installed (editable installs in development), which catches packaging mistakes early.
- **Single `pyproject.toml`** for metadata (PEP 621) and all tool configuration
  (pytest, coverage, ruff, mypy). There is no `setup.py`, `setup.cfg` or `requirements*.txt`.
- **Hatchling** is the build backend.
- **Development dependencies** are declared as [PEP 735](https://peps.python.org/pep-0735/)
  `[dependency-groups]`: `test`, `lint`, and `dev` (which includes both). Groups are not
  published as package extras. CI installs only the group a job needs.
- The version is static in `pyproject.toml`. At runtime it is read with
  `importlib.metadata`, so there is a single source of truth.
- The package ships `py.typed` (PEP 561).

## Alternatives considered

- **Flat layout.** Tests can accidentally import the source tree instead of the installed package.
- **setuptools.** Works, but needs more configuration for the same result. Hatchling is
  minimal and standards-based.
- **`[project.optional-dependencies]` for dev tools.** This publishes them as installable
  extras (`pip install christmas-cards[dev]`), which is not their purpose.
- **Dynamic versioning from git tags (hatch-vcs).** Worth revisiting once releases are
  frequent. For now, a static version is simpler to reason about.

## Consequences

- Installing dependency groups needs pip ≥ 25.1 (`pip install --group dev`).
  [ADR 0005](0005-virtual-environments-for-development.md) covers upgrading pip in a new venv.
- Releasing requires bumping `version` in `pyproject.toml`
  ([ADR 0010](0010-release-process.md)).
