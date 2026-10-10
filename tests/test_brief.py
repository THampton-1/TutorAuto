import pathlib
import sqlite3
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from brief import clean_text, gather_brief_data, get_all_lessons, render_inline_markup, split_summary


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
    # Secure in lesson 2, so no longer open.
    assert data["still_open"] == []


def test_archived_brief_ignores_lessons_that_came_later():
    connection = make_connection_with_two_lessons()
    first_lesson = get_all_lessons(connection, "ruby_t")[0]
    data = gather_brief_data(connection, "ruby_t", as_of_lesson=first_lesson)
    assert data["last_lesson"]["date"] == "2026-09-01"
    # As it stood after lesson 1, rationalising was a struggle -- shown as a
    # sticking point of that lesson, not as "still open from earlier".
    assert data["how_it_went"][0]["heading"] == "Sticking points"
    assert data["how_it_went"][0]["events"][0]["sub_skill_id"] == "N8.3"
    assert data["still_open"] == []


def test_struggle_from_an_earlier_lesson_stays_open_until_revisited():
    connection = make_connection_with_two_lessons()
    # Lesson 3: struggled with simplifying surds. Lesson 4: doesn't touch it.
    # The brief after lesson 4 should list it as open, one lesson since.
    connection.execute("INSERT INTO sub_skills VALUES ('N8.1', 'N8', 'Simplifying surds', 0)")
    connection.execute("INSERT INTO lessons (drive_file_id, student_id, date) VALUES ('f3', 'ruby_t', '2026-09-15')")
    connection.execute("INSERT INTO lessons (drive_file_id, student_id, date) VALUES ('f4', 'ruby_t', '2026-09-22')")
    connection.execute(
        "INSERT INTO coverage_events (lesson_id, student_id, node_id, sub_skill_id, status, evidence_quote, note, created_at) "
        "VALUES (3, 'ruby_t', 'N8', 'N8.1', 'struggled', 'q3', 'Could not find the largest square factor.', 'x')"
    )
    connection.commit()
    data = gather_brief_data(connection, "ruby_t")
    assert data["lesson_number"] == 4
    assert len(data["still_open"]) == 1
    open_unit = data["still_open"][0]
    assert open_unit["sub_skill_id"] == "N8.1"
    assert open_unit["lessons_since"] == 1
    assert open_unit["note"] == "Could not find the largest square factor."


def test_clean_text_removes_zero_width_characters_and_blank_text():
    assert clean_text("No homework was set.\u200b") == "No homework was set."
    assert clean_text("  \u200b ") is None
    assert clean_text(None) is None


def test_render_inline_markup_bolds_italicises_and_escapes():
    text = "**Struggled with *SAS*** when <b>triangles</b> overlapped; *x* × 2"
    rendered = render_inline_markup(text)
    assert "<strong>Struggled with <em>SAS</em></strong>" in rendered
    assert "&lt;b&gt;triangles&lt;/b&gt;" in rendered
    assert "<em>x</em> × 2" in rendered


def test_render_inline_markup_keeps_adjacent_italics_separate():
    # Seen in a real Eliza summary, 2026-10-10.
    rendered = render_inline_markup("relationships (*A* and *√C*)")
    assert rendered == "relationships (<em>A</em> and <em>√C</em>)"


def test_split_summary_one_bullet_per_line():
    assert split_summary("- **Covered** surds\n\n• Struggled with *√3*\u200b") == [
        "**Covered** surds",
        "Struggled with *√3*",
    ]
    assert split_summary(None) == []
