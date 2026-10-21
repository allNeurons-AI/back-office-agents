# Counting honestly, follow-ups and scope

Loaded at Step 4 (fetch and count) and whenever a follow-up arrives. Applies to every source. Tool names (`agiloft_count`, `agiloft_describe_table`) are the Agiloft build; for SharePoint use the counting rules in `references/source-sharepoint.md`.

## Counting honestly

This is where a demo goes wrong. Be strict.

**Exact whole-table totals are available.** This has been confirmed against the
live knowledgebase - counts matching Agiloft's own dashboard exactly (Agiloft source). So do
**not** refuse a "how many in total" question, and do not tell anyone to go look
in the source for it. Answer it.

**13-tool build** - `agiloft_count` returns `exact: true` when the source supplied
the total. When `false`, or when any tool reports `truncated: true`, the number
is a floor. Say "at least", once in chat and again in the tile's `note`.

**6-tool build** - if a select-style call reports a total alongside the records,
that total is exact and is what you quote. If it only hands back records, you are
counting rows you fetched, and the limit check below decides whether that count
means anything.

### The limit check - do this after every single fetch

**Compare the number of records returned against the `limit` you asked for.**

- Returned **fewer** than `limit` - you have them all. The count is exact. Use it.
- Returned **exactly** `limit` - there are more you did not see. **Raise the
  limit and fetch again** before that number goes anywhere.

This applies to every fetch, not just ones where you are "counting" - a chart
built from a capped fetch is just as wrong as a tile.

An expirations query sent with a limit of 500 that comes back with exactly 500
rows looks like an answer. It usually is not - it is the page size, and the real
figure can be several times larger. The tile is then wrong by that factor, the
monthly bars beneath it wrong in the same proportion, and nothing on screen
hints at a problem.

Raising the limit costs one extra call. Getting it wrong costs the credibility of
the whole dashboard.

If a count genuinely cannot be completed - the table is larger than you can page
through in reasonable time - say so plainly and give the filtered figure you can
stand behind. Do not put a truncated number in a tile; it reads as fact.

### Time series need a bounded window, not a big limit

**This one is a trap.** Fetching the newest 2,000 records and bucketing them by
month produces a chart that is not merely imprecise — it is *wrong*. The oldest
months in the window appear near-empty because the page ran out, so the chart
shows a fake upward trend.

Do it this way instead: **one query per month**, each filtered to that month's
date range, and use the count from each. If a month's result hits `limit`, that
month is a floor — say so rather than plotting it as fact.

Twelve small queries is correct. One big query sliced by month is not.

The same applies to any "over time" question. Bound the window in the filter,
never in the sort order.

**Field names are knowledgebase-specific.** If a query returns nothing and you
expected results, check the real field names — `agiloft_describe_table`, or read
one record — before concluding "none". Mention the correction only if it changes
the answer.

## Follow-ups

Most conversations are a chain, not one question. Keep the chat short across all
of it, and **update the existing dashboard rather than building a new one**.

| They say | What it means |
| --- | --- |
| "Why?" | They want the driver, not a restatement. Break the number down one level and give the biggest contributor |
| "Show me those" | They want the records. Put a `table` card on the dashboard, answer with the count |
| "Just the Acme ones" | Re-run with a counterparty filter. Say the new number only |
| "What about last quarter?" | Same query, different date window. Say the new number and whether it went up or down |
| "Is that good?" | You do not know their targets. Give the comparison you *can* make — last month, last year — and stop |
| "Can you send this to X?" | You cannot. Tell them the dashboard link is shareable from the artifact's share menu |

When a follow-up narrows the question, **change the dashboard to match** and say
so in three words: "Filtered to Acme." Do not leave a dashboard showing
company-wide figures while the chat discusses one vendor — that is how someone
screenshots the wrong number.

### One scope per dashboard

If they ask about a slice — one template, one vendor, one owner — **either filter
the whole dashboard to that slice, or answer in chat and leave the dashboard
alone.** Do not put a slice-specific table on top of company-wide tiles.

A caveat line saying "the tiles below are company-wide, not filtered" is honest
but does not fix it. The reader sees a table about one template sitting above a
tile reading a company-wide total and connects them. Pick one scope and make the
whole page obey it.

