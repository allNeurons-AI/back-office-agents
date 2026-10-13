# Conflict priority rules

Read this whenever the Resolve step in SKILL.md needs to decide, for a real conflict, which side should yield. These are defaults tuned to how most people would triage instinctively — not a rigid formula. Weigh the signals below, then state the call in one sentence a human could push back on.

An organization can replace this entire file with its own version — same filename, same purpose (weigh two colliding meetings, pick a side, say why) — without touching SKILL.md at all. That's the whole portability trick: the skill's logic stays generic, the judgment calls live here.

## Default signal weights

Check each colliding meeting against these, roughly in order of how much they should move the decision. No meeting will hit all of them — read for the strongest signals present on each side, not a checklist to fully satisfy.

1. **External beats internal.** A meeting with someone outside the organization — a customer, prospect, partner, candidate — outranks an internal-only meeting by default. Internal meetings can almost always be moved by someone in the room; external counterparts usually can't be asked to reshuffle their day on short notice.

2. **Fixed-date beats flexible.** Some things have a real external deadline attached — a filing date, a renewal date, a close date, a board meeting, an event. Look for these in the title, description, or (if a CRM is connected) the deal's close date or stage. A meeting tied to a hard date outranks one that could happen any day this week.

3. **Seniority and scarcity of the counterpart.** A meeting with someone senior on the other side (an exec, a skip-level, a VIP client) or someone notoriously hard to get time with outranks a meeting with a peer or a standing internal contact the user talks to often.

4. **Standing beats one-off, when both are internal.** A weekly team sync can absorb being skipped once far more easily than a one-off internal meeting that was specifically scheduled to make a decision.

5. **Explicit signals win outright.** Titles or descriptions containing language like "do not move," "hard deadline," "final," "signing," "court," "filing deadline," or similar should be treated as near-absolute — don't let a generic ranking override an explicit flag someone already put in the calendar.

6. **Organizer asymmetry.** All else equal, it's lower-cost for the user to move a meeting they organize (they control the reschedule) than to ask out of someone else's meeting. This is a tiebreaker, not a primary signal — don't let it override points 1–5.

7. **CRM signals, when connected.** Deal stage (late-stage beats early-stage), account tier or ARR, and whether the deal has stalled before (a slipping deal needs momentum more than a healthy one) all sharpen point 1 and 2 rather than replacing them — they tell you *how* external, not just *whether*.

## When it's a genuine toss-up

If two meetings are both external, both flexible, and neither carries an explicit signal, don't force a confident-sounding call just to fill the field. Say plainly that both sides are close and this one needs the user's judgment — a wrong guess stated confidently is worse than an honest "this one's yours to call."

## Writing the reason

The stated reason should name the actual signal that decided it, not a vague appeal to importance:

- Good: "The Meridian renewal outranks the internal roadmap sync — it's tied to their contract date and the roadmap sync happens weekly."
- Good: "Both are external and neither has a fixed date — this one needs you to pick."
- Bad: "This meeting seems more important."

## Example override: professional services / law firm context

An organization can adapt the weighting instead of the whole file. For a law firm or similar professional-services setting, a typical override looks like:

- Court dates, filing deadlines, and anything with a statute-of-limitations or regulatory deadline attached move to the top of the ranking, above general "external beats internal" — these aren't reschedulable by anyone's judgment call.
- A client call tied to an active, billable matter outranks a client call that's exploratory or business-development in nature.
- Internal matter-team syncs are lower priority than almost anything external, but a partner or practice-group-lead 1:1 is treated closer to an external meeting than a normal internal sync, since availability with a partner is often as scarce as availability with a client.
- Add any matter-specific "do not move" language your firm uses in calendar invites (e.g., "hearing," "deposition," "closing") to the explicit-signal list in point 5 above.

Keep the rest of the default framework — it still applies underneath the override.
