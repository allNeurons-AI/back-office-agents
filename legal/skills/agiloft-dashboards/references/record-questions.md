# Questions about one contract

Loaded when the question is about one record, one counterparty or one document. Tool names in brackets are Agiloft and SharePoint equivalents; use whichever matches the source. For a SharePoint document source, the document itself is the record: read it with `read_resource` and answer only from what it says.

## Questions about one contract

Half of what people ask is not a number. These are record-level questions and
they need a different approach — find the record, read it, answer from what is
actually in it.

The pattern is always: find the candidate records (Agiloft: `agiloft_select`; SharePoint: search and list the folder) → read the full record (Agiloft: `agiloft_read`; SharePoint: `read_resource`) for
the full record → answer from fields you can see. Never answer these from
memory, inference, or what the agreement type implies.

### "Does ABC Inc already have an NDA with us?"

**Getting this wrong is worse than not answering.** A false "no" leads someone
to share confidential information with no NDA in place. A careless "yes" leads
them to rely on one that has expired.

1. Search the counterparty **loosely** — `ABC` before `ABC Inc`. Legal entity
   names in the source rarely match how people say them: "ABC Inc", "ABC Inc.",
   "ABC Incorporated", "ABC Holdings Ltd" are different records.
2. Use full-text search (Agiloft: `agiloft_search`; SharePoint: `sharepoint_search`) as well as a field filter. Do not conclude "no" off one
   exact-match query.
3. Filter to the NDA agreement types you discovered for this knowledgebase -
   anything matching non-disclosure, NDA, or confidentiality. Deployments often
   have several variants.
4. **Split the hits back out by counterparty before counting.** This is the step
   that makes loose search safe. List the distinct counterparty values the search
   returned, then decide which are the same company and which are not:
   - Same company: case and spacing differences - `ABC Inc`, `abc inc `, `ABC INC`.
   - **Different company:** a different legal suffix or word - `ABC Holdings`
     alongside `ABC Systems`, `ABC Inc` alongside `ABC Incorporated`.

   Never report one total across the group. Answer for the entity asked about,
   and mention the others separately: *"Brightline Systems has 30 NDAs in force.
   There are also 39 filed under Brightline Holdings, which I've treated as a
   different entity - tell me if they're the same company."*

   A loose search that is counted as one company is how a false "yes" happens:
   the entity asked about has nothing in force, a similarly-named one does, and
   the answer reads as cover that doesn't exist.
5. **Check status and end date, not just existence.** An executed NDA that ended
   last year is not cover.

Answer shape:

- Found and live → "Yes — executed 12 March 2025, runs to 12 March 2027."
- Found but not executed → "There's an NDA with ABC Inc but it's still Pending
  Counterparty Signature, so it isn't in force yet."
- Found but expired → "Yes, but it expired 4 June 2026."
- Nothing found → "I can't find an NDA with ABC Inc. I searched *ABC* across
  NDA types — worth checking the exact legal entity name, since they may be on
  file under a different one."

That last phrasing matters. Say what you searched, so a wrong entity name shows
itself rather than reading as a confirmed absence.

### "What are the terms of this agreement with X?"

Find the record, read it in full, and report the fields that are actually
populated. **How much you can answer depends on how the knowledgebase is set
up** - see "What you can get out of an attachment" below. Establish which of the
three levels applies before deciding this cannot be answered.

- **AI-extracted term fields present and populated** → answer from them, and say
  they were extracted from the document rather than typed by a person.
- **Only record metadata** → report parties, dates, value, renewal, notice
  period, owner, status, and say the commercial terms are in the signed file.
- **Nothing relevant populated** → say so plainly.

**Always say what you read from.** "From the contract record" and "from terms
extracted out of the signed PDF" are different claims, and someone acting on a
liability cap needs to know which one they got.

Never infer a term from the agreement type. A Vendor Agreement does not
automatically have 30-day payment terms.

### What you can get out of an attachment

The signed document is a file on the record, not a set of columns. There are
three levels of access, and knowledgebases differ - check, do not assume.

| Level | What you get | How to tell |
| --- | --- | --- |
| **Metadata** | Filename, size, type. Always available. | An attachment field on the record; an attachment-info call if the connector exposes it; for SharePoint the file's own metadata |
| **Full-text search** | Which records contain a phrase - matching, not reading | Search on `-TEXT-` rather than a named field. Covers .doc, .docx, .txt and text-based PDFs. Files scanned as images are not indexed unless OCR'd |
| **AI-extracted fields** | Actual term values, queryable like any other field | Ordinary fields on the contract record - governing law, payment terms, liability cap, auto-renew, notice period - populated by the source's own extraction (Agiloft: Extract Key Terms) |

**Look for the third level during discovery.** When you read the first contract
record, check for fields that look like extracted terms. If they exist and carry
values, the terms question is answerable and the answer comes from fields, not
guesswork.

**Full-text search finds, it does not read.** `-TEXT-` search tells you a
contract contains the phrase "auto-renewal"; it does not tell you what the
clause says. Use it to locate records, never to assert what a document
provides. And if a record has several attachments, a match returns the record
without saying which file matched.

**Label AI-extracted values as extracted.** They were produced by a model
reading a PDF, not typed by a lawyer. That provenance belongs in the answer:
"Payment terms are Net 45 and the liability cap is $2M - both extracted from the
signed PDF by the source's key-terms extraction, so worth confirming against the
document before you rely on them."

**Never open, transcribe or summarise an attachment you have not actually
read.** If all you have is the filename, you have the filename.

### "When does this agreement terminate?"

Read the contract end date. One sentence.

Watch for two traps: a blank end date means no fixed end, **not** "no data" —
say "it has no end date set; it's open-ended." And if auto-renew is on, say so,
because "terminates 30 June" is misleading when it silently renews: "Ends 30
June 2027, but it auto-renews unless cancelled 60 days before."

### "What does this contract do for us?" / "Summarize this contract"

The honest answer depends on what you can reach - the three levels above.

- **If AI-extracted term fields are populated**, use them and say where they came
  from: "A Vendor Agreement with NXGN, signed 30 September 2026, running to 29
  September 2027. Payment terms Net 45, liability capped at $2M, governing law
  New York - those three were extracted from the signed PDF by the source rather
  than entered by hand, so confirm them against the document before relying on
  them."
- **If you can read the document text itself**, summarize it: what each side
  provides, term, value, key obligations, how it ends.
- **If you only have the record fields**, say that plainly and summarize those:
  "A Vendor Agreement with NXGN, signed 30 September 2026, running to 29
  September 2027, owned by D. Rossi. That is everything the contract record
  holds - the scope and commercial terms are in the signed document, which this
  knowledgebase does not extract into fields."

**Do not write a plausible-sounding summary of a contract you have not read.**
This is the single most dangerous thing in this skill: a confident paragraph
about obligations, invented from an agreement type and a counterparty name, is
worse than useless because it reads exactly like a real summary.

If someone asks about liability, indemnity, termination rights or payment terms
and you only have record fields, say the record does not cover it.

