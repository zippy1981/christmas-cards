# 0008. Test with pytest and report coverage from coverage.py inside GitHub

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

We need a test framework and code-coverage reporting that is visible on every CI run,
without depending on an external SaaS account if we can avoid it.

## Decision

- **pytest** is the test runner. **pytest-cov** (coverage.py) measures line *and* branch
  coverage. All options live in `pyproject.toml`, so a bare `pytest` locally does exactly
  what CI does.
- Warnings are errors (`filterwarnings = ["error"]`).
- Every test run writes a terminal report, `coverage.xml` (Cobertura) and `htmlcov/`.
- **Quality gate:** `fail_under = 90`. The build fails if total coverage drops below 90%.
- **Reporting in GitHub (first-party only):**
  - each test job appends `coverage report --format=markdown` to the **job summary**
    (`$GITHUB_STEP_SUMMARY`), which is visible on the workflow run page;
  - `coverage.xml`, the HTML report and `junit.xml` are uploaded with
    `actions/upload-artifact` for download and further tooling.

## Alternatives considered

- **Codecov / Coveralls.** These offer PR comments, history and badges, but need a
  third-party service, an action and (for Codecov) a token. They can be added later
  because `coverage.xml` is already produced.
- **Third-party PR-comment actions** (for example `py-cov-action/python-coverage-comment-action`).
  Rejected for now under [ADR 0009](0009-ci-with-github-actions.md).
- **unittest.** More boilerplate, and weaker fixtures and parametrization.

## Consequences

- Coverage is visible on every run with no external accounts.
- There is no coverage trend history or badge yet. If one is wanted, adopt a service in
  a new ADR.
- The 90% threshold should rise once real commands land.
