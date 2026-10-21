# Data dictionary: agiloft-dashboards

The single source of truth for the field roles the skill maps every source onto. SKILL.md and the source files refer to this file and never restate it. Source-specific names (Agiloft's field names, a spreadsheet's headers) are discovered at run time, not stored here.

| Role | Meaning | Typical Agiloft field | Typical spreadsheet header | Documents |
|------|---------|----------------------|----------------------------|-----------|
| id | Unique record key | contract id | ID, Ref | file name |
| title | Short name | Contract Title | Title, Name | document title |
| counterparty | Other party | Counterparty Legal Name | Vendor, Customer | extracted party |
| agreement type | Kind of contract | Agreement Type | Type, Category | extracted type |
| status | Where it is in its life | Status | Status, Stage | not tracked unless stated |
| owner | Person responsible | Contract Owner | Owner, Requester | not the file author |
| created date | When raised | Date Created | Created, Raised | file created date (files, not contracts) |
| effective date | When it starts | Contract Effective Date | Start | extracted, may be ambiguous |
| end date | When it ends | Contract End Date | End, Expiry | extracted, may be ambiguous |
| value | Money | contract value | Value, Amount | extracted when stated |
| days in current status | Time at the current step | Days in Current Status | Days in Stage | never derived |

## Metric definitions
| Metric | Definition | Period rule |
|--------|------------|-------------|
| In force | Signed and live: status mapped to in force at CP2 | As at the check time |
| In flight | Created, not signed, not closed | As at the check time |
| Closed | Cancelled, terminated, expired, rejected or withdrawn | As at the check time |
| Expiring in N days | In force with an end date from today to N days ahead | Inclusive of the end day; say N and the status scope |
| Active vendors | Distinct counterparty names across in-force vendor agreements, trimmed and case-insensitive; near-duplicates counted separately | As at the check time |
| Days in current status | The ageing column in days (convert hours by dividing by 24) | Current status only, not total age |
