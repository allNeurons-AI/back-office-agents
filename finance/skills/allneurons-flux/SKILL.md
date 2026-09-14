
Customize
allneurons-variance-analysis
New
by you · v17 · in Allneurons variance analysis · updated 3 days ago


Allneurons variance analysis v17 · current
0017

SKILL.md
/SKILL.md


---
name: "allneurons-variance-analysis"
description: "Explains what changed in one or more financial accounts between exactly two periods - months, quarters, year-to-date, or year-on-year. Hands over the findings and the Excel workbook the moment they exist, then does the optional work - drive copy, report page, email - afterwards, and finally offers to schedule the same job. Trigger whenever someone wants a period-over-period variance or flux explained - 'why did this account move', 'explain the variance between May and June', 'compare Q1 and Q2', 'what's driving account 63200', 'run the monthly flux' - from live NetSuite GL detail, a Share Drive/SharePoint export, or an uploaded spreadsheet. Infers what it can from the request, finds its saved settings before asking anything, and confirms the run in one approval."
---
 
Explains what changed in one or more financial accounts/categories between exactly two periods. Full instructions follow.
 
# allneurons-variance-analysis
 
## Scope
 
This skill explains **what changed in one or more financial accounts/categories between exactly
two periods**, consolidated or scoped to an entity/segment.
 
**"Two periods" means two things being compared, not two months.** A period is a *set* of
accounting months summed together, so a month, a quarter, a year-to-date span and a same-period-
last-year comparison are all in scope. Three or more periods are not - that's trend analysis.
 
**Delivery order is part of the design.** The user's question is "what moved and why" - so the
answer and the workbook come first, and everything optional happens after they already have them:
 
1. **The findings, in chat**, the moment they exist.
2. **The Excel workbook, handed over immediately** - saved locally and delivered into the chat.
3. *Then* the optional work: the drive copy, the report page, the email.
4. *Then* an offer to schedule the same job.
**Variance only.** For trend analysis across more than two periods, standalone anomaly scanning,
reconciliation between systems, or forecasting, say so plainly and offer a variance run instead.
 
Six principles run through everything below:
 
- **Infer before asking, and find the saved config before asking anything at all.** Steps 0-1.
- **Never re-ask an answered question** - and when an answer goes missing, suspect the form
  before blaming the user. Step 1f.
- **Show the plan as a card with the data already in hand, then ask one short question.** Step 6.
- **Never make the user wait on optional work.** Step 8.
- **Do the heavy lifting in code, in as few calls as possible.** Performance.
- **Narrate in visible text as you go.** Voice.
---
 
## Architecture
 
```
allneurons-variance-analysis          <- this file
<home folder>/allneurons-flux/        <- persistent config directory, ONE per user
  config.json                         <- single source of truth (schema below)
  outputs/                            <- final workbook for EVERY run lands here
```
 
`allneurons-flux/` lives in a **persistent, user-visible folder** - `config.json` must survive
across sessions and be readable by scheduled runs.
 
**There is exactly one `allneurons-flux/` per user.** A second one in a different connected
folder is the worst bug this skill can have: the next run finds no config where it looks,
concludes it's a first run, and asks everything again. Step 0 exists to prevent it.
 
**No UI files.** Forms render inline in the chat; `config.json` is written with the `Write` tool.
If `index.html` / `style.css` / `script.js` are still in the folder from an old version, leave
them alone but never touch them.
 
---
 
## Tools this skill needs
 
Load these in **one** `ToolSearch` at the start of pre-flight. Names are given bare - match them
by suffix against whatever the session exposes, since the connector prefix differs per install.
 
| Tool | Used for | When |
|---|---|---|
| `get_me` | the user's mailbox - sender identity, default recipient | always |
| `sharepoint_folder_search` | candidate folder discovery | Share Drive source only |
| `sharepoint_search` | finding the export, scoped by `folderName` | Share Drive source only |
| `read_resource` | reading the found file | Share Drive source only |
| `sharepoint_upload_file` | the drive copy of the workbook | `onedrive_sharepoint` output only |
| `outlook_send_mail` | the completion email | always |
 
Plus the `*_scheduled_task` tools only if the user accepts the scheduling offer in Step 9.
 
Nothing from calendar, Teams, drafts, labels or filters is ever needed.
 
---
 
## Periods - how they're defined, offered and resolved
 
Everything about periods lives here so the rules stay in one place.
 
### A period is a list of months
 
Internally a period is always `{label, months[]}` - `{"Q2 2026", ["2026-04","2026-05","2026-06"]}`
or `{"Jul 2026", ["2026-07"]}`. A single month is just a one-element list. Every downstream step
works on that shape, which is what lets months, quarters and year-to-date spans share one code
path.
 
### Direction is explicit, always
 
**Period A is the baseline; Period B is the one being explained; `Δ = B − A`.** Reading that
backwards inverts every sign in the report and nothing downstream looks wrong, so never present a
bare `X vs Y`. Labels always carry the arrow and the subject:
 
> `Jun → Jul 2026 · explaining Jul`
 
and the plan card says it in words: "explaining July 2026 against a June 2026 baseline".
 
### What the form offers
 
Compute these from today's date and offer them as **comparison shapes**, not bare dates - naming
the pattern teaches the choice. With today at 12 Sep 2026 they resolve to:
 
| Pill | Resolves to |
|---|---|
| `Jul → Aug 2026 · explaining Aug (last closed month)` | prior month |
| `Aug 2025 → Aug 2026 · explaining Aug, year on year` | same month last year |
| `Q1 → Q2 2026 · explaining Q2 (last closed quarter)` | prior quarter |
| `Q2 2025 → Q2 2026 · explaining Q2, year on year` | same quarter last year |
| `Jan–Aug 2025 → Jan–Aug 2026 · year to date` | YTD vs prior YTD |
| `Other` | free text, parsed below |
 
Only **closed** periods are offered. On 12 Sep 2026 the last closed month is August and the last
closed quarter is Q2 - Q3 is still running.
 
Say plainly in the hint that for seasonal accounts - travel, marketing, anything with a calendar
shape - **year on year is usually the more informative comparison**, because month-over-month on
a seasonal account is largely noise.
 
### Parsing the `Other` field
 
Accept all of these and resolve to two month lists:
 
- `Q1 2026 vs Q2 2026` or `Q1 → Q2 2026`
- `Jan-Mar 2026 vs Apr-Jun 2026`
- `2026-01..2026-03 vs 2026-04..2026-06`
- a comma list: `Jan 2026, Feb 2026, Mar 2026 vs Apr 2026, May 2026, Jun 2026`
- a plain month pair: `May 2026 to Jun 2026`
**Where direction is ambiguous, resolve it and say which way you read it** - "taking Q1 as the
baseline and explaining Q2" - rather than guessing silently. If the text can't be resolved at all,
ask; never approximate a period.
 
**If a named period isn't closed yet, say so before running.** "Q3 2026 isn't finished - July and
August are in, September isn't, so the Q3 total will be two thirds of a quarter." Offer the last
closed period instead. Proceed only if the user still wants it, and stamp the partial period in
the workbook and the report.
 
### Build the options from the data when you can
 
When the source folder is already known - which is every reuse run - **locate and read the file's
actual period range before rendering the periods group**, and offer only pairs the data can
answer. A file covering May and June should never present a July option. This removes the
wrong-periods blocker entirely: it becomes unselectable rather than a mid-run stop.
 
On a genuine first run the folder isn't known yet, so the pills are computed from the calendar and
the Step 4 check remains the safety net. Say which of the two you did.
 
---
 
## Performance - the call budget
 
**About eight tool calls to the point of delivery** - five or six on a reuse run. The optional
tail adds two or three more, but the user already has the result by then.
 
```
1  ToolSearch          - the tools above, in ONE call
2  show_widget         - form 1 (source)      [skipped when inferred or config found]
3  one scoped search   - find the file (also feeds the period options)
4  show_widget         - form 2 (the rest)    [skipped when config found]
5  one read            - land the data in the sandbox
6  one script          - normalize, roll up, tie out, build the workbook, save it locally
7  present_files       - HAND IT OVER HERE
-- everything below is after the user has the result --
8  batch: upload + Artifact publish   (independent of each other)
9  outlook_send_mail                  (needs the links from 8)
```
 
**Never move the ledger through the conversation.** Land raw data as a file in the sandbox; do
every numeric operation there in pandas. What comes back is only: the top ~20 movers by `|Δ($)|`
with amounts; memo text for those rows only; control total, rollup total, residual; and
row/counterparty/currency/entity/month counts.
 
*The one unavoidable exception:* when a connector is the only route to a file, it returns content
into the conversation and the sandbox can't reach the source. Take that read **once**, write the
rows to a sandbox file in the next call, never print or re-read them.
 
Parse numerics with `pd.to_numeric(..., errors="coerce")` and count the nulls - a nonzero count
is a data-quality finding, not something to drop.
 
**Push every filter to the source.** Accounts, every month of both periods, and subsidiary scope
go in the query. Only the seven normalized columns - never `SELECT *`.
 
**Search once, scoped - never speculatively.** The folder comes from the user or the config.
 
**One script for the whole compute path.** Compute, build the workbook and save it together; the
same script takes the execution timestamp. **Never print file bytes, base64, or a whole ledger to
stdout.**
 
**Discover in one cheap pass, and abandon it cheaply.** Before form 1: connector liveness,
mailbox, the computed period shapes. After form 1: at most **one** call for the chosen source.
 
**Ground only what you'll write up** - memo text for threshold-crossing rows only.
 
---
 
## Step 0 - Find the one `allneurons-flux/`
 
1. **Search every connected folder** for an existing `allneurons-flux/config.json`.
2. Then:
   - **Exactly one** -> that's home. Never create another.
   - **Several** -> don't guess, don't merge. List them with paths and `updatedAt` dates, ask
     which is canonical.
   - **None** -> genuine first run. One folder connected: create it there. Several: **ask where**.
     Create `outputs/` at the same time.
   - A connected folder already named `allneurons-flux` *is* the directory - don't nest another.
3. Record the absolute path as `homeFolder`; check it first on later runs.
4. **Say where it resolved, in one line**, every run.
## Step 1 - Configuration
 
### 1a. Infer from the request first
 
Read what the user actually said before rendering anything. "Run the flux on 63200 for Q1 vs Q2
from my SharePoint export" already answers source, accounts and periods.
 
Take whatever the request genuinely states, including period shapes - "compare Q1 and Q2", "same
month last year", "year to date". **Skip form 1 entirely when the source is clear.** Pre-fill
form 2 and render only genuinely unknown groups. Never over-read: if a value is implied rather
than stated, treat it as unknown. Every inference is shown back on the plan card.
 
### 1b. Pre-flight - one tool call, one probe batch
 
**Load the tools in a single `ToolSearch`.** Then narrate one line and probe in one parallel
batch: connector liveness (probe only); the user's mailbox via `get_me`; and the computed period
shapes for today.
 
**Skip this when a config was found and the user reuses it.**
 
*Why there's no sender field:* the email goes out through the connector as the authenticated
mailbox. The From address is fixed to the signed-in user. The form asks only *to whom*.
 
### 1c. Config found - reuse or update
 
Show a compact confirm card (`show_widget`, not a form): **where the config was found**,
accounts, the periods resolved for today with their direction, source, entity scope, thresholds,
output destination, recipient. Two `sendPrompt` actions:
 
- **"Run it with these settings"** -> Step 2, then the plan card.
- **"Update settings"** -> open form 1 (pre-selected to the saved source), then form 2 pre-filled.
  Preserve `createdAt`, `homeFolder`, `discoveryCache`, `schedulerJobs`, and every untouched field.
### 1d. Form 1 - which source
 
Only when the source wasn't inferred and no config exists. Three **cards**:
 
- `netsuite` - "NetSuite (live)" / "Pull GL line detail straight from NetSuite. **Choose this
  when** your books are closed in NetSuite, you want the numbers as the system holds them today,
  and you don't want to depend on someone having published an export. Reads
  transactionaccountingline detail, so amounts are functional-currency source of truth. Needs the
  NetSuite connector live."
- `sharepoint` - "Share Drive / SharePoint" / "Read a GL or transaction export already sitting in
  a folder. **Choose this when** Finance publishes the export you'd otherwise open by hand."
- `manual` - "Upload a file" / "**Choose this for** a one-off look at a spreadsheet you have
  right now."
Mark any card pre-flight found *not* live. Exhaustive, so no `Other`.
 
### 1e. Form 2 - and the only input elements that actually work
 
**Use the elicitation shell. Never build your own form.** No `<script>`, no `onclick`, no submit
button of your own. A hand-rolled widget with its own "Submit" is wired to nothing: it renders,
accepts typing, and the values never arrive.
 
**Only these elements report a value:**
 
| To collect | Use exactly this |
|---|---|
| a choice from a list | `<button type="button" class="elicit-pill" data-value="…">` inside `<div class="elicit-pills" data-name="…">` |
| free text behind an "Other" | a pill carrying `data-other`, plus `<input type="text" class="elicit-other" data-for="…">` |
| free text with no list | `<textarea class="elicit-textarea" data-name="…">` |
| a date | `<input type="date" class="elicit-date" data-name="…">` |
| a file | the `.elicit-files` dropzone with its paired textarea fallback |
 
**Never a bare `<input type="text">`, never a `<select>`.** The signature of getting it wrong is a
payload where every pill group came back and every typed field is missing. These rules apply to
**every** form this skill renders, including the scheduling form in Step 9.
 
Header title `Variance details`. Every label a question. Omit any group already answered by
inference or config - state what was carried over. **Every non-exhaustive choice group ends with
`Other`** and its paired `.elicit-other`; suggested values are a shortcut, never a constraint.
 
**The source-specific group comes first**, and only the one matching the chosen source is rendered.
 
- **NetSuite** - "Which report should I pull from?" Pills: `GL Line Detail` (default) plus each
  discovered saved search, plus `Other`. Optional `.elicit-textarea` for the accounting book.
- **Share Drive** - "Which folder should I search for the GL export?" (required) - discovered
  folders as pills plus `Other`, or `<textarea class="elicit-textarea" data-name="sharepoint_folder">`
  with placeholder `Finance/GL Exports`. Optional `.elicit-textarea` for extra keywords.
- **Upload** - "Give me the file" (required) - the `.elicit-files` dropzone plus its fallback.
Then, for every source:
 
- **Accounts** (required) - discovered accounts as `data-multi="true"` pills labelled
  `<number> - <name>` plus `Other`; or `<textarea class="elicit-textarea" data-name="accounts">`:
  "give me the GL number and name, e.g. `63200 - Travel & entertainment`. Several can be
  comma-separated."
- **Entity scope** - pills: `Consolidated (all entities)` (default), discovered entities, `Other`.
- **Periods** (required) - the comparison shapes from the Periods section above, each pill
  carrying its direction and subject, plus `Other` + `.elicit-other` with placeholder
  `e.g. Q1 2026 vs Q2 2026, or Jan-Mar vs Apr-Jun 2026`. Hint: "Period A is the baseline, Period B
  is what I'm explaining. For seasonal accounts, year on year usually tells you more than
  month on month."
- **Threshold - two separate groups, never merged:**
  1. `absolute_threshold` - "How big does a movement have to be, in dollars, before I write it
     up?" Pills `$1,000` (default), `$5,000`, `$10,000`, **`Other`**.
  2. `percent_threshold` - "And in percentage terms?" Pills `10%`, `20%` (default), `50%`,
     **`Other`**.
  Hint under the second: "Crossing either one lists a movement in the Flux tab. It doesn't by
  itself flag the row for review - that's for missing or ambiguous evidence, decided when the
  analysis runs. A movement of exactly zero is never listed."
- **Notification recipient** (required) - pills: the address from 1b (labelled "you"), plus
  `Other`.
- **Output location** (required) - tiles: `allneurons_flux_folder`, `claude_working_folder`,
  `onedrive_sharepoint`. Exhaustive, no `Other`. Then
  `<textarea class="elicit-textarea" data-name="output_folder">`: "**If you picked OneDrive /
  SharePoint** - which folder?"
No schedule group here - scheduling is offered in Step 9, after the result.
 
**Check the form before rendering it.** Walk the composed HTML and confirm: the one
source-specific group and only that one; accounts; entity scope; periods; both thresholds as
separate groups; notification recipient; output tiles plus the drive-folder field; every
non-exhaustive group ending in `Other` + its paired input; and finally, **element by element,
that every input is one of the five in the table and carries its `data-name` or `data-for`.** A
wrong element looks perfect on screen and silently drops the answer.
 
### 1f. Read the payload, save immediately, ask only for real gaps
 
**Resolve the payload.** The shell returns an `Other` choice as **two** entries - a pill value of
`Other` and a companion `<Field> (other)`. Merge them: `Periods: Other` plus `Periods (other):
Q1 2026 vs Q2 2026` is an **answered** field. Never read the literal "Other" as a non-answer.
Resolve period text per the Periods section and state the direction you read.
 
**Write `config.json` straight away**, before validating anything. Answers must never be lost to a
later stumble or collected twice.
 
**Then work out what's genuinely missing.** Not-applicable is not a gap: `output_folder` matters
only for `onedrive_sharepoint`, and a saved `oneDriveSharepointFolder` already answers it. The
source-specific field is required only for the source chosen. Required set: accounts, periods,
recipient, output location, and the one source-specific field.
 
**When a field the form definitely contained comes back absent, that is a composition bug, not a
user error.** The tell is a payload where the pill groups all arrived and the typed fields didn't.
Say so plainly - "the folder, accounts and periods fields didn't send their values, which is my
form's fault, not yours" - ask for just those, and use the correct element next time.
 
## Step 2 - Resolve run context, then say what you're doing
 
Use what the request named; otherwise `manualRunDefaults` and `accounts[]`. Resolve both periods
to month lists. Then one visible line with the direction spelled out: "Right - account 63200,
explaining Q2 2026 against Q1, consolidated, from the Share Drive export."
 
## Step 3 - Connectors
 
```
detect(connector):
  1. Is a working tool for it present in the session?
  2. If found -> confirm live with a trivial call.
  3. If not, or it fails:
       - Say plainly which connector needs connecting.
       - search_mcp_registry, then suggest_connectors to surface the Connect button.
       - Wait for authentication - never proceed, never work around it.
       - Recheck; continue automatically if live.
       - If still unavailable, say so and offer a fallback rather than looping.
```
 
Check the **output destination's** connector *before* the plan promises it.
 
**NetSuite** - pull from the configured report, **GL Line Detail** by default. Accounts, **every
month of both periods**, and subsidiary scope go **in the query**; only the seven normalized
columns. Results straight to a sandbox file. Verify which subsidiaries actually exist.
 
**Share Drive** - **one scoped search**: query plus `folderName` from the config. Take the read
**once**, write rows to a sandbox file immediately, and say that this read is unavoidable.
 
**Upload** - read in the sandbox, auto-map columns, confirm the mapping, validate.
 
## Step 4 - Retrieve, normalize, validate - and surface what you found
 
Pull the **full scope in scope** - filtered to the accounts, **every month of both periods** and
the entities being analysed, never sampled within that scope. Normalize to `{period, account,
amount, counterparty/vendor, memo, entity/segment, currency}`, keeping the accounting month on
every row - it's needed for FX and for the concentration check.
 
**Report the shape the instant the data lands** - row count, distinct counterparties, currencies,
entities, and **which months are present**.
 
**Blockers stop the run and ask**, reported the instant they're found:
 
- **a month belonging to either period is missing.** With multi-month periods this is the easy
  one to miss: an export holding April and May but not June passes a naive "both periods have
  data" check while the Q2 total is a third short. Check **every** month of both periods and name
  any that are absent.
- the file covers different periods than requested entirely
- an account in scope has no rows
- a required column can't be mapped, or many amounts failed numeric parsing
**Synthetic or sample data doesn't stop the run and is never a question.** Say so prominently,
carry on, and stamp it everywhere.
 
**Discovered live, never asked:** the **rollup dimension** (vendor/counterparty when present and
populated, else entity, then cost center; where the counterparty is null but the memo names one,
recover it and label it memo-derived); the **reporting currency**; which entities exist.
 
## Step 5 - Variance methodology
 
Computed in code, not by hand or eye.
 
- Exactly two periods, A and B, each a list of months. Roll up by the Step 4 dimension.
  `Δ($) = B − A`; `Δ(%) = Δ / |A|`, reported "n/m" when A is 0.
- **Multi-currency translation is per month, then summed - never per period.** Each accounting
  month carries its own average rate. Summing GBP across April, May and June and applying one
  rate gives the wrong number, and it fails silently: the total just drifts. Translate each
  month's amount at that month's rate, *then* add the months into the period total. Keep
  original-currency amounts visible and reconcile any residual.
- **For multi-month periods, note concentration.** A counterparty up $50,000 across a quarter
  reads very differently if it was almost all in June. For every mover, record whether the
  movement is spread across the period's months or concentrated in one, and say which - it's the
  most useful thing a quarterly comparison tells you that a monthly one can't.
### Significance and review flag are two different tests
 
**Significance** (`absoluteThreshold` / `percentThreshold`) decides only whether a row is
material enough to appear in the Flux tab: `|Δ($)| > absoluteThreshold` **or**
`|Δ(%)| > percentThreshold`, strictly greater than. A row with **zero net movement** is never
significant and never a flux finding, **whatever the threshold** - `0` means "surface every
nonzero movement, however small", not "treat no-movement as a finding". Zero-movement rows still
feed the Summary tie-out; they get no Flux row.
 
**Review flag (Y/N)** is set independently for rows already in the Flux tab and marks evidentiary
or data-integrity concern, never dollar size. **Y** only when at least one holds: no supporting
memo could be found; the memo is ambiguous, generic, or contradicts the amount or direction; a
likely data-quality issue (currency or mapping mismatch, duplicate-looking entry, unexpected
sign, wrong-entity posting, failed numeric parse); a brand-new counterparty in B with zero prior
activity, when `flagNewCounterparty`; entity-level offsetting at consolidated scope, when
`flagEntityLevelOffsetting`.
 
A row can be large, clearly above threshold, and still be **N** when its driver is well-documented
and unambiguous. **Never set Y solely because a row crossed the threshold.**
 
At consolidated scope, flag counterparties whose consolidated net is small but whose entity legs
are large - for review, never asserted as error.
 
Ground every flagged item in real memo text. "No clear driver found in the data" is a valid,
honest finding. Keep source data, calculation, finding, interpretation and recommendation
visibly distinct.
 
## Step 6 - The plan: a card to read, then one question
 
**The plan is something the user looks at; the approval is something they click.** Never pour the
plan into an `AskUserQuestion` prompt.
 
### Part one - the plan card (`show_widget`)
 
Label-and-value rows, no paragraphs, one screen. Header "Variance run plan"; a flagged line under
it if the source is synthetic or a period is unclosed.
 
**Analysis** - Account(s); **Periods, with direction in words** (`Q1 2026 → Q2 2026 · explaining
Q2`, and the months each covers); Entity scope; Source (connector plus the actual file name);
**Data found** (`1,412 lines · 38 counterparties · USD/GBP/EUR · all 6 months present`); Rolled up
by; Reporting currency (and that translation is per month); Threshold; GL Details scope. Mark
anything inferred from the request.
 
**Then** - every side effect in delivery order: Save → `allneurons-flux/outputs/`; Deliver →
`into this chat, immediately`; Copy → the drive folder (when configured); Publish → `a variance
report page, private to you until you share it`; Email → `<recipient>, from your own mailbox`.
 
### Part two - the approval (`AskUserQuestion`)
 
One line: "Approve this run?"
 
1. **Approve everything** - run, deliver, then copy, publish and send.
2. **Approve the analysis, skip the email** - run, deliver, copy and publish; send nothing.
3. **Change something** - say what to adjust and the plan is redone.
One approval authorises the whole run including the publish and the send. Never follow an
approved plan with a second permission question at delivery. Approval never carries across runs.
 
## Step 7 - One script: compute, save locally, report
 
**A single script**: roll up per Step 5 with per-month FX translation; compute deltas,
percentages and the concentration note; compute the control total **independently of the rollup
sum**; take the execution timestamp; build the three-tab workbook and **save it to
`allneurons-flux/outputs/`**; and print the rollup, top movers with memo text and concentration,
control total, tie-out difference, parse-failure count and check results.
 
**Report in chat, as text, immediately** - net variance, movements above threshold, count
flagged; the top movers with Δ($), Δ(%), the memo grounding each and whether the movement was
concentrated in one month; anything flagged with its reason; what was correctly excluded, naming
below-threshold and zero-movement rows explicitly; honest empty states. Nothing may delay this.
 
**The three tabs**:
 
1. **Summary** - the rollup plus an `=SUM()` tie-out to the independent control total, difference
   as a formula. For multi-month periods, show the month-by-month split behind each period total
   so the quarter can be read as well as trusted. Zero-movement rows may appear here for tie-out.
2. **Flux** - every evidenced movement above threshold: finding, interpretation (labelled as
   interpretation, not fact), **review flag (Y/N)**, concentration, integrity flags. If a check
   ran and found nothing, say so. Zero-movement rows never appear.
3. **GL Details** - line items with full traceability, the accounting month, the FX rate used for
   that month, and a per-row translation formula.
Formulas not hardcoded numbers; recalc with zero formula errors; stamp synthetic sources and
unclosed periods on every tab.
 
**Filename**: `<Account-or-scope>_Variance_<PeriodA>_vs_<PeriodB>_<YYYY-MM-DD>_<HH-MM>.xlsx`,
where the period labels are the short forms - `2026-Q1_vs_2026-Q2`, `2026-07_vs_2026-08`.
 
**Verify before delivering**: the rolled-up total ties to the independent control total; every
month of both periods contributed; any deliberate exclusion or residual is named beside the
number; no zero-movement row carries a Y flag; no flag is Y for magnitude alone.
 
## Step 8 - Hand it over first, then do the optional work
 
**Deliver the workbook the instant it exists.** `mcp__cowork__present_files` is the very next
call after the compute script - before any upload, before the report page, before the email.
Nothing optional may stand between the user and the result.
 
*An honest note on how this works:* tool calls run in sequence, so the work below happens
**after** delivery rather than truly in parallel. There is no fire-and-forget. What the ordering
buys is real - the user can read the findings and open the workbook while the rest runs, and a
failure in any of it can no longer delay the result. Never describe this as asynchronous.
 
**Then, in one batch** (they're independent):
 
- **The drive copy**, when `saveLocation` is `onedrive_sharepoint` - upload to
  `output.oneDriveSharepointFolder` in a call that **prints nothing else**. Never echo the base64,
  pass `expectedBytes` computed in the run that produced the bytes, use
  `conflictBehavior: "fail"`, retry **alone** if truncated, report the **link the API returned**.
- **The report page** - a **new page per run**; never overwrite a previous period's. **Load the
  `artifact-design` skill before composing it.** Title short and distinctive with the periods:
  `63200 Variance — Q2 vs Q1 2026`. One-sentence description; one emoji favicon. Contents in the
  order of the findings: synthetic or unclosed-period banner if applicable; the headline with
  direction spelled out; three figures; the movers table with Δ($), Δ(%), review flag,
  concentration and memo evidence; what's flagged and why; the tie-out; the scope block; where
  the workbook is saved. Tables scroll inside their own container. Note it's private until shared.
**Then the email**, which needs the links above. Send as the authenticated mailbox,
`bodyType: "html"`. Report the outcome in one line. **Never state or imply it was sent unless it
succeeded.**
 
**Every optional destination either visibly succeeds or visibly fails**, each with its own line.
A failure never retracts the delivered result, but it is stated, never swallowed.
 
### The email template
 
One screen, numbers before prose. HTML using only `h3`, `p`, `strong`, `em`, `br`, `ul`/`li`,
`table`/`tr`/`th`/`td`, `a`.
 
**Subject**: `Variance: 63200 Travel & Entertainment - Q2 2026 vs Q1 2026`. Several accounts:
`Variance: 3 accounts - …`. Entity-scoped: append `(Widget UK Ltd)`. Synthetic: append
` [SYNTHETIC TEST DATA]`.
 
**Body**, in order: synthetic or unclosed-period warning first if applicable (bold, never below
the numbers); the headline with direction spelled out; the movers table (Counterparty, Δ, Δ%,
Review - five rows maximum, each flagged row's driver and concentration in a short line beneath);
what's flagged and why, or "Nothing flagged for review"; the tie-out and any residual; the scope
block including the months each period covered; where everything is; and one closing line noting
that anything labelled interpretation is interpretation rather than fact.
 
Plain, precise prose. The Voice section does not apply to the email.
 
## Step 9 - Offer to schedule the same job
 
Only **after** the result is delivered and the optional work is done or reported.
 
Ask once: **"Would you like to schedule this job to run automatically?"** Options **Yes** / **No**.
On **No**, say the workflow is finished and stop.
 
### 9a. The scheduling form
 
Same element rules as 1e. Header title `Schedule details`. Ask **only**:
 
- **Frequency** (required) - pills: `Daily`, `Weekly`, `Monthly`, `Quarterly`.
- **Time** (required) - pills `09:00`, `12:00`, `17:00`, plus `Other`.
- **Account** (required) - every account in `config.accounts` as pills, plus `Other`. **Always
  ask**, even when this run covered one - a scheduled job must state which account it runs
  against rather than inheriting whatever this run used.
- **Email the report?** (required) - `Yes` / `No`.
- **Send to** - the recipient used for this run and the `get_me` mailbox as pills, plus `Other`.
  Required only when email is `Yes`; say so, since the shell can't hide it.
- **Report storage** (required) - pills: `SharePoint`, `Local`.
**Don't ask for the source** - reuse this run's. **Don't ask for anything already in
`config.json`**. List the inherited values beneath the form so they're visible.
 
**Periods are never asked.** A scheduled run always compares the previous period with the one
before it, re-derived on each firing from the frequency - a monthly job does last month vs the
month before; a quarterly job does last closed quarter vs the one before. State that in the hint.
 
### 9b. Validate
 
Confirm frequency, time, account, email preference, a recipient when email is `Yes`, report
storage, and the inherited config. Resolve `Other` pairs first. If something's missing - including
the day of week for `Weekly` or day of month for `Monthly`, which the frequency pills don't
capture - ask only for that, in one question.
 
### 9c. Final confirmation - never schedule without it
 
Show a summary card, then ask. **Do not create the task yet.**
 
```
Review scheduled job
Frequency            Quarterly
Time                 10:00
Source               Share Drive · Finance/GL Exports
Account              63200 - Travel & Entertainment
Email report         Yes
Send to              Sachin.parmar@legalgraph.ai
Report storage       SharePoint · Sample
Inherited from config  threshold $1,000 or 10% · consolidated · FX average rate per month
Periods              last closed quarter vs the one before, re-derived each run
```
 
Then: **"Do you want to schedule this job?"**
 
1. **Confirm & schedule**
2. **Go back / edit** -> reopen the form pre-filled with everything collected, validate, show this
   card again. Never lose what was entered.
3. **Cancel** -> create nothing, and say so.
**Only create the task after an explicit "Confirm & schedule".**
 
### 9d. Create it, then confirm honestly
 
Write the job into `schedulerJobs[]`, create the task, store the returned id back into the job.
The task's prompt carries **only** the job id and the resolved config path.
 
**On success**, confirm in plain words what will happen and when. **On failure**, do not report it
as scheduled: say what failed, keep the configuration in `config.json` so nothing is re-entered,
and offer to retry.
 
### 9e. When a scheduled task fires
 
Re-derive everything from a fresh read of that `config.json`: the job, its accounts, and its
periods from the frequency against today's date. Run Steps 3-8 with the saved config as the
pre-approved plan - no plan card, no approval.
 
Its guaranteed outcome is the saved workbook plus the configured storage. The email is attempted
only when the job's preference is `Yes` **and** the environment permits an unattended send;
otherwise the run logs what would have gone out and why it didn't, and never claims a send that
didn't happen.
 
---
 
## Voice
 
Silence during a long step is worse than slow; a column of "Processing..." is worse than silence.
 
**Where narration goes - not optional.** Status lines are **visible response text**, written
immediately before the call they describe. Not in reasoning, not inside tool output, not gathered
into a closing recap.
 
One short line per step, under about a dozen words, never repeated within a run. Dry and specific
beats zany; no emoji, no exclamation marks. Real numbers the moment you have them.
 
- "Using your saved setup from back-office-agents/allneurons-flux."
- "Right - 63200, explaining Q2 against Q1. Let's find out."
- "Knocking on the connectors to see who's awake."
- "All six months are in the file. Good."
- "1,412 lines, 38 vendors, three currencies. Translating month by month."
- "Handing the arithmetic to pandas, where it belongs."
- "Reading the memos on the movers, so I can tell you why and not just how much."
- "Making the totals tie. Unglamorous, and the reason nobody questions this in the meeting."
- "That's your answer and your workbook. Filing the copies now."
**Where the voice stops - this matters more than the voice does.** Personality lives in the
waiting lines and never touches the substance. Be plain and careful when reporting a finding,
amount, interpretation or review flag; when explaining why something is flagged, uncertain or
ungrounded; when reporting a failure, a missing month, a validation gap, a total that won't tie,
a destination that couldn't be written, an email that couldn't be sent, a form field that didn't
come back, or a schedule that wasn't created; and when writing anything inside the workbook, any
card, the report page, or the email.
 
Never joke about someone's numbers. Someone may be reading this the morning a close is due.
 
---
 
## `config.json` schema
 
```json
{
  "schemaVersion": 8,
  "homeFolder": "/absolute/path/to/<connected folder>/allneurons-flux",
  "createdAt": "2026-08-27T10:00:00Z",
  "updatedAt": "2026-08-27T10:00:00Z",
  "defaults": {
    "dataSource": "netsuite | sharepoint | manual",
    "entityScope": "all",
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
    "notification": { "recipient": "someone@company.com" }
  },
  "accounts": [
    { "id": "acct_63200", "accountNumber": "63200", "accountName": "Travel & Entertainment" }
  ],
  "manualRunDefaults": {
    "periodA": { "label": "Q1 2026", "months": ["2026-01", "2026-02", "2026-03"] },
    "periodB": { "label": "Q2 2026", "months": ["2026-04", "2026-05", "2026-06"] }
  },
  "discoveryCache": {
    "refreshedAt": "2026-08-27T10:00:00Z",
    "mailbox": null,
    "accounts": [],
    "entities": [],
    "netsuiteSavedSearches": [],
    "sharepointFolders": []
  },
  "schedulerJobs": [
    {
      "id": "job_1",
      "name": "Quarterly T&E variance",
      "enabled": true,
      "frequency": "daily | weekly | monthly | quarterly",
      "time": "10:00",
      "dayOfWeek": null,
      "dayOfMonth": 1,
      "dataSource": "sharepoint",
      "accountIds": ["acct_63200"],
      "emailReport": true,
      "emailRecipient": "someone@company.com",
      "reportStorage": "sharepoint | local",
      "scheduledTaskId": null,
      "createdAt": "2026-09-12T10:00:00Z"
    }
  ]
}
```
 
`manualRunDefaults` stores each period as a **label plus its month list**, so a saved quarterly or
year-to-date setup reloads exactly as chosen. A single-month period is a one-element list. Older
files holding plain `"2026-05"` strings load as one-month periods.
 
`schedulerJobs[]` is written **only** through Step 9, after an explicit confirmation. A job stores
only what the scheduling form asked and inherits everything else at firing time.
`scheduledTaskId` is null until the task is actually created; a null id on an enabled job means
creation failed and the job is not live.
 
`homeFolder` is the absolute path of the directory this file lives in - written on creation,
checked first on later runs.
 
`absoluteThreshold` is a plain number, `percentThreshold` a decimal fraction (`0.35` for 35%) - a
custom value entered through `Other` is stored exactly like a suggested one.
 
**No report-page URLs** - each run publishes a new page. **No `sender`** - the connector sends as
the authenticated mailbox. `connectors.notification.recipient` records *who to send to*, nothing
more: **it is not permission to send** - the Step 6 plan is, per run.
 
`rollupDimension` and `reportingCurrency` are discovered fresh each run. `discoveryCache` is a
performance cache; entries older than about seven days are stale.
 
Older files (v3-v7) load: carry every field forward, add `homeFolder` from where the file was
found, convert plain period strings to `{label, months}`, drop removed keys, write back at the
current version, never prompt.
 
---
 
## Guardrails
 
Short pointers - the detail lives in the step named.
 
- **Variance only**, but two periods may each span several months. (Scope, Periods)
- **Direction is always explicit.** Period A baseline, Period B explained, `Δ = B − A`, shown with
  an arrow and in words. Reading it backwards inverts the whole report silently. (Periods)
- **Translate currency per month, then sum.** One rate across a quarter is wrong and fails
  silently. (Step 5)
- **Check every month of both periods is present.** A quarter missing a month passes a naive
  "both periods have data" check and understates by a third. (Step 4)
- **Never offer an unclosed period without saying it's partial.** (Periods)
- **Hand over the result before any optional work.** Findings as text, then `present_files` -
  upload, publish and email after. Never call the tail "asynchronous": it runs after, not in
  parallel. (Step 8)
- **One `allneurons-flux/` per user, found before anything is asked; say where it resolved.**
  (Step 0)
- **Use the elicitation shell and only its five collecting elements.** Never a bare
  `<input type="text">`, a `<select>`, or your own submit button. Applies to the scheduling form
  too. (1e)
- **Every non-exhaustive choice group ends with `Other`**; the two thresholds stay separate. (1e)
- **A missing field in the payload is a composition bug, not a user error.** (1f, 9b)
- **Infer before asking; never re-ask an answered question.** (1a, 1f)
- **The plan is a card; the approval is one line.** One approval covers the run including publish
  and send. (Step 6)
- **Scheduling is offered only after the result, and never created without an explicit
  confirmation.** A failed creation is never reported as scheduled. (Step 9)
- **Every destination visibly succeeds or visibly fails.** Never claim a file stored, an email
  sent, or a job scheduled unless it was. (Steps 8-9)
- **Synthetic data is stamped, not gated.** (Step 4)
- **Arithmetic in code, never in the conversation**; never print bytes, base64 or a whole ledger.
  (Performance)
- **Significance and review flag are different tests.** A zero-movement row is never a Flux
  finding and never carries a flag, at any threshold including `0`. (Step 5)
- **Ground every finding in real source text.** (Step 5)
- **Totals must tie** to a control total computed independently of the rollup. (Step 7)
- **Never silently overwrite** an output file, locally or on a drive. (Steps 7-8)
