# Design record: agiloft-dashboards

## The brief (summary)
Improve the existing Agiloft dashboards skill so the same plain-language answers and four-tab dashboards can be built from other sources, starting with SharePoint files of any format (including .docx), not only Agiloft. Agiloft stays supported and unchanged in behaviour. Requested by Rajan, 2026-10-15.

## Decisions and reasons
| Decision | Reason | Decided by |
|----------|--------|------------|
| Improve the existing skill, keep the name | Existing shortcuts keep working; the description now says it covers other sources | Rajan, 2026-10-15 |
| Split the 1,000-line SKILL.md into a source-agnostic core and on-demand reference files | The original was twice the 500-line cap; loading only the chosen source's rules keeps context small | Design CP3, 2026-10-15 |
| Agiloft rules moved verbatim to references/source-agiloft.md | Behaviour must not change for Agiloft users | Design CP3 |
| One source per dashboard | Every figure has one named origin; joins hide where a number came from | Rajan, 2026-10-15 |
| Map columns, keep the four tabs, panels without data are `empty` | Consistent layout between runs; no invented figures | Rajan, 2026-10-15 |
| Discover, propose and confirm the status grouping (CP2) | Same rule as before: ambiguous values are flagged, never forced | Rajan, 2026-10-15 |
| Documents read and extracted, capped at 50, labelled, past the cap asks (CP3) | Reading is slow and a few documents say nothing about the rest | Rajan, 2026-10-15 |
| Read-only on every source | A write on a contract system or a shared folder is hard to undo | Rajan, 2026-10-15 |
| assets/dashboard_template.html | Original template restored from the user (2026-10-15); generalised only for source name, footer fields and empty messages | Rajan |
| Failure policy: do not publish | The audience acts on these numbers | Design CP3 |

## Assumptions the user accepted
- Version moves to 2.0 because the steps changed.
- Divergence tolerance 5% flag and 10% block, and a 50-document read cap, as proposed.
- The sample SharePoint folder (NDA test files) is used only to test discovery; no file contents are copied into the skill.
- Hours-in-status remains absent for Agiloft; the ageing field is in days (carried over from v1.0).

## Admin-dependent practices and the skill-level equivalents used
| Practice | Equivalent |
|----------|------------|
| Connectors | Step 1 check, fallback to an attached export, manual mode |
| Rate and spend limits | `TOOL_CALLS_PER_STEP`, `DOC_READ_CAP`, `DOC_PAGES_MAX`, `ROW_PAGE_LIMIT`, `REBUILDS_MAX` |
| Access control | Read-only rule; the header says whose view the figures are |
| Dashboards and monitoring | Run log per run |

## Test record (2026-10-15)
- A public online SharePoint document could not be used: the only public SharePoint pages found were blocked from automated fetching (robots rules), and the skill must not work around that. The person's own sample folder was used instead, read-only through the Microsoft 365 connector, 2 documents opened and 1 workbook read.
- Findings fed back into the skill: a folder-name search matched 17 files across five sibling folders, only 2 of them in the confirmed "Original Files" folder, so counts must come from the folder listing, not search (section 1); the sample folder mixes .docx files with one .xlsx of test results that is not a contract tracker (section 2 non-tracker rule); the workbook has 11 sheets, a banner row above the header and a read of about 90,000 characters (section 3); a document with "[To Be Completed by Recipient]" in the party field must be reported as not completed (section 4); one of the documents showed a single date and no end date, so expirations cannot be extracted from it.

## Known limits
- Choice fields cannot be filtered through the Agiloft connector build used for v1.0; panels that need it are reported as a connector limit (carried over).
- Document extraction is a sample bounded by `DOC_READ_CAP`; it cannot establish status or owner.
- The SharePoint web-link form cannot be opened directly; it is resolved by folder search and path comparison, and repeated folder names need a person's choice.
- The dashboard template was rebuilt from the schema in the v1.0 text, so its look may differ slightly from the original.

## Open items
- None blocking. The master copy location is unset; the owner receives the updated skill as a file.
