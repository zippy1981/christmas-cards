# 0012. Pin the development environment in a generated `requirements.txt`

- **Status:** Accepted
- **Date:** 2026-10-09
- **Supersedes:** the "no lock file" part of [ADR 0005](0005-virtual-environments-for-development.md),
  and "no `requirements*.txt`" in [ADR 0004](0004-packaging-and-project-layout.md)

## Context

[ADR 0005](0005-virtual-environments-for-development.md) deferred a lock file. In practice
that caused two problems:

- Each CI job installed only one dependency group. The lint job had no `pytest`, so
  `mypy` failed type-checking `tests/` with `import-not-found` errors, even though it
  passed in a full local dev environment. Environments differed by job and by day.
- The dev container and many editors and tools expect a conventional
  `pip install -r requirements.txt`.

## Decision

- `requirements.txt` at the repository root pins **every** runtime and development
  dependency (the `dev` group, which includes `test` and `lint`) to exact versions.
  Platform-specific packages carry environment markers.
- It is **generated, never edited by hand**. `pyproject.toml` stays the source of truth
  for version ranges. Regenerate it with:

  ```sh
  uv pip compile pyproject.toml --group dev --universal --python-version 3.12 -o requirements.txt
  ```

  `--universal` resolves for all platforms and Python versions at once. Existing pins are
  kept unless they no longer satisfy `pyproject.toml`. Add `--upgrade` to bump everything.
- Everyone installs the same way: `pip install -r requirements.txt -e .`. That includes
  developers, the dev container and every CI job.
- The CI lint job regenerates the file and fails if it differs from the committed copy.
  This catches a `pyproject.toml` change without a matching regeneration.
- Dependabot's `pip` ecosystem bumps the pins in `requirements.txt`
  ([ADR 0011](0011-dependency-management-with-dependabot.md)).

## Alternatives considered

- **Install `--group dev` in every CI job, with no lock file.** This fixes the mypy failure,
  but builds still aren't reproducible, and it doesn't give the dev container a
  `requirements.txt`.
- **pip-tools (`pip-compile`).** It can't read PEP 735 dependency groups (as of 7.6).
- **`pip lock` / `pylock.toml` (PEP 751).** It is still experimental in pip, and Dependabot
  and most tools don't read it yet. Revisit once support matures.
- **A full `uv` workflow (`uv.lock`).** That would replace pip in development and CI, which
  is a bigger change than this needs. uv is only used here to *generate* the file. It is
  pip-installable, so CI still needs no third-party action
  ([ADR 0009](0009-ci-with-github-actions.md)).

## Consequences

- Local, dev-container and CI environments are identical and reproducible.
- Contributors who change dependencies need `uv` (`pip install uv`) to regenerate the file.
- Installing no longer needs pip ≥ 25.1, because `--group` isn't used. `pip install -e . --group dev`
  still works for anyone who prefers unpinned installs.
