# Decision Log (ADRs)

Significant decisions on this project, newest first. Claude maintains this; see
`CLAUDE.md` → "Session workflow and logs" for the rules. Status is `Active` or
`Superseded by ADR-XXX`. Old entries are never edited — a changed decision gets a
new entry that supersedes the old one.

From ADR-006 on, each entry also has a **Failure signs** line: what it looks like when
this decision is the cause of a problem. `CLAUDE.md` → "When something breaks" maps
symptoms back to these entries, so start there when debugging.

---

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
- **Status:** Active — **ambitious choice, review first if anything misbehaves**
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
