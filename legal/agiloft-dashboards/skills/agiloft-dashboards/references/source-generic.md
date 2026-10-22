# Source: any other connected system, or an attached file

Loaded at Step 1 when the source is neither Agiloft nor SharePoint: a CRM, a database, another contract tool, or a file the person attached to the chat. The goal is the same four dashboards from one source, with the same honesty rules.

1. **Find the tools.** List what the session offers for the system. Prefer read-only tools with filters, counts and group-bys over ones that return raw rows.
2. **Read-only.** Never call a tool whose name or description creates, updates, deletes, sends, uploads or moves anything. If the only way to get the data is a tool that also writes, stop and say so (G6).
3. **Discover.** Read one record to learn the real field names; page the table once to learn the distinct values of each choice field. Apply the limit check from `references/counting.md` on every fetch.
4. **Map (CP2).** Same roles and same status grouping as `references/source-sharepoint.md` section 5. The person confirms before you build.
5. **Count.** Exact when the system returns a total or you have paged to the end. Otherwise it is a floor: say "at least" in chat and in the tile note.
6. **Attached file.** Treat it as a spreadsheet source (`references/source-sharepoint.md` section 3). Read it in the workspace with a short script, report the row count you read, and say it is the file as attached, not the live system.
7. **Whose view.** Say which account or credential the connector uses if the session tells you. Otherwise say the figures reflect the connector's permissions.
8. **No reconciliation figure?** Many systems have no dashboard of their own to compare with. Then the source line says "no independent total available" and QA row Q9 flags it instead of passing it.
9. **Connector missing.** Say which system and what you need, and ask for an attached export with the fields from the mapping roles.
