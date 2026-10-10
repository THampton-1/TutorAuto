# Parking Lot

Technical confusions and rabbit holes worth understanding or fixing properly, but not
blocking progress right now. Theo leads this (see `CLAUDE.md` → "Session workflow and
logs"). Add with "park it", list with "parking lot", work one with "resolve P-XX".

> Distinct from `IMPROVEMENTS.md`, which holds deferred *build features*. This file is for
> things we don't fully understand or that aren't yet good enough — the "why is it like
> this / is this right" items. (We can merge the two later if the split proves fiddly.)

## Open

| ID | Item | Why it matters | Added |
|----|------|----------------|-------|
| P-02 | "Candidate next topics" suggests foundational nodes (N1, N2) for clearly-advanced students, because "never covered" means "never seen in an ingested transcript", not "never taught". | Makes the candidate section naive until many lessons are ingested; may need to bias toward struggled/revisit/stretch and suppress obviously-foundational nodes. | 2026-10-08 |
| P-03 | A-Level curriculum tree not built. Francis, Saska and Daniel (plus inactive Ben, Himmut) have ~63 lessons in Drive that ingest deliberately skips (ADR-007). | Half the roster gets no briefs. Once the tree exists (same label + sub-skill technique as GCSE), the next refresh ingests the backlog automatically, but that's ~63 extraction calls at once, so dry-run first. **Plan agreed 2026-10-10: ADR-015** (inactive students now skipped, 44 docs remain; step 1 "brake" built). Francis's 7 GCSE lessons skipped via Syllabus Since (ADR-016): 37 remain. Step 2 done: 89 A-Level nodes loaded (Pure 62, Stats 14, Mechanics 13). Next: step 3, labels + sub-skills review doc. | 2026-10-08 |
| P-04 | Sorting common title mistakes into Drive subfolders (e.g. `Leson:`, `W:20`, untitled lesson calls) so small errors are easy to spot and fix, rather than silently ignored by the title gate. | Today a typo'd lesson title is silently dropped (by design, ADR-007). Known casualties: `Leson: Francis` 23/09, `W:20 Francis` 19/08, `ben lesson` 08/06, `last lesson himmut` 14/06. | 2026-10-08 |
| P-07 | **What actually drives cost?** ADR-011 lets the refresh run as often as every 2 hours (on unlock), which reads as "many more tokens". Unclear to Theo whether run frequency affects spend at all. Possible fixes: Theo does a short deep-dive on the cost driver, or ADRs gain a standard "Cost impact" line saying whether each decision shifts spend. | A schedule change shouldn't be able to raise the API bill without anyone noticing; Theo wants to judge cost from the docs, not by asking. | 2026-10-09 |

## Resolved

| ID | Item | Outcome | Resolved |
|----|------|---------|----------|
| P-01 | Verbatim quotes under each sub-skill added little planning value. | Quotes now sit behind an "Evidence from transcript" toggle; each sub-skill shows a one-sentence model-written note instead (ADR-012). | 2026-10-10 |
| P-05 | Replace quotes with a short narration. | Done in the existing single extraction call: 4–6 bullet lesson summary (bold key phrases, italic maths, ADR-014) + one-sentence note per sub-skill (ADR-012). New 4-section brief layout (ADR-013). All 16 GCSE lessons re-extracted 2026-10-10. | 2026-10-10 |
| P-06 | Suppress always-present foundational topics (N1–N9, A1–A8). | Closed without code. Mostly fixed by ADR-013: "still open" replaced the chronological candidates that kept surfacing N1. Data check (15 lessons): 26 of 106 rows are N1–N9/A1–A8, 9 of them `struggled`, and most of the rest are real teaching (composite functions A7.3, factorising A4.4, Eliza's rearranging A5.2), so a range filter would hide signal. Revisit if briefs feel crowded after a few weeks; the fallback is a hand-picked list (e.g. A2.1, A4.3, A5.2) whose practised/secure rows collapse to one faded "Also used" line, display-only. | 2026-10-10 |
