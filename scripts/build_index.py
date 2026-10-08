"""Build briefs/index.html -- one link per roster student to their latest brief.

Pure read over students + lessons; writes no new data. Run this after
regenerating briefs so the index reflects whichever students you've
actually run brief.py for.

The page also shows the outcome of the last nightly refresh, read from
data/last_refresh.json (written by refresh.py), and warns -- live, in the
browser -- when that refresh is more than 36 hours old. That staleness
check is the only thing that would catch the scheduled task silently
not running at all (laptop off for days, task disabled), since a job
that never starts can't report its own failure.

Usage: python scripts/build_index.py
"""

import html
import json
import pathlib
import sqlite3

DB_PATH = pathlib.Path("data/lessons.db")
BRIEF_DIR = pathlib.Path("briefs")
STATUS_PATH = pathlib.Path("data/last_refresh.json")
STALE_AFTER_HOURS = 36

INDEX_STYLE = """\
:root {
  color-scheme: light dark;
  --bg: #ffffff;
  --fg: #1a1a1a;
  --muted: #666666;
  --border: #dddddd;
  --card-bg: #f7f7f8;
  --ok: #2e7d32;
  --bad: #c62828;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1a1a1a;
    --fg: #eaeaea;
    --muted: #a0a0a0;
    --border: #3a3a3a;
    --card-bg: #242424;
    --ok: #66bb6a;
    --bad: #ef5350;
  }
}
body {
  background: var(--bg);
  color: var(--fg);
  font-family: -apple-system, Segoe UI, Helvetica, Arial, sans-serif;
  max-width: 640px;
  margin: 0 auto;
  padding: 2rem 1.25rem 4rem;
  line-height: 1.5;
}
.meta { color: var(--muted); font-size: 0.9rem; margin-bottom: 2rem; }
a.card {
  display: block;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.9rem 1.1rem;
  margin-bottom: 0.7rem;
  text-decoration: none;
  color: var(--fg);
}
a.card:hover { border-color: var(--fg); }
a.card .name { font-weight: 600; font-size: 1.05rem; }
a.card .sub { color: var(--muted); font-size: 0.85rem; margin-top: 0.15rem; }
.no-brief { opacity: 0.55; }
.status {
  border: 1px solid var(--border);
  border-left: 4px solid var(--ok);
  border-radius: 6px;
  padding: 0.6rem 0.9rem;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}
.status.bad { border-left-color: var(--bad); }
.status ul { margin: 0.4rem 0 0; padding-left: 1.2rem; }
"""


def get_students_with_last_lesson_date(connection: sqlite3.Connection) -> list[dict]:
    cursor = connection.execute(
        """
        SELECT s.student_id, s.name, s.syllabus, MAX(l.date)
        FROM students s
        LEFT JOIN lessons l ON l.student_id = s.student_id
        GROUP BY s.student_id
        ORDER BY s.name
        """
    )
    students = []
    for student_id, name, syllabus, last_lesson_date in cursor.fetchall():
        students.append(
            {
                "student_id": student_id,
                "name": name,
                "syllabus": syllabus,
                "last_lesson_date": last_lesson_date,
            }
        )
    return students


def load_refresh_status() -> dict | None:
    if not STATUS_PATH.exists():
        return None
    return json.loads(STATUS_PATH.read_text(encoding="utf-8"))


def render_status_html(status: dict | None) -> str:
    if status is None:
        return "<div class='status bad'>No nightly refresh has run yet.</div>"

    finished_at = html.escape(status["finished_at"])
    css_class = "status" if status["ok"] else "status bad"
    if status["ok"]:
        headline = f"Last refresh {finished_at}: OK, {status['new_lessons']} new lesson(s)."
    else:
        headline = f"Last refresh {finished_at}: FAILED. See data/refresh.log."

    parts = []
    # data-finished feeds the staleness check script below the cards.
    parts.append(f"<div class='{css_class}' id='refresh-status' data-finished='{finished_at}'>")
    parts.append(f"<div>{headline}</div>")
    if status["open_reviews"] > 0:
        parts.append(f"<div>{status['open_reviews']} Drive file(s) waiting in needs_review.</div>")
    if len(status["errors"]) > 0:
        parts.append("<ul>")
        for error in status["errors"]:
            parts.append(f"<li>{html.escape(error)}</li>")
        parts.append("</ul>")
    parts.append("</div>")
    return "".join(parts)


STALENESS_SCRIPT = f"""
<script>
(function () {{
  var box = document.getElementById("refresh-status");
  if (!box) {{ return; }}
  var finished = new Date(box.getAttribute("data-finished"));
  var hoursOld = (Date.now() - finished.getTime()) / 3600000;
  if (hoursOld > {STALE_AFTER_HOURS}) {{
    box.className = "status bad";
    var warning = document.createElement("div");
    warning.textContent = "Warning: this is " + Math.round(hoursOld) +
      " hours old. The nightly refresh may not be running.";
    box.appendChild(warning);
  }}
}})();
</script>
"""


def render_index_html(students: list[dict], status: dict | None) -> str:
    parts = []
    parts.append("<!doctype html><html><head><meta charset='utf-8'>")
    parts.append("<meta name='viewport' content='width=device-width, initial-scale=1'>")
    parts.append("<title>Lesson briefs</title>")
    parts.append(f"<style>{INDEX_STYLE}</style></head><body>")
    parts.append("<h1>Lesson briefs</h1>")
    parts.append(render_status_html(status))

    for student in students:
        # Briefs live in briefs/<id>/ (ADR-010); the link is relative to
        # index.html, which sits at the top of briefs/.
        student_id = student["student_id"]
        relative_href = f"{student_id}/{student_id}_latest.html"
        brief_path = BRIEF_DIR / student_id / f"{student_id}_latest.html"
        has_brief = brief_path.exists()
        css_class = "card" if has_brief else "card no-brief"
        href = relative_href if has_brief else "#"
        last_date = student["last_lesson_date"] if student["last_lesson_date"] else "no lessons ingested yet"
        parts.append(f"<a class='{css_class}' href='{html.escape(href)}'>")
        parts.append(f"<div class='name'>{html.escape(student['name'])}</div>")
        parts.append(
            f"<div class='sub'>{html.escape(student['syllabus'])} &middot; last lesson: {html.escape(last_date)}</div>"
        )
        parts.append("</a>")

    parts.append(STALENESS_SCRIPT)
    parts.append("</body></html>")
    return "".join(parts)


def write_index(connection: sqlite3.Connection) -> pathlib.Path:
    students = get_students_with_last_lesson_date(connection)
    BRIEF_DIR.mkdir(exist_ok=True)
    index_path = BRIEF_DIR / "index.html"
    index_path.write_text(render_index_html(students, load_refresh_status()), encoding="utf-8")
    return index_path


if __name__ == "__main__":
    connection = sqlite3.connect(DB_PATH)
    index_path = write_index(connection)
    print(f"Index written to {index_path}")
