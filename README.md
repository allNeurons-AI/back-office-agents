# back-office-agentskills

![logo](./assets/logo.png)

A public collection of reusable AI agent skills built by Allneurons for back-office business workflows.

## Objective

We build AI agent skills for our customers every day — and we're making all of them public.

This repository is where we publish every skill we create for clients across Finance, HR, Legal, Operations, Sales, Procurement, and more. If we built it for a customer, it ends up here — open and available for anyone to use, adapt, and build on.

## Quick install — get all skills at once

Install the [marketplace skill](./marketplace/README.md) and type `/allneurons` in any Claude chat. It shows every skill in this collection, lets you browse by department, and walks you through installing any of them — without leaving your session.

```
/allneurons                            → browse the full catalog
/allneurons install flux               → install a specific skill
/allneurons about coc-lease-extraction → learn more before installing
```

Or install individual skills directly — each skill folder has its own install guide.

---

## Getting Started

1. Install the [marketplace skill](./marketplace/README.md) to browse and install everything from inside Claude.
2. Or navigate directly to the relevant department folder and follow the install guide in that skill's README.
3. For shared utilities and common helpers, check the `shared/` directory first.

---

## Folder Structure

| Folder | Description |
|---|---|
| `marketplace/` | The `/allneurons` marketplace skill — install this to browse and install all other skills |
| `_templates/` | Scaffold for creating a new skill — copy this when building a new plugin |
| `foundation/` | Guides for setting up and using skills in Claude |
| `finance/` | Financial workflows — reporting, reconciliation, budgeting |
| `compliance/` | Compliance workflows — COI tracking, certificate review |
| `hr/` | HR processes — onboarding, payroll, performance reviews |
| `legal/` | Legal workflows — contract review, document management |
| `operations/` | Operational automation — logistics, facilities, support |
| `sales/` | Sales workflows — CRM, pipeline, outreach |
| `procurement/` | Procurement — vendor management, purchase orders |
| `shared/` | Shared utilities and skills used across departments |

### Skill folder layout

Every skill lives in its department folder and follows this structure:

```
department/
└── skill-name/
    ├── README.md       # What the skill does, how to install, how to use
    ├── skill.md        # The skill definition — system prompt and instructions
    └── assets/         # Screenshots and images used in the README
```

Some skills also include a `sample-data/` folder with example input files you can use to try the skill before running it on your own data.

## Creating a new skill

1. Copy `_templates/skill-template/` into the relevant department folder and rename it.
2. Fill in `skill.md` with your skill's instructions, role, and output definition.
3. Fill in `README.md` using the template — document prerequisites, install steps, usage, and output.
4. Add screenshots to `assets/` as you build.
5. Add an entry to `marketplace/registry.json` so the skill appears in the `/allneurons` catalog.
6. Package the skill and link the download in the README once it's ready to publish.

## Contributing

Skills are added as we build them for customers. Each skill is self-contained and documented so it can be dropped into any compatible agent setup. Add new skills under the appropriate domain folder. If a skill is reusable across multiple domains, place it in `shared/`.

---

## About All Neurons

[All Neurons](https://allneurons.ai) helps enterprises **transform AI spend into measurable business outcomes**.

We design and deploy AI agent skills tailored to real back-office workflows — the kind that reduce manual work, eliminate bottlenecks, and generate results you can actually measure. This repository is a direct reflection of that work: every skill we build for a client gets published here so the broader community can benefit.

Learn more at [allneurons.ai](https://allneurons.ai).

---

Open-sourced for the community.
