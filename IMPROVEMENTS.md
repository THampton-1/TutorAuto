# Flagged for later

Things knowingly skipped or deferred to get the first working draft done,
kept here so they don't get lost. Not urgent by definition -- each entry
below was reviewed and judged safe to leave for now because the system
still works correctly without it.

## Phase 3 eval — third lesson not reviewed

Only 2 of the 3 eval lessons (06/19, 07/16) have been walked through
against Theo's memory and Gemini notes. The 07/26 lesson hasn't been
checked, so the conservatism-calibrated prompt hasn't been validated
against it. Extraction still runs fine on it -- this is a confidence gap,
not a functional one.

**To pick back up:** `python scripts/eval_extract.py "eval/lesson_twins_2026_07_26_15_01_bst_notes_by_gemini.txt"`,
then compare against Theo's recall and Gemini notes for that date the same
way the first two were done.

## Time-per-topic tracking

Theo wants to know total time spent per curriculum node, ideally
accumulated across lessons. A `lesson_timestamp` field (single
point-in-time marker per coverage event) was tried and reverted -- it
showed *when* a topic came up but not *how long* was spent on it, which
wasn't the actual ask.

**Design note for next attempt:** don't ask the model to estimate a
duration directly (LLMs are unreliable at that). Instead have it report a
start and end marker per coverage event (both are lookups against
timestamp markers already present in the transcript, not arithmetic), then
compute actual elapsed time and cross-lesson totals in plain Python from
those pairs -- keeps the one-fuzzy-call-then-deterministic-code principle
intact. Both Meet doc shapes (Notes-by-Gemini and transcript-only) carry
usable inline timestamp markers, confirmed during the Phase 3 eval.

"Last date this node was covered" is a related, separate idea that needs
no design work at all -- it's already derivable from `lessons.date` via a
plain query once there's real ingested data to query.
