import pathlib
import sqlite3
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from brief import gather_brief_data, get_all_lessons


def make_connection_with_two_lessons() -> sqlite3.Connection:
    """One student, one sub-skill: struggled in lesson 1, secure in lesson 2."""
    connection = sqlite3.connect(":memory:")
    connection.executescript((REPO_ROOT / "scripts" / "schema.sql").read_text(encoding="utf-8"))
    connection.execute(
        "INSERT INTO curriculum_nodes VALUES ('N8', 'gcse', 'Number', 'surds spec text', 1, 0, 'Surds')"
    )
    connection.execute("INSERT INTO sub_skills VALUES ('N8.3', 'N8', 'Rationalising denominators', 1)")
    connection.execute(
        "INSERT INTO students (student_id, name, exam, year_of_study, syllabus, exam_board) "
        "VALUES ('ruby_t', 'Ruby T', 'GCSE', '11', 'gcse', 'Edexcel')"
    )
    connection.execute("INSERT INTO lessons (drive_file_id, student_id, date) VALUES ('f1', 'ruby_t', '2026-09-01')")
    connection.execute("INSERT INTO lessons (drive_file_id, student_id, date) VALUES ('f2', 'ruby_t', '2026-09-08')")
    connection.execute(
        "INSERT INTO coverage_events (lesson_id, student_id, node_id, sub_skill_id, status, evidence_quote, created_at) "
        "VALUES (1, 'ruby_t', 'N8', 'N8.3', 'struggled', 'q1', 'x')"
    )
    connection.execute(
        "INSERT INTO coverage_events (lesson_id, student_id, node_id, sub_skill_id, status, evidence_quote, created_at) "
        "VALUES (2, 'ruby_t', 'N8', 'N8.3', 'secure', 'q2', 'x')"
    )
    connection.commit()
    return connection


def test_get_all_lessons_returns_oldest_first():
    connection = make_connection_with_two_lessons()
    dates = []
    for lesson in get_all_lessons(connection, "ruby_t"):
        dates.append(lesson["date"])
    assert dates == ["2026-09-01", "2026-09-08"]


def test_latest_brief_sees_every_lesson():
    connection = make_connection_with_two_lessons()
    data = gather_brief_data(connection, "ruby_t")
    assert data["last_lesson"]["date"] == "2026-09-08"
    # Secure in lesson 2, so no longer listed as struggled.
    assert data["struggled_nodes"] == []


def test_archived_brief_ignores_lessons_that_came_later():
    connection = make_connection_with_two_lessons()
    first_lesson = get_all_lessons(connection, "ruby_t")[0]
    data = gather_brief_data(connection, "ruby_t", as_of_lesson=first_lesson)
    assert data["last_lesson"]["date"] == "2026-09-01"
    struggled_ids = []
    for unit in data["struggled_nodes"]:
        struggled_ids.append(unit["sub_skill_id"])
    # As it stood after lesson 1, rationalising was still a struggle.
    assert struggled_ids == ["N8.3"]
