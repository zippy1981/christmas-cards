# 0001. Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

The project started as a handful of loose scripts and is being restructured into an
installable package. Many of the choices made now (CLI framework, tooling, CI design)
will shape it for a long time, and the reasoning behind them is easily
lost. Future contributors, human or AI, need to know *why* things are the way they
are before changing them.

## Decision

We will record every architecturally significant decision as an Architecture
Decision Record (ADR), following Michael Nygard's format
([original post](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)),
with an added "Alternatives considered" section.

- ADRs live in `docs/adr/` as Markdown, numbered sequentially (`NNNN-title.md`).
- [`template.md`](template.md) is the starting point, and [`README.md`](README.md) is the index.
- Accepted ADRs are immutable. A change of direction is a new ADR that supersedes the old one.
- A pull request that makes a significant decision includes its ADR.
- ADRs 0001–0012 were adopted from the sibling
  [tax-data-collection](https://github.com/zippy1981/tax-data-collection) project, which
  uses the same structure and tooling, and adapted to this project's names.

## Alternatives considered

- **No formal records / commit messages only.** Reasoning gets scattered and is hard to find.
- **Wiki pages.** These live outside the repository, so they aren't reviewed alongside the code
  and drift from it.
- **MADR or other heavier templates.** More structure than a small project needs. Nothing
  stops us adopting one later.

## Consequences

- Decisions are reviewable in pull requests, versioned with the code, and searchable.
- There is a small overhead to writing an ADR for each significant change.
