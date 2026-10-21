# Source: SharePoint (files, spreadsheets, lists and documents)

Loaded at Step 1 when the source is SharePoint or OneDrive. Read-only, like every source. Tools are the Microsoft 365 connector's: `sharepoint_folder_search`, `sharepoint_search`, `read_resource`, `get_me`. Config keys: `DOC_READ_CAP`, `DOC_PAGES_MAX`, `ROW_PAGE_LIMIT`.

## Never call these (read-only rule)

`sharepoint_upload_file`, `sharepoint_update_file`, `sharepoint_create_folder`, `sharepoint_copy_item`, `sharepoint_move_item`, `sharepoint_rename_item`, `sharepoint_delete_item`. If asked to change a file, say the skill is read-only and the person should do it in SharePoint.

## 1. Pin down exactly what is being read (CP1)

- A pasted SharePoint web link cannot be opened by `read_resource` (it takes `file:///` URIs, not `https://`). Resolve it: take the last folder name from the link, run `sharepoint_folder_search`, and compare each hit's `webUrl` path with the path in the link.
- **Folder names repeat.** A search for one folder name can return many folders with that name in different places. Never pick the newest or the first. Show the candidates as full paths and ask which, unless exactly one path matches the link. This is CP1.
- `sharepoint_search` looks across everything the signed-in account can reach, not only the folder you care about. Keep only results whose `webUrl` starts with the confirmed folder's path, and say how many were dropped.
- List the confirmed folder with `read_resource` on the folder URI. That listing, not search, is the record count for a folder source.

## 2. Work out what kind of source it is

Take an inventory first: number of files, count per extension, oldest and newest modified date, distinct authors. Say it in one line. Then:

| What is in the location | Records are | How to read | Counts are |
|---|---|---|---|
| One Excel or CSV tracker | Rows | `read_resource` on the file. CSV pages by lines with the header repeated; Excel workbook reads ignore page numbers | Exact once every row is read |
| Several spreadsheets with the same columns | Rows across all files | Read each; confirm the columns match; say which file each figure came from | Exact once all read |
| A SharePoint List | Items | Read the list through the connector if it exposes one; otherwise ask for an export and treat it as a spreadsheet | Exact when the connector returns a total |
| Documents (.docx, .pdf, .pptx, .txt) | One record per file | Metadata always; text by `read_resource`, within the caps below | Files listed are exact; extracted fields are a sample of what was read |
| A mix | Say which part you are using | Pick one record type per dashboard | Per type |

If no column or extracted field can be mapped to status, agreement type, a date or a counterparty, the file is not a contract tracker (for example a test-results sheet). Say so in one sentence, show what the file is, and ask what the person wants (G6); do not build four empty tabs.

Do not guess the type from the folder name. If a folder holds both a tracker and the documents it describes, ask which is the source of truth (CP1); one source per dashboard.

## 3. Spreadsheets: discover before you count

1. List the sheets. The workbook read opens with the sheet count and a heading per sheet (`## Sheet: name - rows x columns`). If there are several, ask which holds the records unless one is obviously a data table; a summary sheet and per-item detail sheets in one workbook are common, and they are different record types.
2. Find the header row. It is not always row 1: a title or banner row often sits above it. Skip title rows, and exclude total or subtotal rows and blank rows, saying how many were excluded.
3. For each column report: name, type (text, number, date, choice), share blank, and for text columns with 3 to 12 distinct values, the values and counts. Those are the choice fields (status, agreement type, region) and become panels.
4. Dates stored as text (for example `03/04/2026`) are ambiguous between day-first and month-first. If both readings are possible for every row, ask; never choose silently.
5. **A workbook read can be very large** (one real workbook returned about 90,000 characters). When the tool saves the output to a file instead of returning it, read that file in chunks with the shell, record rows read against the rows the sheet heading states, and never paste the whole thing into chat. A mismatch is G1.
6. Use cached cell values. If a formula cell has no cached value, tag it "not calculated" rather than computing it.

## 4. Documents: read, extract, label, cap

- **Cap.** Read at most `DOC_READ_CAP` documents per run and at most `DOC_PAGES_MAX` pages of each. Past the cap is CP3: ask before reading more. Say on the page how many were read of how many exist. Reading is slow and the text of a few documents says nothing certain about the rest.
- **Search is not reading.** `sharepoint_search` returns a short snippet (`isPartialContent: true`). Use it to find files, never to assert what a document says. Do not count records from search results: it pages 50 at a time and is relevance-ranked. If you must, page with `offset` until a page returns fewer than the limit and compare with `totalResultCount`.
- **Placeholders are not values.** Text such as `[To Be Completed by Recipient]` or a blank signature line means the field is not filled in. Report "party not completed", never a guess.
- **Fields you may extract, only when the text states them:** document type, parties, effective date, end or expiry date, term and auto-renew, governing law, signature state. Each extracted value carries the label "extracted from document" wherever it is shown.
- **Dates.** Contracts often carry several: document date, effective date, "date of last signature", end date. If more than one candidate exists for a field, report the field as ambiguous and show the candidates. Do not pick.
- **Status and owner are not in a document unless it says so.** A signature block with a name is not proof of execution. Mark status "not tracked in these documents" and leave the status-based panels empty. File author is the person who saved the file, not the contract owner; do not present it as the owner.
- **Look-alike files.** Names such as `Copy`, `Copyy`, `- Web`, dates in the name or repeated titles suggest duplicates or versions. Count files as listed, report how many look like duplicates, and never remove them silently. Whether they are the same contract is the person's call.
- **Files you cannot read** (scanned images with no text, password-protected, unsupported type): list them as "not readable" with a count. Never drop them from the total.

## 5. Map the fields (CP2)

Propose a mapping from the columns or extracted fields to these roles, with the evidence for each: id, title, counterparty, agreement type, status, owner, created date, effective date, end date, value, days in current status.

- Group status values into **in force**, **in flight**, **closed** by meaning, not spelling. Flag ambiguous values rather than forcing them.
- A role with no column is "not mapped" and its panels are `empty` with the reason. Never fill one by inference.
- Show the mapping as a short table and wait for the person's yes (CP2). Put the confirmed mapping in the dashboard header (`meta.mappedColumns`).

## 6. Which panels each source can fill

| Dashboard | Needs | If it is missing |
|---|---|---|
| Contract Reporting | status, agreement type or equivalent, a date | Counts by file type and by modified month are always possible and must say they are about files, not contracts |
| Contract Requester | an owner or requester column | `empty`: "no owner column" |
| Cycle Times | days in current status, or a status-change date | `empty`. Do not use file modified date as a stand-in unless asked, and then label it "days since file last modified" |
| Vendor Management | counterparty and an end date | Count distinct counterparties only when the column or extraction exists |

A documents-only folder with no tracker usually fills Reporting partly and leaves the rest `empty`. Say so in one line in chat. That is a correct result.

## 7. Whose view this is

The connector is the signed-in account (`get_me`); put the name in the dashboard header. It sees only what that account can open. Two people can get different counts for the same folder. Zero hits can mean "no access", not "none exist": say what you searched and that the account's access may be narrower.

## 8. Freshness

State the newest modified date among the files used. If the person gave a period and the newest file predates its end, fire G1 and ask whether to continue with the older data.

## 9. When something goes wrong

| What happened | What to say |
|---|---|
| Access denied or not found | "I can't open that location with this account. It may have been moved or not shared with you." |
| Connector not available | "The SharePoint connector isn't enabled for this chat. Enable it in connector settings, or attach the file here and I'll work from that." Then use manual mode on an attached file. |
| File too large or too slow | Read it in pages and say so, or narrow to a sheet, folder or date range. |
| Same error twice | Stop and say what failed and what you tried. |
