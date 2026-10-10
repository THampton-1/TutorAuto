"""Generate a lesson brief (markdown and HTML) for one student.

Ordinary deterministic Python over already-extracted coverage_events -- no
model calls here (CLAUDE.md principle #1: the one LLM call happens in
ingest.py, nothing downstream needs the model). The lesson summary and the
per-row notes it shows were written by that one call at ingest (ADR-012);
this file only arranges them. "Current state" (last status per sub-skill,
what is still open) is a derived read over the append-only coverage_events
log, never a separate mutable table (principle #4).

Layout, top to bottom:
  1. Summary of the lesson -- 4-6 bullets, key phrases bold, maths italic (ADR-014)
  2. Topics at a glance -- module > topic > sub-skill chips, coloured by status
  3. How it went -- one note per sub-skill, sticking points first; the
     verbatim quote sits behind a toggle as the audit trail (principle #5)
  4. Still open from earlier lessons -- struggled / revisit-requested
     sub-skills from before this lesson that nothing has touched since

The "candidate next topics" section is paused (ADR-013): it suggested
foundational topics to advanced students (P-02). Section 4 is the
cross-lesson view that replaces it for now.

Writes every lesson's archived brief for that student plus <id>_latest.html.

Usage: python scripts/brief.py <student_id>
"""

import datetime
import html
import pathlib
import re
import sqlite3
import sys

DB_PATH = pathlib.Path("data/lessons.db")
BRIEF_DIR = pathlib.Path("briefs")

STATUS_LABELS = {
    "introduced": "Introduced",
    "practised": "Practised",
    "secure": "Secure",
    "struggled": "Struggled",
    "revisit_requested": "Revisit requested",
}

# Statuses that stay "open" until a later lesson touches the sub-skill again.
OPEN_STATUSES = ["struggled", "revisit_requested"]

# "How it went" groups, in display order: (heading, statuses in that group).
HOW_IT_WENT_GROUPS = [
    ("Sticking points", ["struggled", "revisit_requested"]),
    ("Worked on", ["introduced", "practised"]),
    ("Secure", ["secure"]),
]

# Zero-width characters the model occasionally leaves in its text (seen at
# the end of a lesson summary, 2026-10-10). Python's str.strip() does not
# remove them, so they are taken out explicitly before display.
ZERO_WIDTH_CHARACTERS = ["​", "‌", "‍", "﻿"]


def clean_text(text: str | None) -> str | None:
    if text is None:
        return None
    for character in ZERO_WIDTH_CHARACTERS:
        text = text.replace(character, "")
    text = text.strip()
    if text == "":
        return None
    return text


# The summary bullets carry two marks from the extraction prompt (ADR-014):
# **key phrase** for bold and *maths* for italics. Only these two are ever
# turned into HTML, and only after the text has been escaped, so nothing a
# transcript contains can inject markup into the page.
# The (?!\*) means a closing ** can't be followed by another *, so a bold
# phrase ending in maths -- **struggled with *SAS*** -- closes on the last
# two asterisks, leaving *SAS* intact for the italic pass.
BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*(?!\*)")
# Italic content may not contain an asterisk, so "(*A* and *√C*)" pairs as
# two separate italics rather than one run from the first * to the last.
ITALIC_PATTERN = re.compile(r"\*([^*\s](?:[^*]*[^*\s])?)\*")


def render_inline_markup(text: str) -> str:
    escaped = html.escape(text)
    escaped = BOLD_PATTERN.sub(r"<strong>\1</strong>", escaped)
    escaped = ITALIC_PATTERN.sub(r"<em>\1</em>", escaped)
    return escaped


def split_summary(summary: str | None) -> list[str]:
    """lessons.summary holds one bullet per line; return them as a list.

    A stray leading "-" or bullet character is dropped, since the page adds
    its own. Empty when the lesson has no summary yet.
    """
    cleaned = clean_text(summary)
    if cleaned is None:
        return []
    bullets = []
    for line in cleaned.split("\n"):
        line = line.strip()
        if line.startswith("- ") or line.startswith("• "):
            line = line[2:].strip()
        if line != "":
            bullets.append(line)
    return bullets


def format_date(iso_date: str) -> str:
    """'2026-07-26' -> 'Sun 26 Jul 2026'."""
    day = datetime.date.fromisoformat(iso_date)
    return f"{day.strftime('%a')} {day.day} {day.strftime('%b %Y')}"


def get_student(connection: sqlite3.Connection, student_id: str) -> dict:
    row = connection.execute(
        "SELECT student_id, name, syllabus, active FROM students WHERE student_id = ?",
        (student_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"No student with id {student_id!r}")
    return {"student_id": row[0], "name": row[1], "syllabus": row[2], "active": bool(row[3])}


def get_last_lesson(connection: sqlite3.Connection, student_id: str) -> dict | None:
    row = connection.execute(
        """
        SELECT lesson_id, date
        FROM lessons
        WHERE student_id = ?
        ORDER BY date DESC, lesson_id DESC
        LIMIT 1
        """,
        (student_id,),
    ).fetchone()
    if row is None:
        return None
    return {"lesson_id": row[0], "date": row[1]}


def get_lesson_summary(connection: sqlite3.Connection, lesson_id: int) -> list[str]:
    row = connection.execute("SELECT summary FROM lessons WHERE lesson_id = ?", (lesson_id,)).fetchone()
    return split_summary(row[0])


def _event_from_row(row: tuple) -> dict:
    """Build one coverage-unit dict from a joined coverage_events row.

    A "unit" is a sub-skill when the row has one, or the whole node for the
    legacy rows ingested before sub-skill tracking existed. unit_id is what
    the brief groups and de-duplicates on; it is the sub_skill_id if present,
    otherwise the node_id, so old and new data coexist without special-casing.
    """
    (
        node_id, module, short_label, topic, stretch_content, spec_order,
        status, evidence_quote, note, sub_skill_id, sub_label, sub_order,
        lesson_id, date,
    ) = row
    return {
        "node_id": node_id,
        "module": module,
        "short_label": short_label,
        "topic": topic,
        "stretch_content": bool(stretch_content),
        "spec_order": spec_order,
        "status": status,
        "evidence_quote": evidence_quote,
        "note": clean_text(note),
        "sub_skill_id": sub_skill_id,
        "sub_label": sub_label,
        "sub_order": sub_order if sub_order is not None else 0,
        "lesson_id": lesson_id,
        "date": date,
        "unit_id": sub_skill_id if sub_skill_id is not None else node_id,
    }


# Columns every coverage-unit query selects, in the order _event_from_row expects.
_EVENT_COLUMNS = """
    ce.node_id, cn.module, cn.short_label, cn.topic, cn.stretch_content, cn.spec_order,
    ce.status, ce.evidence_quote, ce.note, ce.sub_skill_id, ss.label, ss.sub_order,
    l.lesson_id, l.date
"""


def get_lesson_events(connection: sqlite3.Connection, lesson_id: int) -> list[dict]:
    cursor = connection.execute(
        f"""
        SELECT {_EVENT_COLUMNS}
        FROM coverage_events ce
        JOIN curriculum_nodes cn ON ce.node_id = cn.node_id
        JOIN lessons l ON ce.lesson_id = l.lesson_id
        LEFT JOIN sub_skills ss ON ce.sub_skill_id = ss.sub_skill_id
        WHERE ce.lesson_id = ?
        ORDER BY ce.event_id
        """,
        (lesson_id,),
    )
    events = []
    for row in cursor.fetchall():
        events.append(_event_from_row(row))
    return events


def get_all_lessons(connection: sqlite3.Connection, student_id: str) -> list[dict]:
    cursor = connection.execute(
        """
        SELECT lesson_id, date
        FROM lessons
        WHERE student_id = ?
        ORDER BY date ASC, lesson_id ASC
        """,
        (student_id,),
    )
    lessons = []
    for lesson_id, date in cursor.fetchall():
        lessons.append({"lesson_id": lesson_id, "date": date})
    return lessons


def get_latest_status_per_unit(
    connection: sqlite3.Connection, student_id: str, as_of_lesson: dict
) -> dict[str, dict]:
    """One entry per coverage unit: its most recent event, by lesson date then event_id.

    Walking events oldest-to-newest and overwriting by unit_id leaves each key
    holding its latest row -- so a sub-skill only shows as e.g. "struggled"
    here if nothing has touched it since, which is exactly "not revisited
    since" for the still-open section. Units are sub-skills where available,
    whole nodes for legacy rows.

    Only lessons up to and including as_of_lesson count, so a brief for a
    past lesson shows the picture as it stood right after that lesson --
    not one quietly informed by lessons that came later.
    """
    cursor = connection.execute(
        f"""
        SELECT {_EVENT_COLUMNS}
        FROM coverage_events ce
        JOIN curriculum_nodes cn ON ce.node_id = cn.node_id
        JOIN lessons l ON ce.lesson_id = l.lesson_id
        LEFT JOIN sub_skills ss ON ce.sub_skill_id = ss.sub_skill_id
        WHERE ce.student_id = ?
          AND (l.date < ? OR (l.date = ? AND l.lesson_id <= ?))
        ORDER BY l.date ASC, ce.event_id ASC
        """,
        (student_id, as_of_lesson["date"], as_of_lesson["date"], as_of_lesson["lesson_id"]),
    )
    latest_by_unit = {}
    for row in cursor.fetchall():
        event = _event_from_row(row)
        latest_by_unit[event["unit_id"]] = event
    return latest_by_unit


def get_still_open(latest_by_unit: dict[str, dict], lessons_so_far: list[dict], this_lesson: dict) -> list[dict]:
    """Struggled / revisit-requested units from *earlier* lessons, untouched since.

    Units whose latest event is in this lesson are left out: they already
    appear under "How it went", and repeating them here would bury the
    genuinely old items. Each unit gains lessons_since -- how many lessons
    have happened since it was last seen -- so long-forgotten items stand out.
    Oldest first: the longest-outstanding item is the one most at risk of
    being forgotten.
    """
    lesson_position = {}
    for position, lesson in enumerate(lessons_so_far):
        lesson_position[lesson["lesson_id"]] = position
    last_position = len(lessons_so_far) - 1

    still_open = []
    for unit in latest_by_unit.values():
        if unit["status"] not in OPEN_STATUSES:
            continue
        if unit["lesson_id"] == this_lesson["lesson_id"]:
            continue
        unit["lessons_since"] = last_position - lesson_position[unit["lesson_id"]]
        still_open.append(unit)

    still_open.sort(key=lambda unit: (unit["date"], unit["spec_order"], unit["sub_order"]))
    return still_open


def group_topics(events: list[dict]) -> list[dict]:
    """Arrange one lesson's events as module > topic > sub-skills, in spec order.

    Returns [{"module": ..., "topics": [{"label", "node_id", "stretch",
    "events": [...]}, ...]}, ...]. Spec order (not the order the model
    happened to list them) keeps the same topic in the same place from one
    brief to the next, which is what makes the glance quick.
    """
    ordered_events = sorted(events, key=lambda event: (event["spec_order"], event["sub_order"]))

    modules = []
    module_by_name = {}
    topic_by_node = {}
    for event in ordered_events:
        if event["module"] not in module_by_name:
            module_entry = {"module": event["module"], "topics": []}
            module_by_name[event["module"]] = module_entry
            modules.append(module_entry)
        if event["node_id"] not in topic_by_node:
            topic_entry = {
                "label": event["short_label"] if event["short_label"] else event["topic"],
                "node_id": event["node_id"],
                "stretch": event["stretch_content"],
                "events": [],
            }
            topic_by_node[event["node_id"]] = topic_entry
            module_by_name[event["module"]]["topics"].append(topic_entry)
        topic_by_node[event["node_id"]]["events"].append(event)
    return modules


def group_how_it_went(events: list[dict]) -> list[dict]:
    """Split one lesson's events into HOW_IT_WENT_GROUPS, each in spec order.

    Empty groups are dropped so the brief never shows a bare heading.
    """
    ordered_events = sorted(events, key=lambda event: (event["spec_order"], event["sub_order"]))
    groups = []
    for heading, statuses in HOW_IT_WENT_GROUPS:
        group_events = []
        for event in ordered_events:
            if event["status"] in statuses:
                group_events.append(event)
        if len(group_events) > 0:
            groups.append({"heading": heading, "events": group_events})
    return groups


def unit_label(unit: dict) -> str:
    """'Surds > Rationalising denominators' -- the short label, not spec text.

    Falls back to the spec text only if a node has no short_label yet, and
    drops the '> sub-skill' part for legacy node-level rows.
    """
    headline = unit["short_label"] if unit["short_label"] else unit["topic"]
    if unit["sub_label"]:
        return f"{headline} › {unit['sub_label']}"
    return headline


def unit_ref(unit: dict) -> str:
    return unit["sub_skill_id"] if unit["sub_skill_id"] else unit["node_id"]


def lessons_since_text(count: int) -> str:
    if count == 1:
        return "1 lesson since"
    return f"{count} lessons since"


def gather_brief_data(
    connection: sqlite3.Connection, student_id: str, as_of_lesson: dict | None = None
) -> dict:
    """Everything one brief needs, as it stood right after as_of_lesson.

    as_of_lesson defaults to the student's most recent lesson (the
    pre-lesson brief). Passing an earlier lesson rebuilds that lesson's
    archived brief from the same append-only log.
    """
    student = get_student(connection, student_id)
    if as_of_lesson is None:
        last_lesson = get_last_lesson(connection, student_id)
    else:
        last_lesson = as_of_lesson

    if last_lesson is None:
        return {"student": student, "last_lesson": None}

    lessons_so_far = []
    for lesson in get_all_lessons(connection, student_id):
        if (lesson["date"], lesson["lesson_id"]) <= (last_lesson["date"], last_lesson["lesson_id"]):
            lessons_so_far.append(lesson)

    last_events = get_lesson_events(connection, last_lesson["lesson_id"])
    latest_by_unit = get_latest_status_per_unit(connection, student_id, last_lesson)

    return {
        "student": student,
        "last_lesson": last_lesson,
        "lesson_number": len(lessons_so_far),
        "summary": get_lesson_summary(connection, last_lesson["lesson_id"]),
        "last_events": last_events,
        "topics": group_topics(last_events),
        "how_it_went": group_how_it_went(last_events),
        "still_open": get_still_open(latest_by_unit, lessons_so_far, last_lesson),
    }


def render_markdown(data: dict) -> str:
    """Plain-text copy of the brief (greppable, readable by Claude). Not the reading format."""
    student = data["student"]

    lines = []
    lines.append(f"# Lesson brief -- {student['name']}")
    if not student["active"]:
        lines.append("")
        lines.append("> **INACTIVE student -- lessons currently paused. Shown for reference only.**")
    lines.append("")
    lines.append(f"Syllabus: {student['syllabus']}")
    lines.append(f"Generated: {datetime.date.today().isoformat()}")
    lines.append("")

    if data["last_lesson"] is None:
        lines.append("No lessons ingested yet for this student.")
        return "\n".join(lines)

    lines.append(f"## Last lesson ({data['last_lesson']['date']}, lesson {data['lesson_number']})")
    lines.append("")
    for bullet in data["summary"]:
        lines.append(f"- {bullet}")
    if len(data["summary"]) > 0:
        lines.append("")

    lines.append("## Topics at a glance")
    lines.append("")
    if len(data["topics"]) == 0:
        lines.append("No curriculum coverage was extracted from this lesson.")
    for module in data["topics"]:
        lines.append(f"**{module['module']}**")
        for topic in module["topics"]:
            chips = []
            for event in topic["events"]:
                sub_label = event["sub_label"] if event["sub_label"] else topic["label"]
                chips.append(f"{sub_label} ({event['status']})")
            lines.append(f"- {topic['label']} [{topic['node_id']}]: " + "; ".join(chips))
        lines.append("")

    lines.append("## How it went")
    lines.append("")
    for group in data["how_it_went"]:
        lines.append(f"### {group['heading']}")
        lines.append("")
        for event in group["events"]:
            lines.append(f"- **{event['status']}** -- {unit_label(event)} [{unit_ref(event)}]")
            if event["note"] is not None:
                lines.append(f"  {event['note']}")
            lines.append(f"  > {event['evidence_quote']}")
        lines.append("")

    lines.append("## Still open from earlier lessons")
    lines.append("")
    if len(data["still_open"]) == 0:
        lines.append("Nothing outstanding from earlier lessons.")
    for unit in data["still_open"]:
        lines.append(
            f"- **{unit['status']}** {unit['date']} ({lessons_since_text(unit['lessons_since'])}) -- "
            f"{unit_label(unit)} [{unit_ref(unit)}]"
        )
        if unit["note"] is not None:
            lines.append(f"  {unit['note']}")
        lines.append(f"  > {unit['evidence_quote']}")
    lines.append("")

    return "\n".join(lines)


HTML_STYLE = """\
:root {
  color-scheme: light dark;
  --bg: #ffffff;
  --fg: #1a1a1a;
  --muted: #666666;
  --border: #dddddd;
  --card-bg: #f7f7f8;
  --quote-bg: #f0f0f2;
  --accent: #8a1f1f;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1a1a1a;
    --fg: #eaeaea;
    --muted: #a0a0a0;
    --border: #3a3a3a;
    --card-bg: #242424;
    --quote-bg: #202020;
    --accent: #ff8a8a;
  }
}
body {
  background: var(--bg);
  color: var(--fg);
  font-family: -apple-system, Segoe UI, Helvetica, Arial, sans-serif;
  max-width: 780px;
  margin: 0 auto;
  padding: 2rem 1.25rem 4rem;
  line-height: 1.5;
}
h1 { margin-bottom: 0.1rem; }
.meta { color: var(--muted); font-size: 0.9rem; margin-bottom: 1.5rem; }
h2 {
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.3rem;
  margin-top: 2.2rem;
}
h3 { font-size: 1rem; margin: 1.4rem 0 0.6rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
.summary {
  font-size: 1.05rem;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.8rem 1.2rem 0.8rem 2.2rem;
  margin: 0;
}
.summary li { margin: 0.35rem 0; }
.summary em { font-family: Cambria, Georgia, serif; }
.module { font-weight: 700; margin: 1rem 0 0.3rem; }
.topic-row { margin: 0.25rem 0 0.25rem 0.8rem; }
.topic-name { font-weight: 600; margin-right: 0.4rem; }
.ref { color: var(--muted); font-size: 0.75rem; font-family: Consolas, monospace; margin-left: 0.3rem; }
.chip {
  display: inline-block;
  font-size: 0.85rem;
  padding: 0.1rem 0.55rem;
  border-radius: 999px;
  margin: 0.15rem 0.25rem 0.15rem 0;
}
.chip small { opacity: 0.75; margin-left: 0.25rem; }
.item {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.8rem 1rem;
  margin-bottom: 0.8rem;
}
.item .unit { font-weight: 600; }
.item .when { color: var(--muted); font-size: 0.85rem; margin-top: 0.15rem; }
.item .note { margin-top: 0.4rem; }
details { margin-top: 0.4rem; }
summary { color: var(--muted); font-size: 0.8rem; cursor: pointer; }
blockquote {
  background: var(--quote-bg);
  border-left: 3px solid var(--border);
  margin: 0.4rem 0 0;
  padding: 0.4rem 0.8rem;
  font-style: italic;
}
.badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  margin-right: 0.5rem;
}
.status-introduced { background: #d6e4ff; color: #1a3d7c; }
.status-practised { background: #d3f2e9; color: #0f5c46; }
.status-secure { background: #d7f5d0; color: #1f5c1a; }
.status-struggled { background: #ffdede; color: #8a1f1f; }
.status-revisit_requested { background: #f0dcff; color: #5a1a8a; }
.stretch {
  font-size: 0.75rem;
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0 0.3rem;
  margin-left: 0.4rem;
}
.empty { color: var(--muted); font-style: italic; }
"""


def html_status_badge(status: str) -> str:
    label = html.escape(STATUS_LABELS.get(status, status))
    return f'<span class="badge status-{html.escape(status)}">{label}</span>'


def html_unit_line(unit: dict) -> str:
    stretch = ' <span class="stretch">stretch</span>' if unit["stretch_content"] else ""
    return (
        f'<div class="unit">{html.escape(unit_label(unit))}'
        f'<span class="ref">{html.escape(unit_ref(unit))}</span>{stretch}</div>'
    )


def html_note_and_evidence(unit: dict) -> str:
    """The note, with the verbatim quote folded away beneath it.

    Rows extracted before narration existed (ADR-012) have no note; for
    those the quote is shown openly, since it is the only description there is.
    """
    quote = f"<blockquote>{html.escape(unit['evidence_quote'])}</blockquote>"
    if unit["note"] is None:
        return quote
    return (
        f"<div class='note'>{html.escape(unit['note'])}</div>"
        f"<details><summary>Evidence from transcript</summary>{quote}</details>"
    )


def render_html(data: dict) -> str:
    student = data["student"]
    generated = datetime.date.today().isoformat()

    parts = []
    parts.append("<!doctype html><html><head><meta charset='utf-8'>")
    parts.append("<meta name='viewport' content='width=device-width, initial-scale=1'>")
    parts.append(f"<title>Brief -- {html.escape(student['name'])}</title>")
    parts.append(f"<style>{HTML_STYLE}</style></head><body>")
    parts.append(f"<h1>{html.escape(student['name'])}</h1>")
    if not student["active"]:
        parts.append(
            "<div class='item' style='border-color:var(--accent)'>"
            "<strong>INACTIVE student</strong> &mdash; lessons currently paused. "
            "Shown for reference only.</div>"
        )

    if data["last_lesson"] is None:
        parts.append(f"<div class='meta'>Syllabus: {html.escape(student['syllabus'])} &middot; Generated: {generated}</div>")
        parts.append("<p>No lessons ingested yet for this student.</p>")
        parts.append("</body></html>")
        return "".join(parts)

    parts.append(
        f"<div class='meta'>Brief after lesson {data['lesson_number']} &middot; "
        f"{html.escape(format_date(data['last_lesson']['date']))} &middot; "
        f"{html.escape(student['syllabus'])} &middot; generated {generated}</div>"
    )

    # 1. Summary
    if len(data["summary"]) > 0:
        parts.append("<ul class='summary'>")
        for bullet in data["summary"]:
            parts.append(f"<li>{render_inline_markup(bullet)}</li>")
        parts.append("</ul>")

    # 2. Topics at a glance
    parts.append("<h2>Topics at a glance</h2>")
    if len(data["topics"]) == 0:
        parts.append("<p class='empty'>No curriculum coverage was extracted from this lesson.</p>")
    for module in data["topics"]:
        parts.append(f"<div class='module'>{html.escape(module['module'])}</div>")
        for topic in module["topics"]:
            stretch = ' <span class="stretch">stretch</span>' if topic["stretch"] else ""
            parts.append("<div class='topic-row'>")
            parts.append(
                f"<span class='topic-name'>{html.escape(topic['label'])}</span>"
                f"<span class='ref'>{html.escape(topic['node_id'])}</span>{stretch} "
            )
            for event in topic["events"]:
                chip_text = event["sub_label"] if event["sub_label"] else topic["label"]
                status_text = STATUS_LABELS.get(event["status"], event["status"]).lower()
                parts.append(
                    f"<span class='chip status-{html.escape(event['status'])}'>"
                    f"{html.escape(chip_text)}<small>{html.escape(status_text)}</small></span>"
                )
            parts.append("</div>")

    # 3. How it went
    parts.append("<h2>How it went</h2>")
    if len(data["how_it_went"]) == 0:
        parts.append("<p class='empty'>Nothing to report.</p>")
    for group in data["how_it_went"]:
        parts.append(f"<h3>{html.escape(group['heading'])}</h3>")
        for event in group["events"]:
            parts.append("<div class='item'>")
            parts.append(html_status_badge(event["status"]))
            parts.append(html_unit_line(event))
            parts.append(html_note_and_evidence(event))
            parts.append("</div>")

    # 4. Still open from earlier lessons
    parts.append("<h2>Still open from earlier lessons</h2>")
    if len(data["still_open"]) == 0:
        parts.append("<p class='empty'>Nothing outstanding from earlier lessons.</p>")
    for unit in data["still_open"]:
        parts.append("<div class='item'>")
        parts.append(html_status_badge(unit["status"]))
        parts.append(html_unit_line(unit))
        parts.append(
            f"<div class='when'>{html.escape(format_date(unit['date']))} &middot; "
            f"{html.escape(lessons_since_text(unit['lessons_since']))}</div>"
        )
        parts.append(html_note_and_evidence(unit))
        parts.append("</div>")

    parts.append("</body></html>")
    return "".join(parts)


def student_brief_dir(student_id: str) -> pathlib.Path:
    return BRIEF_DIR / student_id


def write_brief_files(data: dict, also_write_latest: bool = True) -> list[pathlib.Path]:
    """Write the brief into briefs/<id>/ as <id>_<last lesson date>.{md,html},
    plus <id>_latest.html when also_write_latest is set.

    Each student gets their own folder (ADR-010) so the top of /briefs/
    stays just index.html plus one folder per student, however many
    lessons accumulate. File names still carry the student id, so a brief
    is self-identifying even when opened or shared on its own.

    Files are named after the lesson the brief follows, not the day it was
    generated (ADR-008). The nightly refresh therefore rewrites the same
    file until a new lesson arrives, then starts a new one -- so there is
    exactly one stored brief per lesson, and no pile of identical daily
    copies. Re-generating is cheap (pure SQL, no model call), so a stored
    brief always reflects the current database, e.g. after re-extraction.
    """
    student_id = data["student"]["student_id"]
    if data["last_lesson"] is not None:
        file_stem = f"{student_id}_{data['last_lesson']['date']}"
    else:
        file_stem = f"{student_id}_no-lessons"

    student_dir = student_brief_dir(student_id)
    student_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = student_dir / f"{file_stem}.md"
    markdown_path.write_text(render_markdown(data), encoding="utf-8")

    html_body = render_html(data)
    dated_html_path = student_dir / f"{file_stem}.html"
    dated_html_path.write_text(html_body, encoding="utf-8")

    written_paths = [markdown_path, dated_html_path]
    if also_write_latest:
        latest_html_path = student_dir / f"{student_id}_latest.html"
        latest_html_path.write_text(html_body, encoding="utf-8")
        written_paths.append(latest_html_path)
    return written_paths


def write_all_briefs(connection: sqlite3.Connection, student_id: str) -> list[pathlib.Path]:
    """Write one archived brief per lesson the student has ever had, plus _latest.

    Writing only the newest lesson's brief left gaps: when several lessons
    arrive in one refresh (a backlog, or the laptop off for a few days),
    the earlier ones never got a brief of their own -- first seen
    2026-10-08, when five Eliza lessons ingested at once produced one file.
    Rebuilding every lesson's brief each run closes that for good, and costs
    milliseconds per lesson (pure SQL, no model call).
    """
    lessons = get_all_lessons(connection, student_id)
    if len(lessons) == 0:
        return write_brief_files(gather_brief_data(connection, student_id))

    written_paths = []
    newest_lesson = lessons[-1]
    for lesson in lessons:
        data = gather_brief_data(connection, student_id, as_of_lesson=lesson)
        is_newest = lesson["lesson_id"] == newest_lesson["lesson_id"]
        written_paths.extend(write_brief_files(data, also_write_latest=is_newest))
    return written_paths


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) != 2:
        print("Usage: python scripts/brief.py <student_id>")
        sys.exit(1)

    target_student_id = sys.argv[1]

    connection = sqlite3.connect(DB_PATH)
    student = get_student(connection, target_student_id)

    if not student["active"]:
        print(f"Note: {student['name']} is marked INACTIVE -- brief generated for reference only.")

    written_paths = write_all_briefs(connection, target_student_id)
    print(f"Wrote {len(written_paths)} file(s) to {student_brief_dir(target_student_id)}")
