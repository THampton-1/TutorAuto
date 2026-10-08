import pathlib
import sqlite3
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))

from ingest import (
    build_output_schema,
    count_failed_attempts,
    is_lesson_title,
    mark_needs_review_resolved,
    normalize_title,
    record_needs_review,
    resolve_student,
)


def make_connection_with_aliases(aliases: dict[str, str]) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE aliases (alias TEXT PRIMARY KEY, student_id TEXT NOT NULL)")
    for alias, student_id in aliases.items():
        connection.execute("INSERT INTO aliases (alias, student_id) VALUES (?, ?)", (alias, student_id))
    connection.commit()
    return connection


def test_normalize_title_lowercases_and_splits_on_punctuation():
    assert normalize_title("W7: Twins lesson") == ["w7", "twins", "lesson"]


def test_resolve_student_matches_single_word_alias_anywhere_in_title():
    connection = make_connection_with_aliases({"twins": "twins", "saska": "saska"})
    student_id, reason = resolve_student(connection, "W7: Twins lesson  – 2026/05/15 18:32 BST")
    assert student_id == "twins"
    assert reason == "matched"


def test_resolve_student_matches_titles_without_lesson_prefix_convention():
    connection = make_connection_with_aliases({"saska": "saska", "daniel": "daniel"})
    student_id, reason = resolve_student(connection, "W13:saska")
    assert student_id == "saska"


def test_resolve_student_matches_multi_word_alias_as_consecutive_tokens():
    connection = make_connection_with_aliases({"ruby_t": "ruby_t"})
    student_id, reason = resolve_student(connection, "Lesson: Ruby T")
    assert student_id == "ruby_t"


def test_resolve_student_does_not_substring_match_inside_a_longer_name():
    # "ben" must not match inside "reuben" -- token comparison, not substring.
    connection = make_connection_with_aliases({"ben": "ben"})
    student_id, reason = resolve_student(connection, "Reuben catch up")
    assert student_id is None
    assert "no alias matched" in reason


def test_resolve_student_flags_zero_matches_as_needs_review():
    connection = make_connection_with_aliases({"twins": "twins"})
    student_id, reason = resolve_student(connection, "Divyalok round up meeting")
    assert student_id is None
    assert "no alias matched" in reason


def test_resolve_student_flags_ambiguous_matches():
    connection = make_connection_with_aliases({"ben": "ben", "twins": "twins"})
    student_id, reason = resolve_student(connection, "Ben and Twins joint session")
    assert student_id is None
    assert "ambiguous" in reason


def test_build_output_schema_includes_unmatched_alongside_valid_sub_skill_ids():
    schema = build_output_schema(["N1.1", "N1.2"])
    sub_skill_enum = schema["properties"]["coverage"]["items"]["properties"]["sub_skill_id"]["enum"]
    assert sub_skill_enum == ["N1.1", "N1.2", "unmatched"]


def test_is_lesson_title_accepts_lesson_and_week_prefixes():
    assert is_lesson_title("Lesson: Twins - 2026/10/01 18:02 BST – Transcript")
    assert is_lesson_title("lesson: Gabriel – 2026/09/14 15:56 BST – Notes by Gemini")
    assert is_lesson_title("W7: Twins lesson")
    assert is_lesson_title("W13:saska")
    assert is_lesson_title("w9: Ben lesson")
    assert is_lesson_title("W6 Himmut lesson")


def test_is_lesson_title_rejects_everything_else():
    # Typos are deliberately not rescued -- fixing the title is Theo's job.
    assert not is_lesson_title("Leson: Francis - 2026/09/23 12:46 BST")
    assert not is_lesson_title("W:20 Francis - 2026/08/19 10:02 BST")
    assert not is_lesson_title("ben lesson – 2026/06/08 19:21 BST")
    assert not is_lesson_title("Week 1: Myco Project Check-in")
    assert not is_lesson_title("Untitled meeting – 2026/09/14 15:22 BST")
    assert not is_lesson_title("mqe-btzs-tfz - 2026/09/08 17:46 BST")


def make_needs_review_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE needs_review (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drive_file_id TEXT NOT NULL,
            file_title TEXT NOT NULL,
            reason TEXT NOT NULL,
            resolved INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    return connection


def test_record_needs_review_does_not_duplicate_on_rerun():
    connection = make_needs_review_connection()
    for night in range(3):
        record_needs_review(connection, "file1", "W8: Finn lesson", "no alias matched")
    count = connection.execute("SELECT COUNT(*) FROM needs_review").fetchone()[0]
    assert count == 1


def test_mark_needs_review_resolved_clears_open_rows_for_that_file_only():
    connection = make_needs_review_connection()
    record_needs_review(connection, "file1", "Lesson: Twins", "APIError: overloaded")
    record_needs_review(connection, "file2", "W8: Finn lesson", "no alias matched")
    mark_needs_review_resolved(connection, "file1")
    open_ids = connection.execute("SELECT drive_file_id FROM needs_review WHERE resolved = 0").fetchall()
    assert open_ids == [("file2",)]


def test_failed_attempts_are_each_recorded_and_counted():
    connection = make_needs_review_connection()
    for night in range(3):
        record_needs_review(connection, "file1", "Lesson: Twins", "FAILED: RuntimeError: max_tokens", deduplicate=False)
    record_needs_review(connection, "file2", "W8: Finn lesson", "no alias matched")
    assert count_failed_attempts(connection, "file1") == 3
    assert count_failed_attempts(connection, "file2") == 0
    mark_needs_review_resolved(connection, "file1")
    assert count_failed_attempts(connection, "file1") == 0
