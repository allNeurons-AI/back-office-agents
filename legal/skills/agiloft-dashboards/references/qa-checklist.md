# QA checklist: agiloft-dashboards

One row per check. Tiers: Block stops delivery; Flag is delivered and listed; Note goes in the report only.

| ID | Check | How to verify | Source of truth | Tier |
|----|-------|---------------|-----------------|------|
| Q1 | Every figure on the page and in the answer comes from a call in this conversation | List each figure and the call that produced it; none from the template or memory | Run trace | Block |
| Q2 | `meta.checked` is set (not "never"), `meta.instance` is not "not connected", and no template placeholder text ("No data fetched yet", "ships empty") remains | Search the published DATA block | assets/dashboard_template.html | Block |
| Q3 | All four tabs exist; a panel with no data is `empty` with a reason, not blank or dropped | Read the DATA block | references/dashboard-schema.md | Block |
| Q4 | Every card has a `source` with query and record count | Check each card | references/dashboard-schema.md | Block |
| Q5 | Header names the source, the account, check time, records and mapped columns; document sources also show documents read | Read `meta` | references/dashboard-schema.md | Block |
| Q6 | No write, upload, edit, move, rename or delete call was made on any source | Read the call trace | Section 9 read-only rule | Block |
| Q7 | Every fetch that returned exactly its limit was raised and refetched, or the figure is labelled "at least" | Compare each fetch's rows with its limit | references/counting.md | Block |
| Q8 | Documents read is at most `DOC_READ_CAP` unless CP3 was approved; extracted values are labelled "extracted from document" | Compare the count; read the labels | config.md | Block |
| Q9 | Figure reconciled with the source's own total or widget within `DIVERGENCE_FLAG_PCT`; if none exists the source line says "no independent total available" | Read the source line | Source's own total | Flag |
| Q10 | The chat answer leads with the answer, names the scope and source, and gives a conclusion not two percentages | Read the answer | references/answering-rules.md | Flag |
| Q11 | Statuses explained on first use; no record ids; money and dates in the house format | Read the answer | SKILL.md section 8 | Note |
| Q12 | Dates read from documents or text columns with two possible values were reported as ambiguous, not picked | Search for date fields in the output | references/source-sharepoint.md | Block |
| Q13 | No invented links; links carry `https://` URLs seen in the source | Check every `url` | SKILL.md section 8 | Block |
| Q14 | No personal data or document text beyond what the question needs appears in the output | Scan the output | Section 10 | Block |
| Q15 | The page was verified to render: DATA parses and every tab shows | Render it or re-read the published file | Artifact result | Flag |

## QA report format

Overall result and attempts used; one line per row (ID, result, evidence); unresolved flags; data freshness for the source.
