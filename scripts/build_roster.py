"""Load Students.xlsx into the students and aliases tables.

Students.xlsx is edited by hand and often (new starters added, grade
predictions updated), so this reads by header name rather than fixed
column position, and re-running is idempotent: each student is upserted
on student_id, never duplicated.

Only two exam types exist in the sheet today: "GCSE" and "A Level". Every
current GCSE student is Higher tier and every student is Edexcel, so
those are hard-coded here rather than read from a column that doesn't
exist yet. A-Level students get syllabus 'edexcel_alevel_maths' even
though no curriculum tree has been built for it yet (out of scope per
CLAUDE.md) -- they'll show 0 nodes on the gate query until that tree
exists, which is expected, not a bug.
"""

import datetime
import pathlib
import re
import sqlite3
import sys

import openpyxl

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from schema_migrate import apply_schema

DB_PATH = pathlib.Path("data/lessons.db")
ROSTER_PATH = pathlib.Path("Students.xlsx")

EXAM_TO_SYLLABUS = {
    "GCSE": "edexcel_gcse_higher",
    "A Level": "edexcel_alevel_maths",
}
EXAM_BOARD = "edexcel"


def slugify(name: str) -> str:
    lowered = name.strip().lower()
    return re.sub(r"\s+", "_", lowered)


def clean(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return value


def parse_active(value: object) -> int:
    # Absent or blank defaults to active; only an explicit negative marker
    # flips it off, so a student is never silently deactivated by a typo.
    text = clean(value)
    if text is None:
        return 1
    if str(text).strip().lower() in ("no", "inactive", "false", "0", "n"):
        return 0
    return 1


def read_roster(roster_path: pathlib.Path) -> list[dict]:
    workbook = openpyxl.load_workbook(roster_path, data_only=True)
    sheet = workbook.active

    rows = list(sheet.iter_rows(values_only=True))

    header_row_index = None
    for index, row in enumerate(rows):
        if any(clean(cell) == "Name" for cell in row):
            header_row_index = index
            break
    if header_row_index is None:
        raise ValueError(f"No header row containing 'Name' found in {roster_path}")

    headers = [clean(cell) for cell in rows[header_row_index]]

    students = []
    for row in rows[header_row_index + 1 :]:
        record = {}
        for header, value in zip(headers, row):
            if header is not None:
                record[header] = clean(value)
        if record.get("Name") is None:
            continue
        students.append(record)
    return students


def build_student_row(record: dict) -> dict:
    name = record["Name"]
    exam = record["Exam"]
    if exam not in EXAM_TO_SYLLABUS:
        raise ValueError(f"Unrecognised exam type {exam!r} for student {name!r}")

    exam_date = record.get("Exam Date")
    exam_date_str = None
    if isinstance(exam_date, datetime.datetime):
        exam_date_str = exam_date.date().isoformat()
    elif exam_date is not None:
        exam_date_str = str(exam_date)

    return {
        "student_id": slugify(name),
        "name": name,
        "exam": exam,
        "year_of_study": record.get("Year of Study"),
        "syllabus": EXAM_TO_SYLLABUS[exam],
        "exam_board": EXAM_BOARD,
        "exam_date": exam_date_str,
        "grade_prediction": record.get("Grade Prediction"),
        "confidence_level": record.get("Confidence Level"),
        "notes": record.get("Notes"),
        "active": parse_active(record.get("Active")),
    }


def write_students(connection: sqlite3.Connection, student_rows: list[dict]) -> None:
    for student in student_rows:
        connection.execute(
            """
            INSERT INTO students (
                student_id, name, exam, year_of_study, syllabus,
                exam_board, exam_date, grade_prediction, confidence_level, notes, active
            )
            VALUES (
                :student_id, :name, :exam, :year_of_study, :syllabus,
                :exam_board, :exam_date, :grade_prediction, :confidence_level, :notes, :active
            )
            ON CONFLICT(student_id) DO UPDATE SET
                name = excluded.name,
                exam = excluded.exam,
                year_of_study = excluded.year_of_study,
                syllabus = excluded.syllabus,
                exam_board = excluded.exam_board,
                exam_date = excluded.exam_date,
                grade_prediction = excluded.grade_prediction,
                confidence_level = excluded.confidence_level,
                notes = excluded.notes,
                active = excluded.active
            """,
            student,
        )
        connection.execute(
            """
            INSERT INTO aliases (alias, student_id)
            VALUES (:alias, :student_id)
            ON CONFLICT(alias) DO UPDATE SET student_id = excluded.student_id
            """,
            {"alias": student["student_id"], "student_id": student["student_id"]},
        )
    connection.commit()


def print_roster_report(connection: sqlite3.Connection) -> None:
    cursor = connection.execute(
        """
        SELECT s.name, s.exam, s.syllabus, s.active, COUNT(cn.node_id) AS node_count
        FROM students s
        LEFT JOIN curriculum_nodes cn ON cn.syllabus = s.syllabus
        GROUP BY s.student_id
        ORDER BY s.active DESC, s.name
        """
    )
    print(f"{'Name':<10} {'Exam':<8} {'Syllabus':<25} {'Active':<8} {'Nodes'}")
    for name, exam, syllabus, active, node_count in cursor.fetchall():
        active_label = "active" if active else "INACTIVE"
        print(f"{name:<10} {exam:<8} {syllabus:<25} {active_label:<8} {node_count}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    records = read_roster(ROSTER_PATH)
    student_rows = [build_student_row(record) for record in records]

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    apply_schema(connection)

    write_students(connection, student_rows)

    print(f"Loaded {len(student_rows)} students from {ROSTER_PATH}")
    print()
    print_roster_report(connection)
