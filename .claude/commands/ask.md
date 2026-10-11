---
description: Ask a question about a student's lessons, answered from lessons.db (read-only)
argument-hint: <question, e.g. "plan Saska's next lesson" or "has Eliza done bounds?">
allowed-tools: Bash(python:*), Read, Grep, Glob
---

Theo's question: **$ARGUMENTS**

Answer it from the lesson data already on disk. This is a quick lookup or a planning
draft, not a build task: no code changes, no new files.

## Where the data is

- `data/lessons.db` — **open it read-only, always**:
  `sqlite3.connect("file:data/lessons.db?mode=ro", uri=True)`, run through
  `python -c` or a heredoc, with `sys.stdout.reconfigure(encoding="utf-8")` first
  (the Windows console garbles curly quotes and maths symbols otherwise).
- `briefs/<student_id>/<student_id>_<date>.md` — each lesson's brief as text; the newest
  date is the current pre-lesson brief (there is no `_latest.md`, only `_latest.html`).
- `data/transcripts/<drive_file_id>.txt` (the path is in `lessons.transcript_path`) — the
  raw transcript. Read only when a specific quote or moment needs checking; they are long.

## Schema essentials (full definitions in `scripts/schema.sql`)

- `students(student_id, name, exam, syllabus, exam_date, grade_prediction,
  confidence_level, notes, active)` — ids are lowercase first names (`saska`, `twins`).
- `lessons(lesson_id, student_id, date, summary)` — `summary` is 4–6 bullet lines.
- `coverage_events(lesson_id, student_id, node_id, sub_skill_id, status, note,
  evidence_quote)` — one row per sub-skill per lesson; `note` says how it went.
- `curriculum_nodes(node_id, syllabus, module, short_label, topic, spec_order,
  stretch_content)` and `sub_skills(sub_skill_id, node_id, label)` — the spec.
  Show `short_label › sub-skill label`, never the dense `topic` spec text.
- `status`: introduced, practised, secure, struggled, revisit_requested.
  **Still open** = a sub-skill whose latest status is struggled or revisit_requested.

## How to answer

- Lead with the answer in one or two sentences, then the evidence: dates like
  "Tue 7 Oct (4 days ago)", status, and the note. Add a short verbatim quote only
  when it settles something.
- "Not in any ingested lesson" is not "never taught". Lessons only count from the first
  one ingested, and extraction under-reports on purpose (ADR-001). Say so whenever an
  absence matters, and offer to grep the transcripts.
- **Asked to plan a lesson:** draft it from the recent lessons, the open sticking points,
  how long since each topic was last seen, and the student's notes and predicted grade.
  Default to 60 minutes unless told otherwise. Give each block a timing and a one-line
  reason tied to evidence (date plus status or note). Theo makes every pedagogical
  decision (principle 7): present it as a draft with the alternatives you rejected, not
  a prescription.
- Keep it short: a terminal answer, not a report. End with at most one follow-up offer.

## Never

- Write to `lessons.db`, run `ingest.py` / `refresh.py` / `brief.py`, touch Drive, or
  make any API call. This command only reads.
- Send student data anywhere or put it in files. Answers stay in this conversation.
