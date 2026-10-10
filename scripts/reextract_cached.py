"""Re-run extraction on already-cached transcripts, in place.

When the extraction prompt or the curriculum changes (e.g. adding the sub-skill
layer), the coverage already in lessons.db is stale, but the transcripts are
still on disk under data/transcripts/. This re-extracts them without
re-downloading from Drive: for each selected lesson it deletes the old
coverage_events (and that lesson's unmatched rows) and rewrites them from a
fresh extraction call, keeping the same lesson row -- same drive_file_id, date
and student, so the lesson's identity and idempotency key are untouched.

Usage: python scripts/reextract_cached.py [student_id]
       python scripts/reextract_cached.py --lesson-ids 6 15 19
  With no argument, re-extracts every lesson that still has a cached
  transcript file. --lesson-ids repairs just those lessons (e.g. ones a
  check found damaged) without paying to re-extract everyone.

This is a maintenance tool, not part of the normal ingest path. It is the one
place coverage_events is deleted and rewritten, so back up lessons.db first if
the coverage currently in it matters.
"""

import pathlib
import sqlite3
import sys

import anthropic

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ingest import call_extraction, load_api_key, load_valid_nodes, summary_bullets_to_text, write_coverage
from schema_migrate import apply_schema

DB_PATH = pathlib.Path("data/lessons.db")


def lessons_to_reextract(connection: sqlite3.Connection, student_id: str | None) -> list[dict]:
    query = """
        SELECT l.lesson_id, l.student_id, l.date, l.transcript_path, s.syllabus
        FROM lessons l
        JOIN students s ON l.student_id = s.student_id
    """
    params: tuple = ()
    if student_id is not None:
        query += " WHERE l.student_id = ?"
        params = (student_id,)
    query += " ORDER BY l.date"

    lessons = []
    for lesson_id, sid, date, transcript_path, syllabus in connection.execute(query, params):
        lessons.append(
            {
                "lesson_id": lesson_id,
                "student_id": sid,
                "date": date,
                "transcript_path": transcript_path,
                "syllabus": syllabus,
            }
        )
    return lessons


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    target_student_id = None
    target_lesson_ids = None
    if len(sys.argv) > 1 and sys.argv[1] == "--lesson-ids":
        target_lesson_ids = []
        for argument in sys.argv[2:]:
            target_lesson_ids.append(int(argument))
    elif len(sys.argv) > 1:
        target_student_id = sys.argv[1]

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    apply_schema(connection)

    client = anthropic.Anthropic(api_key=load_api_key())
    lessons = lessons_to_reextract(connection, target_student_id)
    if target_lesson_ids is not None:
        selected_lessons = []
        for lesson in lessons:
            if lesson["lesson_id"] in target_lesson_ids:
                selected_lessons.append(lesson)
        lessons = selected_lessons

    for lesson in lessons:
        transcript_path = pathlib.Path(lesson["transcript_path"])
        if not transcript_path.exists():
            print(f"lesson {lesson['lesson_id']} ({lesson['date']}): SKIPPED -- no cached transcript at {transcript_path}")
            continue

        transcript_body = transcript_path.read_text(encoding="utf-8")
        nodes = load_valid_nodes(connection, lesson["syllabus"])
        extraction = call_extraction(client, transcript_body, nodes)
        coverage = extraction["coverage"]

        # Clear this lesson's old coverage before rewriting, so re-running is
        # idempotent and never double-counts. The lesson summary (ADR-012)
        # comes from the same call, so it is replaced alongside.
        connection.execute("DELETE FROM coverage_events WHERE lesson_id = ?", (lesson["lesson_id"],))
        connection.execute("DELETE FROM unmatched WHERE lesson_id = ?", (lesson["lesson_id"],))
        connection.execute(
            "UPDATE lessons SET summary = ? WHERE lesson_id = ?",
            (summary_bullets_to_text(extraction["lesson_summary"]), lesson["lesson_id"]),
        )
        connection.commit()

        write_coverage(connection, lesson["lesson_id"], lesson["student_id"], coverage)
        print(f"lesson {lesson['lesson_id']} ({lesson['date']}, {lesson['student_id']}): {len(coverage)} coverage row(s) rewritten")
