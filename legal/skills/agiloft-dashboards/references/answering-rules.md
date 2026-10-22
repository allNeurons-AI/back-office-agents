# Answering rules

Loaded at Step 5 (answer) and Step 6 (source lines). Source-agnostic: "the source" means Agiloft, a SharePoint file or list, or any connected system. Where a rule names an Agiloft field or tool, `references/source-agiloft.md` is the Agiloft detail; for other sources the same rule applies with that source's own names.

## Rule one: complete answers, no padding

The audience is contract requesters, paralegals and business leads. Answer them
properly - then stop.

**Write for someone who has never opened the source system.** A salesperson, a finance
lead, a business requester. They know their own deal; they do not know your
status names, and they are not going to work anything out from percentages.

**Four things make an answer good. Length is not one of them.**

1. **Concrete.** A specific figure, name or date - never "several", "a number
   of", "relatively high".
2. **To the point.** Every clause is doing a job. If a clause is not carrying
   information, delete it.
3. **Reasoned.** Say why the figure is what it is, or what it means. A number
   with no interpretation is data, not an answer.
4. **Sourced.** Say what it was counted from, in the answer, in a few words.

Write however many sentences those four things take - no more, no fewer. A
simple count is one sentence. A bottleneck question is three or four, because
the reasoning is the answer. Never pad a short answer to look thorough; never
compress a real finding into a fragment.

### The source belongs in the answer, not only on the dashboard

Every figure names **where in the source it came from**: the table, the fields it
was filtered on, and the values used. Not "from the system" - that is not a source,
it is the name of the system. Someone should be able to reproduce your number in
the source from what you told them.

Use the real field names you discovered, not your paraphrase of them:

- "...from the Contract table, counting every record - 1,722 in total."
- "...Contract table, `end_date` between today and 24 November with `status` =
  Executed. That matches what the source's own expiring widget counts."
- "...Contract table, `agreement_type` in the two confidentiality types, searched
  on `counterparty_legal_name`."
- "...from `days_in_current_status` on the Contract table - that is time at the
  current step, not total time since the contract was raised."
- "...Invoice table, joined on contract number."

Keep it to a clause. It goes at the end of the answer, after the finding, and it
is the one part that may use the source's own field names rather than plain English
- because its whole job is to be checkable against the system.

When two people get different numbers for the same question, the filter is
always why. Naming it up front is what stops that argument.

### Say the conclusion, not the arithmetic

Never hand someone two percentages and let them work out which is bigger. Do the
comparison yourself and report what it means.

| Do not write | Write |
| --- | --- |
| "Intake holds 18% of the backlog against 18% of the in-flight population." | "Intake has the most stuck contracts, but only because it is the busiest stage - it is not actually slower than the others." |
| "969 in flight, 56% of 1,722 records." | "969 contracts are in progress - more than half of everything on file." |
| "Median 168 days in current status." | "Contracts are sitting about five and a half months at their current step." |
| "87 in force, 104 unsigned, 59 closed, total 250." | "87 signed contracts expire in the next 90 days. The other 163 records in that window were never signed or are already cancelled, so nobody has to renew them." |

- **Explain a status the first time you use it.** "Awaiting Countersignature -
  waiting on the other side to sign." They do not know your workflow names.
- **Say what it means for them.** "Nobody needs to renew those." "That one is
  not cover yet." A number with no consequence attached is trivia.
- **Use scale where scale is the point** - "more than half", "about five
  months" - and give the raw figure too when someone would act on it.

### Worked examples

| Too thin | Padded | Right |
| --- | --- | --- |
| "142." | "Great question! Let me look into the contracts table for you. Based on the data returned, it appears that there are currently 142 contracts in an in-flight status, which represents approximately..." | "142 contracts are in progress - drafted, in review, or waiting for a signature. Most are sitting with Legal Review. From the Contract table, `status` in the ten in-flight values." |
| "With Counterparty." | A six-bullet breakdown restating every number on the dashboard | "Contracts are getting stuck waiting on the other side to sign - 239 have been there over three months. That step holds far more of the old backlog than its share of the workload, so it is genuinely slow rather than just busy. From `days_in_current_status` on the Contract table - time at the current step, not total age." |
| "Yes." | "I searched extensively across multiple agreement types and can confirm that..." | "Yes - Acme Inc has three NDAs in force, the newest running to 29 November 2027, so you are covered. Two more are drafted but unsigned and do not count. Contract table, `agreement_type` in the two confidentiality types, matched loosely on `counterparty_legal_name`." |

**Cut these, always:**

- Preamble. No "I'll check", "Let me look", "Great question".
- Sign-offs and offers. No "Let me know if you'd like more detail!"
- Narrating the method. Which tool you called is not the answer. Naming the
  scope is - "counted across all contract records" is a source; "I ran a select
  on the contract table with a filter on end_date" is narration.
- Reciting the dashboard. Name what is on it; do not read it out.

**Keep these, always:**

- Lead with the answer. The first few words carry the figure or the name.
- Money as `$240K` / `$1.2M`. Dates as `12 March`. No record IDs unless asked.
- The scope of any number that has more than one defensible scope.
- **Never estimate or infer a figure.** If the source did not return it, say
  "the source doesn't track that". A confidently wrong number in front of a
  leadership audience is the failure mode that matters.
- An empty result is a real answer, and needs its source too: "Nothing matches -
  Contract table, `end_date` in that window, all agreement types and all statuses."

## Rule two: answer the question they asked

Read the first word. It decides what comes back.

| They ask | They want | Do not give them |
| --- | --- | --- |
| "**How many** agreements expire in 90 days?" | A number | A list |
| "**What are** the agreements expiring in 90 days?" | The records, as a table | A count and a breakdown |
| "**Which** vendors are affected?" | Names | A total |
| "**Show me** the expiring contracts" | The records | A summary |
| "**Is there** an NDA with ABC?" | Yes or no, plus dates | A count of NDAs |
| "**What's** slowing us down?" | A stage name | A count of old contracts |
| "**Why** is this slow?" | The reason or the stage | A restatement of the number |

"What are" and "which" and "show me" ask for **things**, not totals. Put the
records on the dashboard as a `table` card and answer with the shape of it:
"422 agreements are ending, mostly vendor contracts. The 20 closest are on the
dashboard - the first runs out on 3 September. Contract table, `end_date` within
90 days, all statuses."

A count is a fine *addition* to a list. It is not a substitute for one.

## Rule three: every answer shows where it came from

A number nobody can check is a number nobody should trust. Two mechanisms, and
neither of them makes the chat longer.

### On the dashboard: a source line under every panel

Every card carries a `source` object. The renderer prints it as a small line
beneath the panel.

```
source: {
  query:       "contract end date 26 Aug - 24 Nov 2026, all statuses",
  records:     "422 records",
  widget:      "Upcoming Expiring Contracts 30-60-90 - All Contracts",
  widgetValue: "391",
  differs:     "we include 19 unsigned and 12 cancelled or terminated"
}
```

- `query` — the filter in plain words: which field, which range, which statuses.
  Enough that someone could rebuild it in the source.
- `records` — how many records the figure rests on.
- `widget` / `widgetValue` / `differs` — only when one of the source's own widgets or totals covers the
  same question. See below.

A panel with no `source` is unfinished.

### In the chat: name the scope, not the method

Say what a figure covers. Do not say how you got it.

When your number would differ from what someone sees on their own source
screen, name the difference in the answer itself - that is part of a complete
answer, not an aside:

- "391 signed contracts run out in the next 90 days - that matches the expiring
  widget. There are 31 more records with an end date in that window,
  but they were never signed or have already been cancelled, so they are not
  renewals anyone has to chase."
- Not: "I ran a select on the contract table filtering end_date between..."
- Not: "422 records, of which 391 are Executed status (92.7%)."

The scope belongs in the sentence. The query belongs in the source line on the
panel, where someone who wants to check it will look.

