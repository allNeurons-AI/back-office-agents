---
name: gl-flux-explainer
version: "1.0"
description: "Explain what drove the change in a general-ledger account — or several — between two periods, from a spreadsheet export (no accounting system required). Trigger whenever a user uploads or points to a GL/transaction Excel or CSV and asks why an account moved, what's driving the flux/variance, or wants a month-over-month variance explanation for one or more accounts and a subsidiary — 'why did this account move', 'explain this GL flux', 'what's driving account 63200', 'variance report for these accounts'. Asks three questions (account(s), period range, subsidiary), auto-maps the file's columns, translates each subsidiary's functional-currency amounts to a reporting currency using an FX Rates lookup, rolls vendors up, grounds the top movers in their memo text, checks for entity-level miscoding at consolidated scope, and outputs a formatted Excel workbook. Generic and portable — the uploaded spreadsheet IS the data source."
---

# GL Account Flux Explainer (generic / spreadsheet-based)

Goal: given account(s), a period range, and a subsidiary scope, read a general-ledger
export from a spreadsheet and explain the dollar change using only what the data says —
no guessing, no invented reasons. Ground every claim in a memo/transaction you can point
to. There is **no database and no accounting-system connection**: the uploaded workbook is
the entire source of truth. This makes the skill portable — anyone can run it on their own
GL export.

This is the public, generic sibling of a NetSuite-specific flux skill. All the SuiteQL /
accounting-book / live-query machinery has been replaced with reading and filtering the
spreadsheet in pandas. The analytical discipline is identical: translate to one reporting
currency, tie the summary to a control total, ground reasons in memos, flag entity-level
anomalies "for review" only, and never invent a driver the data doesn't support.

Narrate as you go — one short status line before each step ("Reading the file and mapping
columns...", "Asking for the account and periods...", "Translating to the reporting
currency...", "Rolling up vendors and finding the top movers...", "Grounding movers in the
memos...", "Building the workbook..."). The user should never stare at silence.

## The engine (self-contained — write it out and run it)

This skill is a **single file**. The complete reference engine — auto-map columns → filter
scope → translate to reporting currency → vendor rollup → top movers → memo evidence → entity
anomaly check → formatted workbook — is embedded verbatim in **Appendix A** at the bottom of
this file. It has no external dependencies beyond `pandas` and `openpyxl`.

The happy path is: ask the three questions, then **write the Appendix A code to a temp file
and run it** — don't rebuild the logic ad hoc, it already encodes the tie-outs and the correct
translation. For example:

```bash
# 1. copy the Appendix A code block into flux_report.py (verbatim), then:
python flux_report.py \
  --input   "<path to the user's GL file>.xlsx" \
  --accounts "63200"           # comma-separated for a group, e.g. "70705,707005-C" \
  --period-a "May 2026" \
  --period-b "Jun 2026" \
  --subsidiary "ALL"           # "ALL" = consolidated; or a subsidiary name / substring \
  --output  "flux_63200_May2026_vs_Jun2026.xlsx"
```

It prints the headline to stdout and writes the workbook. Read the printed headline back to
the user, then present the file. Steps 0–8 below explain the design so you can adapt it when a
file is unusual, extend it, or answer follow-ups.

## Step 0 — Get the inputs (the input file first, then one AskUserQuestion round)

**0a. Make sure there's an input file.** This skill runs entirely on a spreadsheet the user
supplies, so the first thing to confirm is that you have one. If the user has already uploaded
or pointed to a GL/transaction file (`.xlsx`/`.csv`), use it. If they haven't, **ask for it**
before anything else — tell them what it needs to contain (at minimum: accounting period,
account number, subsidiary, and an amount column; a memo and vendor column make the output
much richer), and mention that a ready-made `sample_gl_data.xlsx` is available if they just
want to see how it works. Don't proceed to the questions until a file is in hand.

**0b. Peek at the file, then ask the three questions with `AskUserQuestion`.** Once you have
the file, read its GL sheet and pull the distinct **account numbers/names**, **period names**,
and **subsidiaries** actually present. Then ask the user — in a **single `AskUserQuestion`
call** — for the three inputs, using the real values from the file as the options (never make
them type a period name that has to match exactly; offer the ones the file contains):

1. **Account(s)** — one account, or several to combine into one flux (a "group"). Offer the
   accounts found in the file; allow multi-select for a group. Group accounts are passed to
   `--accounts` comma-separated and reported as one combined number with a per-account subtotal.
2. **Period range** — a base period and a compare period, offered from the period names in the
   file (e.g. "May 2026" vs "Jun 2026"). If what the user typed is ambiguous (a garbled year,
   unclear whether they mean month-over-month or a longer span), confirm rather than guessing.
3. **Subsidiary** — default **ALL** (consolidated: every subsidiary in the file), or one
   subsidiary to scope to a single entity. Offer "All / Consolidated" plus each subsidiary in
   the file.

Only ask for what's genuinely missing, and only **one** round — if the user's message already
pins the file and all three inputs unambiguously, skip straight to running the engine. The
point of pre-reading the file is so every option you present is a real, exact value from it,
which removes the most common source of a failed run (a period or subsidiary name that doesn't
match the file's spelling).

Example shape of the `AskUserQuestion` call (fill the options from the file):

- Q1 header "Account" — options: each account number+name found; `multiSelect: true` (so a
  group can be chosen).
- Q2 header "Base period" — options: the period names found (earlier periods).
- Q3 header "Compare period" — options: the period names found (later periods).
- Q4 header "Subsidiary" — options: "All / Consolidated" (recommended) + each subsidiary.

(Fold the group-vs-single distinction into Q1's multi-select rather than adding a separate
question — selecting more than one account means "group".)

## Step 1 — Read the file and map its columns (auto-mapping)

The input can be any `.xlsx`/`.csv` GL export. The skill does not require exact header names —
it normalizes headers (lowercase, strip non-alphanumerics) and maps common variants to a
canonical schema. Recognized inputs:

| Canonical field | Accepted header variants (examples) | Required? |
|---|---|---|
| period | Accounting Period, Period, Posting Period, Fiscal Period | **yes** |
| account_number | Account Number, Acct Number, GL Account, Account Code, Account | **yes** |
| subsidiary | Subsidiary, Entity, Company, Legal Entity, Business Unit | **yes** |
| net_amount | Net Amount, Amount, Functional Amount, Base Amount, GL Amount | **yes** (or Debit+Credit) |
| account_name | Account Name, Acct Name, Account Description | no |
| rate_type | Account Rate Type, Rate Type, General Rate Type | no (defaults to Average) |
| func_ccy | Functional Currency, Base Currency, Local Currency | no |
| vendor | Vendor, Supplier, Payee, Counterparty, Name, Entity Name | no |
| memo | Memo, Description, Details, Narrative, Line Memo | no (but this is where the *reasons* live) |
| docnum | Document Number, Doc Number, Tran ID, Reference, Invoice Number | no |
| type | Type, Transaction Type, Tran Type | no |
| debit / credit | Debit/DR, Credit/CR | no (used if net_amount absent) |
| tx_ccy | Transaction Currency, Currency, Foreign Currency | no |
| foreign_amount | Amount (Foreign Currency), Foreign Amount, Transaction Amount | no |
| cost_center | Cost Center, Department, Dept | no |

The workbook may also contain an **FX Rates** sheet (see Step 3). The script auto-detects
which sheet is the GL detail and which is the FX lookup.

If a **required** field can't be found, stop and tell the user exactly which column is missing
and what headers were detected, so they can rename one column and re-run — don't silently
guess a mapping for a required field. The Appendix A code already does this and exits with a
clear message.

A ready-made example in exactly this shape (`sample_gl_data.xlsx`) is provided alongside this
skill — use it to show the expected format, or to demo the skill when the user has no file yet.

## Step 2 — Filter to scope

Filter the GL rows to: the requested account number(s) (exact match on the account column;
if the file has parent/summary rows, keep only the leaf postings), the two periods, and the
subsidiary. At **ALL / consolidated** scope apply no subsidiary filter — every subsidiary is
swept in. Only narrow to one subsidiary when the user explicitly pins one. Never let
"consolidated" silently collapse to a single entity — that's the easiest way to undercount a
consolidated flux.

## Step 3 — Translate to one reporting currency (do this whenever the data is multi-currency)

Amounts in a GL export are usually stored in **each subsidiary's functional (base) currency**.
A US entity comes back in USD, a UK entity in GBP, a euro-zone entity in EUR. Summing them
straight adds GBP + EUR + USD as if they were one unit — a meaningless total that also
understates every non-USD entity. **Report in one reporting currency (e.g. USD) by default.**

Translation uses the optional **FX Rates** sheet, keyed on `(period, subsidiary)`, with an
`Average`, `Current`, and `Historical` rate to the reporting currency. Each line is
translated at the rate its **account's rate type** selects (income-statement accounts
typically Average; balance-sheet Current; equity Historical). This mirrors how a consolidation
engine translates each subsidiary at its own rate — two entities on the same functional
currency can legitimately land on different reporting rates in the same period.

- If the file has an FX Rates sheet, the script applies it automatically.
- If there is **no** FX Rates sheet, or every row is already in one currency, translation is a
  no-op (rate 1.0) and amounts pass through unchanged. Say plainly in the output that no
  translation was applied.
- Keep the original transaction-currency figure available in the **Amount (Foreign Currency)**
  column; everything else in the workbook is reporting currency.

Cast every numeric field through `float()` (never hand-parse a numeric string) — exports can
serialize very large or very small values (crypto quantities, tiny rates) in scientific
notation, and hand-parsing silently mangles exactly those while leaving ordinary amounts fine.

## Step 4 — Vendor rollup, control total, top movers

Roll the scoped, translated lines up by vendor for each period; delta = period B − period A,
sorted by absolute delta. Compute a **control total** — the same scope with no vendor grouping,
per period. The vendor table must sum to this control total for each period; if it doesn't,
a join or grouping dropped/double-counted rows — fix before presenting.

**Top movers** are the vendors whose absolute delta covers the bulk of the total change (rule
of thumb: individually > ~3% of the total delta). Don't manufacture a story for a tiny vendor;
small ones stay in the table as numbers without a narrative.

A **null / blank vendor** row is a journal entry (accrual or reversal) with no vendor on the
line — bucket these as "(no vendor — JE accrual/reversal)". Don't drop them; their memo almost
always names the real vendor, invoice, and PO (e.g. "AP Accruals | Jun 2026 | Broadridge ICS |
Invoice 206701 | PO 5158"). Read the memo and attribute accordingly.

## Step 5 — Ground each mover in its memo (this is the reason)

For each top mover, read the memo text and write one line:

"[Vendor] — [new / eliminated / ±delta]. Memo: '[quoted memo text]'."

Quote the memo verbatim — that's the receipt. Only add interpretive words ("new contract",
"renewal", "amortizing a prepaid deal") when the memo genuinely supports it. Never invent a
reason a memo doesn't support; "no clear driver in the memo" is a valid, honest answer.

Close with the account-level total: "[ccy] X → Y (±delta, ±pct%)". In group mode the closing
total is the group total, followed by the per-account split.

## Step 6 — Entity-level anomaly check (consolidated scope only)

Only when scope is ALL/consolidated. A consolidated delta can look small while masking a real
booking error — e.g. +400K hit one entity and a −400K offset landed in another, netting to
near-zero. The vendor rollup can't see this because it doesn't group by entity; this step
re-groups by vendor × subsidiary and flags a vendor when its largest single-entity delta is
more than ~2× its consolidated delta, or when its entity deltas have opposite signs and are
each individually material.

Phrase every flag as **"flagged for review"**, never a confirmed error — a legitimate
intercompany allocation or cross-entity cost-share can produce the same pattern. State what the
data shows (the entity split, the memo) and let the reader judge. "No entity-level anomalies
found" is a complete answer when nothing trips the threshold. This check runs structurally only
at consolidated scope; skip it (and the Entity Check tab) when a single subsidiary is pinned.

## Step 7 — Output workbook

Read `xlsx` skill conventions. The Appendix A code builds these tabs (values, not fragile
formulas, except the tie-out `=SUM()`):

1. **Summary** — headline, an optional per-account subtotal table (group mode), and the full
   vendor delta table (every vendor, both periods, delta) in reporting currency, with a
   `=SUM()` TOTAL row and a **"Ties to source" reconciliation line** showing the per-period
   control total next to the SUM, so the match is visible, not just asserted. If a translation
   or a deliberate exclusion creates a residual, name it here rather than hiding it.
2. **Flux Reasons** — one row per top mover: change type, both periods, delta, and the quoted
   memo evidence.
3. **GL Line Detail** — **every** GL line in scope (all subsidiaries at consolidated scope, not
   a sample), in a standard GL-detail column layout: Account, Type, Date, Document Number, Memo,
   Description (Line Level), Debit, Credit, Balance (running total of reporting-currency Amount
   within the window), Amount (Net), Amount (Foreign Currency), Currency, Cost Center,
   Subsidiary, Vendor, Accounting Period. State the line count at the top so it's clear the set
   is complete. The summed Amount column must reconcile to the control total.
4. **Entity Check** — only at consolidated scope. One row per flagged vendor/entity pair
   (vendor, entities, both periods, delta, flag reason, memo evidence), or a one-line statement
   that the check ran and found nothing.

After building, recalc with the `xlsx` skill's `recalc.py`, confirm zero formula errors, and
confirm the Summary TOTAL and the GL Line Detail sum both tie to the control total before
presenting.

File naming: `flux_<account>_<PerA>_vs_<PerB>.xlsx`; for a group,
`flux_group_<first-account>+<n-1>more_<PerA>_vs_<PerB>.xlsx`.

## Step 8 — Follow-ups

Stay available for follow-ups on the same scope without re-reading or re-asking — "break this
down by cost center", "just the PO-backed lines", "what's the currency mix" are all regroups of
data already loaded (the Cost Center and Currency columns are already in the GL Line Detail
tab).

## Guardrails

- Scope is exactly the account(s) the user named (plus leaf children of any parent) — never
  widen.
- At consolidated scope, every rollup and the control total include **all** subsidiaries; the
  only intentional single-subsidiary narrowing is a targeted follow-up on one flagged entity.
- Report in one reporting currency by default; never sum functional-currency amounts straight
  across subsidiaries. When there's no FX Rates sheet, treat amounts as already single-currency
  and say so.
- Cast every numeric field through `float()`; never hand-parse a numeric string (scientific
  notation will bite you on exactly the non-standard rows).
- Never invent a reason a memo doesn't support. "No clear driver found in the memo" is valid.
- One AskUserQuestion round, only for what's actually missing.
- The Summary total must tie exactly to the control total; name any deliberate difference
  (an excluded slice, a translation residual) next to the number, never as a silent mismatch.
- The entity-level check only runs at consolidated scope and only ever flags "for review" —
  never assert a confirmed booking error.

---

## Appendix A — the complete engine (write to `flux_report.py` and run)

Copy this block verbatim into a file and run it as shown in "The engine" above.
Requires `pandas` and `openpyxl` only.

```python
#!/usr/bin/env python3
"""
gl-flux-explainer — generic GL flux report from an Excel file.

Reads a GL export (any spreadsheet with the expected columns, header variants
auto-mapped), filters to one account (or a group of accounts), two periods, and
a subsidiary scope, translates each subsidiary's functional-currency amounts to
the reporting currency using an FX Rates lookup, rolls up by vendor, finds the
top movers, grounds each in its memo text, runs an entity-level anomaly check at
consolidated scope, and writes a Summary / Flux Reasons / GL Line Detail
(+ Entity Check) workbook.

No database required — the input workbook IS the data.

Usage:
  python flux_report.py --input sample_gl_data.xlsx \
      --accounts 63200 --period-a "May 2026" --period-b "Jun 2026" \
      --subsidiary ALL --output flux_63200_May2026_vs_Jun2026.xlsx
"""
import argparse, sys, re
import pandas as pd
import numpy as np
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# ---- Column auto-mapping ---------------------------------------------------
# canonical -> list of accepted header variants (lowercased, non-alnum stripped)
CANON = {
    "date":            ["date","trandate","transactiondate","postingdate"],
    "period":          ["accountingperiod","period","postingperiod","fiscalperiod"],
    "account_number":  ["accountnumber","acctnumber","accountno","glaccount","accountcode","account"],
    "account_name":    ["accountname","acctname","glaccountname","accountdescription"],
    "rate_type":       ["accountratetype","ratetype","generalratetype","translationratetype"],
    "subsidiary":      ["subsidiary","entity","company","legalentity","businessunit"],
    "func_ccy":        ["functionalcurrency","functionalccy","basecurrency","localcurrency"],
    "vendor":          ["vendor","supplier","payee","counterparty","name","entityname"],
    "memo":            ["memo","description","details","narrative","linememo"],
    "docnum":          ["documentnumber","docnumber","docnum","tranid","reference","invoicenumber"],
    "type":            ["type","transactiontype","trantype","abbrevtype"],
    "debit":           ["debit","dr"],
    "credit":          ["credit","cr"],
    "net_amount":      ["netamount","amount","amountnet","functionalamount","baseamount","glamount"],
    "tx_ccy":          ["transactioncurrency","currency","txccy","foreigncurrency"],
    "foreign_amount":  ["amountforeigncurrency","foreignamount","transactionamount","foreignamt"],
    "cost_center":     ["costcenter","department","dept","costcentre"],
}
def norm(s): return re.sub(r"[^a-z0-9]","",str(s).lower())

def map_columns(df):
    lut = {norm(c): c for c in df.columns}
    mapping, missing = {}, []
    for canon, variants in CANON.items():
        hit = next((lut[v] for v in variants if v in lut), None)
        if hit: mapping[canon] = hit
    # required minimum
    for req in ["period","account_number","subsidiary","net_amount"]:
        if req not in mapping: missing.append(req)
    return mapping, missing

# ---- FX Rates --------------------------------------------------------------
FX_CANON = {
    "period":     ["accountingperiod","period","postingperiod"],
    "subsidiary": ["subsidiary","entity","company","fromsubsidiary"],
    "report_ccy": ["reportingcurrency","reportccy","tocurrency"],
    "average":    ["averagerate","average","avgrate"],
    "current":    ["currentrate","current","closingrate","periodendrate"],
    "historical": ["historicalrate","historical","histrate"],
}
def map_fx(fx):
    lut={norm(c):c for c in fx.columns}; m={}
    for canon,variants in FX_CANON.items():
        hit=next((lut[v] for v in variants if v in lut),None)
        if hit: m[canon]=hit
    return m

def load_input(path):
    xls = pd.ExcelFile(path)
    # find the GL sheet (largest sheet that maps cleanly) and the FX sheet
    gl_sheet = None; best = -1
    for sh in xls.sheet_names:
        d = pd.read_excel(path, sheet_name=sh)
        mp,ms = map_columns(d)
        score = len(mp) - 10*len(ms)
        if score > best and not ms:
            best, gl_sheet = score, sh
    if gl_sheet is None:
        # fall back to first sheet, report missing
        gl_sheet = xls.sheet_names[0]
    gl = pd.read_excel(path, sheet_name=gl_sheet)
    fx = None
    for sh in xls.sheet_names:
        if sh == gl_sheet: continue
        d = pd.read_excel(path, sheet_name=sh)
        if len(map_fx(d)) >= 4:
            fx = d; break
    return gl, fx

# ---- Translation -----------------------------------------------------------
def build_rate_lookup(fx):
    if fx is None: return None, None
    m = map_fx(fx)
    fx = fx.rename(columns={m[k]:k for k in m})
    report_ccy = fx["report_ccy"].dropna().iloc[0] if "report_ccy" in fx else "USD"
    lut = {}
    for _,r in fx.iterrows():
        lut[(str(r["period"]).strip(), str(r["subsidiary"]).strip())] = {
            "Average": float(r.get("average",1) or 1),
            "Current": float(r.get("current",1) or 1),
            "Historical": float(r.get("historical",1) or 1),
        }
    return lut, report_ccy

def rate_for(lut, period, sub, rate_type):
    if lut is None: return 1.0
    row = lut.get((str(period).strip(), str(sub).strip()))
    if row is None: return 1.0
    rt = (rate_type or "Average")
    rt = rt if rt in row else "Average"
    return row[rt]

# ---- Core ------------------------------------------------------------------
def to_float(x):
    if pd.isna(x) or x=="" : return 0.0
    return float(x)   # handles scientific notation safely

def run(args):
    gl_raw, fx = load_input(args.input)
    mp, missing = map_columns(gl_raw)
    if missing:
        sys.exit(f"ERROR: input is missing required column(s): {missing}. "
                 f"Detected columns: {list(gl_raw.columns)}")
    df = gl_raw.rename(columns={mp[k]:k for k in mp}).copy()
    lut, report_ccy = build_rate_lookup(fx)

    # normalize
    for c in ["debit","credit","net_amount","foreign_amount"]:
        if c in df: df[c] = df[c].map(to_float)
    if "net_amount" not in df:
        df["net_amount"] = df.get("debit",0).map(to_float) - df.get("credit",0).map(to_float)
    if "rate_type" not in df: df["rate_type"] = "Average"
    if "vendor" not in df: df["vendor"] = None
    if "memo" not in df: df["memo"] = ""

    # scope filters
    accts = [a.strip() for a in args.accounts.split(",")]
    df["account_number"] = df["account_number"].astype(str).str.strip()
    df = df[df["account_number"].isin(accts)]
    df = df[df["period"].astype(str).str.strip().isin([args.period_a, args.period_b])]
    sub_scope = args.subsidiary.strip()
    consolidated = sub_scope.upper() in ("ALL","-1","CONSOLIDATED")
    if not consolidated:
        df = df[df["subsidiary"].astype(str).str.strip().str.contains(sub_scope, case=False, na=False)]
    if df.empty:
        sys.exit("ERROR: no rows match the requested account/period/subsidiary scope.")

    # translate each line to reporting ccy
    df["rate"] = df.apply(lambda r: rate_for(lut, r["period"], r["subsidiary"], r.get("rate_type")), axis=1)
    df["amount_rc"] = df["net_amount"] * df["rate"]
    if "debit" in df:  df["debit_rc"]  = df["debit"]  * df["rate"]
    if "credit" in df: df["credit_rc"] = df["credit"] * df["rate"]
    if "foreign_amount" not in df: df["foreign_amount"] = df["net_amount"]

    df["vendor_disp"] = df["vendor"].fillna("(no vendor — JE accrual/reversal)")

    # control total per period
    ctrl = df.groupby("period")["amount_rc"].sum().to_dict()
    a_tot = ctrl.get(args.period_a,0.0); b_tot = ctrl.get(args.period_b,0.0)

    # vendor rollup
    piv = df.pivot_table(index="vendor_disp", columns="period", values="amount_rc",
                         aggfunc="sum", fill_value=0.0)
    for p in (args.period_a,args.period_b):
        if p not in piv: piv[p]=0.0
    piv["Delta"] = piv[args.period_b] - piv[args.period_a]
    piv = piv.reindex(piv["Delta"].abs().sort_values(ascending=False).index)

    # per-account subtotal (group mode)
    acct_sub = df.pivot_table(index="account_number", columns="period", values="amount_rc",
                              aggfunc="sum", fill_value=0.0)
    for p in (args.period_a,args.period_b):
        if p not in acct_sub: acct_sub[p]=0.0
    acct_sub["Delta"] = acct_sub[args.period_b]-acct_sub[args.period_a]

    # top movers = cover bulk of delta, or > 3% of it
    total_delta = b_tot - a_tot
    thresh = max(abs(total_delta)*0.03, 1.0)
    movers = piv[piv["Delta"].abs() >= thresh].copy()

    # memo evidence per mover
    def evidence(vendor):
        sub = df[df["vendor_disp"]==vendor]
        # representative memos on the larger period
        memos = (sub.groupby("memo")["amount_rc"].sum().abs().sort_values(ascending=False))
        top = memos.index[:2] if len(memos) else [""]
        return " | ".join(str(m) for m in top if str(m).strip())

    flux_rows=[]
    for vendor,row in movers.iterrows():
        a,b,d = row[args.period_a], row[args.period_b], row["Delta"]
        if a==0 and b!=0: kind="new"
        elif b==0 and a!=0: kind="eliminated"
        else: kind=("increase" if d>0 else "decrease")
        flux_rows.append({"Vendor":vendor,"Period A":a,"Period B":b,"Delta":d,
                          "Change":kind,"Memo evidence":evidence(vendor)})

    # entity-level anomaly check (consolidated only)
    entity_flags=[]
    if consolidated:
        ent = df.pivot_table(index=["vendor_disp","subsidiary"], columns="period",
                             values="amount_rc", aggfunc="sum", fill_value=0.0)
        for p in (args.period_a,args.period_b):
            if p not in ent: ent[p]=0.0
        ent["Delta"]=ent[args.period_b]-ent[args.period_a]
        for vendor in piv.index:
            cons_delta = piv.loc[vendor,"Delta"]
            sub_rows = ent.loc[ent.index.get_level_values(0)==vendor]
            if len(sub_rows)<2: continue
            deltas = sub_rows["Delta"]
            largest = deltas.abs().max()
            opposite = (deltas>thresh).any() and (deltas<-thresh).any()
            if (abs(cons_delta) < largest and largest > 2*max(abs(cons_delta),1)) or opposite:
                for (v,s),rr in sub_rows.iterrows():
                    if abs(rr["Delta"])>=thresh:
                        m = df[(df["vendor_disp"]==vendor)&(df["subsidiary"]==s)]["memo"]
                        entity_flags.append({"Vendor":vendor,"Subsidiary":s,
                            "Period A":rr[args.period_a],"Period B":rr[args.period_b],
                            "Delta":rr["Delta"],
                            "Flag reason":"offsetting entities" if opposite else "entity delta >2x consolidated",
                            "Evidence (memo)": (m.iloc[0] if len(m) else "")})

    write_workbook(args, df, piv, acct_sub, flux_rows, entity_flags,
                   a_tot, b_tot, report_ccy, consolidated, accts, len(df))
    # console headline
    pct = (total_delta/a_tot*100) if a_tot else float('nan')
    print(f"{'+'.join(accts)}: {report_ccy} {a_tot:,.2f} -> {b_tot:,.2f} "
          f"(delta {total_delta:+,.2f}, {pct:+.1f}%)")
    for fr in flux_rows[:8]:
        print(f"  {fr['Vendor']}: {fr['Delta']:+,.0f} [{fr['Change']}] — {fr['Memo evidence'][:80]}")
    if consolidated:
        print(f"  entity-level flags: {len(entity_flags)}")

# ---- Workbook --------------------------------------------------------------
def write_workbook(args, df, piv, acct_sub, flux_rows, entity_flags,
                   a_tot, b_tot, report_ccy, consolidated, accts, nlines):
    from openpyxl import Workbook
    wb = Workbook(); 
    F=Font(name="Arial",size=10); FB=Font(name="Arial",size=10,bold=True)
    HDR=Font(name="Arial",size=10,bold=True,color="FFFFFF")
    FILL=PatternFill("solid",fgColor="305496")
    money='#,##0.00;(#,##0.00);-'
    thin=Side(style="thin",color="D9D9D9"); border=Border(thin,thin,thin,thin)
    pA,pB=args.period_a,args.period_b

    def style_header(ws,row,ncols):
        for c in range(1,ncols+1):
            cell=ws.cell(row=row,column=c); cell.font=HDR; cell.fill=FILL
            cell.alignment=Alignment(horizontal="center"); cell.border=border

    # ---- Summary ----
    ws=wb.active; ws.title="Summary"
    ws["A1"]="GL Flux Report"; ws["A1"].font=Font(name="Arial",size=14,bold=True)
    ws["A2"]=f"Account(s): {', '.join(accts)}   |   {pA} vs {pB}   |   Scope: {'Consolidated (all subsidiaries)' if consolidated else args.subsidiary}   |   Reporting currency: {report_ccy}"
    ws["A2"].font=F
    total_delta=b_tot-a_tot; pct=(total_delta/a_tot*100) if a_tot else 0
    ws["A3"]=f"Total: {report_ccy} {a_tot:,.2f} -> {b_tot:,.2f}   (delta {total_delta:+,.2f}, {pct:+.1f}%)"
    ws["A3"].font=FB

    r=5
    if len(accts)>1:
        ws.cell(r,1,"Per-account subtotal").font=FB; r+=1
        hdrs=["Account",pA,pB,"Delta"]
        for i,h in enumerate(hdrs,1): ws.cell(r,i,h)
        style_header(ws,r,len(hdrs)); r+=1
        for acct,row in acct_sub.iterrows():
            ws.cell(r,1,acct).font=F
            for i,p in enumerate([pA,pB,"Delta"],2):
                cell=ws.cell(r,i,round(float(row[p]),2)); cell.font=F; cell.number_format=money
            r+=1
        r+=1

    ws.cell(r,1,"Vendor delta table").font=FB; r+=1
    hdrs=["Vendor",pA,pB,"Delta"]
    for i,h in enumerate(hdrs,1): ws.cell(r,i,h)
    style_header(ws,r,len(hdrs)); hdr_row=r; r+=1
    first_data=r
    for vendor,row in piv.iterrows():
        ws.cell(r,1,str(vendor)).font=F
        for i,p in enumerate([pA,pB,"Delta"],2):
            cell=ws.cell(r,i,round(float(row[p]),2)); cell.font=F; cell.number_format=money
        r+=1
    last_data=r-1
    # total row with formulas
    ws.cell(r,1,"TOTAL").font=FB
    for i,col in enumerate(["B","C","D"],2):
        cell=ws.cell(r,i,f"=SUM({col}{first_data}:{col}{last_data})"); cell.font=FB; cell.number_format=money
    total_row=r; r+=2
    # tie-out line
    ws.cell(r,1,"Ties to source (control total, no vendor grouping):").font=FB; r+=1
    ws.cell(r,1,pA).font=F; ws.cell(r,2,round(a_tot,2)).number_format=money; ws.cell(r,2).font=F
    ws.cell(r+1,1,pB).font=F; ws.cell(r+1,2,round(b_tot,2)).number_format=money; ws.cell(r+1,2).font=F
    ws.cell(r+2,1,"Vendor table SUM must equal the control total above for each period.").font=Font(name="Arial",size=9,italic=True)
    for col,w in zip("ABCD",[42,16,16,16]): ws.column_dimensions[col].width=w

    # ---- Flux Reasons ----
    ws2=wb.create_sheet("Flux Reasons")
    hdrs=["Vendor","Change",pA,pB,"Delta","Memo evidence (verbatim)"]
    for i,h in enumerate(hdrs,1): ws2.cell(1,i,h)
    style_header(ws2,1,len(hdrs))
    for j,fr in enumerate(flux_rows,2):
        ws2.cell(j,1,str(fr["Vendor"])).font=F
        ws2.cell(j,2,fr["Change"]).font=F
        for i,k in enumerate(["Period A","Period B","Delta"],3):
            cell=ws2.cell(j,i,round(float(fr[k]),2)); cell.font=F; cell.number_format=money
        ws2.cell(j,6,fr["Memo evidence"]).font=F
    for col,w in zip("ABCDEF",[30,12,15,15,15,70]): ws2.column_dimensions[col].width=w

    # ---- GL Line Detail ----
    ws3=wb.create_sheet("GL Line Detail")
    ws3["A1"]=f"Complete GL line detail — {nlines} lines (all subsidiaries in scope). Balance = running total of Amount ({report_ccy}) within this window."
    ws3["A1"].font=Font(name="Arial",size=9,italic=True)
    cols=[("Account (Line): Name","account_name"),("Type","type"),("Date","date"),
          ("Document Number","docnum"),("Memo","memo"),("Description (Line Level)","memo"),
          ("Debit ("+report_ccy+")","debit_rc"),("Credit ("+report_ccy+")","credit_rc"),
          ("Balance","__balance__"),("Amount (Net "+report_ccy+")","amount_rc"),
          ("Amount (Foreign Currency)","foreign_amount"),("Currency: Name","tx_ccy"),
          ("Cost Center: Name","cost_center"),("Subsidiary: Name","subsidiary"),
          ("Vendor: Name","vendor_disp"),("Accounting Period: Name","period")]
    hrow=2
    for i,(h,_) in enumerate(cols,1): ws3.cell(hrow,i,h)
    style_header(ws3,hrow,len(cols))
    det=df.copy()
    # sort like a GL detail report
    det["__d"]=pd.to_datetime(det["date"],errors="coerce")
    det=det.sort_values(["period","__d","docnum"],na_position="last").reset_index(drop=True)
    running=0.0
    for j,(_,row) in enumerate(det.iterrows(),hrow+1):
        running+=float(row.get("amount_rc",0))
        for i,(h,key) in enumerate(cols,1):
            if key=="__balance__": val=round(running,2)
            elif key in row: val=row[key]
            else: val=""
            cell=ws3.cell(j,i,(round(float(val),2) if key in ("debit_rc","credit_rc","amount_rc","foreign_amount","__balance__") and val not in ("",None) else val))
            cell.font=F
            if key in ("debit_rc","credit_rc","amount_rc","foreign_amount","__balance__"):
                cell.number_format=money
    widths=[26,10,12,16,42,42,14,14,16,16,20,12,16,20,26,18]
    for i,w in enumerate(widths):
        ws3.column_dimensions[chr(65+i) if i<26 else 'A'+chr(65+i-26)].width=w

    # ---- Entity Check (consolidated only) ----
    if consolidated:
        ws4=wb.create_sheet("Entity Check")
        hdrs=["Vendor","Subsidiary",pA,pB,"Delta","Flag reason","Evidence (memo)"]
        for i,h in enumerate(hdrs,1): ws4.cell(1,i,h)
        style_header(ws4,1,len(hdrs))
        if entity_flags:
            for j,ef in enumerate(entity_flags,2):
                ws4.cell(j,1,str(ef["Vendor"])).font=F; ws4.cell(j,2,str(ef["Subsidiary"])).font=F
                for i,k in enumerate(["Period A","Period B","Delta"],3):
                    cell=ws4.cell(j,i,round(float(ef[k]),2)); cell.font=F; cell.number_format=money
                ws4.cell(j,6,ef["Flag reason"]).font=F; ws4.cell(j,7,str(ef["Evidence (memo)"])).font=F
        else:
            ws4.cell(2,1,"Entity-level anomaly check ran; no offsetting/miscoding patterns tripped the threshold.").font=F
        for col,w in zip("ABCDEFG",[28,20,15,15,15,26,50]): ws4.column_dimensions[col].width=w

    wb.save(args.output)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--accounts",required=True,help="comma-separated account number(s)")
    ap.add_argument("--period-a",required=True,dest="period_a")
    ap.add_argument("--period-b",required=True,dest="period_b")
    ap.add_argument("--subsidiary",default="ALL",help="'ALL' for consolidated, or a subsidiary name/substring")
    ap.add_argument("--output",required=True)
    run(ap.parse_args())
```
