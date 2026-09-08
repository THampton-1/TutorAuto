"""Build briefs/index.html -- one link per roster student to their latest brief.

Pure read over students + lessons; writes no new data. Run this after
regenerating briefs so the index reflects whichever students you've
actually run brief.py for.

Usage: python scripts/build_index.py
"""

import datetime
import html
import pathlib
import sqlite3

DB_PATH = pathlib.Path("data/lessons.db")
BRIEF_DIR = pathlib.Path("briefs")

INDEX_STYLE = """\
:root {
  color-scheme: light dark;
  --bg: #ffffff;
  --fg: #1a1a1a;
  --muted: #666666;
  --border: #dddddd;
  --card-bg: #f7f7f8;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1a1a1a;
    --fg: #eaeaea;
    --muted: #a0a0a0;
    --border: #3a3a3a;
    --card-bg: #242424;
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


def render_index_html(students: list[dict]) -> str:
    parts = []
    parts.append("<!doctype html><html><head><meta charset='utf-8'>")
    parts.append("<title>Lesson briefs</title>")
    parts.append(f"<style>{INDEX_STYLE}</style></head><body>")
    parts.append("<h1>Lesson briefs</h1>")
    parts.append(f"<div class='meta'>Generated: {datetime.date.today().isoformat()}</div>")

    for student in students:
        brief_path = BRIEF_DIR / f"{student['student_id']}_latest.html"
        has_brief = brief_path.exists()
        css_class = "card" if has_brief else "card no-brief"
        href = brief_path.name if has_brief else "#"
        last_date = student["last_lesson_date"] if student["last_lesson_date"] else "no lessons ingested yet"
        parts.append(f"<a class='{css_class}' href='{html.escape(href)}'>")
        parts.append(f"<div class='name'>{html.escape(student['name'])}</div>")
        parts.append(
            f"<div class='sub'>{html.escape(student['syllabus'])} &middot; last lesson: {html.escape(last_date)}</div>"
        )
        parts.append("</a>")

    parts.append("</body></html>")
    return "".join(parts)


if __name__ == "__main__":
    connection = sqlite3.connect(DB_PATH)
    students = get_students_with_last_lesson_date(connection)

    BRIEF_DIR.mkdir(exist_ok=True)
    index_path = BRIEF_DIR / "index.html"
    index_path.write_text(render_index_html(students), encoding="utf-8")

    print(f"Index written to {index_path}")
