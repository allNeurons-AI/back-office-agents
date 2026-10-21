# Source: Agiloft

Loaded at Step 1 when the source is Agiloft. Agiloft behaviour is unchanged from v1.0; everything here is the Agiloft-specific detail.

## Whose data you are looking at

The connector authenticates as **one Agiloft account**, and Agiloft applies that
account's permissions to everything you fetch. You see what it can see - not the
whole knowledgebase.

This has consequences worth stating plainly:

- **Two people can ask the same question and get different numbers**, and both be
  right. A paralegal with full contract visibility and a business requester
  scoped to their own department are looking at different populations.
- **A figure that doesn't match someone's Agiloft screen may be a permissions
  difference, not an error.** Consider it before assuming a bug.
- **"No results" can mean "none visible to this account"** rather than "none
  exist" - and on the NDA question that distinction is the difference between a
  safe answer and a dangerous one.

So: if `agiloft_whoami` exists, call it once at the start and put the account
name in the dashboard header, so anyone reading a screenshot knows whose view it
is. If it doesn't exist, say which account the connector is configured with if
you can tell, and otherwise note that the figures reflect the connector's
permissions.

**When a count comes back as zero on a question that matters** - an NDA search,
a named contract, a specific vendor - say that you may not have visibility rather
than reporting a confident absence:

> "I can't find an NDA with Zenith Partners. I searched *Zenith* across both
> confidentiality types. Worth checking the exact legal entity name, and whether
> this account can see all contract records."

If the connector runs on a **shared service account** rather than a personal
seat, that account's permissions apply to everyone using the skill. Say so on
the dashboard - a shared account usually sees more than the person reading the
screen is entitled to, and that is worth being explicit about.

## Never write to Agiloft

Some builds expose `agiloft_create`, `agiloft_update` and `agiloft_delete`.
**Do not call them.** This skill reads and reports. If someone asks you to change
or create a contract, say it is read-only and they should do it in Agiloft
directly. That holds even if they insist, and even if the change sounds trivial.

## Your tools

Two builds exist. Check your tool list once at the start and use what is there.
Do not narrate this.

**6-tool build.** `agiloft_select`, `agiloft_read`, `agiloft_search`.

- `agiloft_select` with a filter and a `limit` — always start here
- `agiloft_read` for every field on one record, **after** narrowing with select
- `agiloft_search` when you do not know the field or the value is fuzzy
- No aggregation. You count and average from the records you fetched.

**13-tool build.** Adds `agiloft_count`, `agiloft_group_by`,
`agiloft_time_series`, `agiloft_cycle_times`, `agiloft_upcoming_renewals`,
`agiloft_pending_approvals`, `agiloft_find_person`, `agiloft_describe_table`,
`agiloft_whoami`. Prefer these — they aggregate properly and are far more
accurate for tiles.

If `~/CLAUDE.md` exists it carries Legal Engineering's confirmed field names.
Trust it over anything guessed here.


### Reconcile against Agiloft's own widgets

Most Agiloft deployments already have dashboards answering some of these
questions. **When a panel overlaps one, name it and show its number too.**

Agiloft dashboards are built by each customer from saved searches and chart
widgets - there is no fixed set that ships with the product. So you cannot know
in advance what theirs are called. What you can do is recognise the *kinds* of
widget almost every CLM deployment builds, and reconcile against them when the
person mentions one or when their figure differs from yours:

| Kind of widget | Overlaps your panel |
| --- | --- |
| A count of contracts in progress | in-flight tile |
| A count of signed or executed contracts | in-force tile |
| A total record count | total tile |
| A count of cancelled or withdrawn requests | closed tile |
| A breakdown of in-progress work by agreement type | in-flight mix |
| A breakdown of signed contracts by agreement type | in-force mix |
| Expirations at 30 / 60 / 90 days | expirations panel |
| Volume created or signed per month | trend charts |
| A twelve-month renewal outlook | vendor renewals panel |

**Ask rather than guess.** If someone says "that doesn't match our dashboard",
ask which dashboard and what it shows. Their definition of the figure is the one
that matters, and the difference is nearly always a status scope.

**If your number differs from the widget's, that is information, not a bug.**
Say why in `differs`, in one clause. The usual causes:

- **Status scope.** "Expiring" in an Agiloft widget usually means contracts *in
  force*. Counting every record with an end date pulls in unsigned, cancelled
  and terminated ones. This is the most common source of a gap.
- **Window edges.** Ninety days from today is not the same as three calendar
  months, and an inclusive end date differs by one day.
- **Exclusions in the widget name.** A widget labelled "No Legacy" or similar excludes imported records; yours probably does not.
- **Live drift.** Records move between statuses while you work. A gap of one or
  two on a status tile is drift, not error.

If you cannot explain a gap, **say so rather than picking a side**: "Agiloft's
widget shows 391 for this and I count 422 — I haven't reconciled the difference."
Never quietly adjust your number to match, and never present yours as the
correct one without knowing why they differ.


## Learning this knowledgebase

**Nothing about the customer's Agiloft is hardcoded here.** Status names,
agreement types and field names differ between knowledgebases - sometimes
substantially. Discover them once at the start of a session and work from what
you find.

### The three things to establish

1. **Field names.** Read one contract record. That gives you the real column
   names - they differ from the labels shown in the Agiloft UI.
2. **Status values.** The actual list in use, with counts.
3. **Agreement types.** The same, for the agreement-type field.

**How to get 2 and 3 depends on the connector build.** On a build with
`agiloft_group_by`, group the contract table by each field - two calls. On a
read-only build there is no aggregation tool, so **page through the contract
table once and count the distinct values yourself.** Apply the limit check on
every page. A few thousand records is three or four calls and it is worth it -
everything downstream depends on having the real names.

Do not narrate any of this.

**Match status names by meaning, not by string.** The groups below list typical
names, not an allowed list. `Lapsed` is Expired, `Void` is Cancelled, `Withdrawn`
is Rejected, `Live` is Active. If a name has no obvious equivalent, that is the
case to ask about rather than force into a group.

### Working out what "in flight" means here

There is no universal definition. Once you have the status list, classify it:

| Group | Typically |
| --- | --- |
| **In force** | Executed, Active, Signed - the contract is live |
| **In flight** | Anything mid-process: drafts, reviews, pending signatures, approvals |
| **Closed** | Cancelled, Terminated, Expired, Rejected |

If a status is ambiguous, **say so rather than guessing**. "I counted Approved as
in flight rather than in force - tell me if that's wrong for you" is a better
answer than a silently different number.

If the customer's own Agiloft report defines "in flight" differently, that
definition wins. Ask which statuses it includes when a figure needs to match
their dashboard.

### Fields that may or may not exist

Check before relying on any of these. None are guaranteed:

| Field | If present | If absent |
| --- | --- | --- |
| Days or hours in current status | Cycle-time panels work - **check the unit first**, see below | Say the knowledgebase doesn't track it. Do not estimate from dates unless asked, and label it as derived if you do |
| Contract value | Show money figures | Leave value columns and tiles out |
| Auto-renew flag | Mention it when answering "when does this terminate" | Do not imply a contract simply ends |
| Record source / import flag | Native vs imported splits work | Skip those panels |
| Assigned paralegal or reviewer | Workload panels work | Skip them |
| **AI-extracted term fields** - governing law, payment terms, liability cap, notice period, auto-renew | The "what are the terms" question is answerable from fields. Label the values as extracted from the document | The record holds metadata only; terms live in the signed file |

**A missing field is a fact to report, not a gap to fill.**

### The unit on the ageing field

Some knowledgebases hold **days** in current status, others hold **hours**. The
field name usually says which. Read it before you use the number, because the
same threshold is a different figure in each: 90 days is `90` in one and `2160`
in the other.

Convert to days for anything shown to a person - *"a median of 161 days"*, not
*"a median of 3,869"*. State the unit in the source line so the conversion is
checkable. If the name doesn't settle it, look at the range: values in the
thousands across a contract population are hours, not days.

### Identifying NDA types

The NDA question depends on knowing which agreement types count as NDAs, and
that varies. From the discovered type list, take anything matching
non-disclosure, NDA, confidentiality, or a customer-specific variant. When
unsure, include it and say what you searched.

## What is already known about this knowledgebase

**Hints, not truth.** Discovery still runs every session - these are here so you
recognise the values when they come back, and so you can spot a gap fast. If the
connector returns something different, the connector wins.

### Fields confirmed present

`Days in Current Status`, Agreement Type, Agreement Subtype, Template, Contract
Owner, Assigned Paralegal, Date Created, Contract Effective Date, Contract End
Date, Counterparty Legal Name, Contract Title, Status.

**Confirmed absent: hours-in-status.** It is a calculated field configured per
knowledgebase and is not set up here, so the ageing field is in **days** - do
not divide by 24. A meaningful share of in-flight contracts have no value in
`Days in Current Status`; show those as their own "Age not tracked" band.

### Statuses

Draft, Pending Contract Requester, Pending Business Review, Pending Paralegal
Review, Pending Legal Review, With Counterparty, Pending Counterparty Signature,
Pending Company Signature, Pending Signature / Both Parties, Approved, Executed.

- **In force**: Executed
- **In flight**: everything else above - created, not executed, not cancelled
- **Closed**: Cancelled, Terminated, Expired where present

### Agreement types

Non-Disclosure Agreement, BANK Customer Agreement, Listing Program, Capital
Markets, Client Agreement, Loan Agreements, K-Program, Vendor Agreement,
OTC / ISDA, Crypto Integration, Staking, Marketing and Advertising, Referral
Agreement, Trading Agreements.

**NDA types for the cover question**: Non-Disclosure Agreement, D-1 NDA, and any
other type carrying "NDA" or "confidentiality". Ask if unsure rather than
returning a false negative.

### Panels specific to this deployment

Build these in addition to the standard ones, when the fields are reachable:

| Panel | How |
| --- | --- |
| Token Programs | Bar, one per programme. Values seen: Liquidity Program, Marketing Program, Token Rewards, Integration Fee, Drops Program, Monthly Fees |
| Invoice Status for Executed Agreements | Pie, one slice per status. Values seen: paidInFull, pendingApproval, Manually Processed, Draft, Open, rejected. Lives in a separate invoice table, not on the contract record |
| Automated NDA Execution Method | Stacked bar on the DocuSign-automation field, segments "Not Involved" / "Paralegal Involved" |
| Record Source: Native Agiloft vs ZIP | Bar by agreement type, split true/false on the record-source field |
| NDA Reviewer | Bar over the reviewer-status field |

**These exist** - their own dashboards render them, so the data is there. A
previous run reported Token Programs and Invoice Status as "not mapped"; that
was a failure to find the fields, not an absence. Say "I couldn't find the field
for this", never "this isn't tracked".

**Known connector limitation:** choice fields cannot be filtered through this
build. That blocks the DocuSign split, Token Programs and Invoice Status, and
grouping by counterparty for Active Vendors. Report it as a connector limit, not
as missing data.

### Their dashboard names

Use these exact labels on the tabs, since people recognise them: "Contract
Reporting Dashboard", "Contract Requester Dashboard", "Cycle Times Reporting
Dashboard", "Vendor Management".


## When something goes wrong

Translate every error into something actionable. No stack traces, no HTTP codes,
no URLs.

| What happened | What to say |
| --- | --- |
| Auth rejected | "Agiloft turned down the sign-in. The connector's credentials may need refreshing — Legal Engineering can sort that." |
| Cannot reach Agiloft | "I can't reach Agiloft right now. If your Agiloft needs a VPN, connect and I'll try again." |
| Table or field not found | Check the real names, retry once. Then: "That isn't set up in your Agiloft." |
| Empty after checking field names | "Nothing in Agiloft matches that." |
| Query too broad, times out | Narrow it and say "that was too broad — here's the last 12 months instead." |
