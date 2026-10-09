# 0011. Keep dependencies current with Dependabot, guarded by dependency review and CodeQL

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

Both Python dependencies and GitHub Actions go stale and accumulate vulnerabilities.
Without a lock file ([ADR 0005](0005-virtual-environments-for-development.md)), we
rely on version ranges and need to be prompted to move them forward.

## Decision

- **Dependabot version updates** (`.github/dependabot.yml`), weekly on Mondays, for:
  - `pip`: the `[project]` dependencies in `pyproject.toml`. Minor and patch updates are
    grouped into one PR. Major updates get their own PR, because they need a deliberate
    review (for example Cyclopts majors, see [ADR 0002](0002-use-cyclopts-for-the-cli.md)).
  - `github-actions`: all workflow actions, grouped into one PR.
- PRs are labelled (`dependencies` plus the ecosystem) and use `deps:` / `ci:`
  commit prefixes.
- **Dependabot security updates and alerts** should be enabled in the repository settings
  (*Settings → Code security*). These are repository settings, not files.
- **Dependency review** (`actions/dependency-review-action`) fails any PR, including
  Dependabot's, that introduces a dependency with a known vulnerability of moderate
  severity or higher.
- **CodeQL** scans Python code and workflow files on every PR and weekly.

## Alternatives considered

- **Renovate.** More configurable, but a third-party app. Dependabot is built in and
  sufficient.
- **Manual updates.** These get forgotten.

## Consequences

- Expect up to a few Dependabot PRs per week. CI must stay fast and reliable so they
  can be merged with confidence.
- Dependabot's support for PEP 735 `[dependency-groups]` is still limited, so dev-tool
  minimum versions may need occasional manual bumps.
- The labels `dependencies`, `python` and `github-actions` must exist in the repository,
  or Dependabot will skip labelling.
