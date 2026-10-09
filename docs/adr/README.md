# Architecture Decision Records

This directory records the significant decisions made for this project, using
the lightweight format described in [ADR 0001](0001-record-architecture-decisions.md).
ADRs 0001–0012 were adopted from the sibling
[tax-data-collection](https://github.com/zippy1981/tax-data-collection) project.

| ADR | Title | Status |
| --- | ----- | ------ |
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-use-cyclopts-for-the-cli.md) | Use Cyclopts for the command-line interface | Accepted |
| [0003](0003-single-entry-point-with-subcommands.md) | Expose every command as a subcommand of a single `xmascards` entry point | Accepted |
| [0004](0004-packaging-and-project-layout.md) | Use a `src` layout, `pyproject.toml`, Hatchling and PEP 735 dependency groups | Accepted (amended by 0012) |
| [0005](0005-virtual-environments-for-development.md) | Use standard-library virtual environments and pip for development | Accepted (lock file: superseded by 0012) |
| [0006](0006-supported-python-versions.md) | Support Python 3.12 and newer | Accepted |
| [0007](0007-linting-formatting-and-type-checking.md) | Use Ruff for linting/formatting and mypy (strict) for type checking | Accepted |
| [0008](0008-testing-and-code-coverage.md) | Test with pytest and report coverage from coverage.py inside GitHub | Accepted |
| [0009](0009-ci-with-github-actions.md) | Run CI on GitHub Actions, preferring first-party actions | Accepted |
| [0010](0010-release-process.md) | Release by tag to GitHub Releases with build provenance | Accepted |
| [0011](0011-dependency-management-with-dependabot.md) | Keep dependencies current with Dependabot, guarded by dependency review and CodeQL | Accepted |
| [0012](0012-pinned-requirements-txt.md) | Pin the development environment in a generated `requirements.txt` | Accepted |
| [0013](0013-configuration-and-secrets-with-dynaconf.md) | Keep configuration in Dynaconf, with secrets outside version control | Accepted |
| [0014](0014-dev-container-with-powershell.md) | Provide a Python dev container with PowerShell | Accepted |
| [0015](0015-google-sheets-source-and-credentials.md) | Geocode the address list in place in a Google Sheet, re-geocoding only changed addresses | Accepted |

## Adding a new ADR

1. Copy [`template.md`](template.md) to `NNNN-short-title.md`, using the next free number.
2. Fill it in and set the status to **Proposed** in your pull request.
3. Change the status to **Accepted** when the PR merges, and add a row to the table above.
4. Never rewrite an accepted ADR's decision. To change course, write a new ADR and mark
   the old one **Superseded by NNNN**.
