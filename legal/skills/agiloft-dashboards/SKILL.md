---
name: "agiloft-dashboards"
description: 'Answer contract questions in plain language and keep a live four-tab contract dashboard beside the chat, built from Agiloft or from other sources: SharePoint Excel/CSV trackers, SharePoint Lists, Word/PDF contract documents in a SharePoint library, or any connected system or attached file. Use this skill whenever the user asks about contracts, renewals, expirations, approvals, cycle times, vendors, counterparties or contract owners, for example "how many contracts are in flight", "what expires soon", "where is my request", "what''s slowing contracts down", "show me the reporting dashboard", "build a dashboard from this SharePoint folder", "what did we sign last quarter", "does ABC have an NDA with us". Read-only: never writes to any source. Not for drafting, editing or creating contracts, or for analytics that are not about contracts.'
---

# Contract dashboards (Agiloft, SharePoint and other sources)

Version: 2.0   Owner: Rajan   Updated: 2026-10-15   History: see CHANGELOG.md

## 1. Purpose and scope

**Outcome:** one plain-language answer, and when useful one four-tab dashboard, built from a single named source and shown to the person with its source, account and mapped columns. The unit of value is one answer or dashboard that passed QA.

**Two surfaces, two jobs.** The chat carries a short, concrete, reasoned answer that says what it was counted from. The artifact carries the dashboard. Never put dashboard content into the chat as prose; the split is the design.

**Sources.** Agiloft (`references/source-agiloft.md`), SharePoint or OneDrive spreadsheets, lists and documents of any format (`references/source-sharepoint.md`), any other connected system or an attached file (`references/source-generic.md`). One source per dashboard, so every figure on a page has one named origin. Different sources get separate dashboards.

**Anti-patterns (do not):**
- Write to any source. The skill reads and reports; changes happen in the source system. A write by accident on a contract system is hard to undo.
- Estimate, infer or fill a figure the source did not return. Mark the panel `empty` with the reason. A wrong number in front of leadership is the failure that matters.
- Summarise or quote a document you did not read. A confident invented summary reads exactly like a real one.
- Assume the source. If it is unclear, ask (CP1); names repeat across folders and systems.
- Ship the template's placeholder text, or invent a link or a record id.
- Drop, blank out or fake a required panel. Tag the gap visibly instead.
- Put secrets or personal data in any file or in memory.
- Edit this skill's own files or config. Feedback goes to the feedback log and the owner updates the skill through the skill creator (section 13).

## 2. Triggers and inputs

| Input | Required? | Format and example | If missing or wrong |
|-------|-----------|--------------------|---------------------|
| Question or dashboard request | Yes | "what expires in 90 days", "show me the reporting dashboard" | Ask in Step 0 |
| Source | Yes | "Agiloft", a SharePoint folder or file link, an attached file, another system's name | Ask in Step 0 with suggested options |
| Exact location | For SharePoint and files | Folder path or file name | Show candidates as full paths; CP1 |
| Slice (owner, vendor, type, period) | No | "just Acme", "last quarter" | Whole source, say so |

## 3. Step 0: intake and validation

1. **Relevance.** Is this a contract question or a request to build a contract dashboard? If it asks to create, edit or delete a record or a file, say the skill is read-only and stop. If it is not about contracts, point to the right tool.
2. **Source.** Name the source from the request. Agiloft is not the default; if the person did not say, ask which source, offering what the session can reach. One source per dashboard.
3. **Completeness.** List missing inputs and ask for them in one message with a suggested default each.
4. **Sanity.** Is the location one real place? Repeated folder names, a link that resolves to nothing, or an attached file that is empty: say what looks wrong and ask (G6).
5. Restate the source, exact location, slice and the account whose view it is. **CP1.**

## 4. Config

All editable values are in `config.md`: caps, thresholds, fallbacks and paths. Read it at Step 1. Do not restate its values in this file; refer to keys by name. `OWNER` receives escalations and approves changes to this skill.

## 5. Checkpoint index

Every checkpoint waits for the person. If there is no reply, do not proceed.

| ID | After step | Human confirms | Options | If no reply |
|----|------------|----------------|---------|-------------|
| CP1 | Step 0 | Source, exact location or file, slice, whose view | Confirm / correct / pick a candidate | Wait |
| CP2 | Step 3 | The field mapping and the in-flight / in-force / closed grouping for a source not mapped before | Confirm / edit | Wait; build nothing |
| CP3 | Step 4 | Reading more than `DOC_READ_CAP` documents | Read more / stay at the cap | Stay at the cap and say so |

No checkpoint guards a side effect, because the skill has none: it never writes to a source, and the only thing it publishes is the dashboard page.

## 6. Orchestration

Single agent. Each step names what goes in, what comes back and when it is done.

1. **Step 1: connect and check.** Read `config.md`. Load the source file for the chosen source (section 1). Check the connector is reachable and say whose account it is (call the account call if the source has one). Primary down: use the `FALLBACKS` route and say so; otherwise manual mode on an attached export. Done when the source answers one real read.
2. **Step 2: discover.** Learn the real field names, the distinct values of each choice field and, for documents, the inventory. Nothing about a source is assumed; status names, types and column names differ everywhere. Do not narrate this. Done when you can name each role's column or say it is absent.
3. **Step 3: map.** Propose the mapping of fields to roles and the status grouping, with evidence. A mapping confirmed earlier in the session is reused without asking again. **CP2.** Done on the person's yes.
4. **Step 4: fetch and count.** Read `references/counting.md` and apply it after every fetch: compare returned rows with the limit, raise it and refetch if equal, bound time series by month, never plot a truncated figure as fact. Documents follow the caps in `DOC_READ_CAP` and `DOC_PAGES_MAX`; past the cap is **CP3**. Every figure comes from a call in this conversation.
5. **Step 5: answer.** Read `references/answering-rules.md`. For record-level questions (does X have an NDA, what are the terms, when does it end) also read `references/record-questions.md`. Lead with the answer, name the scope and the source in the answer, give the conclusion not the arithmetic.
6. **Step 6: build the dashboard.** Read `references/dashboard-recipes.md` and `references/dashboard-schema.md`. Build all four tabs, never ask which; set `active` to the one that answers the question. Copy `assets/dashboard_template.html`, edit only the DATA block, replace every placeholder message, publish with the Artifact tool using the same file path each time. A record-level question needs no dashboard; do not rebuild one for it.
7. **Step 7: QA.** Section 11. At most `QA_MAX_ATTEMPTS` attempts.
8. **Step 8: record and feedback.** Write the memory and run-log entries (section 10), then capture feedback and show the update prompt if due (section 13). This comes after delivery so it never delays the answer.

Stay inside `TOOL_CALLS_PER_STEP` calls per step and `RUN_MINUTES_MAX` minutes per run. A four-tab build can need many counting calls; if a run needs more, pause and say what is left. Updating an open dashboard: edit the same file and republish, never create a second dashboard in one conversation.

## 7. Agent roster (not applicable: single agent)

No sub-agents. Reading many documents is the one heavy step; it is held in check by `DOC_READ_CAP`, not by splitting the work.

## 8. Rules and formatting

- **Concrete, to the point, reasoned, sourced.** A specific figure, name or date, never "several". Every clause carries information. Say why the figure is what it is. Say what it was counted from, in a few words, using the source's own field or column names so it can be checked. Detail and worked examples are in `references/answering-rules.md`.
- **Answer the question asked.** "How many" gets a number; "what are" and "show me" get the records as a table card with a count as an addition; "is there" gets yes or no with dates; "why" gets the reason. Cut preamble, sign-offs and method narration.
- **Explain jargon once.** Write for someone who has never opened the source. Explain each status the first time it appears.
- **Scope in the sentence.** When a figure has more than one defensible scope (signed only, or every record with a date), say which. When your number differs from the source's own total or widget, say why in one clause, or say you could not explain the gap. Never quietly adjust to match.
- **Missing is a fact.** If the source does not hold it, say "the source doesn't track that" or "I couldn't find the field for this". An empty result needs its source too, and a zero on an important search says the account may not see everything.
- **One scope per dashboard.** A slice either filters the whole page or is answered in chat with the page left alone.
- **Nothing pretends to be interactive.** No invented links, no "click to drill down". Card titles are headings.
- **Every panel has a source line**: filter in plain words, record count, and the source's own figure when one exists. A panel without one is unfinished.
- **Header says whose view.** The page names the source, the account, the check time, the record count, the mapped columns and, for documents, how many were read.
- **Format.** Money as `$240K` or `$1.2M`, dates as `12 March`, no record ids unless asked, averages in whole numbers. Chart choice and page building: `references/dashboard-recipes.md`.

## 9. Guardrails

- **Caps:** values in `config.md`. Count tool calls per step, retries, documents read, QA attempts and rebuilds (`REBUILDS_MAX`), and write the counts in the run log.
- **Retries:** at most `RETRIES_PER_CALL` per failing call, with a pause, then stop and say what failed. The same error twice in a run means stop.
- **Gates:** stop and ask; never continue on a fired gate.
  - G1 stale, missing or incomplete data, a fetch that hit its limit and cannot be completed, or a file that could not be read in full.
  - G2 the figure differs from the source's own total by more than `DIVERGENCE_FLAG_PCT` (flag) or `DIVERGENCE_BLOCK_PCT` (block).
  - G3 a key number cannot be tied to a source; show it as unverified or leave the panel empty.
  - G4 a cap was reached.
  - G5 any step that would write to a source or publish anything other than the dashboard. The skill does not do this; if asked, decline.
  - G6 unclear, contradictory or out-of-scope input, including two possible sources, repeated folder names and ambiguous dates.
- **No loops without a counter.** Rebuilds are capped; the skill never calls itself.
- **Read-only.** The tools that write, upload, edit, move, rename or delete are never called, even if asked and even if the change sounds trivial.

## 10. Memory protocol

Memory lives in `MEMORY_FOLDER`. At start, read `memory.md` as hints and re-check live data. At the end, append one dated entry: source kind, what was built, issues, open items. A mapping the person confirmed may be kept as a hint (column to role, never the values) so the next run proposes it first; it is still shown at CP2. If a recent entry says `status: running`, ask before continuing. No secrets, client names, document contents or personal data. If the folder is unreachable, say so, write the entry locally and ask the person to upload it.

## 11. QA

Checklist: `references/qa-checklist.md`. Maximum `QA_MAX_ATTEMPTS` attempts. Attempt 1 fails: fix only the failed rows. Attempt 2 fails: stop. Failure policy: do not publish or update the dashboard; show the failed rows in chat and leave any earlier version as it was, because the audience acts on these numbers. Block rows stop delivery; Flag rows are delivered and listed first in the QA report. The report gives the result, attempts used, one line per row with evidence, and data freshness for the source.

## 12. Output, filing and notification (not applicable: nothing is filed or sent)

The dashboard is published with the Artifact tool, privately, and shared from the artifact's share menu. The skill cannot send or notify. If the person asks, tell them the link is shareable from the artifact. The run-log entry goes to `RUN_LOG_PATH`.

## 13. Feedback and updates

Feedback is captured on every run, but it never changes this skill directly. The skill cannot rewrite its own installed files, and an unreviewed change could quietly remove a safeguard. Changes go through the skill creator, approved by `OWNER`.

The log is `feedback-log.md` in `MEMORY_FOLDER` (the scaffolded `memory/feedback-log.md` is its starting copy). If the folder is unreachable, follow the memory protocol: write locally and ask the user to upload it.

**Capture (every run, after delivery).**
- If `FEEDBACK_QUESTION` is on and the run is attended, ask once: "Anything to change next time? (optional)". An empty reply, "no" or "all good" logs nothing.
- Log these without asking, one row each: the user edited or rejected output at a checkpoint, a QA Flag or Block row, a gate fired, a cap was reached.
- Set type and severity from the definitions in the log. By is owner, user or auto (never a name). Describe the problem, not the client or matter. No secrets or personal data.

**Lessons (light, automatic learning).** If the owner states a presentation preference ("always put the summary first"), add it to the Lessons section of memory.md, set that row's status to lesson, and apply it from the next run. Lessons may change wording, order, layout and default inputs only. They never change caps, gates, checkpoints, QA rows, recipients, filing or anything in `config.md`. Other users' preferences stay open for the owner, because memory is shared by the whole team.

**Update prompt (end of run).** Rows logged in this run count. The prompt is due when open rows reach `IMPROVE_THRESHOLD`, or any open row has severity high, and "Snooze runs left" is 0. If this run logged a high row, set the snooze to 0 first. If not due, lower "Snooze runs left" by one (not below 0) and stop.
- **Who is the user.** Use the name the session gives (account or introduction); if unknown, ask once. No answer means not the owner.
- **Scheduled or unattended run:** do not ask. Include `OWNER` in this run's notification with one line: "N feedback items are waiting for an update".
- **The owner:** show the open count and the high rows, then two options. **Update now** (recommended when any open row is high): set "Snooze runs left" to `IMPROVE_SNOOZE_RUNS` so the prompt does not repeat while the update is in progress, then hand off as below. **Next time:** set "Snooze runs left" to `IMPROVE_SNOOZE_RUNS`.
- **Anyone else:** if "Owner told" already has a date, say in one line that the owner knows and stop. Otherwise offer **Tell the owner** (record today's date and run in "Owner told", draft a short note to `OWNER` with the open count and the high rows, and send it only if the user says yes, gate G5; otherwise give the user the text) or **Next time** (no change; a non-owner never snoozes the owner's prompt).
- **No reply:** the same as Next time for that user. Record "Last prompt" as date, run and choice. This prompt is not a checkpoint: nothing changes until the owner approves a change plan inside the skill creator.
- Add the feedback rows and the prompt result to this run's run-log entry.

**Hand-off (Update now).** Load the `SKILL_CREATOR` skill and start it with this block, so it goes straight to feedback intake without a new interview:

```
FEEDBACK HAND-OFF
skill: <name>   version: <version from the header>   owner: <OWNER>
master copy: <MASTER_COPY>
feedback log: <MEMORY_FOLDER>/feedback-log.md
open items: <FB IDs with severity, high then medium then low, oldest first>
```

The skill creator shows a change plan for approval, applies only what the owner approves, bumps the version, adds a regression test per fixed item, re-runs QA, marks the rows and resets the prompt state. The skill creator then tells the owner to install the new version. If `SKILL_CREATOR` is not installed, say so in one line, keep the rows open, and tell the owner to install it and then say "apply feedback to <name>".

## 14. Changelog

See CHANGELOG.md.
