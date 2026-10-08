# Decision Log (ADRs)

Significant decisions on this project, newest first. Claude maintains this; see
`CLAUDE.md` → "Session workflow and logs" for the rules. Status is `Active` or
`Superseded by ADR-XXX`. Old entries are never edited — a changed decision gets a
new entry that supersedes the old one.

---

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
