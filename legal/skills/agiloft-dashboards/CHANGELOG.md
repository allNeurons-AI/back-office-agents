# Changelog: agiloft-dashboards

## 2.0 - 2026-10-15 - Rajan
- Changed: the skill is no longer limited to Agiloft. It builds the same plain-language answers and four-tab dashboards from SharePoint spreadsheets, lists and documents of any format, from any other connected system, or from an attached file. One source per dashboard.
- Added: Step 0 source identification; CP2 field-mapping confirmation; CP3 document cap; `DOC_READ_CAP` and related caps; SharePoint and generic source files; dashboard data schema; `assets/dashboard_template.html` restored from the original and made source-neutral (source name, documents-read and mapped footer fields); QA checklist, config, data dictionary, tests, hand-off and feedback loop.
- Changed: the 1,000-line SKILL.md was split into a source-agnostic core plus reference files. Agiloft rules moved verbatim to `references/source-agiloft.md`; Agiloft behaviour is unchanged.
- Why: the owner asked for the skill to work from SharePoint and other sources, not only Agiloft.
- Approved by: Rajan, at design review (2026-10-15).
- Reviewed by: pending

## 1.0 - earlier - Rajan
- Added: Agiloft-only version (single SKILL.md).
