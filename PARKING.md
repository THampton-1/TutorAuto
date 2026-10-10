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
| P-03 | A-Level curriculum tree not built. Francis, Saska and Daniel (plus inactive Ben, Himmut) have ~63 lessons in Drive that ingest deliberately skips (ADR-007). | Half the roster gets no briefs. Once the tree exists (same label + sub-skill technique as GCSE), the next refresh ingests the backlog automatically, but that's ~63 extraction calls at once, so dry-run first. | 2026-10-08 |
| P-04 | Sorting common title mistakes into Drive subfolders (e.g. `Leson:`, `W:20`, untitled lesson calls) so small errors are easy to spot and fix, rather than silently ignored by the title gate. | Today a typo'd lesson title is silently dropped (by design, ADR-007). Known casualties: `Leson: Francis` 23/09, `W:20 Francis` 19/08, `ben lesson` 08/06, `last lesson himmut` 14/06. | 2026-10-08 |
| P-06 | **Suppress always-present foundational topics (N1–N9, A1–A8).** They come up in nearly every lesson as background and crowd the brief. Needs deliberation: hide them where (last-lesson list, struggled list, candidates)? Hide completely vs collapse into one "foundations touched" line? Filter only at display time, never at extraction, so the record stays complete. Keep showing them when `struggled` or `revisit_requested`, since a weak foundation still matters for planning. | Cuts noise from every brief; related to P-02, where foundational nodes also wrongly appear as candidates. | 2026-10-08 |
| P-07 | **What actually drives cost?** ADR-011 lets the refresh run as often as every 2 hours (on unlock), which reads as "many more tokens". Unclear to Theo whether run frequency affects spend at all. Possible fixes: Theo does a short deep-dive on the cost driver, or ADRs gain a standard "Cost impact" line saying whether each decision shifts spend. | A schedule change shouldn't be able to raise the API bill without anyone noticing; Theo wants to judge cost from the docs, not by asking. | 2026-10-09 |

## Resolved

| ID | Item | Outcome | Resolved |
|----|------|---------|----------|
| P-01 | Verbatim quotes under each sub-skill added little planning value. | Quotes now sit behind an "Evidence from transcript" toggle; each sub-skill shows a one-sentence model-written note instead (ADR-012). | 2026-10-10 |
| P-05 | Replace quotes with a short narration. | Done in the existing single extraction call: 4–6 bullet lesson summary (bold key phrases, italic maths, ADR-014) + one-sentence note per sub-skill (ADR-012). New 4-section brief layout (ADR-013). All 16 GCSE lessons re-extracted 2026-10-10. | 2026-10-10 |
