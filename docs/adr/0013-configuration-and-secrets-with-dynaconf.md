# 0013. Keep configuration in Dynaconf, with secrets outside version control

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

The geocoder needs an Azure Maps subscription key, and the return-address labels need
an address. The original scripts already used [Dynaconf](https://www.dynaconf.com/)
with a git-ignored `.secrets.toml`. Secrets must never be committed, but the setup should
stay a one-file affair for a single user running the tool on their own machine.

## Decision

- Settings are loaded by `christmas_cards.config.get_settings()`, a cached Dynaconf
  instance. It reads, in order (later wins):
  1. `settings.toml` in the working directory: committed, **non-secret** settings
     such as `return_address`;
  2. `.secrets.toml` in the working directory: git-ignored (`.secrets.*`), for secrets
     such as `azure_map_key`;
  3. `DYNACONF_*` environment variables (for example `DYNACONF_AZURE_MAP_KEY`), for
     CI, the dev container or anyone who keeps secrets in a password manager or shell profile.
- Both files are looked up by absolute path in the working directory, so Dynaconf never
  picks up a stray file next to the installed package or the test runner.
- Settings are loaded on first use, not at import, so `--help` and commands that don't
  need a secret never touch it, and tests can isolate themselves with an empty directory.
- Commands that need a missing setting fail with a one-line error that names the setting
  and where to put it, rather than a traceback.

## Alternatives considered

- **Plain environment variables only.** Simple, but less convenient for a tool run once
  a year from a checkout; Dynaconf already supports them as an override.
- **OS keyring (`keyring`).** More secure at rest, but adds a dependency and per-platform
  setup for a single API key. Worth revisiting if more secrets arrive.
- **A committed, encrypted secrets file (sops, git-crypt).** Overkill for one user.

## Consequences

- Dynaconf ships no type information, so mypy has an `ignore_missing_imports` override
  for it and `get_settings()` returns `Any`.
- `.secrets.toml` is plain text on disk; users should keep it readable only by themselves
  (`chmod 600 .secrets.toml`).
