# 0015. Geocode the address list in place in a Google Sheet, re-geocoding only changed addresses

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

The address list has lived in a Google Sheet since 2010. Exporting it to CSV, geocoding the
CSV and copying results back by hand is tedious, and geocoding every row on every run is
slow (Nominatim allows one request per second) and spends Azure Maps quota on addresses
that haven't changed. Reading the sheet needs Google credentials, which must never be
committed and should be readable only by their owner.

## Decision

- `xmascards geocode sheet [SPREADSHEET] [--worksheet NAME] [--all]` reads a worksheet with
  [gspread](https://docs.gspread.org/) and writes the geocoding columns back into the same
  rows. Missing columns are appended to the header row. `geocode csv` is unchanged apart
  from gaining the new column.
- Each geocoded row stores an **Address Hash**: the SHA-256 of the address after collapsing
  whitespace and case-folding. By default a row is geocoded only when its hash is missing
  (a new row) or differs (an edited address). `--all` re-geocodes every row.
- Results are written with `batch_update` every 10 rows, as raw values (so JSON and scores
  aren't reinterpreted by Sheets), and an interrupted run keeps its progress.
- The spreadsheet is given as an argument or the `google_sheet_id` setting; it may be a URL
  or a key.
- **Credentials** use the `https://www.googleapis.com/auth/spreadsheets` scope and are found,
  in order:
  1. `google_service_account_info`: a service-account key as JSON, meant to come from the
     `DYNACONF_GOOGLE_SERVICE_ACCOUNT_INFO` environment variable populated by a secret store
     (a password manager CLI, GitHub Codespaces secrets, and so on), so the key never touches
     the disk;
  2. `google_service_account_file`: the path to a key file kept **outside the repository**
     (we suggest `~/.config/christmas-cards/service-account.json`). On POSIX systems the
     command refuses a file that group or other users can read, and tells you to `chmod 600` it;
  3. Google Application Default Credentials (`GOOGLE_APPLICATION_CREDENTIALS`, or
     `gcloud auth application-default login` with the Sheets scope), which avoids a
     long-lived key altogether.
- `.gitignore` additionally ignores `*service-account*.json`, `client_secret*.json` and
  `credentials*.json` as a safety net.
- The Google libraries are imported only when `geocode sheet` runs (see
  [ADR 0003](0003-single-entry-point-with-subcommands.md)).

## Alternatives considered

- **Google Sheets API via `google-api-python-client`.** Official, but much lower level and
  poorly typed; gspread wraps the same API with a small, typed interface.
- **An OAuth desktop client (installed-app flow) with a cached refresh token.** Acts as the
  user, so no sharing is needed, but it needs a Google Cloud OAuth consent screen and stores
  a refresh token with access to all of the user's sheets. A service account only sees the
  sheets shared with it.
- **Storing the key in `.secrets.toml`.** Works, but puts a long-lived private key in the
  working tree, one `git add -f` away from being committed.
- **Change detection by comparing against the previous geocoded address.** Fragile, because
  the geocoder reformats addresses; a hash of the input is exact and compact.
- **Re-geocoding failed lookups automatically.** Rows that failed keep their hash and are
  retried only with `--all`, so a permanently bad address doesn't cost a lookup on every run.

## Consequences

- A service account must be created in Google Cloud with the Sheets API enabled, and the
  sheet shared with its `client_email` as an editor.
- Editing an address in the sheet is enough to have it re-geocoded on the next run.
- `labels prepare` still reads a CSV; download the geocoded sheet as CSV
  (`Geocoded_Addresses.csv`) to make labels.
