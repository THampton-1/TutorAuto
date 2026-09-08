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

## needs_review failure reasons are raw exception text

`ingest.py`'s batch loop (`ee0db1f`) catches any `ingest_one()` failure so one
bad transcript can't stall the whole run, and logs it to `needs_review` with
`f"{type(error).__name__}: {error}"` as the reason. That string is whatever
Python's exception message happens to say, not a categorized, actionable
reason -- fine while failures are rare and reviewed by eye, but if one
failure type starts recurring (e.g. a specific Drive doc shape breaking
repeatedly), it's worth catching that case specifically and writing a
clearer reason instead of a stack-trace fragment.

## Node descriptions are too dense for the brief

`curriculum_nodes.topic` is the verbatim Edexcel spec text (correct and
necessary as the source of truth, per CLAUDE.md's "node_id ... taken
verbatim from the spec document"), but `brief.py` prints that full text on
every line that mentions a node. For a node like R9 that's a 60+ word
run-on sentence -- readable as a spec reference, not as something to
glance at while planning. Theo confirmed (2026-09-08, reviewing the real
Twins brief) this is his single biggest readability complaint: everything
else in the brief -- last-lesson summary, stretch-content flagging, the
overall structure -- landed well.

**Design note for next attempt:** don't hand-write ~97 short labels, and
don't let the model paraphrase spec text live in the extraction call
(that call's job is matching coverage to node_id, not authoring copy, and
paraphrasing risks drifting from the spec's actual meaning). Instead: a
one-off, separate pass (not the recurring per-transcript call) that reads
each of the 97 nodes once and proposes a short human-readable label (a
few words -- e.g. R9 -> "Percentages and percentage change"), stored as a
new `curriculum_nodes.short_label` column. Theo reviews and edits the
proposed labels once, same spirit as the Phase 1 completeness report --
the model proposes, he corrects, and it's a one-time cost, not a
per-lesson one. `brief.py` then shows `short_label` in the bulleted
sections and can keep the full spec text for the "Last lesson" section
only, where the current level of detail already reads well.

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
