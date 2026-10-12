# Source adapter: SharePoint / OneDrive / any folder of files

The engine reads `.xlsx`, `.xlsm` and `.csv` files. It does not care where they came from, so there are
two ways to get SharePoint files in front of it.

## Mode A - synced folder (default, most robust)

The user syncs the SharePoint document library with the OneDrive app (SharePoint -> "Sync"). The files then
sit in a normal folder on the Mac, for example
`~/Library/CloudStorage/OneDrive-Contoso/Finance - Documents/GL`.

* Each configured path is a **host path** to a folder (read every file in it, recursively) or to one file.
* In every session: `request_cowork_directory(path=<host path>)` (skip if the path is inside a folder that is
  already mounted), find where it landed (`ls -d /sessions/*/mnt/*`), then
  `python3 REF/tbr.py map-path --store STORE --host <host path> --sandbox <sandbox path>`.
* No size limit, no base64, keeps working unattended. Tell the user: "Files On-Demand" must be set to
  *Always keep on this device* for these folders, otherwise a cloud-only placeholder cannot be read.

## Mode B - Microsoft 365 connector (optional)

Use only when the user cannot sync the library. Connector tool names differ, so discover them:
`ToolSearch` for `sharepoint`, `onedrive`, `microsoft 365`. If nothing is found, stop and tell the user to either
connect Microsoft 365 or switch to Mode A (use `suggest_connectors`).

`paths` keeps the SharePoint/OneDrive locations (URL or `folder/subfolder`). In connector mode the engine does NOT look
for them on disk; it reads only `STORE/.state/inbox/<dataset>/`, where you put the downloads. Address a OneDrive
location with `read_resource` as `file:///{driveId}/{folder path}` (list the drive root first with
`drive:///users/me`); folder item ids in listings run into the next name, so prefer paths over copied ids.
If the connector returns a workbook as text rather than bytes, do not fake it: use Mode A, or tell the user the file
has to be placed in the inbox another way.

For each configured path (SharePoint URL or `site/library/folder`):
1. List the folder; keep `.xlsx/.xlsm/.csv` only; apply the dataset's `pattern` if set.
2. Download each file and write the bytes to `STORE/.state/inbox/<dataset>/<same file name>`
   (`dataset` is one of `ledger`, `accounts`, `entities`, `fx`, `periods`). Connector downloads arrive as base64
   text inside the conversation: decode and write with bash (`base64 -d`). Skip a download when the connector's
   size/modified-time metadata says it has not changed since the last run (keep a note in `.state/inbox_index.json`).
3. If a file is too large to pass through the conversation, stop with a clear message recommending Mode A.
4. Never delete files from `inbox/` yourself. The engine reads that folder automatically as an extra location.

## The five datasets (roles)

| Role | What it holds | Minimum columns (names are flexible) |
|---|---|---|
| ledger | one row per entity, account and month of **activity** in the entity's own currency | entity, account, period (or date), amount (or debit + credit) |
| accounts | chart of accounts | account, type (Asset, Liability, Equity, Income, Expense ... any common label) |
| entities | the legal entities | entity, currency; optional parent, display name |
| fx | monthly rates, reporting currency per 1 unit of local | currency, period, closing; optional average, historical |
| periods | month status | period, status (open/closed) - or set `closed_through` in config instead |

Several roles may live in one workbook (different sheets) - give the same file for each role and set
`sources.<role>.sheet` if the sheet name is not obvious.

Opening balances: the ledger must start at the first month ever recorded, or include one month of **opening
balance** rows (balance-sheet accounts only) dated before the first activity. Without that the balance sheet
will not tie.

## Column mapping (the user's data will not match our headers)

1. `tbr.py inspect` reads the real files and returns, per sheet: the detected header row, the columns it matched
   by itself, and for every **required** field it could not match, the user's own headers ranked by similarity
   (`suggestions`).
2. Show a chat form with one question per unmatched field; the options are the user's actual headers
   (see `forms/mapping.html`). Save the answers to config:
   `sources.<dataset>.columns = {"amount": "Amount (local currency)"}`.
   Different layouts per file -> `sources.<dataset>.file_columns = {"GL_*.csv": {"amount": "Net Activity"}}`.
3. Saved headers are tried first; built-in aliases are the fallback; nothing is ever guessed during an
   unattended run. A missing column fails the run with the column name in the email.
4. Also handled: month-per-column ledgers (headers like `Jan-26`, `Feb-26`), separate debit and credit columns,
   dates instead of periods, decimal commas (`decimal_separator`), credits-positive exports
   (`sign_convention`), account-type words via `sources.accounts.type_map = {"Cash": "asset"}`, status words
   via `sources.periods.status_map = {"Locked": "closed"}`.

## Change detection

Each ledger file is fingerprinted (SHA-256). Unchanged files are not re-read. A changed file replaces all of its
own entity-months. A file that vanishes fails the run (guards against sync glitches) unless the user passes
`--accept-removed`. A file modified within `settle_seconds` (default 120) is treated as still uploading.
