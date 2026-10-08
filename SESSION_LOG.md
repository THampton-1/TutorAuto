# Session Log

Hand-off notes between sessions. The start-of-session 5-bullet briefing reads the
"Carry-over" block first; the end-of-session prompt writes it. Newest session on top.

## Carry-over for next session

What Theo wants to pick up first next time:

1. **Understand the day-to-day process — briefs aren't refreshing.** Theo clicks into his
   briefs but sees no newly-updated document despite an abundance of new lessons. Work out
   why (has ingest been run on the new Drive lessons? is brief.py being regenerated? is the
   `*_latest.html` pointer the one he's opening?) and give Theo a clear mental model of the
   click-to-fresh-brief loop.
2. **UI/UX pass on the brief.** Iterate 5–6 base HTML layouts for the brief so Theo can see
   which format he likes working with, then settle on one.

Context: brief *depth* (not layout) is parked as **P-01** — evidence quotes add little vs
the Gemini reviews. That's a separate, later concern from the layout iteration above.

---

## 2026-10-08

- Built the **sub-skill layer** end to end: `sub_skills` table, `short_label` on nodes,
  loaded 97 nodes / 182 sub-skills from the hand-reviewed `curriculum_labels_review.md`
  (`build_sublabels.py`). Extraction now selects sub-skill ids; `coverage_events` gained a
  nullable `sub_skill_id`.
- Updated the **roster**: added Gabriel and Eliza (GCSE), marked Ben and Himmut inactive
  via a new `Active` column (names cleaned). `build_roster.py` + schema updated.
- Reworked **`brief.py`** to render at sub-skill granularity (short label › sub-skill,
  no dense spec text) and to flag inactive students.
- Added **`reextract_cached.py`** (re-run extraction on cached transcripts in place) and
  re-extracted the 4 Twins lessons at sub-skill level; generated a sub-skill Twins brief.
- Set up this **logging system**: `DECISIONS.md`, `PARKING.md`, `SESSION_LOG.md`, plus the
  session-briefing / working-rules section in `CLAUDE.md`. Seeded ADR-001..005 and P-01/P-02.
- Verified the Anthropic key is live (Default-workspace user key); real extraction calls succeed.
