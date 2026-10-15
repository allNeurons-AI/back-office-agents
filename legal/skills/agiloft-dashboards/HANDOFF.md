# Hand-off: agiloft-dashboards

## What it does
Answers contract questions in plain language and keeps a live four-tab contract dashboard beside the chat. It reads from Agiloft, from SharePoint spreadsheets, lists and documents (including Word and PDF), from any other connected system, or from an attached file. It is read-only and builds one dashboard per source, always showing the source, the account and the mapped columns.

## Owner and reviewer
Owner: Rajan   Reviewer: to be named

## How to install or share
The skill works the same either way, because its safeguards are inside its own files.
1. Save the updated skill from the review card in the Claude app; it replaces the earlier version.
2. Otherwise keep the folder in the shared team location and attach SKILL.md and its references to a shared project or the session.
3. Confirm each new user has the connector for the source they will use; the skill sees only what their own account can open.

## First-run checklist
- [ ] The connector for the first source (Agiloft or Microsoft 365) is enabled for the chat, or a file is ready to attach
- [ ] Open a SharePoint folder you can see and confirm the skill shows its full path at the first checkpoint
- [ ] Run the test prompts in tests/test-prompts.md
- [ ] The memory folder holds feedback-log.md and users can append to it

## Reading the logs
Run log: `RUN_LOG_PATH` in config.md. Review after the first five runs, then monthly: caps nearly hit, gates that fire often, checkpoints always approved unchanged.

## Feedback and changing the skill
Users' feedback is logged automatically in `feedback-log.md` in the memory folder. When enough builds up, the skill offers the owner "Update now", which opens the legalgraph-skill-creator with the feedback loaded. You can also start it any time by saying "apply feedback to agiloft-dashboards".
Only the owner edits the master copy (`MASTER_COPY` in config.md). Every change gets a CHANGELOG entry listing the feedback IDs it closes. After an update, install the new version: the skill cannot replace itself.
