# agiloft-dashboards — Contract Answers Without Opening Agiloft

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-2ea44f)](https://agentskills.io)
[![Claude Cowork](https://img.shields.io/badge/Claude-Cowork-8a2be2)](https://claude.ai)
[![Agiloft CLM](https://img.shields.io/badge/Agiloft-any%20CLM%20knowledgebase-0d9488)](https://www.agiloft.com)
[![Read only](https://img.shields.io/badge/access-read--only-1f6feb)](#-what-it-will-not-do)
[![Schema](https://img.shields.io/badge/schema-discovered%20at%20runtime-c96442)](#-how-it-works)

**Ask in plain English** · [📖 Skill source](./SKILL.md) · [🗒️ Install](#2-install-the-skill)

A skill that answers contract questions from an Agiloft knowledgebase in plain
language and keeps a live four-tab dashboard open beside the chat. It reads
through an existing Agiloft MCP connector — it ships no connector of its own and
carries no data. Field names, status values and agreement types are discovered at
the start of every session, so nothing is configured and nothing is assumed. Most
of it is not about fetching data at all: it is a set of rules about the specific
ways a contract number goes wrong.

<p align="center">
  <img src="./assets/03-answer.png" width="900" alt="A contract question answered in chat, with the live dashboard beside it">
</p>

<sub>Dashboard panels throughout are real renders against a dummy knowledgebase — every counterparty in them is invented. The Claude Desktop frames around them are reconstructions, tagged <code>illustrative</code>: building a live Agiloft connector needs an Agiloft licence, which we do not hold, so the surrounding UI is drawn rather than captured. The figures shown inside them are computed from the same dummy knowledgebase and are accurate.</sub>

## ✨ Highlights

- **"Complete answers, then stop"** — a count is one sentence, a bottleneck is four, because the reasoning *is* the answer. No fixed length, no padding, and never two percentages handed over for the reader to compare themselves
- **"Every figure names where it came from"** — not "from Agiloft", but the table, the fields filtered on, and the values used, so anyone can reproduce the number and settle the argument about whose report is right
- **"Nothing hardcoded"** — status names, agreement types and field names are read from your knowledgebase at session start; there is no configuration file because there is nothing to configure
- **"Statuses classified by meaning, not string match"** — `Lapsed` is Expired, `Void` is Cancelled, `Live` is Active; a genuinely ambiguous status is reported as counted one way rather than silently counted the other
- **"The limit check"** — every fetch is compared against the page size it asked for. 500 returned against a limit of 500 means records were missed, so it refetches before that number reaches a tile. This is the most likely way a page size gets reported as a company total
- **"Loose company search, split by entity"** — counterparty names are filed inconsistently, so the search is deliberately wide; results are then split back out by entity, so *Brightline Systems* and *Brightline Holdings* never merge into one answer
- **"One query per month"** — time series are fetched a month at a time. Pulling recent records and bucketing them makes early months look empty and invents a trend that is not in the data
- **"Units read off the field"** — some knowledgebases store days in current status, others store hours. 90 days is `90` in one and `2160` in the other; a median of `3,869` reported as days is wrong by a factor of twenty-four
- **"Missing fields reported as facts"** — a field the record does not hold is stated as absent, never filled with plausible prose. Where Agiloft's **Extract Key Terms** has written model-extracted terms onto the record, those are used and labelled as extracted rather than lawyer-entered
- **"Reconciles against Agiloft rather than competing with it"** — where an Agiloft widget covers the same ground, its figure appears alongside and any difference is explained. A difference that cannot be explained is said out loud, not quietly adjusted away
- **"Read-only by construction"** — the connector exposes create, update and delete. This skill never calls them and refuses requests to change anything
- **"Nothing fake on the dashboard"** — no dead links, no "click to drill down" on a static page, no placeholder figures. A panel with no data says why it has none

## 🖼️ Examples

> [!TIP]
> **The dashboard in the hero image above was built from this single question:**

```
what's expiring in the next 90 days?
```

All four dashboards are built every time. The one that answers the question asked
is the one that opens; the rest stay a click away.

<p align="center">
  <img src="./assets/04-dashboard-tabs.png" width="900" alt="The four dashboard tabs — Contract Reporting, Contract Requester, Cycle Times Reporting, Vendor Management">
</p>

<table>
  <tr>
    <td align="center" width="50%">
      <img src="./assets/07-reporting.png" alt="Contract Reporting tab" width="100%"><br>
      <b>Contract Reporting</b> · the whole book<br>
      <sub>In flight, in force, closed and total; the mix by agreement type; month-by-month volumes; and what expires in the next 90 days.</sub>
    </td>
    <td align="center" width="50%">
      <img src="./assets/08-requester.png" alt="Contract Requester tab" width="100%"><br>
      <b>Contract Requester</b> · scoped to you<br>
      <sub>Your drafts, your contracts in progress, anything of yours expiring within 30 and 90 days, and a table with dates, counterparty and status.</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <img src="./assets/09-cycle-times.png" alt="Cycle Times Reporting tab" width="100%"><br>
      <b>Cycle Times Reporting</b> · where it is stuck<br>
      <sub>How long in-flight contracts have sat at their current step, banded and broken down by stage. Contracts with no age recorded get their own band rather than being dropped.</sub>
    </td>
    <td align="center" width="50%">
      <img src="./assets/10-vendor.png" alt="Vendor Management tab" width="100%"><br>
      <b>Vendor Management</b> · who you buy from<br>
      <sub>Active vendors counted as distinct counterparties, vendor agreements by lifecycle state, and a twelve-month view of renewals due.</sub>
    </td>
  </tr>
</table>

Follow-ups re-scope the **same** dashboard rather than opening a second one. A page
still showing company-wide figures while the chat discusses one vendor is exactly
how a wrong number gets screenshotted and forwarded:

<p align="center">
  <img src="./assets/05-followup.png" width="900" alt="A follow-up narrowing the answer to NDAs, with the same dashboard re-scoped">
</p>

## 🚀 Installation

### 1. Connect the Agiloft MCP connector

This skill reads contract data through an Agiloft MCP connector and does not
connect to Agiloft on its own. An Agiloft login is not enough — the connector is
a separate piece, usually maintained by whoever administers Agiloft for your
team. Some deployments also need an endpoint-security exception before it runs.

In Cowork, open the **+** menu → **Connectors** and check `agiloft` is toggled on:

<p align="center">
  <img src="./assets/01-connector.png" width="880" alt="The agiloft connector toggled on in the Cowork connectors menu">
</p>

| Connector build | Tools exposed | What the skill does |
| --- | --- | --- |
| **6-tool** | `agiloft_select`, `agiloft_read`, `agiloft_search` | Pages the contract table and counts in-session |
| **13-tool** | adds `agiloft_count`, `agiloft_group_by`, `agiloft_time_series`, `agiloft_cycle_times` and more | Prefers the aggregation tools — fewer calls, exact counts |

The skill detects which build is present and uses what is there. It never calls
the create, update or delete tools, even on builds that expose them.

### 2. Install the skill

Add this marketplace in Claude (**Plugins → Add Marketplace**):

```
https://github.com/allNeurons-AI/back-office-agents.git
```

then install the **legal** plugin. The skill is available as
`/legal:agiloft-dashboards`. To install this skill on its own instead, zip this
folder and add it in Claude Desktop under **Settings → Skills → Add**. It goes
through a short security scan before it is ready. Restart Claude fully afterwards.

<p align="center">
  <img src="./assets/01b-skill.png" width="880" alt="Uploading the skill under Settings, Skills">
</p>

Requires **Claude Cowork** on a Pro, Team or Enterprise plan. There is no setup
form and no configuration folder — if the connector is live, the skill is ready.

## ⚡ Quick Start

After installation, just ask. For example:

```
what's expiring in the next 90 days?
```

<p align="center">
  <img src="./assets/02-question.png" width="880" alt="Asking a question in plain English">
</p>

Other things worth asking:

> *"does Brightline Systems have an NDA with us?"* · *"what's slowing contracts
> down?"* · *"where has my request got to?"* · *"what did we sign last quarter?"*
> · *"who owns the vendor agreements expiring this month?"*

The skill learns your knowledgebase, works out the answer itself, writes the
figures into a self-contained HTML dashboard, and hands you both.

## 🔍 Every Number Shows Its Source

Each panel carries a source line: the filter in plain words, how many records it
rests on, and — where an Agiloft widget covers the same ground — that widget's
figure alongside, with any difference explained.

<p align="center">
  <img src="./assets/06-source-line.png" width="700" alt="A panel's source line, showing the filter and the record count it rests on">
</p>

The same applies in chat. A figure arrives with a clause naming the table and the
fields, in Agiloft's own field names, because its whole job is to be checkable
against the system:

> **87 contracts in force expire between now and 24 November** — most of them
> Data Processing Addenda (19) and Consulting Agreements (13). Another 163
> records carry an end date in that window but were never signed or are already
> closed, so nobody has to renew them.
>
> *Contract table, `expiry_on` between 26 Aug and 24 Nov 2026 with `wf_state` =
> Live, split by `paper_type`.*

When two people get different numbers for the same question, the filter is always
why. Naming it up front is what stops that argument.

## 👥 Who Sees What

The connector authenticates as **one Agiloft account**, and Agiloft applies that
account's permissions to everything the skill reads. The dashboard shows that
account's view of the knowledgebase, not the whole thing.

| Setup | Consequence |
| --- | --- |
| **Individual seats** | Two people can ask the same question, get different numbers, and both be right |
| **Shared service account** | Everyone sees the same view — usually wider than the person reading the screen would have in Agiloft |

Neither is wrong; it is a decision to make deliberately rather than discover
later. The account being read as goes in the dashboard header, so anyone looking
at a screenshot knows whose view it is. A zero result is reported as "none I can
see", not "none exist".

## 🔄 How It Works

<p align="center">
  <img src="./assets/architecture.png" width="900" alt="Internal workflow — question to answer and dashboard">
</p>

<sub>Solid arrows are the path every question takes. Dashed arrows are conditional — the knowledgebase read, a follow-up re-scoping the page in place, and the Agiloft widget figure, which appears only when it differs from ours.</sub>

`SKILL.md` is the operating procedure. In order:

1. **Detect the connector build** — use whichever read tools are present, never the write ones
2. **Learn the knowledgebase** — one record read gives the real field names, which differ from the UI labels; statuses and agreement types come from the aggregation tools, or from paging the table once and counting
3. **Classify statuses by meaning** — in force, in flight, closed, by what each value means rather than by string match
4. **Read the question, not just the topic** — "how many" returns a number; "what are" returns records. A count is an addition to a list, never a substitute for one
5. **Fetch, then check the fetch** — a returned count equal to the requested limit means records were missed; refetch higher before the number goes anywhere
6. **Bound time ranges properly** — one query per month, so an empty early month is a fact rather than an artefact
7. **Search companies loosely, then split by entity** — the wide search prevents a false "no"; the split prevents a false "yes"
8. **Check the unit on any duration** — convert hours to days for display and say which was used; keep records with no value as their own band
9. **Answer single-contract questions from populated fields only** — including Extract Key Terms fields where they exist, labelled as model-extracted
10. **Build all four dashboards and attach the source lines** — then re-scope in place on follow-ups

## 🎯 When To Use (and When Not To)

**Good fit:**

- Someone who needs a contract answer and does not use Agiloft — a salesperson, a finance lead, a business requester
- Questions of shape and volume: how many, what is expiring, what is stuck, who the counterparty is, what the mix looks like
- Anyone who has to justify a figure afterwards, since every number arrives with the filter that produced it

**Reach for Agiloft itself when you need:**

- **To change something.** This skill is read-only and refuses write requests
- **The terms inside a signed document** — payment terms, liability caps, governing law. Those live in the attachment, not the record, unless the knowledgebase runs Extract Key Terms
- **A figure the record cannot support.** Contract value, ageing, owner — if the field is not in your knowledgebase, the panel stays empty with a reason rather than estimating

## 🚫 What It Will Not Do

- **Write.** The connector exposes create, update and delete. The skill never calls them, under any phrasing of the request
- **Invent.** A missing field is reported as missing. A panel with no data says why
- **Guess a total.** An unverified count gets refetched, not rounded off
- **Merge legal entities.** Similarly-named companies are counted separately and both named
- **Fake interactivity.** Nothing on the dashboard links anywhere it cannot go

## 👤 Author

**allNeurons** — [allneurons.ai](https://allneurons.ai)

## 📄 License

See the repository root.
