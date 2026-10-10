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
| P-03 | A-Level curriculum tree not built. Francis, Saska and Daniel (plus inactive Ben, Himmut) have ~63 lessons in Drive that ingest deliberately skips (ADR-007). | Half the roster gets no briefs. Once the tree exists (same label + sub-skill technique as GCSE), the next refresh ingests the backlog automatically, but that's ~63 extraction calls at once, so dry-run first. **Plan agreed 2026-10-10: ADR-015** (inactive students now skipped, 44 docs remain; step 1 "brake" built). Francis's 7 GCSE lessons skipped via Syllabus Since (ADR-016): 37 remain. Step 2 done: 89 A-Level nodes loaded (Pure 62, Stats 14, Mechanics 13). Step 3 done: 178 sub-skills loaded from `curriculum_labels_review_alevel.md` (Theo signed off). Step 4 pilot done 2026-10-10 (Francis, Saska, Daniel, 7 Oct lessons; briefs built). Next: step 5 backfill (34 lessons) after Theo reads the pilot briefs, then add A-Level to `AUTO_INGEST_SYLLABUSES`. | 2026-10-08 |
| P-04 | Sorting common title mistakes into Drive subfolders (e.g. `Leson:`, `W:20`, untitled lesson calls) so small errors are easy to spot and fix, rather than silently ignored by the title gate. | Today a typo'd lesson title is silently dropped (by design, ADR-007). Known casualties: `Leson: Francis` 23/09, `W:20 Francis` 19/08, `ben lesson` 08/06, `last lesson himmut` 14/06. | 2026-10-08 |
| P-08 | **Haiku as the extraction model?** Claude Haiku 5.5 is $0.10 / $0.50 per M tokens vs Sonnet 5's $2 / $10 (~20× cheaper; ~£0.20 vs ~£4 for the A-Level backfill). Extraction is the one fuzzy, quality-critical step, so a cheaper model risks wrong statuses and missed sub-skills. | Only worth it if spend ever matters; would need the Phase 3 eval re-run on Haiku to compare before switching (same for Sonnet 5.5, same price as Sonnet 5). | 2026-10-10 |

## Resolved

| ID | Item | Outcome | Resolved |
|----|------|---------|----------|
| P-01 | Verbatim quotes under each sub-skill added little planning value. | Quotes now sit behind an "Evidence from transcript" toggle; each sub-skill shows a one-sentence model-written note instead (ADR-012). | 2026-10-10 |
| P-05 | Replace quotes with a short narration. | Done in the existing single extraction call: 4–6 bullet lesson summary (bold key phrases, italic maths, ADR-014) + one-sentence note per sub-skill (ADR-012). New 4-section brief layout (ADR-013). All 16 GCSE lessons re-extracted 2026-10-10. | 2026-10-10 |
| P-07 | What actually drives cost? | **Spend = new lessons × price per lesson for the model.** Run frequency costs nothing: a refresh with no new lessons makes no paid call, and briefs are SQL. One lesson ≈ 15–20K tokens in + a few K out ≈ 10p on Sonnet 5 ($2 / $10 per M). The model is the lever (Opus 5.5 ≈ 2×, Haiku 5.5 ≈ 1/20, see P-08). Cache/batch savings judged not worth it (<1p/lesson, ~£2 per backfill). ADRs carry a **Cost impact** line from ADR-012 on. | 2026-10-10 |
| P-06 | Suppress always-present foundational topics (N1–N9, A1–A8). | Closed without code. Mostly fixed by ADR-013: "still open" replaced the chronological candidates that kept surfacing N1. Data check (15 lessons): 26 of 106 rows are N1–N9/A1–A8, 9 of them `struggled`, and most of the rest are real teaching (composite functions A7.3, factorising A4.4, Eliza's rearranging A5.2), so a range filter would hide signal. Revisit if briefs feel crowded after a few weeks; the fallback is a hand-picked list (e.g. A2.1, A4.3, A5.2) whose practised/secure rows collapse to one faded "Also used" line, display-only. | 2026-10-10 |
