# Decision Log (ADRs)

Significant decisions on this project, newest first. Claude maintains this; see
`CLAUDE.md` → "Session workflow and logs" for the rules. Status is `Active` or
`Superseded by ADR-XXX`. Old entries are never edited — a changed decision gets a
new entry that supersedes the old one.

From ADR-006 on, each entry also has a **Failure signs** line: what it looks like when
this decision is the cause of a problem. `CLAUDE.md` → "When something breaks" maps
symptoms back to these entries, so start there when debugging.

---

### ADR-016: Lessons from before a student's current syllabus are skipped
- **Date:** 2026-10-10
- **Status:** Active
- **Decision:** `Students.xlsx` gains an optional **Syllabus Since** column (a real date),
  loaded into `students.syllabus_since`. Ingest skips any lesson dated before it, writing
  nothing (outcome `before_syllabus`). Blank means every lesson counts. First use:
  Francis, GCSE until June 2026, A-Level since: `2026-07-01`, which skips his 7 GCSE
  lessons (26 Apr – 9 Jun). The split was confirmed from content: April–June lessons are
  angles, circle theorems and mocks with no calculus; from 19 Aug, differentiation in
  every lesson.
- **Why:** The syllabus belongs to the student's single roster row, so without this
  Francis's GCSE lessons would be extracted against the A-Level tree: 7 calls returning
  `unmatched`. Renaming titles can't help (titles pick the student, not the syllabus).
  This will happen again whenever a GCSE student continues to A-Level (Twins, Gabriel in
  2027), so it is a roster field, not a one-off.
- **Rejected:** Picking the syllabus by lesson date and ingesting the old lessons against
  GCSE (7 calls, and the A-Level brief's "still open" would mix in GCSE items; possible
  later upgrade, as nothing is written for skipped lessons); doing nothing (wasted calls,
  noise rows); a second roster row per student per syllabus (breaks alias matching).
- **Failure signs:** A returning student's first lessons on a new syllabus missing (date set
  too late); old-syllabus lessons showing `unmatched`-heavy rows (date missing or too
  early); `build_roster.py` failing with "'Syllabus Since' ... is not a date" (typed as text).
- **Cost impact:** Saves 7 calls now; none ongoing.
- **Revisit if:** Theo wants a student's earlier-syllabus history visible (switch to
  syllabus-by-date), or the Excel Table range is extended to cover the new columns.

---

### ADR-015: A-Level plan: full tree, pilot by hand, then backfill; inactive students skipped
- **Date:** 2026-10-10
- **Status:** Active
- **Decision:** A-Level (P-03) is built in five gated steps: (1) a brake: ingest only runs
  a syllabus unattended if it is listed in `AUTO_INGEST_SYLLABUSES` (`ingest.py`; GCSE only
  today), naming a student with `--student` is the explicit opt-in, and `--limit N` caps a
  run at N lessons, newest first; (2) the tree from Pearson's official Edexcel A Level
  Mathematics (9MA0) spec PDF, fetched into `/specs/`, with a completeness report;
  (3) labels + sub-skills with the GCSE technique, Pure reviewed first but Pure,
  Statistics **and** Mechanics all built before any backfill; (4) pilot: newest lesson
  for each of Francis, Saska, Daniel by hand, Theo reads the briefs; (5) dry-run, priced
  cost estimate, backfill, then add the syllabus to `AUTO_INGEST_SYLLABUSES`. Node IDs are
  the spec reference verbatim with a paper prefix (`P7.3`, `S2.1`, `M8.2`), since Pure and
  Statistics both number from 1. Ingest also now skips **inactive** students (Ben,
  Himmut: 19 docs) with nothing written. Separately, a tree whose nodes are loaded but
  whose sub-skills are not yet counts as no tree, so no call runs against an empty list.
- **Why:** The refresh runs on every unlock, so loading the tree alone would have ingested
  all 44 active A-Level docs at once before a single A-Level brief had been checked.
  Building the whole tree before backfill avoids a second paid re-extract for
  Stats/Mechanics lessons that would otherwise come back `unmatched`. Inactive students'
  briefs aren't read, so their calls are pure cost.
- **Rejected:** A per-run cap on the nightly refresh as the brake (still drains the backlog
  unattended before the pilot is judged); Pure-only tree first (cheaper review, but a
  re-extract later); ingesting inactive students for completeness; hand-transcribing the
  spec as with GCSE (Pearson's PDF is real text); bare spec refs as IDs (collide).
- **Failure signs:** An A-Level student's lessons never arrive after the tree is loaded
  (dry-run says `held (... not in AUTO_INGEST_SYLLABUSES yet)`; step 5 not done); a
  returning student's lessons missing (still `Active = 0` in `Students.xlsx`); A-Level
  briefs full of `unmatched` (tree/label quality, so look at the pilot again).
- **Cost impact:** Saves 19 calls (inactive students). Backfill of 44 calls is deliberate,
  priced at step 5. The pilot is 3 calls.
- **Revisit if:** Further Maths students join (second tree), or the A-Level sub-skill list
  grows so long that extraction accuracy drops (ADR-003's revisit trigger).

---

### ADR-014: Lesson summary is 4–6 skimmable bullets with bold key phrases and italic maths
- **Date:** 2026-10-10
- **Status:** Active (refines the summary *format* in ADR-012; the rest of ADR-012 stands)
- **Decision:** `lesson_summary` is returned as a list of 4–6 bullets in lesson order,
  stored one per line in `lessons.summary`. The model marks one or two key phrases per
  bullet `**bold**` and maths `*italic*`; multiplication is written ×, never `*`. Any
  next-time / homework statement goes last, led by **Next time (tutor said):** or
  **Homework:**. "The student", never he/she. `brief.py` escapes the text first, then turns
  only those two marks into `<strong>` / `<em>`. Social chat about the student's week
  (e.g. school open evenings) is **kept deliberately**.
- **Why:** The paragraph was the only part of the brief that couldn't be read at a glance —
  you had to read all of it to get the overview. Reading just the bold now gives the
  overview, with the full depth still there. Theo values the 5-second catch-up on what the
  student has been up to, so social context is wanted, not noise.
- **Rejected:** Fixed lead-ins (Covered / Confident / Difficulty / Next time) — tidier but
  repeats the "How it went" section and loses the lesson's narrative order; splitting the
  paragraph by sentence in Python (free, but long sentences stay unscannable); a prompt line
  removing social chat (Theo wants it).
- **Double quotes are banned in the summary.** First full run (2026-10-10): wherever the
  model quoted the student in `"…"`, the `"` ended that bullet's JSON string early, so the
  bullet was cut mid-sentence and the quoted words lost (6 bullets, 4 lessons). The prompt
  now requires single quotes; the 4 lessons were re-extracted with
  `reextract_cached.py --lesson-ids`. Per-row notes and quotes were not affected.
- **Failure signs:** A summary bullet that stops mid-sentence (ends without `.`, `?`, `!` or
  `)`) — the double-quote problem back; literal asterisks showing in the brief (model used
  `*` for multiplication or left a mark unclosed); social chat spreading into more than one bullet
  or crowding out the maths; summary bullets mentioning a topic with no coverage row.
- **Cost impact:** None ongoing (same single call). One-off: one re-extract of all 16 GCSE
  lessons, 2026-10-10.
- **Revisit if:** Social chat appears in more than one bullet of a brief or becomes
  distracting (Theo's stated trigger); or bullets grow too long to skim.

---

### ADR-013: Brief layout trial; "candidate next topics" paused
- **Date:** 2026-10-10
- **Status:** Active (trial — under test on Twins' 10 lessons)
- **Decision:** The brief becomes four sections: (1) lesson summary, (2) topics at a glance
  — module › topic › sub-skill chips coloured by status, (3) how it went — one note per
  sub-skill grouped Sticking points / Worked on / Secure, quote behind a toggle, (4) still
  open from earlier lessons — struggled / revisit-requested sub-skills from *before* this
  lesson that nothing has touched since, with date and "N lessons since". The Phase 4
  "three candidate next topics" section is removed for now; section 4 replaces it.
  Extraction is frozen as of ADR-012 while the layout is tested: no further prompt
  changes until reading real briefs shows a concrete gap.
- **Why:** Mirrors the structure of Theo's Gemini recaps (summary → topics → confidence
  signals) while keeping the curriculum rows as the backbone. The old candidates suggested
  foundational nodes to advanced students (P-02); the useful part of "what next" is
  cross-lesson — things raised before and never resolved — which is deterministic and needs
  no model judgement (principle 7). Changing one layer at a time keeps re-extract costs to
  one run.
- **Rejected:** Splitting `note` into went_well / difficulty and adding a
  "said for next time" field now (both need another paid re-extract; deferred until the
  layout shows they're needed); model-written "priorities" (single-lesson view, edges into
  principle 7).
- **Failure signs:** An item listed under "still open" that was in fact covered later
  (would mean the as-of query is wrong); "still open" growing long enough to be noise;
  sticking points from the last lesson missing from section 3.
- **Cost impact:** None — layout is pure SQL over existing rows.
- **Revisit if:** Theo wants forward-looking suggestions back (the suggestion algorithm,
  P-02), or the still-open list needs ranking/pruning.

---

### ADR-012: Briefs lead with model-written narration; quotes stay as hidden evidence
- **Date:** 2026-10-10
- **Status:** Active
- **Decision:** The existing extraction call (still one per lesson) now also returns a
  short lesson summary paragraph (`lessons.summary`) and a one-sentence note per
  coverage row (`coverage_events.note`). The brief shows these in place of the verbatim
  quotes; quotes are still extracted, stored and available under a collapsed toggle.
  Lessons already in the DB gain narration through one full re-extract
  (`reextract_cached.py`). Resolves P-05 (and P-01 with it).
- **Why:** Theo found raw quotes near-useless for planning compared with his Gemini
  recaps; a synthesis of what happened and how it went is what he actually reads. Putting
  it in the existing call keeps principle 1 (one call per lesson) and adds only output
  tokens. A per-row one-liner keeps the narration tied to a specific sub-skill and status;
  the lesson paragraph gives the overall shape the rows can't.
- **Rejected:** 2–3 sentences per sub-skill (repetitive when several sub-skills of one
  topic are taught together); one narration per node (extra table, loses the per-sub-skill
  link); a separate narration-only backfill prompt (keeps old rows unchanged, but a second
  prompt to maintain); dropping quotes entirely (breaks principle 5, auditability).
- **Constraints on the text:** Same conservatism as ADR-001 — a note can never claim more
  than its row's status. Describes what happened, never recommends what to teach next
  (principle 7); something Theo or the student *said* about next steps may be reported
  as said.
- **Failure signs:** A note that reads more positive than its status badge; a summary
  mentioning a topic with no matching row; generic notes ("worked on this topic") that
  could fit any lesson; empty summaries on lessons ingested before the re-extract.
- **Cost impact:** New lessons: a few hundred extra output tokens per call. One-off: one
  extraction call per lesson already in the DB, the same as their original ingest.
- **Revisit if:** Narration drifts from the transcript (hallucinated detail), or Theo
  finds the one-liners too thin and wants longer per-topic text.

---

### ADR-011: Refresh runs at 20:00 and on every unlock, with Drive retries
- **Date:** 2026-10-09
- **Status:** Active (supersedes the schedule part of ADR-009; the rest of ADR-009 stands)
- **Decision:** The task `TutorAuto nightly refresh` (name kept) now has two triggers:
  daily at 20:00 (catch-up on), and one minute after every unlock of Windows. It runs
  `refresh.py --if-stale`, which exits silently if the last *successful* refresh finished
  under 2 hours ago (`MIN_HOURS_BETWEEN_RUNS`); a failed run never blocks the next one.
  "Only run if network available" is on. Every Drive request is retried up to 4 times
  (`DRIVE_RETRIES`) on network errors / 5xx / 429.
- **Why:** On 2026-10-09 the 03:00 run never happened (laptop asleep); Windows started the
  catch-up during a 5-second maintenance wake at 05:50, the laptop slept mid-request, and
  the run hung until Theo opened the laptop at 14:24, then failed with "read operation
  timed out". The laptop is almost never restarted (last boot 26 Sept), so an "at logon"
  trigger would rarely fire; unlock is the real "I've started using the computer" moment.
- **Rejected:** Wake-to-run at 03:00 (laptop waking itself nightly, possibly in a bag);
  an "at logon" trigger (fires only after a restart); running on every unlock with no
  guard (many identical runs a day, ~90 log lines each).
- **Failure signs:** Index stale even though the laptop has been used (task disabled, or
  `--if-stale` wrongly skipping: check `data/last_refresh.json`); a lesson finishing after
  20:00 not appearing until the next unlock (expected); a lesson taught just after an unlock
  run waiting up to 2h for the next unlock-triggered run (expected).
- **Revisit if:** Lessons regularly end after 20:00 and the morning unlock comes too late,
  or the laptop starts being shut down nightly (then add an at-logon trigger).

### ADR-010: Briefs are filed in one folder per student
- **Date:** 2026-10-08
- **Status:** Active (supersedes the file-location part of ADR-008)
- **Decision:** Every brief file lives in `briefs/<student_id>/`: the per-lesson archive
  `<id>_<lesson date>.{html,md}` and the pre-lesson brief `<id>_latest.html`. The top of
  `/briefs/` holds only `index.html` and the student folders; index cards link to
  `<id>/<id>_latest.html`. File names keep the student id so a brief identifies itself
  when opened alone. The future history page (Phase 6) goes in the same folder.
- **Why:** With one brief per lesson, a flat `/briefs/` fills with every student's
  archive mixed together. Theo asked for per-student folders.
- **Rejected:** Shortening names inside the folder (e.g. `twins/latest.html`): fewer
  characters, but a brief would no longer say whose it is once opened or shared on its own.
- **Failure signs:** Index card links that go nowhere (the link must include the folder);
  a stray `<id>_latest.html` at the top of `/briefs/` (left over from before this change,
  so it's stale); an old bookmark to `briefs/<id>_latest.html` that stopped updating (re-bookmark
  `index.html`).
- **Revisit if:** A student needs sub-grouping (e.g. per term), or the history page wants a
  different home.

### ADR-009: Nightly scheduled refresh (the project's one background worker)
- **Date:** 2026-10-08
- **Status:** Active; schedule (03:00, catch-up only) superseded by ADR-011 — **ambitious choice, review first if anything misbehaves**
- **Decision:** A Windows Task Scheduler task (`TutorAuto nightly refresh`) runs
  `scripts/refresh.py` daily at 03:00, which chains ingest → brief for every active student
  with lessons → index. Catch-up is enabled: if the laptop was off or asleep at 03:00, the
  task runs at the next opportunity. Runs non-interactively: if Drive needs a browser
  login, it fails rather than hangs.
- **Why:** Theo's goal is opening a brief and finding it current with no command to run.
  Every step was already safe to repeat, so a daily rerun is cheap: one extraction call per
  *new* lesson, everything else pure SQL.
- **Rejected:** A manual `refresh` command before planning (Claude's recommendation: simpler,
  failures visible as they happen; Theo chose to be ambitious); running more often than
  daily (no benefit; lessons are planned a day or more ahead); a long-running watcher process.
- **Guardrails:** Every run is appended to `data/refresh.log`. Outcome goes in
  `data/last_refresh.json` and is shown on `briefs/index.html`, which also turns red when
  the last refresh is more than 36h old. The script exits non-zero on any error, so Task
  Scheduler's "Last Run Result" shows it too.
- **Failure signs:** Index red or "hours old" warning; briefs not changing after lessons;
  "Drive login needed" in the log (Google refresh token revoked or expired, so log in by hand
  once); the same lesson failing every night in `needs_review` (a stuck transcript, so
  check its reason); a surprise API bill (a title or alias change suddenly made many
  old lessons eligible, so use `ingest.py --dry-run` first).
- **Revisit if:** Silent failures happen in practice despite the guardrails, the laptop is
  rarely on so catch-up runs collide with lesson time, or the job ever needs to run where
  nobody can see the index page.

### ADR-008: Output is HTML in `/briefs/`, one brief per lesson, plus a history page
- **Date:** 2026-10-08
- **Status:** Active; file *location* superseded by ADR-010 (per-student folders)
- **Decision:** Theo consumes everything as HTML in a browser, starting from
  `briefs/index.html`. Per student: `<id>_latest.html` (pre-lesson brief),
  `<id>_<last lesson date>.html` (archive, one per lesson), and `<id>_history.html`
  (long-term coverage view, Phase 6, not yet built). Brief files are named after the
  lesson they follow, not the day they were generated. Recorded in `CLAUDE.md` →
  "How I consume the output".
- **Why:** CLAUDE.md only ever described "a markdown file", so the HTML output, the
  `_latest` pointer and the expectation of a continuously fresh brief were never written
  down, and nothing kept them up to date. Naming by lesson date makes the nightly rerun
  overwrite the same file until a new lesson arrives, so the archive holds one file per
  lesson, not 365 near-identical daily copies.
- **Rejected:** Markdown as the reading format (kept only as a plain-text copy); naming by
  generation date (older `twins_2026-09-08` / `twins_2026-10-08` files use that scheme and
  were left in place); LLM re-summarisation of old briefs into the history (unnecessary:
  history is a SQL view over `coverage_events`, so it stays exact, cheap and auditable).
- **Failure signs:** Duplicate-looking brief files; a brief whose date doesn't match the
  student's last lesson; the history page disagreeing with the briefs (they must read
  the same table).
- **Revisit if:** Theo wants briefs keyed on the *upcoming* lesson date (needs a timetable
  source, which we don't have), or wants output somewhere other than local files.

### ADR-007: Only lesson-shaped Drive titles are considered; out-of-scope syllabuses skipped
- **Date:** 2026-10-08
- **Status:** Active
- **Decision:** Ingest only considers Docs whose title starts with `Lesson:` or `W` + digits
  (case-insensitive). Everything else is ignored silently: no API call, no `needs_review`
  row. Typos (`Leson:`, `W:20`) are not rescued; Theo owns the titles. Titles that pass
  but match no student go to `needs_review` **once** (no duplicate rows on later runs), and
  are marked resolved automatically if the file later ingests. Students whose syllabus has
  no curriculum tree (A-Level today) are skipped with nothing written, so they ingest
  automatically once the tree exists (P-03).
- **Why:** The Meet folders mix lessons with business meetings. With a nightly run, every
  non-lesson would have re-entered `needs_review` every night. A-Level lessons would
  have cost an extraction call each and returned only `unmatched` noise.
- **Rejected:** A fuzzy title parser (CLAUDE.md says not to build one); reviewing every
  non-matching title; sorting common mistakes into review subfolders (parked as P-04).
- **Failure signs:** A real lesson silently missing from briefs (title typo; check it
  starts with `Lesson:` / `W<n>`); `needs_review` filling with former students (Finn,
  Scarlet, Daisy as of today) or "W2: Round up"-style business meetings that happen to
  carry a W prefix.
- **Revisit if:** Missed lessons from title typos become common, or the title convention
  changes.

### ADR-006: Transcripts are read from `Google Meet` and all its direct subfolders
- **Date:** 2026-10-08
- **Status:** Active
- **Decision:** Ingest lists Docs in the Drive folder `Google Meet` plus every direct
  subfolder (one level, which includes the legacy `Meet Recordings`), deduplicated by file ID.
- **Why:** Around August 2026 Meet switched from writing every Doc into `Meet Recordings`
  to one subfolder per meeting under `Google Meet`. Ingest only looked in `Meet Recordings`,
  so no lesson after 28 July was ever seen. That was the real reason briefs never
  refreshed.
- **Rejected:** Searching all of Drive by title (would pick up copies or shared files
  outside Meet's folders); hard-coding the subfolder list (grows every lesson).
- **Failure signs:** New lessons stop appearing even though the refresh says OK with
  0 new lessons (Meet changed its layout again: check where the newest Doc lives in Drive);
  "Multiple folders named 'Google Meet'" error; one lesson counted twice because a
  subfolder holds two Docs for it (restarted meeting, or Transcript + Notes by Gemini).
  One Drive call per subfolder, so the listing slows linearly over years (fine for now).
- **Revisit if:** Meet changes folder layout again, or the listing gets slow.

### ADR-005: Student active/inactive is a column, not a name marker
- **Date:** 2026-10-08
- **Status:** Active
- **Decision:** Track whether a student is currently taught via a dedicated `Active`
  column in `Students.xlsx` and a `students.active` field; names stay clean.
- **Why:** `student_id` and the matching alias are derived from the name, so
  `"Himmut (Inactive)"` would mint a new id and break title matching. Status must live
  in its own field.
- **Rejected:** Appending "(Inactive)" to the name (breaks identity); a separate
  "former students" table (overkill for a boolean).
- **Revisit if:** We need more than two states (e.g. "paused" vs "left" vs "prospective").

### ADR-004: Schema changes ship via an idempotent migration helper
- **Date:** 2026-10-08
- **Status:** Active
- **Decision:** New columns on existing tables are added through `schema_migrate.py`
  (checks `PRAGMA table_info`, `ALTER` only if missing); `schema.sql` carries the full
  shape for fresh databases. Every script calls `apply_schema()` instead of running
  `schema.sql` directly.
- **Why:** `CREATE TABLE IF NOT EXISTS` never alters an existing table, and sqlite has no
  "ADD COLUMN IF NOT EXISTS", so added columns would never reach the live DB otherwise.
- **Rejected:** Bare `ALTER` in `schema.sql` (errors on second run); rebuilding the DB
  from scratch (throws away real ingested lessons).
- **Revisit if:** We adopt a real migration framework, or need column drops/renames that
  this simple add-only helper can't express.

### ADR-003: Coverage is recorded per sub-skill, not per node
- **Date:** 2026-10-08
- **Status:** Active
- **Decision:** Each node is split into spec-clause sub-skills (`sub_skills` table,
  ids like `N8.3`); extraction emits one `coverage_events` row per sub-skill, each with
  its own status and quote.
- **Why:** Node-level coverage ("Surds, practised") hid *which* part was taught —
  Theo's core complaint. Sub-skill rows let status differ within a node (e.g. simplifying
  secure, rationalising struggled) and answer "only rationalising" precisely.
- **Rejected:** Node-level + a sharper evidence quote (still unqueryable); a full
  prerequisite sub-node tree (out of scope). Legacy node-level rows kept via a nullable
  `sub_skill_id`.
- **Revisit if:** The ~182-item sub-skill grain proves too fine to plan at in practice, or
  the longer constrained enum measurably hurts extraction accuracy.

### ADR-002: Nodes carry a short human-readable label
- **Date:** 2026-10-07
- **Status:** Active
- **Decision:** Add `curriculum_nodes.short_label` (e.g. "Surds") via a one-off,
  Theo-reviewed pass (`build_sublabels.py` reading `curriculum_labels_review.md`); the
  verbatim spec text stays in `topic`. The brief shows the label, not the spec text.
- **Why:** The full Edexcel spec sentence per node made briefs unreadable at a glance —
  Theo's single biggest readability complaint.
- **Rejected:** Letting the extraction call paraphrase spec text live (drifts from the
  spec's meaning, and isn't that call's job); hand-writing all ~97 labels blind.
- **Revisit if:** Labels start drifting from the spec's actual meaning, or the A-Level
  tree needs a different labelling convention.

### ADR-001: Extraction errs conservative (under-report over over-claim)
- **Date:** 2026-09-05
- **Status:** Active
- **Decision:** When it's ambiguous whether something was covered or which status fits,
  the extraction prompt biases to the lower reading — omit a borderline item, or downgrade
  status (introduced < practised < secure).
- **Why:** For planning, Theo prefers false negatives to false positives: better to
  re-cover something than to wrongly believe it's secure. Stated directly in Phase 3 eval.
- **Rejected:** Neutral/optimistic labelling that treats any mention as coverage.
- **Revisit if:** Briefs start systematically missing topics that were genuinely covered.
