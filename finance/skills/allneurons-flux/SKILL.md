---
name: allneurons-variance-analysis
description: "Fixes false-positive review flags on zero/no-variance rows, adds a sender email field alongside the recipient, moves output-save-location into config.json (no more runtime OneDrive question), and guarantees every run's final workbook lands in allneurons-flux/outputs/."
---

# allneurons-variance-analysis

## Scope - read this first

This skill explains **what changed in one or more financial accounts/categories between
exactly two periods** (e.g. May 2026 vs June 2026), consolidated or scoped to an entity/segment,
and generates a timestamped Excel workbook with the findings.

**This skill is variance-only.** If the user asks for trend analysis across more than two
periods, standalone anomaly/exception scanning unrelated to a two-period comparison,
reconciliation between two systems, or forecasting/projections, say so plainly:

> "allneurons-variance-analysis is built specifically for period-over-period variance - it
> doesn't cover [trend analysis / reconciliation / forecasting / anomaly scanning]. Want me to
> run a variance comparison instead?"

Do not attempt to satisfy an off-scope request by stretching this skill's method.

**Narrate as you go**, one short status line before each step, same discipline as any long-running
analysis skill - the user should never sit through silence.

---

## Architecture

```
allneurons-variance-analysis          <- this file: the engine/workflow
allneurons-flux/                      <- persistent config directory (created on first run)
  index.html / style.css / script.js  <- configuration UI (see Appendix)
  config.json                         <- single source of truth (schema below)
  outputs/                            <- final workbook for EVERY run lands here (manual and
                                          scheduled alike) - this is the unconditional local copy,
                                          on top of whatever additional save location config.json
                                          specifies (see Step 9)
```

`allneurons-flux/` must live inside a **persistent, user-visible folder** - not a temporary
per-run scratch directory, since `config.json` has to survive across sessions and be readable by
scheduled jobs. If no folder is currently connected, request one from the user (the normal
"connect a folder" flow) before creating `allneurons-flux/` inside it.

---

## Step 0 - Locate or create `allneurons-flux/`

1. Check whether a folder is connected/accessible. If not, ask the user to connect/select one -
   explain briefly that this is where the skill keeps its configuration so it doesn't have to
   ask the same questions every run.
2. Look for `allneurons-flux/` inside it.
   - **Missing** -> create the folder, then write `index.html`, `style.css`, and `script.js`
     from the Appendix below into it verbatim (only if those files don't already exist - never
     overwrite a user's edited copy of the UI files). Also create an empty `outputs/` subfolder
     now, so it exists before the first workbook is ever produced. Then continue to Step 1
     knowing `config.json` does not exist yet.
   - **Present** -> use it as-is (create `outputs/` too if it's somehow missing), continue to
     Step 1.

## Step 1 - Check `config.json`

- **Missing** -> tell the user you need to set up their variance-analysis configuration, and use
  `mcp__cowork__present_files` to present `allneurons-flux/index.html` as a file card in chat so
  they can launch it from inside Claude (clicking it opens the page in their browser - the config
  page needs a real browser tab to read/write `config.json` directly via the File System Access
  API, so it cannot run purely inside the chat UI). The page's Save button creates `config.json`
  automatically the first time it's clicked (it prompts once for where to save - point it at the
  `allneurons-flux/` folder - and every Save after that writes straight back to the same file, no
  further prompts). If a save ever fails because a stored file handle's permission has gone stale
  (e.g. "write permission not granted"), the page automatically discards it and re-prompts for a
  location rather than dead-ending. Once the user returns to the chat, **ask explicitly**:
  > "Have you finished entering your configuration and saved it? (yes/no)"
  - **No** -> wait; don't re-check the file or proceed until they say yes.
  - **Yes** -> re-read `allneurons-flux/config.json`. If it's genuinely not there yet, say so
    plainly and ask again rather than fabricating defaults or guessing they meant something else.
- **Present** (interactive/manual run only) -> load it, then ask:
  > "I found your existing variance-analysis configuration. Would you like to update it?"
  - **No** -> continue straight to Step 2 with the loaded config.
  - **Yes** -> present `index.html` again via `present_files` (it auto-loads the existing
    `config.json` via the File System Access API, or via its Load button as a fallback) and let
    the user edit accounts, data source, thresholds, notification sender/recipient, output
    location, and scheduler jobs. Once they return to chat, ask the same **"Have you finished
    entering your configuration and saved it?"** yes/no question - only re-read `config.json` and
    continue on a **yes**.
- **Present** (scheduled-job run) -> load it silently, no question asked - see the Scheduler
  section below for how a scheduled firing works end to end.

Everything the skill would otherwise ask about at delivery time - including where the output
file is saved beyond the always-on local copy - is a config.json field, decided once in the form
and simply read back at run time. Step 9 below never re-asks these questions.

## Step 2 - Resolve run context

- **Interactive manual run**: if the user's request already named specific account(s) and
  period(s) that differ from `manualRunDefaults`, use what they said (ad hoc, via
  `AskUserQuestion` for anything still missing - objective is always "variance," so don't ask
  that; just fill gaps like which account(s), which two periods, entity scope). Otherwise use
  `manualRunDefaults` and the `accounts[]` list from config, confirming with the user before
  proceeding.
- **Scheduled job run**: the triggering prompt names a `schedulerJobs[].id`. Look it up in the
  freshly-loaded `config.json`. If it's missing (job was deleted from config since the task was
  scheduled), do nothing further - this scheduled task is stale.

## Step 3 - Connector / data-source flow

Shared subroutine, used identically for NetSuite, SharePoint, OneDrive-on-save, and the
notification email:

```
detect(connector):
  1. Check if a working tool for this connector exists in the current session.
  2. If found -> confirm it's live with a trivial call (metadata read / small list call).
  3. If not found or the trivial call fails:
       - Tell the user plainly which connector needs to be connected.
       - search_mcp_registry with connector-specific keywords.
       - suggest_connectors to surface the Connect button.
       - Wait for the user to authenticate - never proceed, never work around it.
       - Recheck (repeat step 2). If now live, continue automatically.
       - If still unavailable, say so and offer a fallback rather than looping forever.
```

**NetSuite** (`connectors.netsuite` in config): `detect("netsuite")`, then pull from the
configured report - default is **GL Line Detail** (the transactionaccountingline-level detail,
same source the netsuite-flux-explainer skill uses, since those amounts are the functional-
currency source of truth), or the named saved search if `connectors.netsuite.report ==
"saved_search"`. Resolve the account(s), the two periods, and discover which subsidiaries
actually exist in the live instance (don't trust a stale `defaultSubsidiaryScope` blindly -
verify it). Probe schema before querying. Handle multi-book and multi-currency exactly as
described in Step 6 below. Never hardcode a report ID beyond what config specifies.

**Share Drive / SharePoint** (`connectors.sharepoint`): `detect("sharepoint")`, then search the
configured `folder` first (this is a required field in the UI - the skill should not have to
guess where the file lives), using `hint` keywords plus the account name/number and period as
additional search terms if the first search doesn't find it. Retrieve and validate.

**Manual**: no connector step. Ask the user to provide the file (or use one already attached),
read it, auto-map columns, confirm the mapping with the user, validate. Never call `detect()`
for NetSuite or SharePoint when Manual is selected.

**Notification email** (`connectors.notification`): `detect("outlook")` (or whichever email
connector is live in the session) at delivery time, per Step 9 below.

**Output save location** (when `output.saveLocation == "onedrive_sharepoint"`):
`detect("onedrive")` or `detect("sharepoint")` (whichever matches the connector implied by the
configured folder path / whichever is live), per Step 9 below.

**A scheduler job may override the data source** via `schedulerJobs[].dataSource` and
`sourceOverride` (its own report/saved-search choice for NetSuite, or its own folder for
SharePoint) - if set, it takes precedence over `defaults` for that job only. A scheduler job may
similarly override where its output is saved via `schedulerJobs[].output` - see the schema below.

**Failure handling**: report connector errors in plain language, offer retry or fallback, never
silently retry more than once, never bypass with a direct API call or script.

**Scheduled-job specific**: an unattended run cannot pause and wait for authentication. If the
configured connector isn't live when a job fires, fail that run cleanly - report why, stop - do
not hang and do not silently substitute a different data source. This applies to the output
connector too: if `onedrive_sharepoint` output is configured and the connector isn't live, the
job still counts as successful because the local `outputs/` copy is unconditional (Step 9) - just
note the additional save was skipped and why.

## Step 4 - Retrieve, normalize, validate

Same discipline regardless of source: pull the full scope (never a sample), collapse every row
to `{period, account, amount, counterparty/vendor, memo, entity/segment, currency}`, and check
sufficiency before moving on - both periods must have data in scope, and a memo/description
field must be present to ground findings later. If something critical is missing (empty result,
unmappable required column, ambiguous scope), stop and ask (interactive run) or fail cleanly with
a clear reason (scheduled run) - never guess past a validation gap.

**Runtime discovery over pre-configuration**: `config.json` intentionally does not try to pin
every detail up front. The following are never asked in the config UI and are always discovered
live, at the moment the analysis actually runs:

- **Rollup dimension** - inferred from the data's own shape. If a vendor/counterparty field is
  present and populated, roll up by vendor; otherwise fall back to entity, then cost center,
  in that order of preference. State which dimension was used in the plan (Step 6) so the user
  can redirect it for that run if it picked the wrong one.
- **Reporting currency** - inferred from the data itself: use the functional/base currency the
  source system reports in if there is only one; if multiple currencies are present, translate
  to whichever currency the majority of the in-scope activity is already denominated in, falling
  back to USD only if no dominant currency is discoverable. State the chosen currency in the plan.
- Which entities/subsidiaries actually exist, and whether an account shows any movement at all
  between the two periods.

## Step 5 - Variance methodology

- Exactly two periods, Period A and Period B - never more.
- Roll up by the dimension discovered in Step 4 (vendor/counterparty by default; entity or cost
  center when the data calls for it).
- Per rollup row: `Δ($) = Period B − Period A`; `Δ(%) = Δ / |Period A|`, reported as "n/m" when
  Period A is zero.
- Multiple accounts in scope each get their own rollup (one Flux tab section per account, or an
  Account column - confirm with the user at the plan stage).
- Multi-currency: translate to the reporting currency discovered in Step 4 using the source's own
  FX mechanism (average rate for P&L-type accounts unless told otherwise), keep original-currency
  amounts visible, reconcile any residual.

### Significance threshold vs. review flag - these are two different things

A common mistake is to treat "crossed the threshold" and "needs review" as the same test. They
are not, and the skill must keep them distinct:

- **Significance (`defaults.significance.absoluteThreshold` / `percentThreshold`)** decides which
  rollup rows are material enough to surface as a named movement in the Flux tab at all. A row
  crosses if `|Δ($)| > absoluteThreshold` **or** `|Δ(%)| > percentThreshold` (strictly greater
  than - not "greater than or equal to"). A row with **zero net movement** between Period A and
  Period B is never significant and is never listed as a flux finding, **regardless of the
  configured threshold** - a `0` threshold means "surface every nonzero movement, however small",
  it does not mean "treat no-movement as a finding." Rows with zero movement still contribute to
  the Summary tab's tie-out total, they just don't get a Flux narrative row.
- **Review flag (Y/N)**, set independently for each row that *is* included in the Flux tab, marks
  evidentiary or data-integrity concern - not dollar size. Set it to **Y** only when at least one
  of these is true for that row:
  - No supporting memo/description/document text could be found to ground the movement (the
    driver could not be evidenced from source data).
  - The available memo/description is ambiguous, generic, or appears to contradict the computed
    amount or direction of the movement.
  - A likely data-quality or data-entry issue was detected (e.g. a currency/mapping mismatch, a
    duplicate-looking entry, an unexpected sign, an account posted to the wrong entity).
  - It's a brand-new counterparty appearing in Period B with zero prior activity, when
    `flagNewCounterparty` is true.
  - Entity-level offsetting was detected at consolidated scope, when `flagEntityLevelOffsetting`
    is true (see below).
  A row can be large, clearly above threshold, and still get **Review flag = N** if its driver is
  well-documented and unambiguous (e.g. a clearly-memo'd one-time payment, an expected seasonal
  swing tied to a specific invoice or contract). **Never set Review flag = Y solely because a row
  crossed the significance threshold** - magnitude alone is not evidence of a problem.
- At consolidated scope, if `flagEntityLevelOffsetting` is true, flag counterparties whose
  consolidated net is small but whose individual entity-level legs are large - flagged for review,
  never asserted as an error.
- Ground every flagged item in the actual memo/description/document that supports it. "No clear
  driver found in the data" is a valid, honest finding, and it is exactly the kind of thing the
  review flag exists for. Keep source data, calculation, finding, interpretation, and reviewer
  recommendation visibly distinct.

## Step 6 - Analysis plan + approval gate

Build a short plan: accounts in scope, the two periods, data source and exactly what was
retrieved, the rollup dimension and reporting currency discovered in Step 4, entity handling, the
threshold(s) in effect, where the output will be saved (per `defaults.output` / the job's own
`output` - this is confirmed here, once, and never re-asked at delivery time in Step 9), and the
proposed output structure.

- **Interactive manual run**: present the plan via `AskUserQuestion`, iterate on edits, and do
  not proceed to execution without explicit approval. This gate is mandatory - never skip it for
  a manual run.
- **Scheduled job run**: the job's saved config *is* the pre-approved plan (the user approved
  these settings when they saved the job in the UI). Skip the interactive gate and proceed
  directly to execution - there is no one to ask.

## Step 7 - Execute

Pull the full scope, roll up per Step 5, ground findings in real memo/document text, parse every
numeric value through a real numeric parser (never hand-split a numeric string), translate
currency with reconciliation where needed.

## Step 8 - Excel output

Build (via the `xlsx` skill conventions) exactly **three** tabs:

1. **Summary** - the rollup plus an `=SUM()` tie-out to an independently computed control total.
   Zero-movement rows may appear here for completeness/tie-out purposes even though they never
   appear as Flux findings.
2. **Flux** - every evidenced movement that crossed the significance threshold (Step 5): the
   finding, the interpretation (clearly labeled as interpretation, not fact), a **review flag
   (Y/N)** that reflects evidentiary certainty and data integrity - not dollar size (see Step 5's
   distinction; do not set Y merely because the row is large) - and, folded into this same tab
   rather than a separate one, any entity-level-offsetting or other integrity flags from Step 5.
   If that check ran and found nothing, say so plainly in this tab rather than omitting it. Rows
   with zero net movement are not listed here at all, at any threshold setting.
3. **GL Details** - every underlying line item, full traceability back to source.

Use formulas, not hardcoded numbers; recalc with zero formula errors before delivering.

**Filename**: `<Account-or-scope-name>_Variance_<PeriodA>_vs_<PeriodB>_<YYYY-MM-DD>_<HH-MM>.xlsx`
- always the real execution date/time, never a placeholder.

**Verify before delivering**: rolled-up total ties to an independently computed control total;
name any deliberate exclusion/residual next to the number; no row with zero net movement carries
a Y review flag; no row's review flag is Y for magnitude alone without an evidentiary or
integrity reason logged next to it.

## Step 9 - Delivery + completion email

**Local save - every run, manual or scheduled, unconditional, first:**

Save the finished workbook to `allneurons-flux/outputs/` (creating the folder if it somehow
doesn't exist yet). This always happens, for every run, before anything else in this step, and
never depends on any connector being authenticated.

**Additional save, per the configured output location - `defaults.output.saveLocation` for a
manual run, or the job's own `output` for a scheduled run:**

- `allneurons_flux_folder` -> nothing further; the local save above already satisfies it.
- `claude_working_folder` -> (manual runs only; not offered for scheduled jobs, since there is no
  interactive session to place a working copy into) satisfied by delivering the file into the
  chat below.
- `onedrive_sharepoint` -> `detect("onedrive")` or `detect("sharepoint")` per the configured
  connector/folder, then upload to `output.oneDriveSharepointFolder`. Never silently overwrite a
  same-named file there - surface the conflict and let the user choose (manual run) or append a
  timestamp and note it (scheduled run, since nobody's watching to decide). For a scheduled run,
  do not pause to wait for authentication - if the connector isn't live or the upload fails, the
  job still counts as successful (the local copy is secured); simply note that the additional
  save was skipped and why. For a manual run, follow the standard connector detect/wait/recheck
  flow (Step 3) once; if still unavailable, report it and move on rather than looping.

**No question is asked here about where to save** - that decision was made once in
`config.json` and confirmed at the Step 6 plan/approval gate. Step 9 only executes it.

**Chat delivery (interactive manual runs only):** deliver the file to the user unconditionally,
regardless of `output.saveLocation`, so they always have it in hand immediately. Scheduled runs
produce no chat delivery - nobody is watching.

**Completion email - every run, manual or scheduled, no exceptions:**

The instant the output file exists (after the local save, and after any additional save
completes or is skipped), send a real email - never a draft, no approval gate, nobody needs to
confirm this:

1. `detect("outlook")` (or whichever email connector is live in the session).
2. If live, send the email to `connectors.notification.recipient`, with a short subject and body
   stating where the file landed: the local `allneurons-flux/outputs/` path, plus the
   OneDrive/SharePoint link if that additional save also happened. Use
   `connectors.notification.sender` as the From address if the live connector supports sending as
   an arbitrary address; if it only supports sending as the authenticated mailbox (the common
   case for most connectors), send from the authenticated identity but set Reply-To to
   `connectors.notification.sender` and sign the body with that address, so the configured sender
   identity is still honestly represented rather than silently dropped.
3. If the connector isn't live or the send fails, do not block or retry the run over it - the
   output file has already been delivered/saved either way. Just tell the user (interactive run)
   or note it in the job's own log (scheduled run) that the completion email could not be sent
   and why.

No OneDrive/output-location question and no email approval step is ever asked for a scheduled
run, and no chat delivery happens for a scheduled run - nobody is watching. The completion email
is the only notification a scheduled run produces.

---

## Scheduler - reconciling jobs with actual scheduled tasks

Whenever the user saves scheduler jobs through the config UI, reconcile `config.json`'s
`schedulerJobs[]` with real `mcp__scheduled-tasks__*` entries:

```
for each job in config.json.schedulerJobs:
  if job.enabled and job.scheduledTaskId is null:
      create_scheduled_task(
        cron/fireAt derived from job.frequency/time/dayOfWeek/dayOfMonth,
        prompt: "Run allneurons-variance-analysis, scheduler job id <job.id>, "
                "from allneurons-flux/config.json"
      )
      -> store the returned task id into job.scheduledTaskId, save config.json again
  if job.enabled and job.scheduledTaskId exists and the schedule changed:
      update_scheduled_task(job.scheduledTaskId, new cron/time)
  if not job.enabled and job.scheduledTaskId exists:
      delete_scheduled_task(job.scheduledTaskId); clear scheduledTaskId
for each previously-known scheduledTaskId no longer present in schedulerJobs (job deleted in UI):
      delete_scheduled_task(that id)
```

The scheduled task's prompt only ever carries the job id and the config path - never accounts,
dates, thresholds, or output locations directly. That's what makes an edit in the UI take effect
on the very next firing without touching the scheduled task itself; only a frequency/time change
requires updating the task.

**When a scheduled task fires**, re-derive everything from a fresh read of `config.json` (never
from anything cached at schedule-creation time): resolve the job -> resolve its account(s) from
`config.json.accounts` -> resolve its `periodPattern` against today's date (e.g.
`previous_month_vs_month_before` evaluated relative to *now*, not frozen at config-save time) ->
run Steps 3-9 above, auto-approved, local (+ optional additional) output, plus the mandatory
completion email.

---

## `config.json` schema

```json
{
  "schemaVersion": 3,
  "createdAt": "2026-08-27T10:00:00Z",
  "updatedAt": "2026-08-27T10:00:00Z",
  "defaults": {
    "dataSource": "netsuite | sharepoint | manual",
    "significance": {
      "absoluteThreshold": 1000,
      "percentThreshold": 0.20,
      "flagNewCounterparty": true,
      "flagEntityLevelOffsetting": true
    },
    "output": {
      "saveLocation": "allneurons_flux_folder | claude_working_folder | onedrive_sharepoint",
      "oneDriveSharepointFolder": null
    }
  },
  "connectors": {
    "netsuite": {
      "report": "gl_line_detail | saved_search",
      "savedSearchName": null,
      "accountingBookNote": "",
      "defaultSubsidiaryScope": "all"
    },
    "sharepoint": { "folder": "Documents/Finance/GL Exports", "hint": "" },
    "manual": {},
    "notification": { "sender": "finance-bot@company.com", "recipient": "someone@company.com" }
  },
  "accounts": [
    { "id": "acct_63200", "accountNumber": "63200", "accountName": "Travel & Entertainment", "defaultEntityScope": "all" }
  ],
  "manualRunDefaults": { "periodA": "2026-05", "periodB": "2026-06" },
  "schedulerJobs": [
    {
      "id": "job_1",
      "name": "Monthly T&E variance",
      "enabled": true,
      "frequency": "daily | weekly | monthly",
      "time": "09:00",
      "dayOfWeek": "monday",
      "dayOfMonth": null,
      "periodPattern": "previous_month_vs_month_before | previous_week_vs_week_before | custom",
      "customPeriod": null,
      "accountIds": ["acct_63200"],
      "entityScope": "all",
      "dataSource": null,
      "sourceOverride": { "netsuiteReport": "gl_line_detail", "netsuiteSavedSearchName": null, "sharepointFolder": null },
      "output": {
        "saveLocal": true,
        "localFolder": "allneurons-flux/outputs",
        "saveLocation": "allneurons_flux_folder | onedrive_sharepoint",
        "oneDriveSharepointFolder": null
      },
      "scheduledTaskId": null
    }
  ]
}
```

`rollupDimension` and `reportingCurrency` are intentionally **not** stored in config - they are
discovered fresh from the data on every run (Step 4). `connectors.notification.sender` and
`connectors.notification.recipient` are both required; the config UI will not save without both.
`defaults.output.saveLocation` is required and defaults to `allneurons_flux_folder`; when it is
`onedrive_sharepoint`, `oneDriveSharepointFolder` is required too. A scheduler job's `output`
only offers `allneurons_flux_folder` or `onedrive_sharepoint` (not `claude_working_folder`,
which only makes sense for an interactive chat delivery) - if unset, it inherits
`defaults.output`, treating an inherited `claude_working_folder` as equivalent to
`allneurons_flux_folder` for that job.

No connector credentials or tokens are ever stored in this file - only preferences (which
source, which folder/report, who gets the completion email, where output is saved).
Authentication stays entirely with the MCP connector layer.

---

## Guardrails

- **Variance only.** Redirect trend/anomaly/reconciliation/forecasting requests rather than
  stretching this skill to cover them.
- **Plan before you run - interactive runs only.** The Step 6 approval gate is mandatory for a
  manual run; skip it only for scheduled runs, where the saved config is the pre-approval.
- **Assume nothing not in config.** Subsidiaries, currencies, rollup dimension, report
  availability, and folder contents are verified/discovered at runtime, not trusted blindly from
  a possibly-stale config value or asked of the user up front.
- **Own the connector setup** - detect, explain, surface the connect link, wait, recheck,
  continue automatically; never ask the user to go configure a connector themselves, never work
  around a missing one with scripts.
- **`config.json` is the only source of truth for the scheduler and for output location.** Never
  duplicate accounts, thresholds, or schedule details into a scheduled task's prompt, and never
  ask at delivery time (Step 9) where to save the output - that's a config field, confirmed once
  at the Step 6 plan gate.
- **Never silently overwrite** the UI files if they already exist, or a same-named output file
  on save.
- **Significance threshold and review flag are not the same test.** Crossing
  `absoluteThreshold`/`percentThreshold` only decides whether a row is material enough to appear
  in the Flux tab. It never by itself sets Review flag = Y. A row with zero net movement between
  the two periods is never listed as a Flux finding and never carries a review flag, no matter
  what the threshold is set to (including `0`). Review flag = Y is reserved for rows with missing
  or ambiguous evidence, a suspected data-quality issue, a brand-new counterparty, or an
  entity-level-offsetting flag - never for magnitude alone.
- **Ground every finding in real source text**; "no clear driver in the data" is a valid answer,
  and it belongs with Review flag = Y. Keep source data, calculation, finding, interpretation, and
  review recommendation visibly distinct.
- **Totals must tie** - reconcile every summary number to an independently computed control
  total; name any deliberate difference next to the number.
- **Local save to `allneurons-flux/outputs/` always happens, for every run** - manual or
  scheduled - regardless of whether any additional save location (OneDrive/SharePoint) succeeds
  or is even configured. A connector hiccup must never lose the output entirely.
- **The completion email is mandatory and automatic**, every run, the moment the output file is
  ready - it is a real send, never a draft, and never gated on approval, and it always identifies
  both the configured sender and recipient. A missing/broken email connector is reported, never
  allowed to block delivery of the file itself.

---

## Appendix A - `allneurons-flux/index.html`

On first run, if `allneurons-flux/index.html` does not exist, write exactly this content to it:

```html
<title>Variance Analysis Configuration</title>
<link rel="stylesheet" href="style.css">

<div class="wrap">
  <header>
    <h1>Variance Analysis Configuration</h1>
    <p id="statusLine" class="status">Checking for an existing configuration...</p>
  </header>

  <section class="filebar">
    <button id="btnOpen" type="button">Load config.json</button>
    <button id="btnSaveAs" type="button" class="secondary">Save As...</button>
    <button id="btnSave" type="button" disabled>Save</button>
    <span id="fileName" class="filename"></span>
  </section>

  <form id="cfgForm">

    <fieldset>
      <legend>1. Data Source</legend>
      <div class="radio-row">
        <label><input type="radio" name="dataSource" value="netsuite"> NetSuite (live)</label>
        <label><input type="radio" name="dataSource" value="sharepoint" checked> Share Drive / SharePoint</label>
        <label><input type="radio" name="dataSource" value="manual"> Manual (upload / provide a file)</label>
      </div>

      <div class="sub" id="src-netsuite" hidden>
        <label>Report to pull from
          <select name="ns_report">
            <option value="gl_line_detail" selected>GL Line Detail (transactionaccountingline detail - recommended)</option>
            <option value="saved_search">A specific existing saved search / report I already use</option>
          </select>
        </label>
        <label id="ns_savedSearchNameWrap" hidden>Saved search / report name
          <input type="text" name="ns_savedSearchName" placeholder="e.g. GL Detail by Account (Custom)">
        </label>
        <p class="hint">Default is GL Line Detail - the same report the netsuite-flux-explainer skill pulls from, since transactionaccountingline amounts are the functional-currency source of truth. Only pick a saved search if you specifically want to source from one you already use.</p>
        <label>Accounting book note (optional)
          <input type="text" name="ns_accountingBookNote" placeholder="e.g. Primary book only">
        </label>
        <label>Default subsidiary scope
          <input type="text" name="ns_defaultSubsidiaryScope" placeholder="all">
        </label>
      </div>

      <div class="sub" id="src-sharepoint">
        <label>Which folder should I look in? <span class="req">*</span>
          <input type="text" name="sp_folder" placeholder="e.g. Documents/Finance/GL Exports" required>
        </label>
        <label>Extra search keywords (optional)
          <input type="text" name="sp_hint" placeholder="e.g. GL Export, Travel">
        </label>
        <p class="hint">The folder is where I'll search first for the GL/transaction file each run. If it ever moves, I'll ask again rather than guess.</p>
      </div>

      <div class="sub" id="src-manual" hidden>
        <p class="hint">No connector setup needed - you'll be asked to provide the file when a manual run starts.</p>
      </div>
    </fieldset>

    <fieldset>
      <legend>2. Accounts</legend>
      <div id="accountsList" class="cardlist"></div>
      <button type="button" id="btnAddAccount" class="add">+ Add account</button>
    </fieldset>

    <fieldset>
      <legend>3. Analysis Period (default for manual runs)</legend>
      <div class="row">
        <label>Period A (from)
          <input type="month" name="periodA">
        </label>
        <label>Period B (to)
          <input type="month" name="periodB">
        </label>
      </div>
      <p class="hint">Scheduled jobs use their own relative period pattern (set per job below), not this fixed range.</p>
    </fieldset>

    <fieldset>
      <legend>4. Variance Configuration - Flux Threshold</legend>
      <p class="hint">A movement is listed as a Flux finding if it crosses <strong>either</strong> threshold below (a movement of exactly zero is never listed, whatever the threshold). Crossing a threshold only decides whether a row appears - it does <strong>not</strong> by itself mark a row for review; the review flag is reserved for missing/ambiguous evidence or a data-quality concern, decided when the analysis runs. Rollup dimension and reporting currency are not set here either - the skill figures both out from the data itself each time it runs.</p>
      <div class="row">
        <label>Absolute $ threshold
          <input type="number" name="absoluteThreshold" min="0" step="1" value="1000">
        </label>
        <label>Percent threshold (%)
          <input type="number" name="percentThreshold" min="0" step="1" value="20">
        </label>
      </div>
    </fieldset>

    <fieldset>
      <legend>5. Notifications</legend>
      <label>Send completion email from <span class="req">*</span>
        <input type="email" name="notify_sender" placeholder="e.g. finance-bot@company.com" required>
      </label>
      <label>Send completion email to <span class="req">*</span>
        <input type="email" name="notify_recipient" placeholder="e.g. you@company.com" required>
      </label>
      <p class="hint">Every run - manual or scheduled - sends a completion email automatically the moment the output file is ready (never a draft, no approval step), stating where the file(s) landed. If the connected mailbox can only send as its own authenticated address, the sender address above is used as the Reply-To and in the signature instead of the From line.</p>
    </fieldset>

    <fieldset>
      <legend>6. Output Location (default for manual runs; each scheduled job below can override it)</legend>
      <div class="radio-row">
        <label><input type="radio" name="outputLocation" value="allneurons_flux_folder" checked> Same folder as allneurons-flux (allneurons-flux/outputs)</label>
        <label><input type="radio" name="outputLocation" value="claude_working_folder"> Claude's working folder (delivered into this chat)</label>
        <label><input type="radio" name="outputLocation" value="onedrive_sharepoint"> A OneDrive / SharePoint location</label>
      </div>
      <div class="sub" id="outputloc-onedrive" hidden>
        <label>OneDrive / SharePoint folder <span class="req">*</span>
          <input type="text" name="outputLocation_folder" placeholder="e.g. Documents/Finance/Variance Reports">
        </label>
      </div>
      <p class="hint">A copy of the finished workbook always lands in allneurons-flux/outputs regardless of this choice - this setting only controls where an additional copy goes, and it's read from here automatically, never asked again when a run finishes.</p>
    </fieldset>

    <fieldset>
      <legend>7. Scheduler Jobs</legend>
      <div id="jobsList" class="cardlist"></div>
      <button type="button" id="btnAddJob" class="add">+ Add scheduled job</button>
    </fieldset>

    <div class="savebar">
      <button type="submit" id="btnSubmit">Save Configuration</button>
      <span id="saveMsg" class="savemsg"></span>
    </div>
  </form>
</div>

<template id="accountCardTpl">
  <div class="card account-card">
    <div class="card-row">
      <label>Account number <input type="text" class="acc-number" required></label>
      <label>Account name <input type="text" class="acc-name" required></label>
      <label>Default entity scope <input type="text" class="acc-scope" placeholder="all"></label>
      <button type="button" class="remove">Remove</button>
    </div>
  </div>
</template>

<template id="jobCardTpl">
  <div class="card job-card">
    <div class="card-row">
      <label>Job name <input type="text" class="job-name" required></label>
      <label class="checkbox"><input type="checkbox" class="job-enabled" checked> Enabled</label>
      <button type="button" class="remove">Remove</button>
    </div>
    <div class="card-row">
      <label>Frequency
        <select class="job-frequency">
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly" selected>Monthly</option>
        </select>
      </label>
      <label>Time <input type="time" class="job-time" value="09:00"></label>
      <label class="job-dow-wrap" hidden>Day of week
        <select class="job-dow">
          <option>monday</option><option>tuesday</option><option>wednesday</option>
          <option>thursday</option><option>friday</option><option>saturday</option><option>sunday</option>
        </select>
      </label>
      <label class="job-dom-wrap">Day of month
        <input type="number" class="job-dom" min="1" max="28" value="1">
      </label>
    </div>
    <div class="card-row">
      <label>Period pattern
        <select class="job-period-pattern">
          <option value="previous_month_vs_month_before" selected>Previous month vs. month before</option>
          <option value="previous_week_vs_week_before">Previous week vs. week before</option>
          <option value="custom">Custom (fixed dates, set below)</option>
        </select>
      </label>
      <label class="job-custom-wrap" hidden>Custom period A/B
        <input type="text" class="job-custom-period" placeholder="e.g. 2026-05,2026-06">
      </label>
    </div>
    <div class="card-row">
      <label>Data source
        <select class="job-datasource">
          <option value="">(use global default)</option>
          <option value="netsuite">NetSuite</option>
          <option value="sharepoint">Share Drive / SharePoint</option>
          <option value="manual">Manual</option>
        </select>
      </label>
      <label>Entity scope <input type="text" class="job-entity-scope" placeholder="all"></label>
    </div>
    <div class="card-row job-ns-override-wrap" hidden>
      <label>NetSuite report for this job
        <select class="job-ns-report">
          <option value="gl_line_detail" selected>GL Line Detail (recommended)</option>
          <option value="saved_search">Specific saved search</option>
        </select>
      </label>
      <label class="job-ns-savedsearch-wrap" hidden>Saved search name
        <input type="text" class="job-ns-savedsearch">
      </label>
    </div>
    <div class="card-row job-sp-override-wrap" hidden>
      <label>Share Drive folder for this job <span class="req">*</span>
        <input type="text" class="job-sp-folder" placeholder="e.g. Documents/Finance/GL Exports">
      </label>
    </div>
    <div class="card-row">
      <label class="job-accounts-label">Accounts for this job</label>
    </div>
    <div class="job-accounts-checklist"></div>
    <div class="card-row output-row">
      <label class="checkbox"><input type="checkbox" class="job-save-local" checked disabled> Save to allneurons-flux/outputs (always on)</label>
      <label>Additional output location
        <select class="job-output-location">
          <option value="allneurons_flux_folder" selected>None (outputs/ copy only)</option>
          <option value="onedrive_sharepoint">OneDrive / SharePoint</option>
        </select>
      </label>
      <label class="job-output-folder-wrap" hidden>OneDrive / SharePoint folder
        <input type="text" class="job-output-folder" placeholder="e.g. Variance Reports">
      </label>
    </div>
  </div>
</template>

<script src="script.js"></script>
```

## Appendix B - `allneurons-flux/style.css`

On first run, if `allneurons-flux/style.css` does not exist, write exactly this content to it:

```css
/* Must come first and win over any later class rule that also sets
   display (e.g. .card-row{display:flex}) - otherwise an element that is
   both .card-row and [hidden] stays visible. */
[hidden]{display:none !important;}

:root{
  --bg:#f6f7f9; --card:#ffffff; --border:#d9dce1; --text:#1f2430; --muted:#6b7280;
  --accent:#2454ff; --accent-ink:#ffffff; --danger:#c0392b; --ok:#1f8a4c;
}
*{box-sizing:border-box;}
body{
  margin:0; font-family:Arial, Helvetica, sans-serif; background:var(--bg); color:var(--text);
  line-height:1.4;
}
.wrap{max-width:860px; margin:0 auto; padding:24px 20px 80px;}
header h1{font-size:22px; margin:0 0 4px;}
.status{color:var(--muted); margin:0 0 20px; font-size:13px;}
.filebar{
  display:flex; align-items:center; gap:10px; margin-bottom:20px; flex-wrap:wrap;
  background:var(--card); border:1px solid var(--border); border-radius:8px; padding:10px 12px;
}
.filename{color:var(--muted); font-size:12px;}
button{
  font-family:inherit; font-size:13px; padding:8px 14px; border-radius:6px; border:1px solid var(--border);
  background:#fff; cursor:pointer;
}
button.secondary{background:#fff;}
button:disabled{opacity:.5; cursor:not-allowed;}
#btnSubmit{background:var(--accent); color:var(--accent-ink); border-color:var(--accent); font-weight:bold; padding:10px 20px;}
button.add{background:#eef1ff; border-color:#c7d0ff; color:var(--accent); font-weight:bold; margin-top:8px;}
button.remove{background:#fdecea; border-color:#f3c2bc; color:var(--danger); margin-left:auto;}

fieldset{
  background:var(--card); border:1px solid var(--border); border-radius:8px; padding:16px 18px; margin:0 0 18px;
}
legend{font-weight:bold; padding:0 6px; font-size:14px;}
.hint{color:var(--muted); font-size:12px; margin:6px 0 0;}
.req{color:var(--danger);}

.radio-row{display:flex; gap:18px; flex-wrap:wrap; margin-bottom:10px;}
.radio-row label{font-size:13px; display:flex; align-items:center; gap:6px;}

.sub{border-top:1px dashed var(--border); margin-top:10px; padding-top:10px;}
.row{display:flex; gap:16px; flex-wrap:wrap; margin-bottom:10px;}
.row label{flex:1; min-width:180px; font-size:13px; display:flex; flex-direction:column; gap:4px;}
label.checkbox{flex-direction:row !important; align-items:center; gap:8px !important;}

input[type="text"], input[type="number"], input[type="month"], input[type="time"], input[type="email"], select{
  padding:7px 8px; border:1px solid var(--border); border-radius:5px; font-size:13px; font-family:inherit;
}
input:invalid{border-color:var(--danger);}

.cardlist{display:flex; flex-direction:column; gap:10px; margin-bottom:4px;}
.card{
  border:1px solid var(--border); border-radius:7px; padding:12px; background:#fbfbfd;
}
.card-row{display:flex; gap:14px; flex-wrap:wrap; align-items:flex-end; margin-bottom:8px;}
.card-row label{display:flex; flex-direction:column; gap:4px; font-size:12px; min-width:140px;}
.card-row label.job-accounts-label{font-weight:bold; min-width:auto;}
.job-accounts-checklist{display:flex; flex-wrap:wrap; gap:10px; margin:0 0 8px; font-size:12px;}
.job-accounts-checklist label{display:flex; align-items:center; gap:5px;}
.output-row{border-top:1px dashed var(--border); padding-top:10px;}

.savebar{
  position:sticky; bottom:0; background:var(--bg); padding:14px 0; display:flex; align-items:center; gap:12px;
}
.savemsg{font-size:13px; color:var(--ok);}
.savemsg.error{color:var(--danger);}

@media (max-width:600px){
  .row label{min-width:100%;}
}
```

## Appendix C - `allneurons-flux/script.js`

On first run, if `allneurons-flux/script.js` does not exist, write exactly this content to it:

```javascript
/* allneurons-variance-analysis - configuration UI logic
 *
 * Read/write strategy:
 *   - Chrome/Edge (File System Access API available): a file handle to
 *     config.json is acquired once (Load or Save As) and remembered in
 *     IndexedDB, so every later Save writes straight back to the same
 *     file with no re-prompting, and reopening the page can re-request
 *     the same handle.
 *   - Safari/Firefox (no File System Access API): fallback to a plain
 *     file <input> for loading and a download-triggered Blob for saving.
 *     The user is told, once, to keep the downloaded file inside the
 *     allneurons-flux/ folder.
 *
 * Either way, the user only ever edits form fields - config.json itself
 * is never hand-edited.
 */

(function () {
  "use strict";

  const SCHEMA_VERSION = 3;
  const HAS_FS_ACCESS = "showOpenFilePicker" in window && "showSaveFilePicker" in window;

  const form = document.getElementById("cfgForm");
  const statusLine = document.getElementById("statusLine");
  const fileNameEl = document.getElementById("fileName");
  const saveMsg = document.getElementById("saveMsg");

  const btnOpen = document.getElementById("btnOpen");
  const btnSaveAs = document.getElementById("btnSaveAs");
  const btnSave = document.getElementById("btnSave");

  const accountsList = document.getElementById("accountsList");
  const jobsList = document.getElementById("jobsList");
  const accountCardTpl = document.getElementById("accountCardTpl");
  const jobCardTpl = document.getElementById("jobCardTpl");

  let fileHandle = null;   // File System Access API handle, when available
  let loadedConfig = null; // last loaded/saved config, for updatedAt diffing

  // ---------------------------------------------------------------
  // IndexedDB: remember the file handle across page loads (Chrome/Edge)
  // ---------------------------------------------------------------
  function idbOpen() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open("allneurons-flux-ui", 1);
      req.onupgradeneeded = () => req.result.createObjectStore("handles");
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }
  async function idbGetHandle() {
    try {
      const db = await idbOpen();
      return await new Promise((resolve) => {
        const tx = db.transaction("handles", "readonly");
        const r = tx.objectStore("handles").get("config");
        r.onsuccess = () => resolve(r.result || null);
        r.onerror = () => resolve(null);
      });
    } catch (e) { return null; }
  }
  async function idbSetHandle(handle) {
    try {
      const db = await idbOpen();
      const tx = db.transaction("handles", "readwrite");
      tx.objectStore("handles").put(handle, "config");
    } catch (e) { /* non-fatal */ }
  }

  async function verifyPermission(handle, mode) {
    const opts = { mode };
    if ((await handle.queryPermission(opts)) === "granted") return true;
    if ((await handle.requestPermission(opts)) === "granted") return true;
    return false;
  }

  // ---------------------------------------------------------------
  // Load / Save
  // ---------------------------------------------------------------
  async function tryAutoLoad() {
    if (!HAS_FS_ACCESS) {
      statusLine.textContent = "No configuration loaded yet - use \"Load config.json\" or fill the form and Save.";
      return;
    }
    const handle = await idbGetHandle();
    if (!handle) {
      statusLine.textContent = "No configuration found yet - fill in the form below, then Save.";
      return;
    }
    const ok = await verifyPermission(handle, "readwrite");
    if (!ok) {
      statusLine.textContent = "Found a previous configuration file, but permission was not (re)granted - click \"Load config.json\".";
      return;
    }
    fileHandle = handle;
    await loadFromHandle(handle);
  }

  async function loadFromHandle(handle) {
    try {
      const file = await handle.getFile();
      const text = await file.text();
      const cfg = JSON.parse(text);
      applyConfig(cfg);
      fileNameEl.textContent = file.name;
      btnSave.disabled = false;
      statusLine.textContent = "I found your existing variance-analysis configuration. Update anything you like, then Save - or just close this page to keep it as-is.";
    } catch (e) {
      statusLine.textContent = "Could not read that file as valid configuration JSON (" + e.message + "). Starting blank.";
    }
  }

  btnOpen.addEventListener("click", async () => {
    if (HAS_FS_ACCESS) {
      try {
        const [handle] = await window.showOpenFilePicker({
          types: [{ description: "Config JSON", accept: { "application/json": [".json"] } }],
        });
        const ok = await verifyPermission(handle, "readwrite");
        if (!ok) { statusLine.textContent = "Permission to read/write that file was not granted."; return; }
        fileHandle = handle;
        await idbSetHandle(handle);
        await loadFromHandle(handle);
      } catch (e) { /* user cancelled */ }
    } else {
      // Fallback: plain file input
      const input = document.createElement("input");
      input.type = "file";
      input.accept = "application/json";
      input.onchange = async () => {
        const f = input.files[0];
        if (!f) return;
        try {
          const text = await f.text();
          applyConfig(JSON.parse(text));
          fileNameEl.textContent = f.name + " (loaded - Save will download an updated copy)";
          statusLine.textContent = "I found your existing variance-analysis configuration. Update anything you like, then Save.";
        } catch (e) {
          statusLine.textContent = "Could not read that file as valid configuration JSON.";
        }
      };
      input.click();
    }
  });

  btnSaveAs.addEventListener("click", async () => {
    if (!HAS_FS_ACCESS) {
      statusLine.textContent = "Your browser doesn't support direct file saving - use Save, which will download config.json (keep it inside the allneurons-flux folder).";
      return;
    }
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: "config.json",
        types: [{ description: "Config JSON", accept: { "application/json": [".json"] } }],
      });
      fileHandle = handle;
      await idbSetHandle(handle);
      fileNameEl.textContent = handle.name;
      btnSave.disabled = false;
      statusLine.textContent = "File location set. Fill in the form and click Save.";
    } catch (e) { /* user cancelled */ }
  });

  // Write `text` to `fileHandle`, verifying/acquiring write permission
  // first. Throws if permission is refused - callers decide what to do.
  async function writeToHandle(handle, text) {
    const ok = await verifyPermission(handle, "readwrite");
    if (!ok) throw new Error("write permission not granted");
    const writable = await handle.createWritable();
    await writable.write(text);
    await writable.close();
  }

  // Prompt the user to pick (or re-pick) where config.json lives, then
  // write it there and remember the handle for next time.
  async function pickLocationAndWrite(text) {
    const handle = await window.showSaveFilePicker({
      suggestedName: "config.json",
      types: [{ description: "Config JSON", accept: { "application/json": [".json"] } }],
    });
    await writeToHandle(handle, text);
    fileHandle = handle;
    await idbSetHandle(handle);
    fileNameEl.textContent = handle.name;
    btnSave.disabled = false;
  }

  async function writeConfig(cfg) {
    const text = JSON.stringify(cfg, null, 2);

    if (fileHandle) {
      try {
        await writeToHandle(fileHandle, text);
        fileNameEl.textContent = fileHandle.name;
        btnSave.disabled = false;
        return "handle";
      } catch (e) {
        // Stale or denied handle (file moved/deleted, permission revoked,
        // or a page reload lost live access). Don't dead-end on an error -
        // drop it and ask once more where to save, same as a first save.
        fileHandle = null;
      }
    }

    // No handle yet (first-ever save, or just cleared above). Rather than
    // silently downloading a copy the user then has to move by hand, ask
    // them once (via the picker) to point at allneurons-flux/config.json -
    // every Save after this writes straight back to that same file.
    if (HAS_FS_ACCESS) {
      try {
        await pickLocationAndWrite(text);
        return "handle";
      } catch (e) {
        // User cancelled the picker - fall through to the download fallback.
      }
    }

    // Fallback: trigger a download
    const blob = new Blob([text], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "config.json";
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    return "download";
  }

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    saveMsg.textContent = "";
    saveMsg.classList.remove("error");

    if (!form.reportValidity()) return;
    const accErr = validateAccountsAndJobs();
    if (accErr) {
      saveMsg.textContent = accErr;
      saveMsg.classList.add("error");
      return;
    }

    const cfg = serializeConfig();
    try {
      const mode = await writeConfig(cfg);
      loadedConfig = cfg;
      saveMsg.textContent = mode === "handle"
        ? "Saved to " + (fileHandle ? fileHandle.name : "config.json") + "."
        : "Downloaded config.json - move it into your allneurons-flux folder if it isn't there already.";
      statusLine.textContent = "Configuration saved.";
    } catch (e) {
      saveMsg.textContent = "Save failed: " + e.message;
      saveMsg.classList.add("error");
    }
  });

  document.getElementById("btnSave").addEventListener("click", () => form.requestSubmit());

  // ---------------------------------------------------------------
  // Data source sub-sections
  // ---------------------------------------------------------------
  form.querySelectorAll('input[name="dataSource"]').forEach((r) => {
    r.addEventListener("change", () => {
      const val = document.querySelector('input[name="dataSource"]:checked').value;
      document.getElementById("src-netsuite").hidden = val !== "netsuite";
      document.getElementById("src-sharepoint").hidden = val !== "sharepoint";
      document.getElementById("src-manual").hidden = val !== "manual";
      syncSharepointFolderRequired();
    });
  });

  function syncSharepointFolderRequired() {
    const val = document.querySelector('input[name="dataSource"]:checked').value;
    form.querySelector('[name="sp_folder"]').required = val === "sharepoint";
  }

  const nsReportSel = form.querySelector('[name="ns_report"]');
  if (nsReportSel) {
    nsReportSel.addEventListener("change", () => {
      document.getElementById("ns_savedSearchNameWrap").hidden = nsReportSel.value !== "saved_search";
    });
  }

  // ---------------------------------------------------------------
  // Output location
  // ---------------------------------------------------------------
  function syncOutputLocationField() {
    const val = document.querySelector('input[name="outputLocation"]:checked').value;
    document.getElementById("outputloc-onedrive").hidden = val !== "onedrive_sharepoint";
    form.querySelector('[name="outputLocation_folder"]').required = val === "onedrive_sharepoint";
  }
  form.querySelectorAll('input[name="outputLocation"]').forEach((r) => {
    r.addEventListener("change", syncOutputLocationField);
  });

  // ---------------------------------------------------------------
  // Accounts
  // ---------------------------------------------------------------
  function addAccountCard(data) {
    const node = accountCardTpl.content.cloneNode(true);
    const card = node.querySelector(".account-card");
    if (data) {
      card.querySelector(".acc-number").value = data.accountNumber || "";
      card.querySelector(".acc-name").value = data.accountName || "";
      card.querySelector(".acc-scope").value = data.defaultEntityScope || "";
    }
    card.querySelector(".remove").addEventListener("click", () => {
      card.remove();
      refreshJobAccountChecklists();
    });
    accountsList.appendChild(node);
    refreshJobAccountChecklists();
  }
  document.getElementById("btnAddAccount").addEventListener("click", () => addAccountCard());

  function currentAccounts() {
    return Array.from(accountsList.querySelectorAll(".account-card")).map((card, i) => ({
      id: "acct_" + (card.querySelector(".acc-number").value.trim() || i),
      accountNumber: card.querySelector(".acc-number").value.trim(),
      accountName: card.querySelector(".acc-name").value.trim(),
      defaultEntityScope: card.querySelector(".acc-scope").value.trim() || "all",
    }));
  }

  // Keep each job's account checklist in sync with the Accounts section
  function refreshJobAccountChecklists() {
    const accounts = currentAccounts();
    jobsList.querySelectorAll(".job-card").forEach((jobCard) => {
      const checklist = jobCard.querySelector(".job-accounts-checklist");
      const previouslyChecked = new Set(
        Array.from(checklist.querySelectorAll("input:checked")).map((i) => i.value)
      );
      checklist.innerHTML = "";
      accounts.forEach((a) => {
        const label = document.createElement("label");
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.value = a.id;
        cb.checked = previouslyChecked.has(a.id);
        label.appendChild(cb);
        label.appendChild(document.createTextNode(
          (a.accountNumber || "?") + " - " + (a.accountName || "unnamed")
        ));
        checklist.appendChild(label);
      });
      if (accounts.length === 0) {
        checklist.textContent = "Add at least one account above first.";
      }
    });
  }
  accountsList.addEventListener("input", refreshJobAccountChecklists);

  // ---------------------------------------------------------------
  // Scheduler jobs
  // ---------------------------------------------------------------
  function addJobCard(data) {
    const node = jobCardTpl.content.cloneNode(true);
    const card = node.querySelector(".job-card");

    const freqSel = card.querySelector(".job-frequency");
    const dowWrap = card.querySelector(".job-dow-wrap");
    const domWrap = card.querySelector(".job-dom-wrap");
    function syncFreqFields() {
      const v = freqSel.value;
      dowWrap.hidden = v !== "weekly";
      domWrap.hidden = v !== "monthly";
    }
    freqSel.addEventListener("change", syncFreqFields);

    const periodSel = card.querySelector(".job-period-pattern");
    const customWrap = card.querySelector(".job-custom-wrap");
    function syncPeriodFields() { customWrap.hidden = periodSel.value !== "custom"; }
    periodSel.addEventListener("change", syncPeriodFields);

    const outputLocSel = card.querySelector(".job-output-location");
    const outputFolderWrap = card.querySelector(".job-output-folder-wrap");
    function syncOutputLocation() {
      const isOnedrive = outputLocSel.value === "onedrive_sharepoint";
      outputFolderWrap.hidden = !isOnedrive;
      card.querySelector(".job-output-folder").required = isOnedrive;
    }
    outputLocSel.addEventListener("change", syncOutputLocation);

    // Per-job data-source override: which report (NetSuite) / which folder (SharePoint)
    const dsSel = card.querySelector(".job-datasource");
    const nsOverrideWrap = card.querySelector(".job-ns-override-wrap");
    const spOverrideWrap = card.querySelector(".job-sp-override-wrap");
    const nsReportSel = card.querySelector(".job-ns-report");
    const nsSavedSearchWrap = card.querySelector(".job-ns-savedsearch-wrap");
    const spFolderInput = card.querySelector(".job-sp-folder");
    function syncDataSourceOverride() {
      const v = dsSel.value;
      nsOverrideWrap.hidden = v !== "netsuite";
      spOverrideWrap.hidden = v !== "sharepoint";
      spFolderInput.required = v === "sharepoint";
    }
    dsSel.addEventListener("change", syncDataSourceOverride);
    nsReportSel.addEventListener("change", () => {
      nsSavedSearchWrap.hidden = nsReportSel.value !== "saved_search";
    });
    syncDataSourceOverride();

    card.querySelector(".remove").addEventListener("click", () => card.remove());

    if (data) {
      card.querySelector(".job-name").value = data.name || "";
      card.querySelector(".job-enabled").checked = data.enabled !== false;
      freqSel.value = data.frequency || "monthly";
      card.querySelector(".job-time").value = data.time || "09:00";
      if (data.dayOfWeek) card.querySelector(".job-dow").value = data.dayOfWeek;
      if (data.dayOfMonth) card.querySelector(".job-dom").value = data.dayOfMonth;
      periodSel.value = data.periodPattern || "previous_month_vs_month_before";
      if (data.customPeriod) card.querySelector(".job-custom-period").value = data.customPeriod;
      card.querySelector(".job-datasource").value = data.dataSource || "";
      card.querySelector(".job-entity-scope").value = data.entityScope || "";
      if (data.output) {
        const loc = data.output.saveLocation === "onedrive_sharepoint" ? "onedrive_sharepoint" : "allneurons_flux_folder";
        outputLocSel.value = loc;
        card.querySelector(".job-output-folder").value = data.output.oneDriveSharepointFolder || "";
      }
      if (data.sourceOverride) {
        nsReportSel.value = data.sourceOverride.netsuiteReport || "gl_line_detail";
        card.querySelector(".job-ns-savedsearch").value = data.sourceOverride.netsuiteSavedSearchName || "";
        spFolderInput.value = data.sourceOverride.sharepointFolder || "";
      }
    }
    syncFreqFields();
    syncPeriodFields();
    syncOutputLocation();
    syncDataSourceOverride();
    nsSavedSearchWrap.hidden = nsReportSel.value !== "saved_search";

    jobsList.appendChild(node);
    refreshJobAccountChecklists();

    // restore selected accounts after checklist render
    if (data && data.accountIds) {
      const justAdded = jobsList.querySelectorAll(".job-card");
      const thisCard = justAdded[justAdded.length - 1];
      data.accountIds.forEach((id) => {
        const cb = thisCard.querySelector('.job-accounts-checklist input[value="' + CSS.escape(id) + '"]');
        if (cb) cb.checked = true;
      });
    }
  }
  document.getElementById("btnAddJob").addEventListener("click", () => addJobCard());

  function currentJobs() {
    return Array.from(jobsList.querySelectorAll(".job-card")).map((card, i) => {
      const freq = card.querySelector(".job-frequency").value;
      return {
        id: card.dataset.jobId || ("job_" + (i + 1) + "_" + Date.now().toString(36)),
        name: card.querySelector(".job-name").value.trim(),
        enabled: card.querySelector(".job-enabled").checked,
        frequency: freq,
        time: card.querySelector(".job-time").value,
        dayOfWeek: freq === "weekly" ? card.querySelector(".job-dow").value : null,
        dayOfMonth: freq === "monthly" ? Number(card.querySelector(".job-dom").value || 1) : null,
        periodPattern: card.querySelector(".job-period-pattern").value,
        customPeriod: card.querySelector(".job-period-pattern").value === "custom"
          ? card.querySelector(".job-custom-period").value.trim() : null,
        accountIds: Array.from(card.querySelectorAll(".job-accounts-checklist input:checked")).map((i2) => i2.value),
        entityScope: card.querySelector(".job-entity-scope").value.trim() || "all",
        dataSource: card.querySelector(".job-datasource").value || null,
        sourceOverride: {
          netsuiteReport: card.querySelector(".job-ns-report").value,
          netsuiteSavedSearchName: card.querySelector(".job-ns-savedsearch").value.trim() || null,
          sharepointFolder: card.querySelector(".job-sp-folder").value.trim() || null,
        },
        output: {
          saveLocal: true,
          localFolder: "allneurons-flux/outputs",
          saveLocation: card.querySelector(".job-output-location").value,
          oneDriveSharepointFolder: card.querySelector(".job-output-folder").value.trim() || null,
        },
        scheduledTaskId: card.dataset.scheduledTaskId || null,
      };
    });
  }

  function validateAccountsAndJobs() {
    const accounts = currentAccounts();
    if (accounts.some((a) => !a.accountNumber || !a.accountName)) {
      return "Every account needs at least a number and a name.";
    }
    const jobs = currentJobs();
    for (const j of jobs) {
      if (!j.name) return "Every scheduler job needs a name.";
      if (j.accountIds.length === 0) return 'Job "' + j.name + '" needs at least one account selected.';
      if (j.output.saveLocation === "onedrive_sharepoint" && !j.output.oneDriveSharepointFolder) {
        return 'Job "' + j.name + '" saves output to OneDrive/SharePoint but no folder is specified.';
      }
      if (j.dataSource === "sharepoint" && !j.sourceOverride.sharepointFolder) {
        return 'Job "' + j.name + '" sources from Share Drive but no folder is specified for it.';
      }
    }
    const ds = document.querySelector('input[name="dataSource"]:checked').value;
    if (ds === "sharepoint" && !form.querySelector('[name="sp_folder"]').value.trim()) {
      return "Please specify which Share Drive folder to look in (Data Source section).";
    }
    if (!form.querySelector('[name="notify_sender"]').value.trim()) {
      return "Please specify the completion email's sender address (Notifications section).";
    }
    if (!form.querySelector('[name="notify_recipient"]').value.trim()) {
      return "Please specify who should receive the completion email (Notifications section).";
    }
    const outputLoc = document.querySelector('input[name="outputLocation"]:checked').value;
    if (outputLoc === "onedrive_sharepoint" && !form.querySelector('[name="outputLocation_folder"]').value.trim()) {
      return "Please specify the OneDrive/SharePoint folder for output (Output Location section).";
    }
    return null;
  }

  // ---------------------------------------------------------------
  // Serialize form -> config.json shape
  // ---------------------------------------------------------------
  function serializeConfig() {
    const fd = new FormData(form);
    const now = new Date().toISOString();
    return {
      schemaVersion: SCHEMA_VERSION,
      createdAt: (loadedConfig && loadedConfig.createdAt) || now,
      updatedAt: now,
      defaults: {
        dataSource: fd.get("dataSource"),
        significance: {
          absoluteThreshold: Number(fd.get("absoluteThreshold") || 0),
          percentThreshold: Number(fd.get("percentThreshold") || 0) / 100,
          // Always on - not exposed in the UI; the skill treats these as
          // standard variance-analysis discipline, not a per-run choice.
          flagNewCounterparty: true,
          flagEntityLevelOffsetting: true,
        },
        output: {
          saveLocation: fd.get("outputLocation") || "allneurons_flux_folder",
          oneDriveSharepointFolder: fd.get("outputLocation_folder") || null,
        },
      },
      connectors: {
        netsuite: {
          report: fd.get("ns_report") || "gl_line_detail",
          savedSearchName: fd.get("ns_savedSearchName") || null,
          accountingBookNote: fd.get("ns_accountingBookNote") || "",
          defaultSubsidiaryScope: fd.get("ns_defaultSubsidiaryScope") || "all",
        },
        sharepoint: {
          folder: fd.get("sp_folder") || "",
          hint: fd.get("sp_hint") || "",
        },
        manual: {},
        notification: {
          sender: fd.get("notify_sender") || "",
          recipient: fd.get("notify_recipient") || "",
        },
      },
      accounts: currentAccounts(),
      manualRunDefaults: {
        periodA: fd.get("periodA") || null,
        periodB: fd.get("periodB") || null,
      },
      schedulerJobs: currentJobs(),
    };
  }

  // ---------------------------------------------------------------
  // Apply loaded config.json -> form
  // ---------------------------------------------------------------
  function applyConfig(cfg) {
    loadedConfig = cfg;
    if (cfg.defaults) {
      const ds = cfg.defaults.dataSource || "sharepoint";
      const dsInput = form.querySelector('input[name="dataSource"][value="' + ds + '"]');
      if (dsInput) { dsInput.checked = true; dsInput.dispatchEvent(new Event("change")); }
      const sig = cfg.defaults.significance || {};
      form.querySelector('[name="absoluteThreshold"]').value = sig.absoluteThreshold != null ? sig.absoluteThreshold : 1000;
      form.querySelector('[name="percentThreshold"]').value = sig.percentThreshold != null ? sig.percentThreshold * 100 : 20;
      // flagNewCounterparty / flagEntityLevelOffsetting are always true -
      // no form fields to populate for them (see serializeConfig).
      const out = cfg.defaults.output || {};
      const loc = out.saveLocation || "allneurons_flux_folder";
      const locInput = form.querySelector('input[name="outputLocation"][value="' + loc + '"]');
      if (locInput) { locInput.checked = true; }
      form.querySelector('[name="outputLocation_folder"]').value = out.oneDriveSharepointFolder || "";
      syncOutputLocationField();
    }
    if (cfg.connectors) {
      if (cfg.connectors.netsuite) {
        form.querySelector('[name="ns_report"]').value = cfg.connectors.netsuite.report || "gl_line_detail";
        form.querySelector('[name="ns_savedSearchName"]').value = cfg.connectors.netsuite.savedSearchName || "";
        document.getElementById("ns_savedSearchNameWrap").hidden = (cfg.connectors.netsuite.report || "gl_line_detail") !== "saved_search";
        form.querySelector('[name="ns_accountingBookNote"]').value = cfg.connectors.netsuite.accountingBookNote || "";
        form.querySelector('[name="ns_defaultSubsidiaryScope"]').value = cfg.connectors.netsuite.defaultSubsidiaryScope || "";
      }
      if (cfg.connectors.sharepoint) {
        form.querySelector('[name="sp_folder"]').value = cfg.connectors.sharepoint.folder || "";
        form.querySelector('[name="sp_hint"]').value = cfg.connectors.sharepoint.hint || "";
      }
      if (cfg.connectors.notification) {
        form.querySelector('[name="notify_sender"]').value = cfg.connectors.notification.sender || "";
        form.querySelector('[name="notify_recipient"]').value = cfg.connectors.notification.recipient || "";
      }
    }
    syncSharepointFolderRequired();
    accountsList.innerHTML = "";
    (cfg.accounts || []).forEach((a) => addAccountCard(a));

    if (cfg.manualRunDefaults) {
      form.querySelector('[name="periodA"]').value = cfg.manualRunDefaults.periodA || "";
      form.querySelector('[name="periodB"]').value = cfg.manualRunDefaults.periodB || "";
    }

    jobsList.innerHTML = "";
    (cfg.schedulerJobs || []).forEach((j) => {
      addJobCard(j);
      const cards = jobsList.querySelectorAll(".job-card");
      const thisCard = cards[cards.length - 1];
      thisCard.dataset.jobId = j.id;
      if (j.scheduledTaskId) thisCard.dataset.scheduledTaskId = j.scheduledTaskId;
    });
  }

  // ---------------------------------------------------------------
  // Init
  // ---------------------------------------------------------------
  if (accountsList.children.length === 0) addAccountCard();
  syncSharepointFolderRequired();
  syncOutputLocationField();
  tryAutoLoad();
})();
```
