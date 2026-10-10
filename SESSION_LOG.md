# Session Log

Hand-off notes between sessions. The start-of-session 5-bullet briefing reads the
"Carry-over" block first; the end-of-session prompt writes it. Newest session on top.

## Carry-over for next session

What Theo wants to pick up first next time:

1. **Present P-05 and P-06 as options; Theo picks which to do.** P-05 = replace the quotes
   with a 2–3 sentence narration (generated in the existing extraction call). P-06 =
   suppress always-present foundational topics (N1–N9, A1–A8), which needs deliberation.
   Give a short tradeoff for each and let Theo choose. Don't start either unprompted.
2. **Afterwards: brief UI/UX pass + Phase 6 history page together.** Iterate 5–6 base HTML
   layouts so both views share one design.

Optional, small: make the refresh log list A-Level/needs_review skips only the first time
(it repeats ~84 skip lines per run in `data/refresh.log`; runs are now more frequent, ADR-011).

Decided 2026-10-08: students' first names are fine in committed docs and tests (no
initials needed).

---

## 2026-10-09 / 10

- **Phase 5 gate passed (2026-10-10):** refresh ran automatically on Theo's first unlock
  of the morning; index green with nothing run by hand.
- **Why the first nightly run failed:** laptop asleep at 03:00; Windows started the
  catch-up during a 5-second maintenance wake at 05:50, slept mid-Drive-request, and the
  run hung until 14:24 then timed out. Nothing lost or written.
- **New schedule (ADR-011):** task now runs at 20:00 daily and 1 minute after every unlock,
  as `refresh.py --if-stale` (skips if the last successful run was < 2h ago; failures never
  skip). Network-required setting on. Drive requests retry up to 4 times. 36 tests passing.
- **Parked P-07:** what actually drives cost. Short answer given: run frequency costs
  nothing; only one extraction call per *new* lesson is paid.

---

## 2026-10-08 (second session)

- **Found why briefs weren't refreshing:** Meet moved to one subfolder per meeting under
  `Google Meet` (~Aug 2026), and ingest only read `Meet Recordings`, so it hadn't seen any
  lesson since 28 July. Ingest now reads `Google Meet` plus all its subfolders (ADR-006).
- **Ingested 11 new GCSE lessons:** Twins now 9, Eliza 5, Gabriel 1. Fixed a parse
  failure on transcripts with no speaker labels (Gabriel 14/09).
- **Title gate + in-scope rule (ADR-007):** only `Lesson:` / `W<n>` titles are considered;
  A-Level is skipped until a tree exists (P-03); `needs_review` no longer duplicates; paid
  retries are capped at 3 per lesson.
- **Nightly refresh (ADR-009):** `scripts/refresh.py`, Task Scheduler task
  `TutorAuto nightly refresh` at 03:00 with catch-up. Status line on index (red on failure
  or if >36h old), `data/refresh.log`. Verified by triggering through Task Scheduler.
- **Output defined (ADR-008, ADR-010):** HTML in `briefs/<student>/`, one brief per lesson
  rebuilt as it stood after that lesson (~3 ms each, £0), plus `_latest`. Phase 6
  (long-term history page) specified in CLAUDE.md, not built.
- **CLAUDE.md:** new "How I consume the output" and "When something breaks" sections;
  ADRs now carry **Failure signs**. Parked P-03..P-06. 31 tests passing.

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
