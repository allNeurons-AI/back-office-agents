---
name: "allneurons-variance-analysis"
description: "Explains what changed in one or more financial accounts between exactly two periods and delivers a three-tab Excel workbook with the findings. Trigger whenever someone wants a period-over-period variance or flux explained - 'why did this account move', 'explain the variance between May and June', 'what's driving account 63200', 'run the monthly flux', 'variance report for these accounts' - from live NetSuite GL detail, a Share Drive/SharePoint export, or an uploaded spreadsheet. Asks which source first, then one tailored form with everything that source needs, confirms the whole run once at a single approval gate, does all numeric work in code rather than in the conversation, reports the findings before it builds the file, saves settings to allneurons-flux/config.json and every run's workbook to allneurons-flux/outputs/, emails a formatted summary, and can run itself on a schedule."
---

Explains what changed in one or more financial accounts/categories between exactly two periods and delivers a three-tab Excel workbook. Full instructions follow.

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

Five operating principles run through every step below, and they matter as much as the method:

- **Ask which source first, then ask only what that source needs - and check the form is whole
  before showing it.** See Step 1. Two forms: one question, then one tailored and verified form.
- **Confirm the whole run once, at one gate.** See Step 6. Every side effect - the local save, any
  drive copy, the email and its recipient - is named there and approved in a single answer. Never
  drip-feed separate permission questions through the run.
- **Say what you're doing, in visible text, as you do it.** See **Voice**. Status lines are part
  of the response, not something buried in reasoning or tool output.
- **Do the heavy lifting in code, in as few calls as possible.** See **Performance**. Every round
  trip is a wait the user sits through, and most runs waste half of them.
- **Give the answer before the file.** Findings are reported the moment they exist, while the
  workbook is still being built. Nobody should wait on an `.xlsx` to learn what moved.

---

## Architecture

```
allneurons-variance-analysis          <- this file: the engine/workflow
allneurons-flux/                      <- persistent config directory (created on first run)
  config.json                         <- single source of truth (schema below)
  outputs/                            <- final workbook for EVERY run lands here (manual and
                                          scheduled alike) - the unconditional local copy, on top
                                          of whatever additional save location config specifies
```

`allneurons-flux/` must live inside a **persistent, user-visible folder** - not a temporary
per-run scratch directory, since `config.json` has to survive across sessions and be readable by
scheduled jobs. If no folder is currently connected, request one from the user before creating
`allneurons-flux/` inside it.

**There are no UI files.** Both configuration forms render inline in the chat (Step 1) and
`config.json` is written by this skill with the `Write` tool, into `allneurons-flux/`. Nothing is
ever saved to disk by a web page, no browser tab is involved, no file or folder picker is ever
shown, and the user is never asked where to put anything or whether they saved it. Earlier
versions shipped `index.html` / `style.css` / `script.js` into `allneurons-flux/` and opened them
in Chrome; if those files are still there, **leave them alone** but never write, update or open
them.

---

## Performance - the call budget

A slow run is rarely slow because the analysis is hard. It is slow because of round trips that do
no work: tools loaded one at a time, speculative searches that find nothing, and a compute path
chopped into pieces. **A well-run analysis of one account is about seven tool calls end to end.**

**The shape of a fast run**

```
1  ToolSearch          - every tool the run could need, in ONE call
2  show_widget         - form 1 (which source)
3  one scoped search   - find the file, now that the folder is known
4  show_widget         - form 2 (everything else)
5  one read            - land the data in the sandbox
6  one script          - normalize, roll up, tie out, build the workbook, save it
7  present_files       - deliver
```

**1. Load every tool once, up front.**

Loading tools one at a time is the most common waste and the easiest to fix: each `ToolSearch` is
a full round trip that accomplishes nothing on its own. Make **one** call at the very start of
pre-flight requesting everything the run could plausibly need - the mailbox lookup, both drive
searches, the resource reader, the file uploader, the mail sender. It costs the same as one narrow
call, and it lands while the user is still reading form 1, so the time is free.

**2. Never move the ledger through the conversation.**

Land the raw data as a file in the sandbox and do every numeric operation there in Python/pandas:
parse amounts, group by the rollup dimension, compute Δ($) and Δ(%), translate currency,
reconcile, compute the control total, and write the workbook. Reading a few thousand ledger lines
into context costs more than the entire rest of the run, and the model adds nothing to a `groupby`.

What comes back into the conversation is only:

- the rollup's top movers (roughly the top 20 by `|Δ($)|`), with their amounts
- the memo/description text for those rows only
- the control total, the rollup total, and any residual
- row counts, distinct-counterparty counts, currencies seen, entities seen

The judgment - what drove a movement, whether the evidence supports it, whether a row deserves a
review flag - is the part that needs a model. Arithmetic isn't.

**The one unavoidable exception:** when the only route to a file is a connector that returns
content into the conversation (a SharePoint read, an attachment), that single read cannot be
avoided - the sandbox has no path to the source. Take it **once**, write the rows into a sandbox
file in the very next call, and never print or re-read them. Say so in a line of voice.

Parse every numeric with a real parser (`pd.to_numeric(..., errors="coerce")`) and count how many
values coerced to null - a nonzero count is a data-quality finding, not something to drop.

**3. Push every filter to the source.**

Accounts, both periods, and subsidiary scope belong in the query or the read, not in
post-processing. Never pull a whole report and narrow it locally. Request only the columns the
normalized shape needs (`period, account, amount, counterparty/vendor, memo, entity/segment,
currency`) - never `SELECT *`. On a large ledger this alone is frequently a 10x difference.

**4. Search once, scoped - never speculatively.**

Hunting for a file with guessed queries is the second big waste, and worse than it looks: on a
large, unstructured drive those searches return unrelated screenshots and meeting recordings, so
they cost round trips *and* teach you nothing. The fix is ordering: **the folder comes from the
user in form 2, and the search happens after that**, scoped as query plus `folderName`. One call.

Corollary: **do not go looking for the file during pre-flight.**

**5. Two-phase retrieval when the source can aggregate.**

- Phase 1: an **aggregate** query - totals by account × period × counterparty. Enough by itself to
  compute the whole variance and decide which rows cross the threshold.
- Phase 2: line-level detail **only for the counterparties that crossed**, for memo grounding and
  the GL Details tab.

State it in the plan: "GL Details will cover the movers in scope rather than every line." If the
user wants every line, honour it and say so - never silently.

**6. Ground only what you'll write up.** Memo text is read for threshold-crossing rows only,
largest first.

**7. One script for the whole compute path - and never print bulk data.**

Compute, build the workbook, and save it to `outputs/` in **a single script**. Splitting them buys
nothing: if it fails you fix it and rerun the whole thing anyway. The same script takes the
execution timestamp for the filename, so no separate call for the clock, and prints the rollup,
top movers with memos, control total, tie-out difference, parse-failure count and the check
results - everything needed to write the findings and the email.

Never run exploratory one-liners to inspect a file: one script prints shape, columns, head, null
counts and period range in a single pass. And **never print file bytes, base64, or a whole ledger
to stdout** - one echoed workbook can exhaust the output budget and force the step to be redone.

**8. Discover in one cheap pass, and abandon it cheaply.**

- **Before form 1**: connector liveness, the user's mailbox, and the default period pairs.
- **After form 1**: at most **one** call for the chosen source - the NetSuite saved-search list,
  or a single drive-folder search. Never both. If what comes back isn't obviously finance-shaped,
  **stop and let the field be typed.** A folder search returning meeting recordings is a miss, not
  a result, and a second guess won't fix it.
- Reuse `discoveryCache` when fresh; never re-discover what `config.json` answers.

Be honest that this trade can go the other way: on a large unstructured drive, folder discovery
often costs three calls and finds nothing while the user would have typed the path in seconds.

**9. Make the second run nearly free.** Once `config.json` exists, an interactive run should skip
pre-flight and both forms: one confirm card, one click, straight to retrieval. That removes four
to six calls from every later run - the single largest speed win available.

**10. Parallelize anything independent.** Fire independent lookups as one batch. For multi-account
runs beyond two accounts, give each account its own subagent and merge - but discover the rollup
dimension and reporting currency **once** before fanning out and pass them down as fixed
parameters, or two accounts silently roll up on different dimensions. Recompute the tie-out on the
merged whole. Splitting a *single* account's groupby across workers is pointless.

**11. Time the run, and answer before artifact.** If a run passes a couple of minutes, say which
step owned it. And report the findings as soon as they exist, then say the workbook is building.

---

## Step 0 - Locate or create `allneurons-flux/`

1. Check whether a folder is connected. If not, ask the user to connect one - explain briefly that
   this is where the skill keeps its configuration so it doesn't re-ask every run.
2. Look for `allneurons-flux/` inside it. If the connected folder is itself named
   `allneurons-flux`, treat it as that directory directly - don't nest another inside it.
   - **Missing** -> create it plus an empty `outputs/` subfolder. Continue to Step 1 knowing
     `config.json` does not exist yet.
   - **Present** -> use it as-is (create `outputs/` if missing), continue to Step 1.

Do this silently, folded into work you're already doing. It needs no dedicated call.

## Step 1 - Configuration: two forms, then write the file

Configuration is collected through **two forms rendered inline in the chat** via
`mcp__visualize__show_widget` (call `mcp__visualize__read_me` with `modules: ["elicitation"]`
once per session to load the form contract):

1. **Form 1 asks one thing: which data source.**
2. **Form 2 is composed for that source** and asks everything else the run needs.

Then this skill writes `allneurons-flux/config.json` itself with the `Write` tool.

Why two: the elicitation shell cannot show or hide fields based on an answer. A single combined
form shows NetSuite fields, Share Drive fields and an upload dropzone to everyone, leaving a Share
Drive user reading two sections that don't apply.

Rules governing both forms:

- **Form 2 is complete, and verified complete before it renders** (Step 1e-check). No third form,
  no follow-up round of questions.
- **Both forms are mandatory.** No Skip button - omit `.elicit-skip`, leaving Continue only.
- **"Required" is advisory, so verify.** The shell cannot force a selection: an unanswered pill
  group comes back absent and the marker changes nothing mechanically. Put the answers you most
  need early; Step 1f is the real enforcement.
- **Never ask where to save `config.json`**, never show a picker, never ask whether they saved it.

Header title on both forms is `Variance details`.

### 1a. Pre-flight - one tool call, one probe batch

**First, load every tool the run could need in a single `ToolSearch`**: the mailbox lookup, both
drive searches, the resource reader, the file uploader, the mail sender.

Then narrate one visible line and probe in a single parallel batch - only these three:

- **Connector status** for NetSuite, the drive connector, and the email connector. Probe only.
- **The user's own mailbox** (`get_me` or equivalent). This is the sender identity and the default
  recipient. Never ask for a sender - see the note below.
- **Default periods** - Period B = last complete month, Period A = the month before, plus the two
  earlier pairs.

**Do not search for the data file here.** The folder is a form 2 answer.

**Why there is no sender field:** the email goes out *through* the connector, so it is sent as the
authenticated mailbox. The From address is fixed to the signed-in user and cannot be set to
anything else - a different From needs a shared mailbox with send-as permission in the tenant,
which is outside this skill. So the form asks only *to whom*.

Put connector status in a status line above form 1 - "NetSuite connected · Microsoft 365 connected
· Share Drive not connected". If the mailbox lookup failed, that does **not** remove the recipient
question from form 2; it just means no prefilled pill and a text field instead.

### 1b. Config already exists

- **Scheduled-job run** -> load `config.json` silently. No forms, no card. Go to Step 2.
- **Interactive run** -> do not re-ask "would you like to update it?" and do not re-render either
  form. Show a compact confirm card (a small `show_widget` card, not a form): accounts, the two
  periods computed for today, data source, threshold, where output goes, the schedule if any, and
  **the email recipient**. Two `sendPrompt` actions:
  - "Run it" -> this card **is** the Step 6 gate for this run: it names every side effect, so
    proceed through to delivery and the email without asking again.
  - "Change something" -> form 1 pre-selected to the saved source, then form 2 pre-filled from
    `config.json`. Preserve `createdAt`, `schedulerJobs[].scheduledTaskId`, `discoveryCache`, and
    any untouched field.

This path is the biggest speed win in the skill. A run needing no changes costs one click.

### 1c. Form 1 - which source

One group, three **cards** (icon + title + subtitle), nothing else. Each explains *when to choose
it*, because this is the decision the user is least equipped to make:

- `netsuite` - "NetSuite (live)" / "Pull GL line detail straight from NetSuite. **Choose this
  when** your books are closed in NetSuite, you want the numbers as the system holds them today,
  and you don't want to depend on someone having published an export. It reads
  transactionaccountingline detail, so amounts are functional-currency source of truth, and it can
  see which subsidiaries actually exist. Best for a recurring monthly close. Needs the NetSuite
  connector live."
- `sharepoint` - "Share Drive / SharePoint" / "Read a GL or transaction export already sitting in
  a folder. **Choose this when** Finance publishes the export you'd otherwise open by hand."
- `manual` - "Upload a file" / "**Choose this for** a one-off look at a spreadsheet you have right
  now. No connector needed."

Mark any card pre-flight found *not* live.

### 1d. One discovery call - after form 1, before form 2

**At most one call:**

- **NetSuite** -> saved searches / reports, plus chart of accounts and subsidiary list if the same
  call can carry them. Don't touch the drive.
- **Share Drive** -> one folder search for finance/GL/export-shaped names. If the results are
  unrelated files, **stop** - form 2 asks for the folder as a text field. Don't touch NetSuite.
- **Upload** -> nothing to discover. If a file is already attached, read its shape in the sandbox
  so form 2's account and period options come from the file itself.

Write anything worth keeping into `discoveryCache`.

### 1e. Form 2 - everything else, tailored to the source

Declarative HTML with `data-*` attributes, **no `<script>`, no `onclick`, no buttons of your
own**, no Skip. Phrase every label as a question. Substitute live values from 1d.

**The source-specific group comes first**, then the common groups. Only one source-specific group
is ever rendered.

**NetSuite.** "Which report should I pull from?" Cards: `GL Line Detail` (default) plus each
discovered saved search, plus `Other`. Then optional: "Anything I should know about the accounting
book?"

**Share Drive / SharePoint.** "Which folder should I search for the GL export?" (required) - pills
of discovered folders plus `Other` revealing a text field, placeholder `Finance/GL Exports`. Then
optional: "Any extra keywords that would help me find the right file?"

**Upload.** "Give me the file" (required) - dropzone plus textarea fallback. Skip entirely if a
suitable file is already attached; say so rather than asking twice.

Then, for every source:

**Accounts** (required). "Which accounts should I compare?" A **multi-select**
(`data-multi="true"`) of discovered accounts labelled `<number> - <name>` plus `Other`; or, if
nothing was discovered, a required text field: "give me the GL number and name, e.g.
`63200 - Travel & entertainment`. Several can be comma-separated."

**Entity scope.** "Which entity should I look at?" Pills: `Consolidated (all entities)` (default),
discovered entities, `Other`.

**Periods** (required). "Which two months should I compare? Period A is the baseline, Period B is
the month you're explaining." Pills from the computed pairs, `(last closed month)` on the default,
then `Other`.

**Threshold.** "How big does a movement have to be before I write it up?" Two pill groups:
absolute (`$1,000` default, `$5,000`, `$10,000`, `Other`) and percent (`20%` default, `10%`,
`50%`, `Other`). Hint: "Crossing either one gets a movement listed. It does not by itself flag the
row for review - that's for missing or ambiguous evidence, decided when the analysis runs. A
movement of exactly zero is never listed, whatever this is set to."

**Notification recipient** (required - easy to forget, so never omit). Question: **"Who should get
the finished workbook? I'll send it from your own mailbox and show you the email before it
goes."** Pills: the address from 1a (labelled "you"), plus `Other`. If the mailbox lookup failed,
a plain required text field, placeholder `you@company.com` - never dropped for lack of a prefill.
**One address only**, and no sender field (see 1a).

Saying the send is confirmed *in the question itself* matters: otherwise the later confirmation
reads as re-asking something already answered, which is exactly the friction to avoid.

**Output location** (required). Preview tiles: `allneurons_flux_folder` ("Just my folder" / "Stays
in allneurons-flux/outputs"), `claude_working_folder` ("Into this chat"), `onedrive_sharepoint`
("OneDrive / SharePoint" / "Also copied to a folder you name"). Hint: "A copy always lands in
allneurons-flux/outputs, whichever you pick." Then a text field: "**If you picked OneDrive /
SharePoint** - which folder?"

**Schedule** (required - an explicit "no" counts, and the group most often left blank). "Should
this run on a schedule, or just manually for now?" Pills: `Just manually` (default), `Every
month`, `Every week`, `Every day`, plus a time group. Hint: "A scheduled run always compares the
previous month with the month before it, re-derived each firing - not the fixed months above."

### 1e-check. Verify the form before rendering it

**Do not render form 2 until you have checked it against this list.** Composing a multi-group form
is where a question quietly goes missing - and the ones that vanish feel like settings rather than
analysis, the recipient question most of all.

Confirm each is present with a `data-name` the payload will carry back:

1. the one source-specific group matching form 1 - and **only** that one
2. accounts
3. entity scope
4. periods
5. absolute threshold and percent threshold
6. **notification recipient**
7. output location tiles, plus the OneDrive/SharePoint folder field
8. schedule, plus its time group

If any is missing, fix the composition and check again. **Never render an incomplete form and plan
to ask for the rest later.** If length is a concern, cut optional fields - never a required one.

### 1f. Validate, then write

Check the payload against the required set. Expect gaps - the shell can't enforce required. Ask
**only** for what's missing, in one `AskUserQuestion`, combining related gaps into a single
question (frequency and time together, for instance). Don't re-render either form.

Never invent a value. For an analysis input - accounts, periods, folders - stop and ask. For a
side-effectful setting like the schedule, if the answer is ambiguous take the **reversible** path
(create no scheduled task), say plainly that's what you did, and offer to change it.

Then write `allneurons-flux/config.json` (`schemaVersion: 4`) with `Write` and confirm in one line
what was saved. Reading a v3 file: carry every field forward, drop
`connectors.notification.sender` and `accounts[].defaultEntityScope`, no prompt.

If a schedule was set, reconcile it against real scheduled tasks and say when it next runs.

## Step 2 - Resolve run context, then say what you're about to do

- **Interactive run**: if the request named accounts and periods differing from
  `manualRunDefaults`, use what they said. Otherwise use `manualRunDefaults` and `accounts[]`.
- **Scheduled run**: the prompt names a `schedulerJobs[].id`. If it's gone, the task is stale.

Then post **one visible line** naming the run: "Right - account 63200, July vs June 2026,
consolidated, from the Share Drive export. Going to find it."

## Step 3 - Connector / data-source flow

```
detect(connector):
  1. Is a working tool for this connector present in the session?
  2. If found -> confirm live with a trivial call.
  3. If not, or the call fails:
       - Say plainly which connector needs connecting.
       - search_mcp_registry with connector-specific keywords.
       - suggest_connectors to surface the Connect button.
       - Wait for the user to authenticate - never proceed, never work around it.
       - Recheck. If live, continue automatically.
       - If still unavailable, say so and offer a fallback rather than looping.
```

Step 1a already probed these - reuse what it found; only run the connect flow when the connector
is about to be used.

**NetSuite**: pull from the configured report - **GL Line Detail** by default, or the named saved
search. Put the account list, both periods and subsidiary scope **into the query**, select only
the seven normalized columns, prefer aggregate-then-drill. Write results straight to a sandbox
file. Verify which subsidiaries exist. Probe schema in the same pass. Never hardcode a report ID
beyond config.

**Share Drive / SharePoint**: **one scoped search** - query plus `folderName` set to the folder
from form 2, with `hint` keywords and the account number as extra terms. The connector returns
content into the conversation and the sandbox can't reach the drive, so take that read **once**
and write the rows into a sandbox file immediately. Say in a line of voice that this read is
unavoidable.

**Upload / manual**: read the file in the sandbox, auto-map columns, confirm the mapping, validate.

**Notification email**: `detect("outlook")` at delivery time.

**Output save location** (`onedrive_sharepoint`): `detect("onedrive")` / `detect("sharepoint")`.

A scheduler job may override the source via `dataSource` / `sourceOverride`, and its output via
`output`.

**Failure handling**: report errors plainly, offer retry or fallback, never silently retry more
than once, never bypass with a direct API call. A scheduled run cannot pause for authentication -
if the connector isn't live, fail cleanly and stop.

## Step 4 - Retrieve, normalize, validate - and surface what you found immediately

Pull the **full scope in scope** - filtered to the accounts, periods and entities being analysed,
never sampled within that scope - normalize every row to `{period, account, amount,
counterparty/vendor, memo, entity/segment, currency}`, and check sufficiency. Both periods must
have data, and a memo field must be present.

**Report the shape the instant the data lands** - one visible line: row count, distinct
counterparties, currencies, entities, and the period range actually present.

**A mismatch or blocker is reported the instant it's found, in visible text, with the choices.**
Never work past it, mention it late, or bury it in a tool result:

- the file covers different periods than requested
- the data is labelled sample/test/synthetic, or has a "read me" describing seeded scenarios
- an account in scope has no rows
- a required column can't be mapped, or many amounts failed numeric parsing
- both periods aren't present

**A wrong-periods or missing-data mismatch stops the run and asks.** For a *synthetic-data* label
where nothing else is wrong, report it prominently and continue, but stamp every output as
synthetic - the chat summary, all three tabs, and the email subject and body. Never let test
output be mistakable for a real close. On a scheduled run, fail cleanly with the reason recorded.

**Discovered live, never asked in a form:**

- **Rollup dimension** - vendor/counterparty if present and populated, else entity, then cost
  center. Where the counterparty field is null but the memo names one, recover it from the memo
  and label it memo-derived. State the dimension in the plan.
- **Reporting currency** - the single functional currency if there's one; otherwise the currency
  most in-scope activity is denominated in, translated via the source's own FX mechanism, falling
  back to USD only if no dominant currency exists. State it.
- Which entities exist, and whether the account moved at all.

On a multi-account parallel run, discover both **once** and pass them down.

## Step 5 - Variance methodology

Computed in code, not by hand or by eye.

- Exactly two periods, A and B - never more.
- Roll up by the dimension from Step 4.
- Per row: `Δ($) = B − A`; `Δ(%) = Δ / |A|`, reported "n/m" when A is zero.
- Multiple accounts each get their own rollup; beyond two, run them in parallel.
- Multi-currency: translate using the source's FX mechanism (average rate for P&L accounts unless
  told otherwise), keep original amounts visible, reconcile any residual.

### Significance threshold vs. review flag - these are two different things

- **Significance (`absoluteThreshold` / `percentThreshold`)** decides which rows are material
  enough to appear in the Flux tab. A row crosses if `|Δ($)| > absoluteThreshold` **or**
  `|Δ(%)| > percentThreshold` (strictly greater than). A row with **zero net movement** is never
  significant and never a flux finding, **whatever the threshold** - `0` means "surface every
  nonzero movement, however small", not "treat no-movement as a finding". Zero-movement rows still
  contribute to the Summary tie-out; they get no Flux row.
- **Review flag (Y/N)**, set independently for each row *in* the Flux tab, marks evidentiary or
  data-integrity concern - not dollar size. **Y** only when at least one holds:
  - no supporting memo/document text could be found to ground the movement
  - the memo is ambiguous, generic, or contradicts the amount or direction
  - a likely data-quality issue (currency/mapping mismatch, duplicate-looking entry, unexpected
    sign, wrong-entity posting, or a value that failed numeric parsing)
  - a brand-new counterparty appears in B with zero prior activity, when `flagNewCounterparty`
  - entity-level offsetting at consolidated scope, when `flagEntityLevelOffsetting`

  A row can be large, clearly above threshold, and still be **N** if its driver is well-documented
  and unambiguous. **Never set Y solely because a row crossed the threshold.**
- At consolidated scope, flag counterparties whose consolidated net is small but whose entity legs
  are large - for review, never asserted as error. Note how the flag would behave at a higher
  threshold, since offsetting checks are threshold-sensitive.
- Ground every flagged item in real memo text, reading evidence only for threshold-crossing rows.
  "No clear driver found in the data" is a valid, honest finding. Keep source data, calculation,
  finding, interpretation and recommendation visibly distinct.

## Step 6 - One gate: the plan and every side effect, approved together

This is the **only** place the run asks permission for anything. Present a short plan via
`AskUserQuestion` covering both what will be analysed and what will happen afterwards:

**What I'll analyse** - accounts, the two periods, source and what was retrieved, rollup dimension
and reporting currency, entity handling, thresholds in effect, whether GL Details covers movers or
every line.

**What I'll do with it** - and name each side effect explicitly:

- save the workbook to `allneurons-flux/outputs/` (always)
- deliver it into this chat (interactive runs)
- copy it to `<the configured drive folder>`, if output location is `onedrive_sharepoint`
- **email the summary to `<recipient>` from your own mailbox**

Then: "Approving this covers all of it - I won't ask again at the end."

**A single clear approval authorises the whole run, including the send.** That is the point of the
gate: the user is told in chat, before anything happens, exactly which message will go to which
address from which mailbox, and agrees to it once. Never follow an approved gate with a second
permission question at delivery - re-asking something already answered is the friction this design
removes.

Equally, the gate is the *only* thing that authorises a send. A recipient stored in `config.json`
is a preference, not permission; no config field can pre-authorise anything, and approval does not
carry across runs. If the user edits the plan to drop the email, drop it.

- **Interactive run**: gate is mandatory. Iterate on edits. One screen - it's a gate, not a
  report. On the fast path (1b), the confirm card *is* this gate, provided it named the recipient.
- **Scheduled run**: the saved config is the pre-approved plan for the analysis and the saves. It
  is **not** permission to send mail - see Step 8.

## Step 7 - One script: compute, report, build, save

**A single script** does all of this and prints what's needed:

- roll up per Step 5; compute deltas and percentages; translate currency with reconciliation
- compute the control total **independently of the rollup sum**, so the tie-out is a real check
- take the execution timestamp for the filename - no separate call for the clock
- build the three-tab workbook and save it to `allneurons-flux/outputs/`
- print the rollup, top movers with memo text, control total, tie-out difference, parse-failure
  count, and the offsetting / new-counterparty check results

Then read the printed memo text for threshold-crossing rows and form the findings and flags.

**Report before mentioning the file.** Post the answer as soon as the script returns: net variance
in the reporting currency, movements above threshold, count flagged; the top movers with Δ($),
Δ(%) and the memo grounding each; anything flagged with its reason; what was correctly excluded -
below-threshold rows, and zero-movement rows named explicitly so the false-positive guard is
visible; and honest empty states where they apply.

**The three tabs**, built by that same script:

1. **Summary** - the rollup plus an `=SUM()` tie-out to the independent control total, difference
   shown as a formula. Zero-movement rows may appear here for tie-out purposes.
2. **Flux** - every evidenced movement that crossed the threshold: finding, interpretation
   (labelled as interpretation, not fact), **review flag (Y/N)**, and any integrity flags folded
   into this tab. If a check ran and found nothing, say so here. Zero-movement rows are not listed
   at all, at any threshold.
3. **GL Details** - underlying line items with full traceability, including the FX rate and a
   per-row translation formula. Say which scope the tab covers.

Formulas, not hardcoded numbers; recalc with zero formula errors. If the source was synthetic,
stamp that on every tab.

**Filename**: `<Account-or-scope>_Variance_<PeriodA>_vs_<PeriodB>_<YYYY-MM-DD>_<HH-MM>.xlsx`.

**Verify before delivering**: the rolled-up total ties to the independent control total; any
deliberate exclusion or residual is named next to the number; no zero-movement row carries a Y
flag; no row's flag is Y for magnitude alone without an evidentiary reason logged beside it.

## Step 8 - Deliver and send

**The local save already happened inside the Step 7 script.** Never overwrite a same-named file;
on collision, say so and keep both.

**Chat delivery (interactive runs):** `mcp__cowork__present_files`, unconditionally.

**Summary card (interactive runs):** three metric cards (net variance, movements above threshold,
count flagged), the top five movers with Δ($), Δ(%) and grounding memo, flagged rows marked with a
few words of reason, and a `sendPrompt` follow-up per mover. Round every number on screen; keep
prose outside the card. If the card would delay the answer, the Step 7 text report stands alone.

**Additional save per `defaults.output.saveLocation`:**

- `allneurons_flux_folder` -> nothing further.
- `claude_working_folder` -> satisfied by the chat delivery.
- `onedrive_sharepoint` -> upload to `output.oneDriveSharepointFolder`:
  - the upload needs the workbook base64-encoded **inside the tool call**. Encode and upload in
    **one dedicated call that prints nothing else** - never echo the base64 to stdout first.
  - compute the byte count in the run that produced the bytes and pass it as `expectedBytes`.
  - `conflictBehavior: "fail"` so nothing is silently overwritten. On collision, surface it
    (manual) or retry with a timestamped name (scheduled).
  - if the call is cut short, retry the upload **alone**.

**Send the email - no second question, because Step 6 already covered it.**

Send it the moment the file exists and the saves are done. Do not re-ask; do not turn delivery
into another approval. If the gate was approved, this is simply the run finishing.

Send as the authenticated mailbox to `connectors.notification.recipient`, `bodyType: "html"`.
Report the outcome in one line - sent, or not sent and why. **Never state or imply it was sent
unless the send succeeded.** If the connector isn't live or the send fails, say so plainly naming
the recipient and the reason; the file is already saved, so the run still succeeded.

The only case that still needs a question is a run where **no gate was approved** - the user
skipped it, or a scheduled run has nobody to ask. Then don't send; say the file is saved and offer
the send in one line.

### The email template

One screen, skimmable in twenty seconds, numbers before prose. HTML, using only tags the
connector's allowlist keeps: `h3`, `p`, `strong`, `em`, `br`, `ul`/`li`, `table`/`tr`/`th`/`td`,
`a`. No images, no inline styles beyond what survives sanitising, no colour as the only signal.

**Subject** - scope first so it sorts and searches well:

```
Variance: 63200 Travel & Entertainment - Jun 2026 vs May 2026
```

Multiple accounts: `Variance: 3 accounts - Jun 2026 vs May 2026`. Entity-scoped: append
`(Widget UK Ltd)`. Synthetic source: append ` [SYNTHETIC TEST DATA]`.

**Body**, in this order:

1. **Synthetic warning first, if applicable.** A single bold paragraph before anything else:
   "This run used synthetic test data - the source file's own Read Me sheet identifies it as
   dummy data. Not a real close. Every tab in the workbook is stamped accordingly." Never bury
   this below the numbers.
2. **The headline**, one sentence with the direction spelled out: "Account 63200 Travel &
   Entertainment, consolidated, moved from $8,184.94 in May 2026 to $30,400.13 in Jun 2026 -
   an increase of $22,215.19 (+271%)."
3. **The movers table** - the rows that crossed the threshold, largest first. Four columns:
   Counterparty, Δ, Δ%, Review. Put the driver in a short line under the table per flagged row
   rather than crowding the cells. Never more than five rows; say "plus N smaller movements above
   threshold" if there are more.
4. **What's flagged and why**, as a short list - one line each, naming the reason (missing
   evidence, ambiguous memo, new counterparty, entity-level offsetting, parse failure). If nothing
   is flagged, say "Nothing flagged for review" rather than omitting the section.
5. **Tie-out** - "Rollup ties to an independently computed control total. Difference: $0.00." Name
   any deliberate residual here.
6. **Scope**, as a compact list so the reader can judge the numbers: account(s), the two periods,
   entity scope, reporting currency and how it was translated, thresholds in effect, source file
   or report, and what the GL Details tab covers.
7. **Where the file is** - the local `allneurons-flux/outputs/` path, plus the drive link if that
   save happened.
8. **One closing line**: generated by allneurons-variance-analysis, and that anything labelled
   interpretation in the workbook is interpretation rather than fact.

Plain, precise prose throughout. The **Voice** section does not apply to the email - no jokes, no
personality, nothing that could read as more confident than the evidence supports. Someone may
forward this to their controller.

If the run took more than a couple of minutes, close the chat response by naming the step that
owned the time.

---

## Voice - how this skill talks while it works

Waiting is part of the job: connectors probed, ledgers pulled, memos read, formulas checked.
Silence is worse than slow, and a column of "Processing..." is worse than silence.

**Where the narration goes - not optional**

Status lines are **visible response text**, written immediately before the tool call they
describe. Not in reasoning, not inside tool output, not gathered into a recap. If the user can't
read it as it happens, it isn't narration. When several calls fire together, precede the batch
with one line naming what it's for.

**The shape of it**

- One short line per step. Under about a dozen words. Never a paragraph.
- Say what you're doing and, where it isn't obvious, why it matters.
- Never repeat a line within a run.
- Dry and specific beats zany. The humour comes from being honest about the work, not jokes pasted
  on top. No emoji, no exclamation marks, no "let's dive in".
- Real numbers the moment you have them - "1,412 lines, 38 vendors" beats "retrieving data".

**Lines that work** - register, not a script:

- Opening: "Right - 63200, July vs June, consolidated. Let's find out."
- Pre-flight: "Knocking on the connectors to see who's awake."
- After form 1: "Share Drive it is."
- Retrieval: "Asking the source for exactly what's in scope. No dragging the whole ledger over."
- Shape: "1,412 lines, 38 vendors, one currency. Workable."
- Computation: "Handing the arithmetic to pandas, where it belongs."
- Grounding: "Reading the memos on the movers, so I can tell you why and not just how much."
- Tie-out: "Making the totals tie. Unglamorous, and the reason nobody questions this in the
  meeting."
- Delivery: "You've got the answer above. File's saved, note's away."

**Where the voice stops - this matters more than the voice does**

Personality lives in the waiting lines and never touches the substance. Be plain and careful when:

- reporting a finding, amount, interpretation or review flag
- explaining why something is flagged, uncertain or ungrounded
- reporting a failure, missing connector, validation gap, data mismatch, a total that won't tie,
  or an email that couldn't be sent
- writing anything inside the workbook, the card's data, or the email

Never joke about someone's numbers, and never let a light tone imply more confidence than the
evidence supports. A missing driver is "no clear driver found in the data" - not a punchline.
Someone may be reading this the morning a close is due.

---

## Scheduler - reconciling jobs with actual scheduled tasks

```
for each job in config.json.schedulerJobs:
  if job.enabled and job.scheduledTaskId is null:
      create_scheduled_task(
        cron/fireAt from job.frequency/time/dayOfWeek/dayOfMonth,
        prompt: "Run allneurons-variance-analysis, scheduler job id <job.id>, "
                "from allneurons-flux/config.json"
      )
      -> store the returned id into job.scheduledTaskId, save config.json again
  if job.enabled and job.scheduledTaskId exists and the schedule changed:
      update_scheduled_task(job.scheduledTaskId, new cron/time)
  if not job.enabled and job.scheduledTaskId exists:
      delete_scheduled_task(job.scheduledTaskId); clear scheduledTaskId
for each previously-known scheduledTaskId no longer in schedulerJobs:
      delete_scheduled_task(that id)
```

The task's prompt carries only the job id and the config path - never accounts, dates, thresholds
or output locations. That's what makes a config edit take effect on the next firing without
touching the task; only a frequency/time change needs an update.

Never create a task on an ambiguous answer (Step 1f). After reconciling, say when it next runs
("next run: Thursday 1 October, 09:00").

**When a task fires**, re-derive everything from a fresh read of `config.json`: resolve the job,
its accounts, and its `periodPattern` against today's date, then run Steps 3-8 auto-approved for
the analysis and the saves. Its guaranteed outcome is the saved workbook. The email is attempted
only if the environment permits an unattended send; otherwise the job logs what would have gone
out, to whom, and why it didn't - and never claims a send that didn't happen. If the user wants
unattended email, say plainly it needs standing permission the run can't grant itself.

---

## `config.json` schema

```json
{
  "schemaVersion": 4,
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
  "manualRunDefaults": { "periodA": "2026-05", "periodB": "2026-06" },
  "discoveryCache": {
    "refreshedAt": "2026-08-27T10:00:00Z",
    "mailbox": null,
    "accounts": [],
    "entities": [],
    "netsuiteSavedSearches": [],
    "sharepointFolders": []
  },
  "schedulerJobs": []
}
```

Only the chosen source's block is meaningfully populated - Share Drive fills
`connectors.sharepoint` and leaves `connectors.netsuite` at defaults, and vice versa. Never ask
for a field belonging to a source the user didn't pick.

`connectors.notification.recipient` is **required and must always be collected** - the field most
likely to be dropped when composing form 2, which is largely why 1e-check exists. It records *who
to send to*, and nothing more: **it is not permission to send.** Step 6's gate is what authorises
that, per run. There is **no `sender`** - the email goes out through the connector as the
authenticated mailbox, so the From address is fixed to the signed-in user and cannot be set here.

`rollupDimension` and `reportingCurrency` are deliberately **not** stored - discovered fresh from
the data every run (Step 4).

`discoveryCache` is a performance cache, never a source of truth. Treat entries older than about
seven days as stale, re-verify before relying on one, never let a cached value override the live
source.

Accounts carry no `defaultEntityScope`; entity scope lives at `defaults.entityScope` for manual
runs and `schedulerJobs[].entityScope` for scheduled ones.

`defaults.output.saveLocation` defaults to `allneurons_flux_folder`; with `onedrive_sharepoint`,
`oneDriveSharepointFolder` is required too. A job's `output` offers only `allneurons_flux_folder`
or `onedrive_sharepoint`; unset, it inherits `defaults.output`, treating an inherited
`claude_working_folder` as `allneurons_flux_folder`.

**Reading a `schemaVersion: 3` file:** carry every field forward, ignore
`connectors.notification.sender` and `accounts[].defaultEntityScope` (promoting the latter to
`defaults.entityScope` if it wasn't `all`), and write back as v4 next save. Never prompt.

No credentials or tokens are ever stored here - only preferences and cached lookups.

---

## Guardrails

- **Variance only.** Redirect trend/anomaly/reconciliation/forecasting requests.
- **One gate, one approval.** Step 6 names every side effect - local save, drive copy, and the
  email with its recipient - and a single approval covers them all. **Never ask a second
  permission question at delivery.** Re-asking something already answered is the friction this
  design exists to remove.
- **The gate is per run, and nothing else substitutes for it.** A recipient in `config.json` is a
  preference, not permission; approval doesn't carry across runs; a scheduled run's saved config
  authorises the analysis and the saves but never a send.
- **Never state or imply an email was sent unless it was.** A failed, skipped or unapproved send
  gets its own visible line naming the recipient and the reason.
- **The email has a fixed shape** (Step 8): synthetic warning first if applicable, headline with
  direction, movers table, what's flagged and why, tie-out, scope, file location, one closing
  line. Plain prose - the Voice section does not apply to it.
- **No sender field, ever.** The connector sends as the authenticated mailbox; the From address is
  fixed to the signed-in user.
- **Seven calls is the budget.** One `ToolSearch` up front; no speculative searching; one script
  for compute-build-save; no separate call for the clock.
- **Never print file bytes, base64, or a whole ledger to stdout.** Upload payloads go into their
  own dedicated call with nothing else printed, with `expectedBytes` and
  `conflictBehavior: "fail"`; on truncation, retry that call alone.
- **Search once, scoped, after the folder is known.** Pre-flight does not hunt for the data file.
  One discovery call per source; a search returning unrelated files is a miss - hand off to a text
  field rather than guessing again.
- **The arithmetic happens in code, never in the conversation.** Only top movers, their memo text,
  control totals and counts come back into context. The one exception is a connector-only file
  read - take it once, land it in a file, never re-print it.
- **Two forms: source first, then everything for that source.** A Share Drive user must never see
  a NetSuite report question or an upload dropzone.
- **Check form 2 against the 1e-check list before rendering**, and remember "required" is advisory
  - Step 1f validation is the real enforcement.
- **The recipient question is never omitted**, and its wording says the email will be shown before
  it goes, so the gate reads as a promise kept rather than a repeated question.
- **Answer before artifact.** Findings are reported the moment they exist.
- **Report a data mismatch immediately.** Wrong periods, an account with no rows, unmappable
  columns or mass parse failures stop the run and ask. Synthetic labelling, where nothing else is
  wrong, is reported prominently and stamped on every output - chat, all three tabs, and the email
  subject and body - rather than stopping a test.
- **Never invent a value.** Analysis inputs: stop and ask. Side-effectful settings: take the
  reversible path, say so, offer to change it.
- **Narrate in visible text, as it happens** - before the call, not in reasoning or a closing
  recap. Narrate with personality; report findings, flags and failures plainly.
- **Assume nothing not in config.** Subsidiaries, currencies, rollup dimension, report
  availability and folder contents are verified at runtime.
- **Parallelize independent work, and pin what must be shared** - dimension and currency
  discovered once, tie-out recomputed on the merged whole.
- **Own the connector setup** - detect, explain, surface the link, wait, recheck, continue.
- **`config.json` is the only source of truth for the scheduler and output location.**
- **Never silently overwrite** a same-named output file, locally or on a drive.
- **Significance threshold and review flag are not the same test.** Crossing the threshold only
  decides whether a row appears in the Flux tab; it never by itself sets Y. A row with zero net
  movement is never a Flux finding and never carries a flag, at any threshold including `0`. Y is
  for missing or ambiguous evidence, a suspected data-quality issue, a brand-new counterparty, or
  entity-level offsetting - never magnitude alone.
- **Ground every finding in real source text**; "no clear driver in the data" is a valid answer
  and belongs with Review flag = Y.
- **Totals must tie** - reconcile the rollup to a control total computed independently of it. A
  tie-out that restates the same sum is not a check.
- **Local save to `allneurons-flux/outputs/` always happens, for every run.**
