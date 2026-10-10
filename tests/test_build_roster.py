import datetime
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))

from build_roster import build_student_row, slugify


def test_slugify_lowercases_and_joins_spaces():
    assert slugify("Ruby T") == "ruby_t"


def test_slugify_strips_trailing_whitespace():
    assert slugify("Twins  ") == "twins"


def test_gcse_student_maps_to_edexcel_gcse_higher():
    record = {
        "Name": "Twins",
        "Exam": "GCSE",
        "Year of Study": "Year 11",
        "Exam Date": datetime.datetime(2026, 5, 15),
        "Grade Prediction": "Grade 8",
        "Confidence Level": "Very High",
        "Notes": "2 students, taught together",
    }
    row = build_student_row(record)
    assert row["student_id"] == "twins"
    assert row["syllabus"] == "edexcel_gcse_higher"
    assert row["exam_board"] == "edexcel"
    assert row["exam_date"] == "2026-05-15"


def test_a_level_student_maps_to_edexcel_alevel_maths():
    record = {
        "Name": "Ben",
        "Exam": "A Level",
        "Year of Study": "Year 1",
        "Exam Date": None,
        "Grade Prediction": "B",
        "Confidence Level": "Low",
        "Notes": None,
    }
    row = build_student_row(record)
    assert row["syllabus"] == "edexcel_alevel_maths"
    assert row["exam_date"] is None


def test_unrecognised_exam_type_raises():
    record = {"Name": "Mystery", "Exam": "IB", "Year of Study": None, "Exam Date": None}
    try:
        build_student_row(record)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_syllabus_since_read_from_date_cell():
    import datetime
    record = {"Name": "Francis", "Exam": "A Level", "Syllabus Since": datetime.datetime(2026, 7, 1)}
    assert build_student_row(record)["syllabus_since"] == "2026-07-01"


def test_syllabus_since_blank_means_every_lesson_counts():
    record = {"Name": "Saska", "Exam": "A Level"}
    assert build_student_row(record)["syllabus_since"] is None


def test_syllabus_since_rejects_non_dates():
    import pytest
    record = {"Name": "Francis", "Exam": "A Level", "Syllabus Since": "September"}
    with pytest.raises(ValueError):
        build_student_row(record)
