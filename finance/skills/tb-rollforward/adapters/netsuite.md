# Source adapter: NetSuite (beta)

Ported from a production roll-forward that runs against one company's NetSuite. The queries are standard
SuiteQL on core tables, but they have been proven on that instance only. Tell the user it is **beta**, and run
the validation step (end of this file) before trusting numbers.

NetSuite results are turned into small CSV files in the canonical shape and dropped in
`STORE/.state/inbox/<dataset>/`. The engine reads them exactly like SharePoint files. Use
`ns_runCustomSuiteQL` (connector tool name varies by install; discover with ToolSearch `suiteql`).

Let `BOOK` = `netsuite.accounting_book` (default 1) and `ROOT` = `netsuite.root_subsidiary` (default 1, the
top-level subsidiary that rates are quoted against). Subsidiary filter = `netsuite.subsidiaries` (empty = all).

## Reference tables (small; pull every run and overwrite the CSV)

`inbox/accounts/accounts.csv` - columns `account,name,type,rate_class`

    SELECT id AS account, acctnumber || ' ' || accountsearchdisplayname AS name, accttype AS type,
           generalrate AS rate_class FROM account

`inbox/entities/entities.csv` - columns `entity,display_name,parent,currency,is_elim`

    SELECT S.id AS entity, S.name AS display_name, S.parent AS parent, C.symbol AS currency,
           S.iselimination AS is_elim FROM subsidiary S JOIN currency C ON S.currency = C.id

`inbox/periods/periods.csv` - columns `period,status`

    SELECT TO_CHAR(startdate,'YYYY-MM') AS period,
           CASE WHEN closed = 'T' THEN 'closed' ELSE 'open' END AS status
    FROM accountingperiod WHERE isquarter='F' AND isyear='F' AND isadjust='F'

`inbox/fx/fx.csv` - columns `currency,period,closing,average,historical`

    SELECT C.symbol AS currency, TO_CHAR(AP.startdate,'YYYY-MM') AS period,
           CER.currentrate AS closing, CER.averagerate AS average, CER.historicalrate AS historical
    FROM consolidatedexchangerate CER
    JOIN accountingperiod AP ON CER.postingperiod = AP.id
    JOIN subsidiary S ON CER.fromsubsidiary = S.id JOIN currency C ON S.currency = C.id
    WHERE CER.tosubsidiary = ROOT AND CER.accountingbook = BOOK
      AND AP.isquarter='F' AND AP.isyear='F' AND AP.isadjust='F'

Write exact values (including scientific notation such as `1.5E-4`). Duplicate rows for the same currency are
fine if identical.

## Ledger activity (one small file per entity-month)

Needs the NetSuite period id (`accountingperiod.id`) for each month: take it from the periods query (add `id`).
Query one month and one subsidiary at a time with **equality** filters (IN lists and ranges time out):

    SELECT TL.subsidiary AS entity, A.id AS account, SUM(TAL.amount) AS amount
    FROM transactionaccountingline TAL
    JOIN transactionline TL ON TAL.transactionline = TL.id AND TAL.transaction = TL.transaction
    JOIN transaction T ON TAL.transaction = T.id
    JOIN account A ON TAL.account = A.id
    WHERE TAL.posting = 'T' AND TAL.accountingbook = BOOK
      AND T.postingperiod = <period id> AND TL.subsidiary = <subsidiary id>
    GROUP BY TL.subsidiary, A.id HAVING SUM(TAL.amount) <> 0

Write the rows to `inbox/ledger/ns_<YYYY-MM>_<subsidiary id>.csv` with header `entity,account,period,amount`
(the `period` column is the `YYYY-MM` label). Page with `pageSize=1000`; the server silently truncates larger
pages.

### Pull only what changed (daily runs)

1. For each open month (every month after the baseline) run one control query per month:

        SELECT sub AS entity, COUNT(*) AS n, SUM(amt) AS sum, SUM(ABS(amt)) AS abs
        FROM (<the ledger query above without the subsidiary filter, selecting TL.subsidiary AS sub, SUM(TAL.amount) AS amt>)
        GROUP BY sub

   Save as `controls.csv` with header `entity,period,n,sum,abs` (add the period label).
2. `python3 REF/tbr.py ns-diff --store STORE --controls controls.csv` -> JSON `pull` list of
   `{period, entity, file}` that are new or whose count / sum / abs-sum differ from the cache. Also removes
   entity-months that no longer exist in NetSuite.
3. Pull only those, write the files, then `tbr.py run`.

### First baseline (interactive, once)

Pull **every month from `netsuite.history_start`** (ask the user; the first month with data) up to the last
closed month, with the same per-entity-month files, then
`tbr.py bootstrap --store STORE --through <last closed month>`. This is slow for long histories; say so before
starting. Bootstrap deletes the temporary `ns_*` files afterwards.

## Getting rows from the connector into files (transcription)

Large connector results may be saved to a host file that the shell cannot read. If a spill file is readable from
bash, parse the JSON directly. Otherwise `Grep -o` the rows with a field regex, `Read` the output in chunks of
at most 300 lines, and `Write` them verbatim to the CSV (copy numbers exactly). Every file is later checked
against the control totals (count, sum, abs-sum); a mistyped value shows up as a mismatch on the next `ns-diff`,
so re-pull just that file. Use sub-agents for big pulls (one per month) and have each return the file name and
row count.

## Validate before trusting

Pick two entity-account pairs (one large, one small) and compare the life-to-date local balance in the baseline
(`Baseline/baseline_<month>.json` -> `bal[entity][account][0]`) with NetSuite's balance for the same entity and
account up to the same period (`... AND T.postingperiod <= <period id>`). They must agree to the cent. If not,
the history is incomplete (missing opening balance month or a restated closed month): tell the user and
rebuild the baseline.
