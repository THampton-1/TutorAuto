import pathlib
import sqlite3
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))

from ingest import build_output_schema, normalize_title, resolve_student


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


def test_build_output_schema_includes_unmatched_alongside_valid_node_ids():
    schema = build_output_schema(["N1", "N2"])
    node_id_enum = schema["properties"]["coverage"]["items"]["properties"]["node_id"]["enum"]
    assert node_id_enum == ["N1", "N2", "unmatched"]
