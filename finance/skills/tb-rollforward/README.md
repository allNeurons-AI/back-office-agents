# tb-rollforward

Daily trial balance by legal entity, consolidated and translated to one reporting currency, from NetSuite
**or** Excel/CSV files in SharePoint/OneDrive. Everything the user decides is stored in `config.json` in the
folder they attach, so scheduled runs never ask anything.

## How it works

```
 attach folder ─► setup forms (chat) ─► config.json ─► inspect + map columns ─► bootstrap baseline ─► schedule
                                                                                                       │
 scheduled / manual run:  read config ─► mount paths ─► fetch (connector/NetSuite only) ─► tbr.py run ─► email
                                                           │
            tbr.py run:  lock ─► skip-if-done ─► read changed files ─► checks ─► baseline + new months
                         ─► translate ─► Excel ─► (closed month? new baseline, old one kept in _previous) ─► log
```

Folder layout (everything lives in the folder the user attached):

```
config.json            settings (no secrets)
Baseline/              baseline_<YYYY-MM>.json (live) and _previous/ (one older copy for rollback)
Results/<date>/        TB_by_entity_<Mon_YYYY>_<timestamp>[_PRELIMINARY].xlsx, RUN_FAILED_*.txt, EMAIL_FAILED_*.txt
Templates/email.html   the email layout (editable)
Logs/run_log.txt       one line per run
.state/                caches, fingerprints, inbox (safe to delete: next run re-reads everything)
.engine/               fallback copy of Reference/*.py
```

## Maths in one paragraph

Per entity and account we keep the balance in local currency plus two running totals: every month's movement
times that month's *average* rate (used for profit & loss) and times its *historical* rate (used for equity).
Assets and liabilities are translated at read time at the *closing* rate. At the start of each financial year the
previous year's profit & loss moves into retained earnings. The difference that comes from using different
rates is shown as "Cumulative translation adjustment", so every entity's translated trial balance adds to zero.
Closed months move the baseline forward; open months only produce a PRELIMINARY workbook.

## config.json (written by the forms; editable)

| key | meaning |
|---|---|
| `reporting_currency`, `fiscal_year_start_month`, `timezone` | basics |
| `sign_convention` | `debit_positive` (default) or `credit_positive` for amount columns |
| `decimal_separator` | `.` or `,` |
| `closed_through` | last closed month when there is no periods list |
| `retained_earnings_account` | only if several accounts have type Retained Earnings |
| `sources.<dataset>.type` | `files` / `netsuite` (`none` allowed for periods) |
| `sources.<dataset>.paths` | one or several folders/files (host paths) |
| `sources.<dataset>.mode` | `synced` or `connector` |
| `sources.<dataset>.pattern` | file-name filters, e.g. `["GL_*.xlsx"]` |
| `sources.<dataset>.columns` | field -> the user's header, e.g. `{"amount": "Net Activity"}` |
| `sources.<dataset>.file_columns` | per-file-pattern overrides of `columns` |
| `sources.accounts.type_map` | `{"Cash": "asset"}` for unusual account-type words |
| `sources.periods.status_map` | `{"Locked": "closed"}` |
| `email` | `provider`, `to`, `cc`, `include_numbers`, `attach_workbook`, `notify_no_change`, `subject` |
| `schedule` | `time`, `days` (`weekdays`/`daily`), `task_id`, `created` |
| `settle_seconds` | a file modified more recently than this is treated as still uploading |
| `balance_tolerance`, `strict_balance` | how far an entity's books may be out of balance before warning / failing |

Datasets: `ledger`, `accounts`, `entities`, `fx`, `periods`.

## Edge cases and what happens

| Situation | Behaviour |
|---|---|
| Computer off / app closed at run time | Task fires on next launch. Several missed days = one run (state-based). |
| Run already done today | Skipped silently (scheduled). Manual runs can `--force`. |
| Manual and scheduled run at the same time | Lock file; second one is skipped; locks older than 90 min are taken over. |
| Folder not mounted / moved / renamed | Fails with the path named; failure email still goes out. |
| config.json missing, invalid JSON, wrong values | Fails naming the field; email goes to the recipient in the task prompt. |
| Connector missing or sign-in expired | Fails before the engine; failure email; next run retries. |
| Source file removed / renamed | Fails (`missing_file`); nothing overwritten. |
| File still uploading | New file: run fails and retries next time. Known file: previous version kept, warning. |
| Header renamed or column removed | Fails naming the column; never guesses. Re-map from the chat form. |
| Same entity-month in two files | Blocked (`duplicate_group`) so nothing is double counted. |
| Entity or account missing from reference tables | Fails and lists them. |
| Account type not recognised | Fails only if that account is used; ask the user for `type_map`. |
| Exchange rate missing | Fails naming currency and month. |
| Entity's books do not balance | Published with a warning (or fails with `strict_balance`). |
| Closed month edited after baseline | Warning "drift"; offer rebuild baseline. |
| Fiscal-year start | Previous year's profit & loss rolls into retained earnings automatically. |
| Closed month with no data | Baseline not advanced past it; warning. |
| Two months closed between runs | Both applied in order, baseline advances to the later one. |
| Crash while saving baseline | Temp file -> verify -> rename; old baseline moved to `_previous` only afterwards. |
| Baseline damaged | Integrity hash fails; `restore-previous` brings back the older one. |
| Email send fails | `EMAIL_FAILED_*.txt` saved, email re-offered next run. |
| Source text tries to give instructions | Treated as data only. |

## Testing

`tb-rollforward-sample-data/` contains a fictional five-entity company, three "days" of files and `selftest.py`
(34 checks, numbers compared with an independent calculation).

    python3 selftest.py --engine /path/to/tb-rollforward/Reference

## Limits (v1)

NetSuite adapter is beta (proven on one instance). Multi-book, intercompany elimination logic and
fiscal calendars that are not 12 calendar months are out of scope. Excel `.xls` (old format) is not read;
save as `.xlsx` or `.csv`.
