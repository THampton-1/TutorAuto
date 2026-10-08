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
| P-01 | The brief's evidence beneath each sub-skill (verbatim quotes) adds little planning value — titles/sub-skills are good, the "further description" is close to useless vs Theo's own Gemini reviews. | The brief isn't yet on par with the Gemini workflow it's meant to replace; evidence layer needs rethinking (better synthesis, not raw quotes). | 2026-10-08 |
| P-02 | "Candidate next topics" suggests foundational nodes (N1, N2) for clearly-advanced students, because "never covered" means "never seen in an ingested transcript", not "never taught". | Makes the candidate section naive until many lessons are ingested; may need to bias toward struggled/revisit/stretch and suppress obviously-foundational nodes. | 2026-10-08 |
| P-03 | A-Level curriculum tree not built. Francis, Saska and Daniel (plus inactive Ben, Himmut) have ~63 lessons in Drive that ingest deliberately skips (ADR-007). | Half the roster gets no briefs. Once the tree exists (same label + sub-skill technique as GCSE), the next refresh ingests the backlog automatically, but that's ~63 extraction calls at once, so dry-run first. | 2026-10-08 |
| P-04 | Sorting common title mistakes into Drive subfolders (e.g. `Leson:`, `W:20`, untitled lesson calls) so small errors are easy to spot and fix, rather than silently ignored by the title gate. | Today a typo'd lesson title is silently dropped (by design, ADR-007). Known casualties: `Leson: Francis` 23/09, `W:20 Francis` 19/08, `ben lesson` 08/06, `last lesson himmut` 14/06. | 2026-10-08 |
| P-05 | **Replace quotes with a short narration (extends P-01).** Theo's direction (2026-10-08, after reading the first real multi-lesson briefs): under each sub-skill, show a 2–3 sentence intuitive summary of what was covered and how it went, instead of the verbatim quote. Things to settle: generate it inside the existing extraction call as an extra field, so it's still one LLM call per lesson (principle 1); keep the verbatim quote stored for auditing (principle 5) and just stop displaying it by default; narration is model paraphrase, so it must follow the same conservatism as ADR-001; existing lessons would need one re-extraction (`reextract_cached.py`) to gain it. | Quotes don't help planning; a narration would. This is the main remaining gap vs the Gemini reviews. | 2026-10-08 |
| P-06 | **Suppress always-present foundational topics (N1–N9, A1–A8).** They come up in nearly every lesson as background and crowd the brief. Needs deliberation: hide them where (last-lesson list, struggled list, candidates)? Hide completely vs collapse into one "foundations touched" line? Filter only at display time, never at extraction, so the record stays complete. Keep showing them when `struggled` or `revisit_requested`, since a weak foundation still matters for planning. | Cuts noise from every brief; related to P-02, where foundational nodes also wrongly appear as candidates. | 2026-10-08 |

## Resolved

| ID | Item | Outcome | Resolved |
|----|------|---------|----------|
