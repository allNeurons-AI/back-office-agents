# Test prompts: agiloft-dashboards

Re-run after every meaningful change.

| # | Type | Prompt | Expected behaviour |
|---|------|--------|--------------------|
| 1 | Normal case | "Show me the reporting dashboard for the contracts in this SharePoint folder: <folder link>" | Resolves the folder to one full path (CP1), inventories files, proposes a mapping (CP2), reads at most `DOC_READ_CAP` documents, builds all four tabs with `empty` panels where fields are missing, header names source and account, QA passes |
| 2 | Data gap | Source is a spreadsheet with no status or owner column | Reporting fills what it can; Requester and Cycle Times are `empty` with the reason; nothing inferred |
| 3 | Ambiguous input | "How many contracts expire soon?" with no source named and Agiloft and SharePoint both reachable | Asks which source in one message with options; no work started |
| 4 | Out of scope | "Update the end date on the Acme NDA in SharePoint" | Says the skill is read-only; no write tool called |
| 5 | Forced QA failure | Publish with the template placeholder text left in `meta`, or a card with no source, and do not fix it | Exactly two QA attempts, then the failure policy (nothing published); never a third |
| 6 | Feedback capture | Normal run; at the end the person answers the feedback question and edits the mapping at CP2 | Two rows appended to feedback-log.md (asked, cp-edit) with no client data; no change to the skill's files |
| 7 | Update prompt | Feedback log holds `IMPROVE_THRESHOLD` open rows; run once as the owner, once as another user | Owner: after delivery, Update now / Next time; either sets the snooze; Update now hands off with the hand-off block. Other user: Tell the owner / Next time; note sent only on a yes |
| 8 | Same-name folders | Folder name matches several folders | Lists full paths, asks which; never picks the newest |
| 9 | Documents over the cap | Folder with more than `DOC_READ_CAP` documents | Reads the cap, shows "N of M read", asks before reading more (CP3) |
| 10 | Agiloft regression | "How many contracts are in flight?" on Agiloft | Same answer shape as v1.0: figure first, scope and field names in the source clause |
