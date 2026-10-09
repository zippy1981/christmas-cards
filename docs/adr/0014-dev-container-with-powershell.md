# 0014. Provide a Python dev container with PowerShell

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

The labels must be printed from Linux, because Windows print dialogs rescale the PDF
(see `PrintingFromLinux.md`). The author works mostly from Windows, with PowerShell as
their shell. A dev container gives a ready-made Linux environment from VS Code or
GitHub Codespaces, and having PowerShell inside it keeps the shell familiar.

## Decision

- `.devcontainer/devcontainer.json` uses the Microsoft Python dev container image for
  the development Python version (`3-3.13-bookworm`, matching `.python-version`).
- It adds the `ghcr.io/devcontainers/features/powershell:2` feature (PowerShell LTS).
- `postCreateCommand` creates `.venv` and installs the pinned `requirements.txt` plus the
  package in editable mode, exactly as [ADR 0012](0012-pinned-requirements-txt.md) describes.
- VS Code is pointed at the venv interpreter and gets the Python, mypy, Ruff,
  markdownlint and PowerShell extensions.

## Alternatives considered

- **Debian 13 (trixie) image.** Newer, but Microsoft's PowerShell packages target
  Debian 12 first. Move up once the feature supports it fully.
- **A custom Dockerfile.** More to maintain than an image plus a published feature.

## Consequences

- Dependabot does not update the image tag or feature version; bump them by hand when the
  development Python version changes ([ADR 0006](0006-supported-python-versions.md)).
