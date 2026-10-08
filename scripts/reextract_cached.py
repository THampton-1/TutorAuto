"""Re-run extraction on already-cached transcripts, in place.

When the extraction prompt or the curriculum changes (e.g. adding the sub-skill
layer), the coverage already in lessons.db is stale, but the transcripts are
still on disk under data/transcripts/. This re-extracts them without
re-downloading from Drive: for each selected lesson it deletes the old
coverage_events (and that lesson's unmatched rows) and rewrites them from a
fresh extraction call, keeping the same lesson row -- same drive_file_id, date
and student, so the lesson's identity and idempotency key are untouched.

Usage: python scripts/reextract_cached.py [student_id]
  With no student_id, re-extracts every lesson that still has a cached
  transcript file.

This is a maintenance tool, not part of the normal ingest path. It is the one
place coverage_events is deleted and rewritten, so back up lessons.db first if
the coverage currently in it matters.
"""

import pathlib
import sqlite3
import sys

import anthropic

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ingest import call_extraction, load_api_key, load_valid_nodes, write_coverage
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

    target_student_id = sys.argv[1] if len(sys.argv) > 1 else None

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    apply_schema(connection)

    client = anthropic.Anthropic(api_key=load_api_key())
    lessons = lessons_to_reextract(connection, target_student_id)

    for lesson in lessons:
        transcript_path = pathlib.Path(lesson["transcript_path"])
        if not transcript_path.exists():
            print(f"lesson {lesson['lesson_id']} ({lesson['date']}): SKIPPED -- no cached transcript at {transcript_path}")
            continue

        transcript_body = transcript_path.read_text(encoding="utf-8")
        nodes = load_valid_nodes(connection, lesson["syllabus"])
        coverage = call_extraction(client, transcript_body, nodes)

        # Clear this lesson's old coverage before rewriting, so re-running is
        # idempotent and never double-counts.
        connection.execute("DELETE FROM coverage_events WHERE lesson_id = ?", (lesson["lesson_id"],))
        connection.execute("DELETE FROM unmatched WHERE lesson_id = ?", (lesson["lesson_id"],))
        connection.commit()

        write_coverage(connection, lesson["lesson_id"], lesson["student_id"], coverage)
        print(f"lesson {lesson['lesson_id']} ({lesson['date']}, {lesson['student_id']}): {len(coverage)} coverage row(s) rewritten")
