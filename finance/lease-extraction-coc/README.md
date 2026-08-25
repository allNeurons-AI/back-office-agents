# Change of Control (CoC) Lease Extraction Skill

A Claude Skill that reads a commercial lease package — the original lease plus every amendment, rider, and exhibit — and turns it into a structured Excel summary of every **Change of Control (CoC)** obligation buried inside it: consent requirements, recapture rights, termination triggers, "deemed assignment" clauses, public-company carve-outs, permitted transfers, fees, and notice requirements.

Built by **allNeurons** for use with [Claude Skills](https://www.claude.com) (Cowork, Claude apps, and Claude Code with Skills enabled).

---

## About

Any Change of Control event — an M&A deal, merger, restructuring, take-private, or change in ultimate ownership — can quietly trigger obligations buried inside a company's commercial leases. Finding these usually means manually working through every lease in a portfolio (often several amendments per property, each running 50+ pages) and compiling every CoC-related risk into a report before a transaction can proceed. Miss one clause, and an unexpected consent requirement, recapture right, or termination trigger can surface mid-deal.

This skill automates that first pass. Upload a lease package — a single lease or a full portfolio, each with all its amendments — and the skill:

1. Reads every document in the package (original lease, amendments, riders, exhibits, guaranties).
2. Identifies every clause relevant to a Change of Control: who needs to consent, on what standard, what counts as a "change of control" under the lease, what transfers are pre-permitted, what happens if the tenant doesn't comply, and more.
3. Produces a single Excel workbook — one row per lease package — with **20 standardized columns** covering every CoC-relevant term, plus a narrative "Key Issues / Comments" column flagging the risks that matter most.

In testing, the skill reviewed 5 lease packages in under 5 minutes (vs. 2–3 hours of manual review for the same packages), and improved extraction accuracy on these terms from 47% to 86% compared to asking Claude the same question with a generic prompt — with the biggest gains on the hardest clauses, like consent-to-transfer and take-private provisions.

## Who is this for

- **In-house counsel / General Counsel** preparing for a Change of Control event (M&A, merger, restructuring, take-private) who need to know what their lease portfolio exposes them to.
- **M&A and transaction legal teams** running lease diligence across a portfolio of properties.
- **Legal operations and legal clerks** who need a consistent, structured first-pass CoC abstract before attorney review.
- **CRE / real estate counsel** managing multi-property, multi-amendment lease portfolios who need a fast way to compare CoC terms across leases.

This skill is scoped specifically to **Change of Control / transfer-risk review** — it is not a general-purpose lease abstraction tool.

## How to use

**1. Attach your lease files and run the skill**

Drop the lease PDF(s) into a new chat and run `/coc-lease-extraction`.

<img width="1250" height="700" alt="usage-01-attach-and-run" src="https://github.com/user-attachments/assets/a20026f9-766a-4296-89f1-ab5550747632" />


**2. The skill asks a clarifying question when it needs one**

If the skill reads multiple, unrelated lease packages, it pauses and asks which perspective to use for the "Reviewing Party" and "Key Issues" framing — with quick-select options so you don't have to type a full answer.

<img width="1320" height="740" alt="usage-02-clarifying-question" src="https://github.com/user-attachments/assets/2771c64e-d6aa-44e2-939c-2165b23a8535" />


**3. Done — review and share the workbook**

The skill confirms what it produced (one workbook, 20 columns, one row per lease package) and shares the finished `.xlsx` file in the chat.

<img width="620" height="600" alt="output-04-completion-summary" src="https://github.com/user-attachments/assets/9fefe9b1-437c-4200-93fd-833a8880d91a" />


## Sample output

The skill produces a workbook (`CoC_Lease_Extraction.xlsx`, sheet **`CoC Extraction`**) titled **"Commercial Lease Change of Control Key-Terms Extraction"**, with one row per lease package and the following 20 columns:

<img width="1320" height="350" alt="output-01-columns-overview" src="https://github.com/user-attachments/assets/38cf111a-2b23-493a-b243-ea7874453f27" />


<img width="1300" height="350" alt="output-02-columns-consent-transfer" src="https://github.com/user-attachments/assets/65347f67-4b25-4405-93bb-c5754d1f1e85" />


<img width="1920" height="350" alt="output-03-columns-financial-issues" src="https://github.com/user-attachments/assets/aabffbb2-118f-4ff2-bde9-ba354d710d37" />



| # | Column | What it captures |
|---|--------|-------------------|
| 1 | Lease ID / Store No. | Internal identifier for the lease/property |
| 2 | Lease Description | The lease and every amendment, rider, and exhibit reviewed, with dates |
| 3 | Store / Property Name | Property address and/or store identifier |
| 4 | Landlord | Named landlord entity |
| 5 | Landlord Parent | Ultimate/parent landlord entity, if disclosed |
| 6 | Lease Expiry Date | Current expiration date, including any extension options exercised |
| 7 | Reviewing Party | The perspective the abstract is written from (Tenant or Landlord) |
| 8 | Definition of Change of Control | How the lease defines a "Change of Control" event for the tenant (and/or landlord) |
| 9 | Consent Required? | Whether landlord/tenant consent is required for a CoC event (e.g., Conditional, Not Required) |
| 10 | Consent Standard | The standard governing consent (e.g., "not unreasonably withheld, conditioned, or delayed") |
| 11 | Public Company Exception | Whether transfers of stock in a publicly traded parent are carved out of the consent requirement |
| 12 | Permitted Transfers / Affiliate Transfers | Transfers that are pre-approved without consent (affiliate transfers, qualifying M&A, etc.) and any conditions attached |
| 13 | Notice Required? | Whether and when the landlord/tenant must be notified of a CoC event |
| 14 | Fees | Transfer, assignment, or review fees triggered by a CoC event |
| 15 | Financial Conditions / Successor Requirements | Net worth, creditworthiness, or other financial tests a successor must meet |
| 16 | Other Conditions to Transfer | Additional conditions attached to a Permitted Transfer (timing, documentation, etc.) |
| 17 | Rent Escalation / Economic Impact | Rent increases, percentage-rent resets, or other economic terms triggered by a CoC event |
| 18 | Termination or Recapture Rights | Landlord's (or tenant's) right to terminate or recapture the premises in connection with a CoC event |
| 19 | Unauthorized Transfer = Default? | Whether an unauthorized CoC event is automatically a default, and what the landlord can do about it |
| 20 | Key Issues / Comments | Narrative summary of the risks that matter most for this lease, in plain language |

## Sample data file

The `sample-data/` folder in this repo includes example lease packages you can use to try the skill out before running it on your own portfolio — for example, a multi-document office lease (original lease plus several amendments and an office space rider) and a single-document retail lease agreement, matching the packages used in the demo above.

> Add your own lease PDFs anywhere in the chat and run `/coc-lease-extraction` the same way — the skill works on any commercial lease package, not just the samples.

## How to install

1. In Claude, open **Customize → Skills**.
2. Click the **+** button next to "Skills" and choose **Upload a skill**.

<img width="1200" height="750" alt="install-01-upload-menu" src="https://github.com/user-attachments/assets/b3896c4f-e113-4d73-bd08-38d5bf40ee9f" />


3. In the **Upload skill** dialog, drag and drop the `.skill` file from this repo (or click to browse and select it).

<img width="1020" height="950" alt="install-02-upload-dialog" src="https://github.com/user-attachments/assets/3cd36b27-8ec6-4b19-b6d3-1e0a55ccc462" />


4. Once uploaded, the skill appears in your **Personal skills** list as `coc-lease-extraction`, with the trigger set to **Slash command + auto**. It's ready to use immediately — no further configuration needed.

## How to use

1. Start a new chat (or task).
2. Attach the lease PDF(s) you want reviewed — a single lease or a full portfolio, each including all of its amendments, riders, and exhibits.
3. Type `/coc-lease-extraction` and send.
4. If the skill needs clarification (for example, which party's perspective to use, or how to treat multiple unrelated lease packages), it will ask a short question with quick-select options. Pick one, or reply with your own answer, or choose **Skip** to let the skill proceed on its best assumption.
5. The skill reads every document, builds the extraction, and shares a finished `.xlsx` workbook in the chat when it's done.
6. Open the workbook and review the **Key Issues / Comments** column first — it summarizes the risks that need attorney attention.

## FAQ

**What file types can I upload?**
Text-based Docx, PDFs work best. Each lease "package" can include the original lease plus any number of amendments, riders, exhibits, and guaranties — upload them all together so the skill can read them as one lease history.

**How many leases can I review at once?**
You can upload a single lease or an entire portfolio in one go. We recommend reviewing in batch of 5 for best results. The skill produces one row per lease package, all in the same workbook.

**Why did the skill ask me a question instead of just running?**
The skill asks a clarifying question when something in the documents is genuinely ambiguous — most commonly, when it can't tell which party (tenant or landlord) you want the abstract written from, or when it detects multiple unrelated lease packages in one upload. Answering (or picking **Skip**) lets it proceed with the right assumptions instead of guessing silently.

**Is this only for Change of Control review?**
Yes — this skill is scoped specifically to CoC, consent, recapture, and transfer-risk provisions. It is not intended as a general-purpose lease abstraction tool.

**Does this replace attorney review?**
No. The skill produces a structured first-pass summary to speed up diligence and flag the clauses that matter most — it does not provide legal advice, and all output should be reviewed by qualified counsel before being relied on in a transaction.

**Where does my lease data go?**
Your documents and the resulting workbook stay within your Claude conversation/working folder, the same as any other file you upload to Claude. allNeurons does not receive a copy of your lease documents.

**What Claude model does this run on?**
The skill is model-agnostic but was built and tested on Claude Sonnet 4.6.

## Requirements

- A Claude product with **Skills** support (e.g., Cowork, Claude apps, or Claude Code with Skills enabled).
- Lease documents in **PDF** format (text-based; scanned/image-only PDFs may reduce extraction quality).
- A spreadsheet application (Excel, Google Sheets, or similar) to open the `.xlsx` output.

## Uninstall

1. In Claude, open **Customize → Skills**.
2. Select **coc-lease-extraction** under Personal skills.
3. Click the **⋯** menu next to the toggle and choose **Remove** (or simply turn off the enable toggle to disable it without deleting).

---

*Questions, feedback, or ideas for the next legal-ops skill? Open an issue on this repo or reach out to allNeurons.*
