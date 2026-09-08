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
"""

import datetime
import pathlib
import re
import sqlite3
import sys

import anthropic

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from drive_client import (
    export_transcript_text,
    extract_transcript_body,
    find_meet_recordings_folder,
    get_drive_service,
    list_transcripts,
)

DB_PATH = pathlib.Path("data/lessons.db")
SCHEMA_PATH = pathlib.Path("scripts/schema.sql")
TRANSCRIPT_DIR = pathlib.Path("data/transcripts")
MODEL = "claude-sonnet-5"

VALID_STATUSES = ["introduced", "practised", "secure", "struggled", "revisit_requested"]

SYSTEM_PROMPT_TEMPLATE = """\
You are analysing the transcript of a one-to-one maths tutoring lesson. Your \
only job is to identify which curriculum points from the list below were \
covered in this lesson, and how.

For each curriculum point actually discussed or practised in the transcript, \
report:

- node_id: the exact ID from the list below. Never invent an ID and never \
  alter one.
- status: one of introduced, practised, secure, struggled, revisit_requested
    - introduced: the topic was taught or explained for the first time this lesson
    - practised: the student worked through examples or questions on it
    - secure: the student demonstrated clear, confident understanding
    - struggled: the student had noticeable difficulty with it
    - revisit_requested: the tutor or student explicitly said this needs to
      be covered again in a future lesson
- evidence_quote: a short quote copied verbatim from the transcript that
  supports this classification. Do not paraphrase.
- raw_label: leave this as an empty string when node_id is a real ID from
  the list below.

If the transcript clearly covers a maths topic that is NOT in the list
below, report it with node_id "unmatched", still give a status and an
evidence_quote, and set raw_label to a short plain-English description of
the topic (e.g. "trigonometric identities").

Only report coverage actually evidenced in the transcript body. Do not infer
coverage from a lesson title, date, or anything outside the transcript text
itself.

When it is unclear whether a curriculum point was genuinely covered, or
unclear which status best fits, prefer the more conservative reading. It is
better to omit a borderline point entirely, or to under-state its status
(introduced rather than practised, practised rather than secure), than to
claim coverage or mastery the transcript does not clearly support.

Curriculum points for this student's syllabus:
{node_catalogue}
"""


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
        SELECT node_id, module, topic
        FROM curriculum_nodes
        WHERE syllabus = ?
        ORDER BY spec_order
        """,
        (syllabus,),
    )
    nodes = []
    for node_id, module, topic in cursor.fetchall():
        nodes.append({"node_id": node_id, "module": module, "topic": topic})
    return nodes


def build_node_catalogue(nodes: list[dict]) -> str:
    lines = []
    for node in nodes:
        lines.append(f"{node['node_id']} -- {node['module']}: {node['topic']}")
    return "\n".join(lines)


def build_output_schema(valid_node_ids: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {
            "coverage": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "node_id": {"type": "string", "enum": valid_node_ids + ["unmatched"]},
                        "status": {"type": "string", "enum": VALID_STATUSES},
                        "evidence_quote": {"type": "string"},
                        "raw_label": {"type": "string"},
                    },
                    "required": ["node_id", "status", "evidence_quote", "raw_label"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["coverage"],
        "additionalProperties": False,
    }


def call_extraction(client: anthropic.Anthropic, transcript_body: str, nodes: list[dict]) -> list[dict]:
    valid_node_ids = [node["node_id"] for node in nodes]
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
        output_config={"format": {"type": "json_schema", "schema": build_output_schema(valid_node_ids)}},
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
    return parsed["coverage"]


def insert_lesson(
    connection: sqlite3.Connection,
    drive_file_id: str,
    student_id: str,
    date: str,
    transcript_path: pathlib.Path,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO lessons (drive_file_id, student_id, date, transcript_path, processed_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (drive_file_id, student_id, date, str(transcript_path), datetime.datetime.now(datetime.timezone.utc).isoformat()),
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
        if event["node_id"] == "unmatched":
            connection.execute(
                """
                INSERT INTO unmatched (lesson_id, raw_label, suggested_node, resolved_to)
                VALUES (?, ?, NULL, NULL)
                """,
                (lesson_id, event["raw_label"]),
            )
        else:
            connection.execute(
                """
                INSERT INTO coverage_events
                    (lesson_id, student_id, node_id, status, evidence_quote, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (lesson_id, student_id, event["node_id"], event["status"], event["evidence_quote"], created_at),
            )
    connection.commit()


def record_needs_review(connection: sqlite3.Connection, drive_file_id: str, file_title: str, reason: str) -> None:
    connection.execute(
        "INSERT INTO needs_review (drive_file_id, file_title, reason, resolved) VALUES (?, ?, ?, 0)",
        (drive_file_id, file_title, reason),
    )
    connection.commit()


def ingest_one(
    connection: sqlite3.Connection,
    drive_service,
    anthropic_client: anthropic.Anthropic,
    transcript: dict,
) -> str:
    drive_file_id = transcript["id"]
    file_title = transcript["name"]

    if already_ingested(connection, drive_file_id):
        return "skipped (already ingested)"

    student_id, reason = resolve_student(connection, file_title)
    if student_id is None:
        record_needs_review(connection, drive_file_id, file_title, reason)
        return f"needs_review ({reason})"

    cursor = connection.execute("SELECT syllabus FROM students WHERE student_id = ?", (student_id,))
    syllabus = cursor.fetchone()[0]
    nodes = load_valid_nodes(connection, syllabus)

    raw_text = export_transcript_text(drive_service, drive_file_id)
    transcript_body = extract_transcript_body(raw_text)

    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    transcript_path = TRANSCRIPT_DIR / f"{drive_file_id}.txt"
    transcript_path.write_text(transcript_body, encoding="utf-8")

    # The extraction call runs before any DB write for this lesson. If it
    # fails, nothing is committed, so a re-run does not see a phantom
    # "already ingested" row with no coverage attached to it.
    coverage = call_extraction(anthropic_client, transcript_body, nodes)

    date = transcript["createdTime"][:10]
    lesson_id = insert_lesson(connection, drive_file_id, student_id, date, transcript_path)
    write_coverage(connection, lesson_id, student_id, coverage)

    return f"ingested -> student={student_id}, {len(coverage)} coverage row(s)"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        connection.executescript(f.read())

    drive_service = get_drive_service()
    anthropic_client = anthropic.Anthropic()
    folder_id = find_meet_recordings_folder(drive_service)
    transcripts = list_transcripts(drive_service, folder_id, page_size=100)

    for transcript in transcripts:
        try:
            result = ingest_one(connection, drive_service, anthropic_client, transcript)
        except Exception as error:
            # One bad transcript (empty doc, extraction failure, transient
            # API error, ...) must not stop every other transcript in this
            # batch from being processed. Record it and move on; re-running
            # the script will retry it, since nothing was committed for it.
            record_needs_review(
                connection,
                transcript["id"],
                transcript["name"],
                f"{type(error).__name__}: {error}",
            )
            result = f"FAILED, logged to needs_review -- {type(error).__name__}: {error}"
        print(f"{transcript['name']!r}: {result}")
