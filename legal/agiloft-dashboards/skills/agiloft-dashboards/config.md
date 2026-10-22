# Config: agiloft-dashboards

Values only, no logic. Every key is used by a step in SKILL.md. The owner edits this file; the skill never edits it.

## OWNERSHIP
OWNER = Rajan
MASTER_COPY = (unset)
# Folder holding the master copy of this skill; used for the Update now hand-off. Unset means the owner hands the file back through the skill review card.

## PATHS
MEMORY_FOLDER = memory/
RUN_LOG_PATH = logs/run-log.md

## DATA SOURCES
FALLBACKS = connector -> file the person attaches to the chat (xlsx, csv, docx, pdf) -> stop and say what is needed

## CAPS
QA_MAX_ATTEMPTS = 2
RETRIES_PER_CALL = 2
TOOL_CALLS_PER_STEP = 40
REBUILDS_MAX = 2
RUN_MINUTES_MAX = 15
DOC_READ_CAP = 50
DOC_PAGES_MAX = 10
ROW_PAGE_LIMIT = 2000

## GATES
DIVERGENCE_FLAG_PCT = 5
DIVERGENCE_BLOCK_PCT = 10

## FEEDBACK
FEEDBACK_QUESTION = on
IMPROVE_THRESHOLD = 3
IMPROVE_SNOOZE_RUNS = 5
SKILL_CREATOR = legalgraph-skill-creator
