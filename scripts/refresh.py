"""Nightly refresh: new lessons in, fresh briefs and index out.

This is the one script the scheduled task runs (ADR-009). It chains the
three manual steps:

    1. ingest.py      -- pull any new lesson transcripts from Drive, one
                         extraction call each (the only step that costs money)
    2. brief.py       -- regenerate every lesson's brief (archive + latest)
                         for each active student with lessons (pure SQL, free)
    3. build_index.py -- rebuild briefs/index.html, including a status line
                         for this run

Every step is safe to repeat: ingest skips lessons it already has, and
briefs are rebuilt from the database each time. Running it by hand is fine.

Nobody watches a scheduled job, so failures must be loud somewhere Theo
actually looks:
  - every run appends to data/refresh.log
  - data/last_refresh.json records the outcome, and index.html shows it
    (and warns if the last successful run is more than a day and a half old)
  - the process exits non-zero when the run as a whole failed (Drive or
    network unreachable, a brief or the index crashing), so Task
    Scheduler's "Last Run Result" shows it, and its restart-on-failure
    setting retries 15 minutes later -- useful when a catch-up run fires at
    boot before Wi-Fi is up. One lesson failing does NOT make the exit
    code non-zero: that would trigger restarts that re-attempt (and
    re-bill) the same failing lesson several times in one night. Per-lesson
    failures show on the index instead and retry the next night, capped by
    ingest.MAX_FAILED_ATTEMPTS.

When it runs (ADR-011): daily at 20:00, and one minute after every unlock
of the laptop, with catch-up if 20:00 was missed. The scheduled task passes
--if-stale, which exits silently if the last successful run was under
MIN_HOURS_BETWEEN_RUNS ago, so frequent unlocks don't pile up runs.

Usage: python scripts/refresh.py [--if-stale]
"""

import datetime
import json
import os
import pathlib
import sqlite3
import sys
import traceback

# Task Scheduler starts us in whatever directory it likes. Every path in
# this project is relative to the repo root, so move there first.
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from brief import write_all_briefs
from build_index import write_index
from ingest import run_ingest
from schema_migrate import apply_schema

DB_PATH = pathlib.Path("data/lessons.db")
LOG_PATH = pathlib.Path("data/refresh.log")
STATUS_PATH = pathlib.Path("data/last_refresh.json")
MIN_HOURS_BETWEEN_RUNS = 2


def now_local() -> str:
    # Local time with its UTC offset (e.g. +01:00 in BST), so both the log
    # and the index page read naturally and stay unambiguous across the
    # October/March clock changes.
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def make_logger(log_file):
    def log(line: str) -> None:
        stamped = f"[{now_local()}] {line}"
        print(stamped)
        log_file.write(stamped + "\n")
        log_file.flush()
    return log


def students_to_brief(connection: sqlite3.Connection) -> list[str]:
    """Active students with at least one ingested lesson.

    Inactive students keep whatever brief they last had. Active students
    with no lessons (today: every A-Level student, see P-03) have nothing
    to brief yet.
    """
    cursor = connection.execute(
        """
        SELECT s.student_id
        FROM students s
        WHERE s.active = 1
          AND EXISTS (SELECT 1 FROM lessons l WHERE l.student_id = s.student_id)
        ORDER BY s.student_id
        """
    )
    student_ids = []
    for (student_id,) in cursor.fetchall():
        student_ids.append(student_id)
    return student_ids


def count_open_reviews(connection: sqlite3.Connection) -> int:
    return connection.execute("SELECT COUNT(*) FROM needs_review WHERE resolved = 0").fetchone()[0]


def last_ok_run_is_recent(status: dict | None, now: datetime.datetime) -> bool:
    """True if the last refresh succeeded less than MIN_HOURS_BETWEEN_RUNS ago.

    The scheduled task fires on every unlock as well as at 20:00 (ADR-011),
    which can be many times a day. --if-stale uses this to skip runs that
    would change nothing. A failed last run never counts as recent, so the
    next unlock always retries it.
    """
    if status is None or not status.get("ok"):
        return False
    finished_at = datetime.datetime.fromisoformat(status["finished_at"])
    age = now - finished_at
    return age < datetime.timedelta(hours=MIN_HOURS_BETWEEN_RUNS)


def read_last_status() -> dict | None:
    if not STATUS_PATH.exists():
        return None
    try:
        return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def run_refresh() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    errors = []
    whole_run_failed = False
    ingest_counts = {}
    briefed = []

    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        log = make_logger(log_file)
        log("=== refresh started ===")

        connection = sqlite3.connect(DB_PATH)
        connection.execute("PRAGMA foreign_keys = ON")
        apply_schema(connection)

        # Step 1. If Drive or the API is unreachable, still carry on and
        # rebuild briefs from what we already have -- a stale-but-present
        # brief beats none, and the failure is surfaced on the index.
        try:
            ingest_counts = run_ingest(connection, interactive=False, log=log)
            log(f"ingest: {ingest_counts}")
            if ingest_counts.get("failed", 0) > 0:
                errors.append(f"{ingest_counts['failed']} lesson(s) failed to ingest; will retry next night (see needs_review)")
            if ingest_counts.get("held", 0) > 0:
                errors.append(f"{ingest_counts['held']} lesson(s) held after repeated failures; need your review (see needs_review)")
        except Exception as error:
            log("ingest FAILED:\n" + traceback.format_exc())
            errors.append(f"ingest failed: {type(error).__name__}: {error}")
            whole_run_failed = True

        # Step 2.
        for student_id in students_to_brief(connection):
            try:
                write_all_briefs(connection, student_id)
                briefed.append(student_id)
            except Exception as error:
                log(f"brief for {student_id} FAILED:\n" + traceback.format_exc())
                errors.append(f"brief for {student_id} failed: {type(error).__name__}: {error}")
                whole_run_failed = True
        log(f"briefs regenerated: {briefed}")

        open_reviews = count_open_reviews(connection)
        status = {
            "finished_at": now_local(),
            "ok": len(errors) == 0,
            "new_lessons": ingest_counts.get("ingested", 0),
            "open_reviews": open_reviews,
            "errors": errors,
        }
        STATUS_PATH.write_text(json.dumps(status, indent=2), encoding="utf-8")

        # Step 3.
        try:
            write_index(connection)
        except Exception as error:
            log("index FAILED:\n" + traceback.format_exc())
            errors.append(f"index failed: {type(error).__name__}: {error}")
            whole_run_failed = True

        if len(errors) == 0:
            log("=== refresh finished OK ===")
        else:
            log(f"=== refresh finished with {len(errors)} error(s): {errors} ===")

    if whole_run_failed:
        return 1
    return 0


if __name__ == "__main__":
    # Under some Task Scheduler setups there is no console at all and
    # sys.stdout is None; the log file is the real record anyway.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")

    # The scheduled task passes --if-stale; running by hand never skips.
    if "--if-stale" in sys.argv:
        now = datetime.datetime.now().astimezone()
        if last_ok_run_is_recent(read_last_status(), now):
            sys.exit(0)
    sys.exit(run_refresh())
