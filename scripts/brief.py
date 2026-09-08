"""Generate a lesson brief (markdown and HTML) for one student.

Ordinary deterministic Python over already-extracted coverage_events -- no
model calls here (CLAUDE.md principle #1: the one LLM call happens in
ingest.py, nothing downstream needs the model). This proposes candidate
next topics with a plain rationale each; it never picks one for Theo
(principle #7). "Current state" (last status per node, still-outstanding
revisit requests) is a derived read over the append-only coverage_events
log, never a separate mutable table (principle #4).

Usage: python scripts/brief.py <student_id>
"""

import datetime
import html
import pathlib
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


def get_student(connection: sqlite3.Connection, student_id: str) -> dict:
    row = connection.execute(
        "SELECT student_id, name, syllabus FROM students WHERE student_id = ?",
        (student_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"No student with id {student_id!r}")
    return {"student_id": row[0], "name": row[1], "syllabus": row[2]}


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


def get_lesson_events(connection: sqlite3.Connection, lesson_id: int) -> list[dict]:
    cursor = connection.execute(
        """
        SELECT ce.node_id, cn.module, cn.topic, cn.stretch_content, ce.status, ce.evidence_quote
        FROM coverage_events ce
        JOIN curriculum_nodes cn ON ce.node_id = cn.node_id
        WHERE ce.lesson_id = ?
        ORDER BY ce.event_id
        """,
        (lesson_id,),
    )
    events = []
    for node_id, module, topic, stretch_content, status, evidence_quote in cursor.fetchall():
        events.append(
            {
                "node_id": node_id,
                "module": module,
                "topic": topic,
                "stretch_content": bool(stretch_content),
                "status": status,
                "evidence_quote": evidence_quote,
            }
        )
    return events


def get_latest_status_per_node(connection: sqlite3.Connection, student_id: str) -> dict[str, dict]:
    """One entry per node: its most recent coverage_event, by lesson date then event_id.

    Walking events oldest-to-newest and overwriting by node_id leaves each
    key holding its latest row -- so a node only shows as e.g. "struggled"
    here if nothing has touched it since, which is exactly "not revisited
    since" for the struggled/revisit-requested sections below.
    """
    cursor = connection.execute(
        """
        SELECT ce.node_id, cn.module, cn.topic, cn.stretch_content, ce.status,
               ce.evidence_quote, l.date
        FROM coverage_events ce
        JOIN curriculum_nodes cn ON ce.node_id = cn.node_id
        JOIN lessons l ON ce.lesson_id = l.lesson_id
        WHERE ce.student_id = ?
        ORDER BY l.date ASC, ce.event_id ASC
        """,
        (student_id,),
    )
    latest_by_node = {}
    for node_id, module, topic, stretch_content, status, evidence_quote, date in cursor.fetchall():
        latest_by_node[node_id] = {
            "node_id": node_id,
            "module": module,
            "topic": topic,
            "stretch_content": bool(stretch_content),
            "status": status,
            "evidence_quote": evidence_quote,
            "date": date,
        }
    return latest_by_node


def get_never_covered_nodes(
    connection: sqlite3.Connection, syllabus: str, covered_node_ids: set[str]
) -> list[dict]:
    cursor = connection.execute(
        """
        SELECT node_id, module, topic, stretch_content
        FROM curriculum_nodes
        WHERE syllabus = ?
        ORDER BY spec_order
        """,
        (syllabus,),
    )
    never_covered = []
    for node_id, module, topic, stretch_content in cursor.fetchall():
        if node_id not in covered_node_ids:
            never_covered.append(
                {
                    "node_id": node_id,
                    "module": module,
                    "topic": topic,
                    "stretch_content": bool(stretch_content),
                }
            )
    return never_covered


def build_candidates(latest_by_node: dict[str, dict], never_covered_nodes: list[dict]) -> list[dict]:
    """Propose up to three next-topic candidates, each with a one-line rationale.

    Priority: the longest-outstanding struggled node, then the
    longest-outstanding revisit request, then the next never-covered node
    in spec order -- filling any remaining slots the same way. This never
    picks a topic for Theo, only surfaces candidates with a plain reason
    (CLAUDE.md principle #7); the full struggled/revisit lists above this
    section already show everything outstanding, not just these three.
    """
    struggled = []
    revisit_requested = []
    for node in latest_by_node.values():
        if node["status"] == "struggled":
            struggled.append(node)
        elif node["status"] == "revisit_requested":
            revisit_requested.append(node)
    struggled.sort(key=lambda n: n["date"])
    revisit_requested.sort(key=lambda n: n["date"])

    candidates = []
    used_node_ids = set()

    if len(struggled) > 0:
        node = struggled[0]
        candidates.append(
            {
                "node": node,
                "rationale": f"Struggled with this on {node['date']} and it hasn't come up since -- worth reinforcing.",
            }
        )
        used_node_ids.add(node["node_id"])

    if len(revisit_requested) > 0:
        node = revisit_requested[0]
        if node["node_id"] not in used_node_ids:
            candidates.append(
                {
                    "node": node,
                    "rationale": f"You flagged this for a revisit on {node['date']}.",
                }
            )
            used_node_ids.add(node["node_id"])

    never_covered_index = 0
    while len(candidates) < 3 and never_covered_index < len(never_covered_nodes):
        node = never_covered_nodes[never_covered_index]
        never_covered_index += 1
        if node["node_id"] in used_node_ids:
            continue
        candidates.append(
            {
                "node": node,
                "rationale": "Next topic in spec order that hasn't been introduced yet.",
            }
        )
        used_node_ids.add(node["node_id"])

    return candidates


def format_node_line(node: dict) -> str:
    label = f"{node['node_id']} -- {node['module']}: {node['topic']}"
    if node["stretch_content"]:
        label += " [stretch]"
    return label


def gather_brief_data(connection: sqlite3.Connection, student_id: str) -> dict:
    student = get_student(connection, student_id)
    last_lesson = get_last_lesson(connection, student_id)

    if last_lesson is None:
        return {"student": student, "last_lesson": None}

    last_events = get_lesson_events(connection, last_lesson["lesson_id"])
    latest_by_node = get_latest_status_per_node(connection, student_id)

    revisit_nodes = [node for node in latest_by_node.values() if node["status"] == "revisit_requested"]
    revisit_nodes.sort(key=lambda n: n["date"])

    struggled_nodes = [node for node in latest_by_node.values() if node["status"] == "struggled"]
    struggled_nodes.sort(key=lambda n: n["date"])

    covered_node_ids = set(latest_by_node.keys())
    never_covered_nodes = get_never_covered_nodes(connection, student["syllabus"], covered_node_ids)
    candidates = build_candidates(latest_by_node, never_covered_nodes)

    return {
        "student": student,
        "last_lesson": last_lesson,
        "last_events": last_events,
        "revisit_nodes": revisit_nodes,
        "struggled_nodes": struggled_nodes,
        "candidates": candidates,
    }


def render_markdown(data: dict) -> str:
    student = data["student"]

    lines = []
    lines.append(f"# Lesson brief -- {student['name']}")
    lines.append("")
    lines.append(f"Syllabus: {student['syllabus']}")
    lines.append(f"Generated: {datetime.date.today().isoformat()}")
    lines.append("")

    if data["last_lesson"] is None:
        lines.append("No lessons ingested yet for this student.")
        return "\n".join(lines)

    lines.append(f"## Last lesson ({data['last_lesson']['date']})")
    lines.append("")
    if len(data["last_events"]) == 0:
        lines.append("No curriculum coverage was extracted from this lesson.")
    else:
        for event in data["last_events"]:
            lines.append(f"- **{event['status']}** -- {format_node_line(event)}")
            lines.append(f"  > {event['evidence_quote']}")
    lines.append("")

    lines.append("## Explicit revisit requests")
    lines.append("")
    if len(data["revisit_nodes"]) == 0:
        lines.append("None outstanding.")
    else:
        for node in data["revisit_nodes"]:
            lines.append(f"- {format_node_line(node)} (requested {node['date']})")
            lines.append(f"  > {node['evidence_quote']}")
    lines.append("")

    lines.append("## Struggled, not revisited since")
    lines.append("")
    if len(data["struggled_nodes"]) == 0:
        lines.append("None outstanding.")
    else:
        for node in data["struggled_nodes"]:
            lines.append(f"- {format_node_line(node)} (struggled {node['date']})")
            lines.append(f"  > {node['evidence_quote']}")
    lines.append("")

    lines.append("## Candidate next topics")
    lines.append("")
    if len(data["candidates"]) == 0:
        lines.append("No candidates available -- every node in this syllabus has been covered.")
    else:
        for candidate in data["candidates"]:
            lines.append(f"- {format_node_line(candidate['node'])}")
            lines.append(f"  {candidate['rationale']}")
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
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1a1a1a;
    --fg: #eaeaea;
    --muted: #a0a0a0;
    --border: #3a3a3a;
    --card-bg: #242424;
    --quote-bg: #202020;
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
.meta { color: var(--muted); font-size: 0.9rem; margin-bottom: 2rem; }
h2 {
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.3rem;
  margin-top: 2.2rem;
}
.item {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.8rem 1rem;
  margin-bottom: 0.8rem;
}
.item .node-line { font-weight: 600; }
.item .sub { color: var(--muted); font-size: 0.85rem; }
blockquote {
  background: var(--quote-bg);
  border-left: 3px solid var(--border);
  margin: 0.5rem 0 0;
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
.badge-introduced { background: #d6e4ff; color: #1a3d7c; }
.badge-practised { background: #d3f2e9; color: #0f5c46; }
.badge-secure { background: #d7f5d0; color: #1f5c1a; }
.badge-struggled { background: #ffdede; color: #8a1f1f; }
.badge-revisit_requested { background: #f0dcff; color: #5a1a8a; }
.stretch {
  font-size: 0.75rem;
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0 0.3rem;
  margin-left: 0.4rem;
}
.empty { color: var(--muted); font-style: italic; }
.rationale { margin-top: 0.3rem; color: var(--muted); }
"""


def html_status_badge(status: str) -> str:
    label = html.escape(STATUS_LABELS.get(status, status))
    return f'<span class="badge badge-{html.escape(status)}">{label}</span>'


def html_node_line(node: dict) -> str:
    label = html.escape(f"{node['node_id']} -- {node['module']}: {node['topic']}")
    stretch = ' <span class="stretch">stretch</span>' if node["stretch_content"] else ""
    return f'<div class="node-line">{label}{stretch}</div>'


def render_html(data: dict) -> str:
    student = data["student"]
    generated = datetime.date.today().isoformat()

    parts = []
    parts.append("<!doctype html><html><head><meta charset='utf-8'>")
    parts.append(f"<title>Brief -- {html.escape(student['name'])}</title>")
    parts.append(f"<style>{HTML_STYLE}</style></head><body>")
    parts.append(f"<h1>{html.escape(student['name'])}</h1>")
    parts.append(
        f"<div class='meta'>Syllabus: {html.escape(student['syllabus'])} &middot; Generated: {generated}</div>"
    )

    if data["last_lesson"] is None:
        parts.append("<p>No lessons ingested yet for this student.</p>")
        parts.append("</body></html>")
        return "".join(parts)

    parts.append(f"<h2>Last lesson ({data['last_lesson']['date']})</h2>")
    if len(data["last_events"]) == 0:
        parts.append("<p class='empty'>No curriculum coverage was extracted from this lesson.</p>")
    else:
        for event in data["last_events"]:
            parts.append("<div class='item'>")
            parts.append(html_status_badge(event["status"]))
            parts.append(html_node_line(event))
            parts.append(f"<blockquote>{html.escape(event['evidence_quote'])}</blockquote>")
            parts.append("</div>")

    parts.append("<h2>Explicit revisit requests</h2>")
    if len(data["revisit_nodes"]) == 0:
        parts.append("<p class='empty'>None outstanding.</p>")
    else:
        for node in data["revisit_nodes"]:
            parts.append("<div class='item'>")
            parts.append(html_node_line(node))
            parts.append(f"<div class='sub'>Requested {html.escape(node['date'])}</div>")
            parts.append(f"<blockquote>{html.escape(node['evidence_quote'])}</blockquote>")
            parts.append("</div>")

    parts.append("<h2>Struggled, not revisited since</h2>")
    if len(data["struggled_nodes"]) == 0:
        parts.append("<p class='empty'>None outstanding.</p>")
    else:
        for node in data["struggled_nodes"]:
            parts.append("<div class='item'>")
            parts.append(html_node_line(node))
            parts.append(f"<div class='sub'>Struggled {html.escape(node['date'])}</div>")
            parts.append(f"<blockquote>{html.escape(node['evidence_quote'])}</blockquote>")
            parts.append("</div>")

    parts.append("<h2>Candidate next topics</h2>")
    if len(data["candidates"]) == 0:
        parts.append("<p class='empty'>No candidates available -- every node in this syllabus has been covered.</p>")
    else:
        for candidate in data["candidates"]:
            parts.append("<div class='item'>")
            parts.append(html_node_line(candidate["node"]))
            parts.append(f"<div class='rationale'>{html.escape(candidate['rationale'])}</div>")
            parts.append("</div>")

    parts.append("</body></html>")
    return "".join(parts)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) != 2:
        print("Usage: python scripts/brief.py <student_id>")
        sys.exit(1)

    target_student_id = sys.argv[1]

    connection = sqlite3.connect(DB_PATH)
    data = gather_brief_data(connection, target_student_id)

    BRIEF_DIR.mkdir(exist_ok=True)
    today = datetime.date.today().isoformat()

    markdown_path = BRIEF_DIR / f"{target_student_id}_{today}.md"
    markdown_path.write_text(render_markdown(data), encoding="utf-8")

    html_body = render_html(data)
    dated_html_path = BRIEF_DIR / f"{target_student_id}_{today}.html"
    dated_html_path.write_text(html_body, encoding="utf-8")

    latest_html_path = BRIEF_DIR / f"{target_student_id}_latest.html"
    latest_html_path.write_text(html_body, encoding="utf-8")

    print(f"Brief written to {markdown_path}, {dated_html_path}, {latest_html_path}")
