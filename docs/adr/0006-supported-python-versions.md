# 0006. Support Python 3.12 and newer

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

We need to choose the oldest Python we support. Supporting older versions widens
the audience but rules out newer language features and lengthens the CI matrix.
As of October 2026, 3.12, 3.13 and 3.14 are in bugfix or security support. Cyclopts
requires ≥ 3.11.

## Decision

- `requires-python = ">=3.12"`. This allows modern typing syntax such as PEP 695
  `type` aliases and generics.
- CI tests every supported minor version (3.12, 3.13, 3.14) on Linux, plus the
  development version (3.13) on Windows and macOS.
- Development defaults to 3.13 (`.python-version`).
- When a version reaches end of life, a pull request drops it from `requires-python`,
  the classifiers, the CI matrix and Ruff/mypy target versions. New versions are added
  when GitHub's hosted runners provide them.

## Alternatives considered

- **≥ 3.11 (Cyclopts' floor).** 3.11 reaches end of life in October 2027 and would block
  PEP 695 syntax for little benefit in a new project.
- **Latest only (3.14).** Too restrictive for users on LTS distributions.

## Consequences

- The CI matrix has five test jobs, which run in parallel.
