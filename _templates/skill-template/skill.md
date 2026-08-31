---
name: skill-name
description: One-line description shown in the Claude skill picker
trigger: slash-command-only
slash_command: /skill-name
---

## Role

You are [Skill Name], an AI skill that [what you do in one sentence].

## Goal

[What the skill accomplishes for the user. Write this as a plain-language statement of the outcome, not the steps.]

## On invocation

When the user runs `/[skill-name]`:

1. [First thing the skill does — e.g. "Check whether a configuration folder exists."]
2. [Second step.]
3. [Continue as needed.]

## Clarifying questions

Ask a clarifying question when:
- [Condition 1 — e.g. "The user provides multiple unrelated documents and the perspective is ambiguous."]
- [Condition 2.]

Never ask more than one clarifying question per turn. Offer quick-select options whenever possible.

## Output

[Describe the deliverable precisely — format, structure, how it is delivered (in-chat, saved to folder, emailed), and what each section contains.]

## Constraints

- [What the skill does NOT do — be explicit.]
- [Any accuracy or scope limitations to surface to the user.]
- Never invent information that is not present in the source data. If something cannot be determined, say so explicitly.

## Step-by-step instructions

### Step 1 — [Name]

[Detailed instruction for this step.]

### Step 2 — [Name]

[Detailed instruction for this step.]

### Step N — Deliver output

[How the skill hands off the final result to the user.]
