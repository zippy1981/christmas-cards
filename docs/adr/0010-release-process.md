# 0010. Release by tag to GitHub Releases with build provenance

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

The "CD" half of CI/CD needs a repeatable way to produce versioned, verifiable artifacts.
There is no requirement yet to publish to PyPI.

## Decision

- Releases are cut by pushing a tag `vX.Y.Z` that matches `version` in `pyproject.toml`.
- `release.yml` calls `ci.yml` as a reusable workflow. The full lint, test and build
  pipeline runs against the tagged commit, and its `dist` artifact (sdist + wheel)
  becomes the release payload. Nothing is rebuilt outside CI.
- `actions/attest-build-provenance` creates signed SLSA build-provenance attestations
  for the artifacts (verifiable with `gh attestation verify`).
- The preinstalled `gh` CLI creates the GitHub Release with auto-generated notes and
  attaches the artifacts.
- Versioning follows [Semantic Versioning](https://semver.org/).

## Alternatives considered

- **Publish to PyPI now** via `pypa/gh-action-pypi-publish` with trusted publishing.
  This is the recommended path when PyPI distribution is wanted. It is deferred because
  it isn't needed yet and the action is not GitHub-owned. Adding it later is one job plus
  a PyPI trusted-publisher configuration.
- **Third-party release actions** (for example `softprops/action-gh-release`). These are
  unnecessary because `gh release create` is preinstalled and maintained by GitHub.
- **release-please / semantic-release.** Automated versioning is useful at higher release
  cadence. Revisit later.

## Consequences

- A release is: bump `version`, merge, `git tag vX.Y.Z && git push origin vX.Y.Z`.
- If the tag and `pyproject.toml` disagree, the artifacts carry the `pyproject.toml`
  version. Reviewers must check the bump.
