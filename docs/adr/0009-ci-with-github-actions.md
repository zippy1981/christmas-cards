# 0009. Run CI on GitHub Actions, preferring first-party actions

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

The repository is hosted on GitHub. Every third-party action we use is code that runs
with access to our repository and tokens, so it adds supply-chain risk and maintenance
burden. A custom shell step duplicates logic that a maintained action already provides.

## Decision

Use GitHub Actions. When choosing how to implement a step, prefer, in order:

1. **Actions maintained by GitHub** (`actions/*`, `github/*`), such as `actions/checkout`,
   `actions/setup-python` (with its built-in pip cache), `actions/upload-artifact`,
   `actions/download-artifact`, `actions/attest-build-provenance`,
   `actions/dependency-review-action` and `github/codeql-action`.
2. **Built-in platform features**, such as job summaries, `--output-format=github`
   annotations, reusable workflows (`workflow_call`) and the preinstalled `gh` CLI.
3. **A short `run:` step** that invokes the project's own tooling (`pip`, `pytest`,
   `ruff`, `mypy`, `python -m build`). These are one-line commands, not custom scripts.
4. **Third-party actions** only with an ADR that justifies them. They must be pinned to
   a full commit SHA.

Workflow layout:

| Workflow | Trigger | Purpose |
| -------- | ------- | ------- |
| `ci.yml` | push to `main`, PRs, manual, `workflow_call` | lint + type-check, test matrix with coverage, build and smoke-test the wheel |
| `release.yml` | tag `v*.*.*` | re-run CI via `workflow_call`, attest, publish a GitHub Release ([ADR 0010](0010-release-process.md)) |
| `codeql.yml` | push, PRs, weekly | static security analysis of Python and workflow files |
| `dependency-review.yml` | PRs | block PRs that introduce vulnerable dependencies |

Hardening applied everywhere: `permissions: contents: read` by default, elevated only
per job where needed; `persist-credentials: false` on checkout; and concurrency that
cancels superseded PR runs.

GitHub-owned actions are pinned to major-version tags. Dependabot keeps them current
([ADR 0011](0011-dependency-management-with-dependabot.md)).

## Alternatives considered

- **Other CI providers (GitLab CI, CircleCI).** Need extra integration, and they lose
  native PR checks, summaries and attestations.
- **tox / nox inside CI.** Useful for running a matrix locally, but adds a layer over
  `actions/setup-python`'s native matrix. They can be added later for local use.
- **SHA-pinning GitHub-owned actions.** Stronger guarantees but noisier diffs. Reserved
  for third-party actions.

## Consequences

- Workflows are short and readable, and use few external dependencies.
- Some conveniences (coverage PR comments, PyPI publishing) are deferred until an ADR
  accepts a specific non-GitHub action.
- CodeQL and dependency review are free for public repositories. If the repository is
  private, they need GitHub Advanced Security, or those two workflows must be removed.
