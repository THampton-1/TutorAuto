"""Apply schema.sql plus any idempotent column additions.

schema.sql uses CREATE TABLE IF NOT EXISTS, which (correctly) will not touch a
table that already exists -- so a column added to a table after its first
release never reaches an existing database from the CREATE statement alone.
sqlite has no "ADD COLUMN IF NOT EXISTS", so we check PRAGMA table_info first
and ALTER only when the column is missing.

Fresh databases get the new columns straight from schema.sql's CREATE
statements; existing ones get them here. Both paths converge on the same shape.
Every script that opens lessons.db should call apply_schema() instead of
running schema.sql directly, so this stays the single place the two paths meet.
"""

import pathlib
import sqlite3

SCHEMA_PATH = pathlib.Path("scripts/schema.sql")

# (table, column, column definition) for columns introduced after the table's
# first release. Applied only when absent, so this is safe to run every time.
# FK clauses are intentionally omitted here: sqlite's ALTER ADD COLUMN cannot
# add a column with a REFERENCES clause, and the CREATE statements in
# schema.sql already carry the references for fresh databases.
_ADDED_COLUMNS = [
    ("curriculum_nodes", "short_label", "TEXT"),
    ("coverage_events", "sub_skill_id", "TEXT"),
    ("students", "active", "INTEGER NOT NULL DEFAULT 1"),
]


def apply_schema(connection: sqlite3.Connection) -> None:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        connection.executescript(f.read())

    for table, column, column_def in _ADDED_COLUMNS:
        existing_columns = [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
        if column not in existing_columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_def}")

    connection.commit()
