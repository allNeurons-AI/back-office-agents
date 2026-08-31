# allNeurons Skill Marketplace

A single Claude skill that lets users browse, learn about, and install every skill in the `back-office-agents` collection — without leaving their Claude session.

---

## What it does

Install this skill once and you get an in-Claude marketplace. Type `/allneurons` in any chat to see every available back-office skill organized by department, get details on any skill, and walk through installation step by step.

```
/allneurons                          → Browse the full skill catalog
/allneurons about flux               → Learn about a specific skill before installing
/allneurons install flux             → Jump straight to the install flow
/allneurons list finance             → Filter by department
```

---

## How to install the marketplace skill

1. [Download the marketplace skill]() — *(link added when published)*
2. In Claude, open **Customize → Skills → Add → Upload a skill**.
3. Upload the `.skill` file.
4. The skill appears under **Personal Skills** as `allneurons`.
5. Type `/allneurons` in any chat and you're in.

Don't know how to upload a skill? [Step-by-step guide here](../foundation/setup-skill-in-claude/readme.md).

---

## How it works

The marketplace skill reads from [`registry.json`](./registry.json) — a catalog of every skill in this repo with metadata: name, slash command, description, required connectors, and output format. When a new skill is added to the repo, it gets an entry in the registry, and the marketplace skill picks it up automatically.

---

## Skills currently in the catalog

| ID | Name | Department | Command |
|---|---|---|---|
| `allneurons-flux` | GL Account Flux Explainer | Finance | `/allneurons-flux` |
| `coc-lease-extraction` | Change of Control Lease Extraction | Finance / Legal | `/coc-lease-extraction` |
| `allneurons-tabular-review` | Contract Tabular Review | Legal | `/allneurons-tabular-review` |

---

## Adding a skill to the marketplace

When you build a new skill and add it to this repo:

1. Open [`registry.json`](./registry.json).
2. Add an entry to the `skills` array with these fields:

```json
{
  "id": "your-skill-id",
  "name": "Human-Readable Skill Name",
  "command": "/your-slash-command",
  "department": "finance",
  "description": "One sentence — what the user gets.",
  "tags": ["finance", "relevant-tag"],
  "docs": "finance/your-skill/README.md",
  "connectors": ["manual-upload"],
  "output": "excel"
}
```

3. Update the **Catalog** section in [`skill.md`](./skill.md) with the same information.
4. The marketplace will surface the new skill to all users on their next invocation.

---

Built by [All Neurons](https://allneurons.ai).
