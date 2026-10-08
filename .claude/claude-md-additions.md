## Session start: 5-bullet briefing

At the start of every session, before doing anything else, read the Decision Log and Parking Lot below and give me a 5-bullet summary:

1. **Where we are**: current state of the project in one line
2. **Last done**: what was completed last session
3. **Open decisions**: anything undecided or recently decided that affects next steps
4. **Parking lot**: the 1-2 most relevant parked items (and the count of the rest)
5. **Next**: what we should do first this session

Keep it to those 5 bullets. No preamble, then wait for me.

---

## Working rules: decisions and parking

**Decision Log (ADR)**
- When we settle something significant (architecture, data format, tool choice, how a pipeline stage works, anything we'd be annoyed to re-argue), add an entry to the Decision Log below before moving on. Tell me in one line that you did.
- Each entry has: what we decided, why, what we rejected, and what would make us revisit it.
- Never delete or rewrite old entries. If a decision changes, add a new entry and mark the old one `Superseded by ADR-XXX`.
- Before proposing a change in direction, check the log first. If it contradicts an existing decision, say so.

**Parking Lot**
- When I say "park it" (or we hit a technical rabbit hole that isn't blocking progress), add it to the Parking Lot with a one-line description and why it matters. Then keep moving.
- Never stop to fully resolve a parked item unless I ask.
- When I say "parking lot", show me the open items. When I say "resolve P-XX", work on that one.

**After fixing a bug or technical problem**
- Give me the root cause in 2 sentences of plain English: what broke, and why the fix works. Add a one-line note to the Decision Log only if it changes how we build things going forward.
- If I say "timebox", spend a fixed amount of effort, then report what you found even if it's incomplete.

**Shortcuts**
- `log it`: write the decision we just made into the Decision Log
- `park it`: add the current issue to the Parking Lot
- `parking lot`: list open parked items
- `decisions`: list the Decision Log headings, newest first
- `where are we`: re-run the 5-bullet briefing

---

## Decision Log

Newest first. Status is `Active` or `Superseded by ADR-XXX`.

### ADR-000: Example entry (delete this once you have a real one)
- **Date:** 2026-10-08
- **Status:** Active
- **Decision:** What we chose, in one or two sentences.
- **Why:** The reasoning. This is the part you will forget.
- **Rejected:** The alternatives we considered and why they lost.
- **Revisit if:** The specific condition that would make us reopen this.

<!-- Template for new entries:

### ADR-XXX: Short title
- **Date:**
- **Status:** Active
- **Decision:**
- **Why:**
- **Rejected:**
- **Revisit if:**

-->

---

## Parking Lot

Things worth understanding or fixing properly, but not blocking progress right now. Move to Resolved when done.

### Open

| ID | Item | Why it matters | Added |
|----|------|----------------|-------|
| P-01 | Example: why X behaves oddly on long transcripts | Might affect brief quality at scale | 2026-10-08 |

### Resolved

| ID | Item | Outcome | Resolved |
|----|------|---------|----------|
