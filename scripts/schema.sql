-- Full schema for data/lessons.db. Single source of truth: every table
-- creation goes through this file, executed with executescript() so
-- CREATE TABLE IF NOT EXISTS statements stay idempotent.

CREATE TABLE IF NOT EXISTS curriculum_nodes (
    node_id TEXT PRIMARY KEY,
    syllabus TEXT NOT NULL,
    module TEXT NOT NULL,
    topic TEXT NOT NULL,
    spec_order INTEGER NOT NULL,
    stretch_content INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    exam TEXT NOT NULL,
    year_of_study TEXT NOT NULL,
    syllabus TEXT NOT NULL,
    exam_board TEXT NOT NULL,
    exam_date TEXT,
    grade_prediction TEXT,
    confidence_level TEXT,
    notes TEXT
);

-- One row per title variant that should resolve to a student. Seeded with
-- just the roster name for now; historical/backfilled transcript titles
-- that don't match the current "Lesson: Name" convention can be added
-- here by hand without touching students.
CREATE TABLE IF NOT EXISTS aliases (
    alias TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES students(student_id)
);

CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
    drive_file_id TEXT NOT NULL UNIQUE,
    student_id TEXT NOT NULL REFERENCES students(student_id),
    date TEXT NOT NULL,
    transcript_path TEXT,
    processed_at TEXT
);

CREATE TABLE IF NOT EXISTS coverage_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL REFERENCES lessons(lesson_id),
    student_id TEXT NOT NULL REFERENCES students(student_id),
    node_id TEXT NOT NULL REFERENCES curriculum_nodes(node_id),
    status TEXT NOT NULL,
    evidence_quote TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS unmatched (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL REFERENCES lessons(lesson_id),
    raw_label TEXT NOT NULL,
    suggested_node TEXT,
    resolved_to TEXT
);

CREATE TABLE IF NOT EXISTS needs_review (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drive_file_id TEXT NOT NULL,
    file_title TEXT NOT NULL,
    reason TEXT NOT NULL,
    resolved INTEGER NOT NULL DEFAULT 0
);
