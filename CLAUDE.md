# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Lesson planning pipeline

## What this is

A pipeline that turns tutoring lesson transcripts into a queryable record of what each
student has covered, so that lesson planning becomes a ten-minute decision made with full
context rather than a thirty-five-minute reconstruction from paper notes.

My main problem is, recalling short / long term content I have covered per student. In the short term (previous lesson) I want to get a bullet pointed doc - backed by quotes from the lesson, reminding me exactly what we covered last lesson. Long term, I want to be able to see what content we have covered over time, what topics have come up and when. This will give me enough context to build my 10 minute lesson structure. 

I (Theo) tutor GCSE and A-Level maths privately. I make every pedagogical decision. This
system supplies context and does nothing else.

## How to work with me

I have a strong maths background and a beginner in writing in Python, but this is my first full project of
this kind. That changes what I need from you:

- **Verify the environment before building on it.** Check Python version, that packages are
  actually installed and importable, that credentials resolve, that paths exist. Do not
  assume tooling is present because it usually is. A failing import at step one is cheap; a
  failing import at step forty is not.
- **Flag the things a seasoned engineer would notice and I would not.** Rate limits, silent
  truncation, encoding issues, timezone handling, files that look like data but aren't,
  anything that will work on three test cases and break on the thirtieth. Say so at the
  time, briefly.
- **Explain the why, not just the what.** When you make a non-obvious choice, give me one
  sentence on the reasoning. I want to be able to maintain this without you.
- **Stop and ask when a decision has a real tradeoff.** Don't quietly pick one.
- **Don't add scope.** If something isn't in the current phase, mention it and move on.

## Session workflow and logs

Three living files track how this project evolves. They are the first thing to read
each session and the record we update as we go:

- `DECISIONS.md` — the Decision Log (ADRs). **Claude maintains this.**
- `PARKING.md` — parked technical confusions and rabbit holes. **Theo leads this.**
- `SESSION_LOG.md` — carry-over notes handed from the end of one session to the start of the next.

### Session start: 5-bullet briefing

At the start of every session, before doing anything else, read `DECISIONS.md`,
`PARKING.md` and `SESSION_LOG.md` and give a 5-bullet summary:

1. **Where we are**: current state of the project in one line
2. **Last done**: what was completed last session
3. **Open decisions**: anything undecided or recently decided that affects next steps
4. **Parking lot**: the 1-2 most relevant parked items (and the count of the rest)
5. **Next**: what to do first — leading with anything recorded as carry-over in `SESSION_LOG.md`

Keep it to those 5 bullets. No preamble, then wait.

### Session end

Before we close, prompt Theo to name anything to continue with next session, and record
it in `SESSION_LOG.md` under "Carry-over". That is what bullet 5 surfaces next time.

### Working rules: decisions and parking

**Decision Log (`DECISIONS.md`) — Claude maintains this.**
- When we settle something significant (architecture, data format, tool choice, how a
  pipeline stage works, anything we'd be annoyed to re-argue), add an entry before moving
  on, and tell Theo in one line that you did.
- Each entry: what we decided, why, what we rejected, and what would make us revisit it.
- Never delete or rewrite old entries. If a decision changes, add a new entry and mark the
  old one `Superseded by ADR-XXX`.
- Before proposing a change in direction, check the log first; if it contradicts an
  existing decision, say so. Theo may also request an ADR, but Claude owns keeping them current.

**Parking Lot (`PARKING.md`) — Theo leads this.**
- When Theo says "park it" (or we hit a technical rabbit hole that isn't blocking
  progress), add it with a one-line description and why it matters, then keep moving.
- Never stop to fully resolve a parked item unless Theo asks.
- "parking lot" → show the open items. "resolve P-XX" → work on that one.

**After fixing a bug or technical problem**
- Give the root cause in 2 sentences of plain English: what broke, and why the fix works.
  Add a one-line Decision Log note only if it changes how we build things going forward.
- If Theo says "timebox", spend a fixed amount of effort, then report what you found even
  if it's incomplete.

**Shortcuts**
- `log it` → write the decision we just made into `DECISIONS.md`
- `park it` → add the current issue to `PARKING.md`
- `parking lot` → list open parked items
- `decisions` → list the Decision Log headings, newest first
- `where are we` → re-run the 5-bullet briefing

## Design principles — do not violate these

1. **One LLM call per transcript.** Its only job is the genuinely fuzzy part: reading a
   transcript and mapping what happened onto curriculum nodes. Everything downstream of
   that call is ordinary deterministic Python.
2. **Metadata is resolved deterministically, never inferred.** Which student, which date,
   which syllabus — all settled in code before the extraction call. The model sees the
   transcript body and nothing else.
3. **Constrained output.** The model is given the list of valid node IDs for that student's
   syllabus and must select from it, or return `unmatched`. It never invents an ID and
   never free-texts a topic name.
4. **Append-only.** `coverage_events` is a log. Nothing is ever updated or deleted. Current
   state is a derived view over the log, so a student's trajectory stays visible.
5. **Evidence on every row.** Each coverage event carries a short verbatim quote from the
   transcript. Any row must be auditable against the source in seconds.
6. **Idempotent ingest.** Re-running must never double-count. Every lesson is keyed on its
   Drive file ID.
7. **The system never picks a topic.** The brief proposes candidates with rationale. I choose.
8. **No outbound communication of any kind.** Nothing is sent to students or parents. No
   email, no messaging, no calendar writes. This is a read-and-summarise system.

## Stack

- Python 3.11+
- `sqlite3` from the standard library. No ORM.
- `anthropic` SDK for the extraction call.
- `google-api-python-client` and `google-auth-oauthlib` for Drive access.
- No web framework, no async, no background workers.

**Style:** explicit over clever. Prefer named loops and plain `if` statements to
comprehension chains, `lambda`, and dense one-liners. I want to be able to read every line
without reconstructing it. Type hints on function signatures.

## Models

- Spec parsing (one-off): `claude-opus-5`
- Transcript extraction (recurring): `claude-sonnet-5`

## Repo layout

```
/specs/            source PDFs, read-only
/eval/             three hand-labelled transcripts plus my answer key
/data/lessons.db   sqlite database
/Students.xlsx     roster, hand-edited — students, exam, grade prediction, confidence, notes
/scripts/          drive_client.py, build_curriculum.py, build_roster.py, schema.sql,
                   ingest.py, brief.py
/tests/            pytest tests for the pure logic in /scripts (no live API calls)
/.secrets/         OAuth client secret and token — gitignored
```

## Transcript source — Google Meet via Drive

Lessons are recorded in Google Meet. Meet writes transcripts into a Drive folder as **Google
Docs, not text files.**

This matters: syncing the folder with Drive for Desktop produces `.gdoc` files, which are a
few lines of JSON containing a URL. They are pointers, not content. Local folder sync does
not work for this. Use the Drive API and export each Doc with `mimeType='text/plain'`.

Meet names each transcript after the calendar event. I have renamed my recurring events to
the form `Ruby T — A-Level maths`, so titles arrive already structured. Do not build a
parser clever enough to cope with arbitrary titles — the roster lookup below is the whole
mechanism.

### Ingest loop

1. List files in the Meet Recordings folder modified since the last run.
2. Skip any whose Drive `fileId` already appears in `lessons`.
3. Export the Doc to plain text.
4. Resolve the student: lowercase the file title, match against the alias list in
   `aliases`. Exactly one match proceeds. Zero matches or more than one goes to
   `needs_review` and is left alone.
5. Resolve the date from the Drive `createdTime` field. Do not parse dates from titles —
   "week 17" is not a date.
6. Look up that student's syllabus and load the valid node IDs for it.
7. One extraction call with the transcript body.

## Schema

`scripts/schema.sql` is the single source of truth for table definitions — every script
that touches `lessons.db` runs it (idempotent, `CREATE TABLE IF NOT EXISTS`) rather than
declaring tables inline. Summary:

```sql
curriculum_nodes(node_id PK, syllabus, module, topic, spec_order, stretch_content)
students(student_id PK, name, exam, year_of_study, syllabus, exam_board, exam_date,
         grade_prediction, confidence_level, notes)
aliases(alias PK, student_id)
lessons(lesson_id PK, drive_file_id UNIQUE, student_id, date,
        transcript_path, processed_at)
coverage_events(event_id PK, lesson_id, student_id, node_id,
                status, evidence_quote, created_at)
unmatched(id PK, lesson_id, raw_label, suggested_node, resolved_to)
needs_review(id PK, drive_file_id, file_title, reason, resolved)
```

`status` is one of: `introduced`, `practised`, `secure`, `struggled`, `revisit_requested`.

`node_id` is the official Edexcel specification point reference, taken verbatim from the
spec document. It is never invented and never renamed.

`stretch_content` flags nodes marked bold in the source spec — content grade 7+ students
are likely to be pushed on, still examinable for everyone. Purely for planning context.

`students.student_id` is the lowercased, underscore-joined student name (e.g. `ruby_t`) —
also the sole seed row in `aliases` for that student. `exam` is `GCSE` or `A Level`, read
straight from `Students.xlsx`; `syllabus` is derived from it deterministically
(`build_roster.py`'s `EXAM_TO_SYLLABUS` map — currently `edexcel_gcse_higher` for GCSE,
`edexcel_alevel_maths` for A Level). All current students are Edexcel; all current GCSE
students are Higher tier — both hard-coded for now since the sheet has no board/tier column
and only one curriculum tree exists. A-Level students correctly show 0 matching nodes until
an A-Level tree is built (out of scope for this pass, see below).

`grade_prediction`, `confidence_level`, and `notes` are loaded but not consumed by anything
yet — they exist for Phase 4's stretch-content filtering (e.g. don't suggest bold/stretch
nodes to a low-confidence, sub-7 student) and are stored now so no backfill is needed later.

"Twins" is a deliberate single `students` row for two real students who are always taught
together and always receive identical coverage — a joint decision, not a data error. If
their coverage ever needs to diverge, this row will need to split into two.

`drive_file_id` carries the UNIQUE constraint that makes ingest idempotent.

## Build phases

Work one phase at a time. Stop at each gate and wait for me to verify before continuing.

**Phase 0 — Drive access.** Set up OAuth, list the Meet Recordings folder, export one
transcript to plain text and print the first 500 characters alongside the file's title and
`createdTime`. Nothing else.
Gate: real transcript text on screen. Do this before anything else — if auth is going to be
painful I want to know in the first twenty minutes, not at hour four.

**Phase 1 — curriculum tree.** Parse the spec PDFs in `/specs/` into `curriculum_nodes`.
Work only from the documents; supply nothing from memory, and list anything ambiguous rather
than filling the gap.
Gate: a completeness report comparing the count of numbered points in each source document
against rows written, plus a check that `spec_order` is monotonic within each module.

**Phase 2 — schema and roster.** Create the database, load students and aliases.
Gate: I can query any student's syllabus and see the right node count.

**Phase 3 — extraction.** Build `ingest.py`. Run it against the three transcripts in
`/eval/` and print a comparison against my hand-written answer key. Expect several rounds of
prompt iteration here — this is the phase that matters.
Gate: agreement with my labels on all three, or disagreements I have explicitly accepted.

**Phase 4 — brief generator.** Build `brief.py`, producing one markdown file per upcoming
lesson containing: last lesson summary, nodes touched with status and quote, explicit
revisit requests, nodes marked `struggled` and not revisited since, and three candidate next
topics with a one-line rationale each.
Gate: I read a real brief and can make a planning decision from it alone.

## Out of scope for v1

- Payment logging and reminders
- A prerequisite graph between nodes (the spec does not encode this; I will add it by hand
  later if the brief needs it)
- Undergraduate teaching — there is no published specification to map onto, so it stays manual
- Any user interface beyond files on disk

## Consent and privacy

Lessons are recorded with parental consent on file. Transcripts stay local and are sent
nowhere other than the extraction call. `/.secrets/`, `/data/`, and `Students.xlsx` (real
student names, grade predictions, notes) are gitignored — this repo has a real GitHub
remote, so none of these should ever enter git history.
