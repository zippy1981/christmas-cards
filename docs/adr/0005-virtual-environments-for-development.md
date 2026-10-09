# 0005. Use standard-library virtual environments and pip for development

- **Status:** Accepted. The lock-file decision is superseded by [0012](0012-pinned-requirements-txt.md)
- **Date:** 2026-10-09

## Context

Development must happen in isolated virtual environments, never in the system or
user site-packages. We want the lowest-friction setup that works the same on Linux,
macOS and Windows, and the same locally and in CI.

## Decision

- Developers create a project-local virtual environment with the standard library:
  `python -m venv .venv`. `.venv/` is git-ignored.
- After activating it, they upgrade pip and do an editable install with the dev group:

  ```sh
  python -m pip install --upgrade pip
  python -m pip install -e . --group dev
  ```

- `.python-version` names the preferred development interpreter (3.13). pyenv, uv and
  `actions/setup-python` all read this file.
- CI installs into the interpreter that `actions/setup-python` provides. Each job already
  runs on a fresh, ephemeral runner, which gives the same isolation as a venv. The wheel
  smoke test in CI uses a real venv to check the installed console script.
- No lock file is committed yet. This is an application-style CLI with a handful of
  runtime dependencies. Version ranges plus Dependabot keep it current
  ([ADR 0011](0011-dependency-management-with-dependabot.md)).

## Alternatives considered

- **uv.** Much faster, with a cross-platform lock file. But it is an extra tool to install,
  and in CI it needs a third-party action (`astral-sh/setup-uv`), which goes against
  [ADR 0009](0009-ci-with-github-actions.md). It works fine with this layout. Developers
  may use `uv venv && uv pip install -e . --group dev` locally, and we can adopt it fully
  in a superseding ADR.
- **Poetry / PDM / Hatch environments.** Each adds a workflow and configuration on top of
  the standards we already use.
- **Conda.** Unnecessary, since there are no native, non-Python dependencies.

## Consequences

- The only prerequisite is a supported Python. Setup works the same everywhere.
- Builds are not bit-for-bit reproducible without a lock file. If that matters
  (for example, for deployments), revisit with a lock file (`pylock.toml` / PEP 751, or uv).
