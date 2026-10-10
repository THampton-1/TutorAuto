"""Ingest new lesson transcripts from Drive into lessons.db.

One LLM call per transcript (CLAUDE.md principle #1) -- everything else here
is ordinary deterministic Python. The model never sees who the student is,
their grade, or their confidence level: only the transcript body and the
list of valid node IDs for their syllabus (principles #2/#3). Idempotency
comes from the UNIQUE constraint on lessons.drive_file_id, not from tracking
a "last run" cursor -- re-running this script is always safe.

Student resolution matches whole word-tokens from the roster alias against
word-tokens in the Drive file title (both lowercased), rather than requiring
an exact "Lesson: Name" format. This handles real-world title drift (e.g.
"W7: Twins lesson", "W13:saska") without a separate backfill path -- see
THOUGHTS.md's open question on this, now resolved by this approach.

Drive files are found across "Google Meet" and all its per-meeting
subfolders (ADR-006), then filtered to lesson-shaped titles only (ADR-007).
Run nightly by refresh.py (ADR-009); safe to run by hand any time.
"""

import datetime
import os
import pathlib
import re
import sqlite3
import sys

import anthropic

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from drive_client import (
    export_transcript_text,
    extract_transcript_body,
    get_drive_service,
    list_all_meet_transcripts,
)
from schema_migrate import apply_schema

DB_PATH = pathlib.Path("data/lessons.db")
SCHEMA_PATH = pathlib.Path("scripts/schema.sql")
TRANSCRIPT_DIR = pathlib.Path("data/transcripts")
KEY_FILE = pathlib.Path(".secrets/TutorScan2- API Key.txt")
MODEL = "claude-sonnet-5"


def load_api_key() -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise RuntimeError(
        f"No API key found. Set ANTHROPIC_API_KEY or write the key to {KEY_FILE}."
    )

VALID_STATUSES = ["introduced", "practised", "secure", "struggled", "revisit_requested"]

SYSTEM_PROMPT_TEMPLATE = """\
You are analysing the transcript of a one-to-one maths tutoring lesson. Your \
job is to identify which curriculum sub-skills from the list below were \
covered in this lesson and how, and to summarise the lesson briefly for the \
tutor. You describe what happened; you never suggest what to teach next.

The curriculum is organised as nodes (a spec point, e.g. N8 Surds), each split \
into sub-skills (e.g. N8.3 Rationalising denominators). You report coverage at \
the sub-skill level, not the node level: a lesson that only rationalised \
denominators is N8.3 alone, not all of N8.

For each sub-skill actually discussed or practised in the transcript, report:

- sub_skill_id: the exact ID from the list below (e.g. "N8.3"). Never invent \
  an ID and never alter one.
- status: one of introduced, practised, secure, struggled, revisit_requested
    - introduced: the sub-skill was taught or explained for the first time this lesson
    - practised: the student worked through examples or questions on it
    - secure: the student demonstrated clear, confident understanding
    - struggled: the student had noticeable difficulty with it
    - revisit_requested: the tutor or student explicitly said this needs to
      be covered again in a future lesson
- evidence_quote: a short quote copied verbatim from the transcript that
  supports this classification. Do not paraphrase.
- note: ONE sentence, in your own words, saying what the student actually did \
  with this sub-skill in this lesson and how it went. Be specific to this \
  lesson: name the kind of question, the step they got right or wrong, the \
  misconception, or whether they needed prompting (e.g. "Rearranged the sine \
  rule correctly to find a side, but twice used the wrong angle until shown \
  how to relabel the triangle."). Never write a generic note that could \
  describe any lesson, such as "worked on this topic". The note must never \
  sound more positive than the status you gave: a practised row cannot read \
  as mastered, and a struggled row must say what the difficulty was.
- raw_label: leave this as an empty string when sub_skill_id is a real ID from
  the list below.

Report each covered sub-skill as its own row with its own status. If several \
sub-skills of the same node were covered, give a separate row for each -- their \
statuses may differ (e.g. simplifying surds secure, rationalising struggled). \
If a node was clearly covered but you genuinely cannot tell which sub-skill, \
choose the sub-skill the evidence best supports; never report a sub-skill with \
no supporting quote.

If the transcript clearly covers a maths topic that is NOT in the list below, \
report it with sub_skill_id "unmatched", still give a status and an \
evidence_quote, and set raw_label to a short plain-English description of the \
topic (e.g. "trigonometric identities").

Only report coverage actually evidenced in the transcript body. Do not infer
coverage from a lesson title, date, or anything outside the transcript text
itself.

When it is unclear whether a sub-skill was genuinely covered, or unclear which \
status best fits, prefer the more conservative reading. It is better to omit a \
borderline sub-skill entirely, or to under-state its status (introduced rather \
than practised, practised rather than secure), than to claim coverage or \
mastery the transcript does not clearly support.

After the coverage rows, write lesson_summary: a list of four to six \
bullet points for the tutor to skim before the next lesson, in the order the \
lesson happened. Each bullet is one or two short sentences. Together they say \
what the lesson covered, where the student was confident, where they had \
difficulty (be specific: the exact step, misconception, wrong value, or what \
they said), and anything the tutor or student explicitly said about homework \
or what to do next time. Keep that detail -- short sentences, not less \
information.

Formatting inside each bullet (it is rendered, so follow it exactly):
- Wrap the key phrase of the bullet in double asterisks, e.g. \
  **struggled to identify which triangles** to compare. One or two bold \
  phrases per bullet, so that reading only the bold gives the overview.
- Wrap mathematical expressions, formulae and named rules in single \
  asterisks, e.g. *½ab sin C*, *fg(x)*, *SAS*, *x² + 3x*.
- Never use asterisks for anything else. Write multiplication as × .
- Never use double quotation marks ("). When quoting the student or tutor, \
  use single quotes, e.g. said 'I'm really confused'.
- Do not start a bullet with "-" or "•"; each list item is already a bullet.
- If something was said about next time or homework, put it in the last \
  bullet, starting **Next time (tutor said):** or **Homework:** as fits.

Only mention topics that appear in your coverage rows. Follow the same \
conservative reading as the rows. Report what happened and what was said; \
never add your own recommendation of what to teach next -- the tutor makes \
that decision. Refer to "the tutor" and "the student" (or "the students" if \
more than one student is taking part); never use "he" or "she".

Curriculum nodes and their sub-skills for this student's syllabus:
{node_catalogue}
"""


# Only Drive titles that look like a lesson are considered at all: "Lesson:"
# (any case) or a week marker "W" + digits ("W7:", "W13:saska"). Everything
# else in the Meet folders -- business meetings, "Untitled meeting",
# auto-named "abc-defg-hij" calls -- is ignored silently: no API call, no
# needs_review row. Theo owns getting lesson titles into this form; typos
# like "Leson:" or "W:20" are deliberately NOT rescued (ADR-007).
LESSON_TITLE_PATTERN = re.compile(r"^\s*(lesson:|w\d+)", re.IGNORECASE)


def is_lesson_title(file_title: str) -> bool:
    return LESSON_TITLE_PATTERN.match(file_title) is not None


def normalize_title(file_title: str) -> list[str]:
    lowered = file_title.lower()
    return re.findall(r"[a-z0-9]+", lowered)


def resolve_student(connection: sqlite3.Connection, file_title: str) -> tuple[str | None, str]:
    title_tokens = normalize_title(file_title)

    cursor = connection.execute("SELECT alias, student_id FROM aliases")
    matched_student_ids = set()
    for alias, student_id in cursor.fetchall():
        alias_tokens = alias.split("_")
        window_size = len(alias_tokens)
        for start in range(len(title_tokens) - window_size + 1):
            if title_tokens[start : start + window_size] == alias_tokens:
                matched_student_ids.add(student_id)
                break

    if len(matched_student_ids) == 1:
        return matched_student_ids.pop(), "matched"
    if len(matched_student_ids) == 0:
        return None, f"no alias matched title {file_title!r}"
    return None, f"ambiguous: title {file_title!r} matched students {sorted(matched_student_ids)}"


def already_ingested(connection: sqlite3.Connection, drive_file_id: str) -> bool:
    cursor = connection.execute("SELECT 1 FROM lessons WHERE drive_file_id = ?", (drive_file_id,))
    return cursor.fetchone() is not None


def load_valid_nodes(connection: sqlite3.Connection, syllabus: str) -> list[dict]:
    cursor = connection.execute(
        """
        SELECT node_id, module, topic, short_label
        FROM curriculum_nodes
        WHERE syllabus = ?
        ORDER BY spec_order
        """,
        (syllabus,),
    )
    nodes = []
    for node_id, module, topic, short_label in cursor.fetchall():
        sub_cursor = connection.execute(
            "SELECT sub_skill_id, label FROM sub_skills WHERE node_id = ? ORDER BY sub_order",
            (node_id,),
        )
        sub_skills = []
        for sub_skill_id, label in sub_cursor.fetchall():
            sub_skills.append({"sub_skill_id": sub_skill_id, "label": label})
        nodes.append(
            {
                "node_id": node_id,
                "module": module,
                "topic": topic,
                "short_label": short_label,
                "sub_skills": sub_skills,
            }
        )
    return nodes


def collect_sub_skill_ids(nodes: list[dict]) -> list[str]:
    sub_skill_ids = []
    for node in nodes:
        for sub_skill in node["sub_skills"]:
            sub_skill_ids.append(sub_skill["sub_skill_id"])
    return sub_skill_ids


def build_node_catalogue(nodes: list[dict]) -> str:
    lines = []
    for node in nodes:
        header = node["short_label"] if node["short_label"] else node["topic"]
        lines.append(f"{node['node_id']} -- {node['module']} -- {header}")
        lines.append(f"    spec: {node['topic']}")
        lines.append("    sub-skills:")
        for sub_skill in node["sub_skills"]:
            lines.append(f"      {sub_skill['sub_skill_id']} {sub_skill['label']}")
    return "\n".join(lines)


def build_output_schema(valid_sub_skill_ids: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {
            "coverage": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "sub_skill_id": {"type": "string", "enum": valid_sub_skill_ids + ["unmatched"]},
                        "status": {"type": "string", "enum": VALID_STATUSES},
                        "evidence_quote": {"type": "string"},
                        "note": {"type": "string"},
                        "raw_label": {"type": "string"},
                    },
                    "required": ["sub_skill_id", "status", "evidence_quote", "note", "raw_label"],
                    "additionalProperties": False,
                },
            },
            # Listed after coverage on purpose: the model writes the rows
            # first, so the summary is grounded in what it has already
            # committed to rather than the other way round.
            "lesson_summary": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["coverage", "lesson_summary"],
        "additionalProperties": False,
    }


def call_extraction(client: anthropic.Anthropic, transcript_body: str, nodes: list[dict]) -> dict:
    """Returns {"coverage": [row, ...], "lesson_summary": [bullet, ...]} (ADR-012, ADR-014)."""
    valid_sub_skill_ids = collect_sub_skill_ids(nodes)
    node_catalogue = build_node_catalogue(nodes)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(node_catalogue=node_catalogue)

    # claude-sonnet-5 runs adaptive thinking by default (no "thinking" param
    # needed to enable it), and that thinking draws from the same max_tokens
    # budget as the JSON answer. A busy, long lesson can burn the whole
    # budget on thinking alone, leaving stop_reason="max_tokens" and zero
    # text blocks -- seen on a 62K-character transcript at max_tokens=8000.
    # Streaming with a much larger ceiling avoids both that failure and the
    # SDK's separate refusal to run a large max_tokens non-streaming.
    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        system=system_prompt,
        messages=[{"role": "user", "content": transcript_body}],
        output_config={"format": {"type": "json_schema", "schema": build_output_schema(valid_sub_skill_ids)}},
    ) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "max_tokens":
        raise RuntimeError(
            "Extraction call ran out of max_tokens before finishing -- "
            "raise max_tokens further or shorten the transcript."
        )

    text = next(block.text for block in response.content if block.type == "text")
    import json

    parsed = json.loads(text)
    return parsed


def summary_bullets_to_text(bullets: list[str]) -> str:
    """Store the summary bullets one per line in lessons.summary (ADR-014).

    Newlines inside a bullet are flattened to spaces so that "one line =
    one bullet" always holds when brief.py splits them back apart.
    """
    lines = []
    for bullet in bullets:
        line = " ".join(bullet.split())
        if line != "":
            lines.append(line)
    return "\n".join(lines)


def insert_lesson(
    connection: sqlite3.Connection,
    drive_file_id: str,
    student_id: str,
    date: str,
    transcript_path: pathlib.Path,
    summary: str,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO lessons (drive_file_id, student_id, date, transcript_path, processed_at, summary)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (drive_file_id, student_id, date, str(transcript_path), datetime.datetime.now(datetime.timezone.utc).isoformat(), summary),
    )
    connection.commit()
    return cursor.lastrowid


def write_coverage(
    connection: sqlite3.Connection,
    lesson_id: int,
    student_id: str,
    coverage: list[dict],
) -> None:
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for event in coverage:
        sub_skill_id = event["sub_skill_id"]
        if sub_skill_id == "unmatched":
            connection.execute(
                """
                INSERT INTO unmatched (lesson_id, raw_label, suggested_node, resolved_to)
                VALUES (?, ?, NULL, NULL)
                """,
                (lesson_id, event["raw_label"]),
            )
        else:
            # node_id is derived here from the authoritative sub_skills table
            # rather than parsed out of the ID string, so the stored node_id
            # can never drift from what the sub-skill actually belongs to.
            node_row = connection.execute(
                "SELECT node_id FROM sub_skills WHERE sub_skill_id = ?", (sub_skill_id,)
            ).fetchone()
            node_id = node_row[0]
            connection.execute(
                """
                INSERT INTO coverage_events
                    (lesson_id, student_id, node_id, sub_skill_id, status, evidence_quote, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (lesson_id, student_id, node_id, sub_skill_id, event["status"], event["evidence_quote"], event["note"], created_at),
            )
    connection.commit()


# Reasons written for a lesson that crashed mid-ingest start with this, so
# they can be counted separately from "no alias matched"-type reviews.
FAILURE_PREFIX = "FAILED: "

# A lesson that keeps failing may be failing *after* the paid extraction
# call (e.g. running out of max_tokens). Retrying it every night forever
# would bill every night forever, so after this many failed attempts it is
# held until Theo looks at it (set its needs_review rows to resolved = 1 to
# allow fresh attempts). Transient failures still get retried automatically
# on the following nights, up to this cap.
MAX_FAILED_ATTEMPTS = 3


def record_needs_review(
    connection: sqlite3.Connection,
    drive_file_id: str,
    file_title: str,
    reason: str,
    deduplicate: bool = True,
) -> None:
    # The nightly refresh sees the same unresolved file every night. Without
    # this check it would add a fresh, identical needs_review row each time.
    # Failed attempts are the exception (deduplicate=False): each one is its
    # own row, because counting them is what enforces MAX_FAILED_ATTEMPTS.
    if deduplicate:
        existing = connection.execute(
            "SELECT 1 FROM needs_review WHERE drive_file_id = ? AND reason = ? AND resolved = 0",
            (drive_file_id, reason),
        ).fetchone()
        if existing is not None:
            return
    connection.execute(
        "INSERT INTO needs_review (drive_file_id, file_title, reason, resolved) VALUES (?, ?, ?, 0)",
        (drive_file_id, file_title, reason),
    )
    connection.commit()


def count_failed_attempts(connection: sqlite3.Connection, drive_file_id: str) -> int:
    row = connection.execute(
        "SELECT COUNT(*) FROM needs_review WHERE drive_file_id = ? AND resolved = 0 AND reason LIKE ?",
        (drive_file_id, FAILURE_PREFIX + "%"),
    ).fetchone()
    return row[0]


def mark_needs_review_resolved(connection: sqlite3.Connection, drive_file_id: str) -> None:
    # Called once a file finally ingests (e.g. after Theo adds a missing
    # alias, or a transient API error clears), so old review rows for it
    # stop showing as outstanding.
    connection.execute(
        "UPDATE needs_review SET resolved = 1 WHERE drive_file_id = ? AND resolved = 0",
        (drive_file_id,),
    )
    connection.commit()


def ingest_one(
    connection: sqlite3.Connection,
    drive_service,
    anthropic_client: anthropic.Anthropic | None,
    transcript: dict,
    dry_run: bool = False,
) -> tuple[str, str]:
    """Process one Drive file. Returns (outcome, human-readable detail).

    outcome is one of: known, needs_review, out_of_scope, would_ingest,
    ingested. dry_run stops just before anything costs money or writes to
    the database.
    """
    drive_file_id = transcript["id"]
    file_title = transcript["name"]

    if already_ingested(connection, drive_file_id):
        return "known", "skipped (already ingested)"

    student_id, reason = resolve_student(connection, file_title)
    if student_id is None:
        if not dry_run:
            record_needs_review(connection, drive_file_id, file_title, reason)
        return "needs_review", f"needs_review ({reason})"

    cursor = connection.execute("SELECT syllabus FROM students WHERE student_id = ?", (student_id,))
    syllabus = cursor.fetchone()[0]
    nodes = load_valid_nodes(connection, syllabus)

    # No curriculum tree for this syllabus yet (all A-Level students today,
    # parked as P-03). An extraction call here could only return
    # "unmatched" rows -- money spent on noise. Nothing is written, so once
    # the tree exists the next run picks these lessons up automatically.
    if len(nodes) == 0:
        return "out_of_scope", f"skipped (no curriculum tree for {syllabus} yet)"

    if dry_run:
        return "would_ingest", f"would ingest -> student={student_id}"

    raw_text = export_transcript_text(drive_service, drive_file_id)
    transcript_body = extract_transcript_body(raw_text)

    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    transcript_path = TRANSCRIPT_DIR / f"{drive_file_id}.txt"
    transcript_path.write_text(transcript_body, encoding="utf-8")

    # The extraction call runs before any DB write for this lesson. If it
    # fails, nothing is committed, so a re-run does not see a phantom
    # "already ingested" row with no coverage attached to it.
    extraction = call_extraction(anthropic_client, transcript_body, nodes)
    coverage = extraction["coverage"]

    date = transcript["createdTime"][:10]
    lesson_id = insert_lesson(connection, drive_file_id, student_id, date, transcript_path, summary_bullets_to_text(extraction["lesson_summary"]))
    write_coverage(connection, lesson_id, student_id, coverage)
    mark_needs_review_resolved(connection, drive_file_id)

    return "ingested", f"ingested -> student={student_id}, {len(coverage)} coverage row(s)"


def run_ingest(
    connection: sqlite3.Connection,
    student_filter: str | None = None,
    dry_run: bool = False,
    interactive: bool = True,
    log=print,
) -> dict[str, int]:
    """Ingest every new lesson transcript Meet has written to Drive.

    Returns a count per outcome (known, needs_review, out_of_scope,
    would_ingest, ingested, failed, held, not_a_lesson) so the nightly refresh
    can summarise the run. `log` receives one line per file considered.
    """
    drive_service = get_drive_service(interactive)
    anthropic_client = None
    if not dry_run:
        anthropic_client = anthropic.Anthropic(api_key=load_api_key())
    transcripts = list_all_meet_transcripts(drive_service)

    counts = {
        "not_a_lesson": 0,
        "known": 0,
        "needs_review": 0,
        "out_of_scope": 0,
        "would_ingest": 0,
        "ingested": 0,
        "failed": 0,
        "held": 0,
    }
    for transcript in transcripts:
        if not is_lesson_title(transcript["name"]):
            counts["not_a_lesson"] += 1
            continue
        if student_filter is not None:
            resolved_student_id, _ = resolve_student(connection, transcript["name"])
            if resolved_student_id != student_filter:
                continue
        failed_attempts = count_failed_attempts(connection, transcript["id"])
        if failed_attempts >= MAX_FAILED_ATTEMPTS:
            counts["held"] += 1
            log(f"{transcript['name']!r}: HELD after {failed_attempts} failed attempts -- see needs_review")
            continue
        try:
            outcome, detail = ingest_one(connection, drive_service, anthropic_client, transcript, dry_run)
        except Exception as error:
            # One bad transcript (empty doc, extraction failure, transient
            # API error, ...) must not stop every other transcript in this
            # batch from being processed. Record it and move on; the next
            # run retries it (nothing was committed for it), up to
            # MAX_FAILED_ATTEMPTS.
            reason = f"{FAILURE_PREFIX}{type(error).__name__}: {error}"
            record_needs_review(connection, transcript["id"], transcript["name"], reason, deduplicate=False)
            outcome = "failed"
            detail = f"FAILED (attempt {failed_attempts + 1} of {MAX_FAILED_ATTEMPTS}), logged to needs_review -- {reason}"
        counts[outcome] += 1
        # Already-known lessons are the bulk of every run after the first;
        # listing them nightly would bury the lines that matter.
        if outcome != "known":
            log(f"{transcript['name']!r}: {detail}")

    return counts


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    # Optional flags:
    #   --student <student_id>  restrict the batch to one student's lessons
    #   --dry-run               list what would be ingested; no extraction
    #                           calls, no database writes, no cost
    student_filter = None
    dry_run = False
    arguments = sys.argv[1:]
    position = 0
    while position < len(arguments):
        if arguments[position] == "--student":
            student_filter = arguments[position + 1]
            position += 2
        elif arguments[position] == "--dry-run":
            dry_run = True
            position += 1
        else:
            print(f"Unknown argument {arguments[position]!r}")
            print("Usage: python scripts/ingest.py [--student <student_id>] [--dry-run]")
            sys.exit(1)

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    apply_schema(connection)

    counts = run_ingest(connection, student_filter, dry_run)
    print()
    print("Summary:", counts)
