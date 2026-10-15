# Dashboard recipes, chart choice and page building

Loaded at Step 6. The panel logic is source-agnostic: each panel is a count, a grouping, a time series or a record table over the mapped fields. The tool calls shown are the Agiloft build; for another source fetch the same records with that source's tools (see `references/source-sharepoint.md` or `references/source-generic.md`) and compute the same panels. A panel whose mapped field does not exist is `empty` with the reason.

## The four dashboards

**These four views are this skill's own layout, not a copy of anyone's Agiloft.**
Agiloft ships a dashboard *builder* - a canvas of widgets each customer
assembles themselves - not a standard set of dashboards. So there is nothing to
mirror. What these four are is the four audiences that exist in every contract
team, and the questions each of them actually asks.

| Dashboard | key | Who | Answers |
| --- | --- | --- | --- |
| Contract Reporting | `reporting` | Leadership, legal ops | Volumes, in progress vs signed, mix by type, month-over-month, expirations |
| Contract Requester | `requester` | Business requesters | My drafts, my contracts, where my request has got to |
| Cycle Times Reporting | `cycletimes` | Legal ops, reviewers | How long contracts sit per status, where the backlog is, by agreement type |
| Vendor Management | `vendor` | Procurement, vendor owners | Vendor contracts, renewal workload a year out, active counterparties |

Build all four every time, with these names. They are stable across deployments
precisely because they describe audiences rather than one customer's
configuration.

**If the customer has their own dashboards, borrow their names.** When someone
refers to "the renewals dashboard" or "our exec report", use their label on the
matching tab so the page looks like something they recognise. Do not invent a
mapping you have not been told about.

## Dashboard recipes

**Always build all four. Never ask which one they want.**

"Show me the dashboard" means all four tabs, populated. Asking "which dashboard
do you want open?" is a wrong answer to that request - it puts the work back on
someone who came here precisely so they would not have to know which Agiloft
report answers their question. The tabs cost one extra query each and the whole
point is that the other three are already there when they think of the next
question.

Set `active` to the dashboard that answers what they actually asked, so the
right tab is in front when the page opens. Populate the other three too. If a
panel on a non-active tab needs data you have not fetched, fetch it - and if
some genuinely cannot be filled, mark those panels `empty` with a reason rather
than leaving the tab bare.

### Contract Reporting

**13-tool build:**

```
agiloft_count   Contract, no filter                     -> Total Number of Contracts
agiloft_count   Contract, status not executed/cancelled -> Number of Contracts in Flight
agiloft_count   Contract, status = executed             -> Number of Executed Contracts
agiloft_count   Contract, status = cancelled            -> Cancelled / Incomplete
agiloft_group_by  Contract by agreement type, in-flight only  -> "Contracts in Flight" pie
agiloft_group_by  Contract by agreement type, executed only   -> "Executed Contracts" donut
agiloft_time_series  Contract by date created, 12 months      -> month-over-month bar, span 2
agiloft_upcoming_renewals  90 days                            -> "Expirations" bar
```

**6-tool build** — one fetch does double duty. Pull the in-flight set once, then
derive both the tile and the chart from those same records:

```
agiloft_select  status in <in-flight list>, limit 2000
    -> count the records          = "Contracts in Flight" tile   (exact)
    -> tally by agreement type    = "Contracts in Flight" pie     (exact)
    -> average hours per status   = Cycle Times, if the field exists

agiloft_select  end date within 90 days, limit 500
    -> bucket by month            = "Expirations" bar

one agiloft_select per month, each filtered to that month
    -> count each                 = month-over-month bar
```

Tile tones: in flight `teal`, executed `purple`, total none, cancelled `red`.
That matches what they see in Agiloft.

**Further panels, built from what this knowledgebase actually has:**

| Panel | How |
| --- | --- |
| Signed month-over-month | The same month-by-month approach, on the execution date field |
| Expirations next 90 days | Bar by month over the end-date field |
| Single-agreement-type donuts | One donut per high-volume agreement type, split by its subtype where one exists |

**Then add panels for the dimension fields you discovered.** Every deployment
carries a handful of choice fields specific to that business - a programme name,
a region, a business unit, a routing or automation flag, a review outcome. These
are where a customer's own dashboard gets its character, and you only learn them
by looking.

The rule: take each choice field on the contract record with a manageable number
of distinct values - roughly three to a dozen - and build one panel per field,
grouping contracts by it. Name the panel after the field's own label. Skip
free-text fields, dates, and anything with hundreds of values.

Build the ones you have fields for. Leave the rest out - an absent panel is
better than a wrong one, and a panel built on a field you guessed at is worse
than both.

### Contract Requester

```
agiloft_select  owner = them, status = draft        -> My Drafts tile
agiloft_select  owner = them, in-flight statuses    -> My Contracts In Progress tile
agiloft_upcoming_renewals  30 days, owner = them    -> Expiring < 30 Days tile
agiloft_upcoming_renewals  90 days, owner = them    -> Expiring < 90 Days tile
agiloft_select  owner = them, limit 10, newest first -> "My Contracts" table, span 3
```

A tile showing zero is correct and useful — do not hide it.

**A shortcuts or hotlinks card needs care.** If a customer's own dashboard has
one, those are working buttons in Agiloft; on your page you do not have their
URLs. Either drop the card or render the labels as plain text with no `url`, so
nobody clicks something dead.

**Look past the contract table for this dashboard.** A requester's view often
depends on related tables - invoices, tasks, approvals, signature records -
which hold the "what happened to my request" detail that the contract record
does not. List the tables the connector exposes before concluding something is
unavailable. A related table you did not look for is the most common reason a
panel gets wrongly reported as impossible.

If you genuinely cannot reach them, say **"I couldn't find the field for this"**
rather than "this isn't tracked" — those mean different things, and the second
one is wrong here.

### Cycle Times

```
agiloft_cycle_times  hours field, all contracts   -> one tile per key status
agiloft_cycle_times  grouped by status            -> "All Contract Average Status" area, span 3
agiloft_cycle_times  filtered to NDA              -> "Standard NDA" area
agiloft_cycle_times  filtered to each major type  -> one area card each
```

**Cycle times need an ageing field, and not every knowledgebase has one.** Look
for a numeric field holding days or hours in the current status. Agiloft does not
ship one as standard - it is normally a calculated field configured per
knowledgebase.

If there is none, say so once and leave these panels empty: "Agiloft isn't
tracking time-in-status in this knowledgebase - it's a calculated field that has
to be configured." Do not estimate it from dates.

Where the field does exist, it turns Cycle Times from an empty dashboard into a
useful one:

```
agiloft_select  status in <the in-flight statuses you discovered>, limit high enough
    -> bucket each record by the ageing field
    -> tiles:  over 30 days / over 90 days / over a year / stuck with
               counterparty over 90 days   (counts, not averages)
    -> chart:  stacked bar per status - "90 days or less", "Over 90 days",
               "Age not tracked"           span 3
```

A meaningful share of in-flight contracts have no value in that field. **Show
them as their own "Age not tracked" band rather than dropping them** - silently
excluding them changes every percentage on the chart.

Say what the measure is: days in *today's* status, not total elapsed cycle time.
Those are different things and someone will assume the wrong one.

### "What's slowing us down" wants a stage, not a total

The answer is the name of a status. "537 contracts are over 90 days" is a
volume, not an answer.

And **the biggest bar is not automatically the bottleneck.** A status with more
contracts in it will have more old contracts in it. Before naming one, compare
stages on a like-for-like basis:

- **Share** - what percentage of contracts *in that status* are over 90 days
- **Median age** within the status
- **Volume** - the raw backlog

A genuine bottleneck leads on share or median, not only on volume. If one stage
holds 40% of the whole over-90 backlog while holding far less than 40% of the
in-flight population, that is real and worth naming.

**If the stages are all similar, say so.** A flat distribution - every status
sitting at roughly the same share and median - means the delay is systemic, not
located in one place. Naming the largest bar anyway invents a bottleneck and
sends someone to fix the wrong thing.

Do that comparison silently and report the conclusion. The percentages are
how you work it out, not what you say.

> Real: "Contracts are getting stuck waiting on the other side to sign. Far more
> of the old backlog sits at that step than its share of the workload would
> explain, so it is genuinely the slow one. About 240 contracts have been there
> over three months."
>
> Flat: "No single step is the hold-up - everything is slow. Contracts sit
> roughly five months at whichever stage they are in, whether that is legal
> review, intake or a signature. Intake has the most stuck simply because it is
> the busiest stage, not because it is slower."

Agiloft's own Cycle Times dashboard usually carries per-agreement-type
breakdowns too - one area chart over status for each higher-volume agreement
type. Build these the same way, using the ageing field, one card per type,
filtered to that type. Pick the types from what you discovered, largest first.

Common filters on this view: date created, signer, and reviewer or paralegal.

### Vendor Management

Structurally close to Contract Requester, with a longer horizon.

```
agiloft_select  owner = them, status = draft         -> My Drafts tile
agiloft_select  owner = them, in-flight statuses     -> My Contracts In Progress
agiloft_select  owner = them, end date within 30d    -> Expiring < 30 Days
agiloft_select  owner = them, end date within 90d    -> Expiring < 90 Days

agiloft_select  end date between today and +12 months, one query per month
    -> "Upcoming Expiring Contracts (Year from Now)" area chart, span 2
       x-axis is Contract End Date by month

agiloft_select  Vendor Agreement, in-force statuses, limit high enough
    -> count DISTINCT counterparty names = "Active Vendors" tile
       one vendor with six live contracts counts once

agiloft_select  owner = them, limit 10, newest first
    -> "My Contracts" table, span 3
       columns: ID, Assigned Paralegal, Agreement Type, Agreement Subtype,
                Date Created, Contract Effective Date, Contract End Date,
                Counterparty Legal Name, Contract Title

one query per month on date created / execution date
    -> "Created Month-over-Month" and "Executed Month-over-Month" bars
```

Its hotlinks card carries one extra entry over the Requester version: **Quick
Legal Request**. Same rule — labels only, unless you have a real URL.

The year-ahead expirations chart is the panel that makes this dashboard worth
opening — it is the one view that shows renewal workload building up. Query
month by month; do not fetch a year of records and bucket them.

**Active Vendors** counts distinct counterparties, not contracts. Two numbers
that look similar mean very different things, so label it plainly and put the
distinction in `source.query`: "distinct counterparty names across Vendor
Agreements currently in force".

Getting this right needs care:

- **Deduplicate on the counterparty name**, case-insensitively and after
  trimming whitespace. "Acme Inc" and "acme inc " are one vendor.
- **Near-duplicates are not yours to merge.** "Acme Inc" and "Acme Incorporated"
  are separate records; count them separately and note it if you see many. Do
  not silently collapse names that look similar - that is a judgement call the
  legal team owns, not you.
- **Blank counterparties do not count as a vendor.** Exclude them and say how
  many you excluded.
- **"In force" means executed, not expired, not terminated** - the same scope
  question as expirations. State which statuses you used.

Pair it with the total vendor agreement count so the ratio is visible: a few
hundred vendors behind a few thousand agreements is a useful thing to see.

## Choosing the chart

| Situation | Use | Not |
| --- | --- | --- |
| One number that matters | KPI tile | a chart with one bar |
| Parts of a whole, 2-6 categories | `donut` | a bar chart |
| Parts of a whole, 7+ categories | `bar` | a pie with 15 slices nobody can read |
| Ranking or comparing sizes | `bar` | `donut` |
| Change over time | `bar` for counts per month, `area` for a measure like hours | `donut` |
| Two things split across categories | `bar` with `stacked: true` | two separate charts |
| Fewer than ~8 records they need to read | `table` | any chart |
| A number you could not get | `empty` | a guess |

Roll anything past the top 10 into `[Other]` — `agiloft_group_by` does this with
`top`. Label slices with business words, never field names: "Non-Disclosure
Agreement", not `agreement_type`.

## Building the dashboard

1. Copy `assets/dashboard_template.html` to `contract-dashboard.html` in the
   outputs folder.
2. **Edit only the `DATA` block at the bottom.** Everything above it is the
   chart engine — leave it alone.
3. Call the Artifact tool on that path. `favicon: "📊"`, title
   `Contract Dashboards`.
4. To update: edit the same file, call Artifact on the same path. Same path,
   same URL. Never create a second dashboard in one conversation.

Card types: `donut`, `pie`, `bar` (add `stacked: true`), `area`, `table`,
`links`, `empty`. Cards take `span: 2` or `span: 3` across the three-column
grid. KPI tiles go in `tiles` with `tone` of `teal`, `purple` or `red`.

### Nothing on the page pretends to be interactive

The dashboard is a report, not an application. Everything on it is either real or
plainly inert — never something that looks clickable and is not.

- **Never invent a link.** A `links` card item renders as an anchor only when you
  supply a real `https://` URL. Without one it renders as plain grey text, which
  is correct. Do not add a `url` you have not seen.
- **Do not reproduce Agiloft's hotlinks as links.** "Create a Contract Request",
  "NDA Self-Service" and the rest are buttons inside Agiloft's own interface. You
  do not have their URLs. Either omit the card, or list the labels as plain text
  so people know where to go once they are in Agiloft.
- **Agiloft's own dashboard URLs are safe to link** if you have them - they take
  the form `https://<host>/ui/-k/m/home/<Dashboard+Name>`. Only use a URL you
  have actually seen, never one you assembled from a guess at the host.
- **Card titles are headings, not links.** Agiloft styles them blue and
  underlined; ours do not, because ours do not drill down.
- **Do not promise interaction you cannot deliver** — no "click a segment to
  drill down", no "click here to count records". If someone wants to drill in,
  they ask you and you rebuild the panel.

If a panel would genuinely be more useful as a live Agiloft view, say so in one
line and name the dashboard. Do not fake the link.

### Accuracy rules

- **Every figure comes from a tool call in this conversation.** The template
  ships with sample numbers from a screenshot. Replace all of them. Shipping the
  sample data to a user is a failure, not a shortcut. (The current template ships empty; the rule still stands for any older copy.)
- **A panel you have no data for gets `type: "empty"`, not a guess.**
- **Every panel carries a `source`.** Filter in plain words, record count, and
  the Agiloft widget it reconciles against when one exists. A panel without one
  is unfinished.
- Set `meta` honestly — host, KB, which account, when it was checked, how many
  records the figures rest on. That is what makes a wrong number traceable.
- Round averages to whole hours. Nobody needs 327.4.
- Do not mix filters silently. If a tile counts all contracts and a chart counts
  only 2026 contracts, say which is which in the labels.

