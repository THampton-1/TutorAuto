"""Load short labels and sub-skills from the hand-reviewed markdown doc.

Source of truth is curriculum_labels_review.md -- the block-per-node document
Theo reviewed and edited by hand. This is a one-off pass in the same spirit as
build_curriculum.py: the model proposed, Theo corrected, and now we load the
corrected result and independently verify nothing was lost.

Re-runnable: short_label is updated in place, and a node's sub_skills are
deleted and rewritten each run, so editing the doc and re-running always
converges on exactly what the doc says.

The doc format this parses (strict -- do not loosen without reason):

    ### N8  *(stretch)*
    - **Label:** Surds
    - **Sub-skills:**
      - Exact values (surds & pi)
      - Simplifying surds
      - Rationalising denominators
    - **Spec:** calculate exactly with ...

Node heading, one Label line, a Sub-skills line, then 2-space-indented sub-skill
bullets, then the Spec line. A "- **(warning) Grain check:**" note may sit
between Label and Sub-skills; it is ignored (it is a top-level "- " bullet, not
an indented "  - " sub-skill bullet, so indentation alone separates them).
"""

import pathlib
import re
import sqlite3
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from schema_migrate import apply_schema

DB_PATH = pathlib.Path("data/lessons.db")
REVIEW_PATH = pathlib.Path("curriculum_labels_review.md")

NODE_HEADING = re.compile(r"^### ([A-Z][0-9]+)\b")
LABEL_LINE = re.compile(r"^- \*\*Label:\*\* (.+)$")
SUBSKILLS_LINE = re.compile(r"^- \*\*Sub-skills:\*\*\s*$")
SUBSKILL_BULLET = re.compile(r"^  - (.+)$")
SPEC_LINE = re.compile(r"^- \*\*Spec:\*\* ")


def parse_review(review_text: str) -> list[dict]:
    """Return [{node_id, label, sub_skills: [str, ...]}, ...] in document order."""
    nodes: list[dict] = []
    current: dict | None = None
    collecting_subskills = False

    for line in review_text.splitlines():
        heading_match = NODE_HEADING.match(line)
        if heading_match:
            if current is not None:
                nodes.append(current)
            current = {"node_id": heading_match.group(1), "label": None, "sub_skills": []}
            collecting_subskills = False
            continue

        if current is None:
            continue

        label_match = LABEL_LINE.match(line)
        if label_match:
            current["label"] = label_match.group(1).strip()
            continue

        if SUBSKILLS_LINE.match(line):
            collecting_subskills = True
            continue

        if collecting_subskills:
            bullet_match = SUBSKILL_BULLET.match(line)
            if bullet_match:
                current["sub_skills"].append(bullet_match.group(1).strip())
                continue
            # Any non-indented-bullet line (the Spec line, a blank line, the
            # next heading) ends the sub-skill list for this node.
            if SPEC_LINE.match(line) or line.strip() == "" or line.startswith("- "):
                collecting_subskills = False

    if current is not None:
        nodes.append(current)
    return nodes


def write_sublabels(connection: sqlite3.Connection, parsed_nodes: list[dict]) -> None:
    for node in parsed_nodes:
        connection.execute(
            "UPDATE curriculum_nodes SET short_label = ? WHERE node_id = ?",
            (node["label"], node["node_id"]),
        )
        # Rewrite this node's sub-skills from scratch so re-running after an
        # edit never leaves stale rows behind.
        connection.execute("DELETE FROM sub_skills WHERE node_id = ?", (node["node_id"],))
        for index, sub_label in enumerate(node["sub_skills"], start=1):
            sub_skill_id = f"{node['node_id']}.{index}"
            connection.execute(
                "INSERT INTO sub_skills (sub_skill_id, node_id, label, sub_order) VALUES (?, ?, ?, ?)",
                (sub_skill_id, node["node_id"], sub_label, index),
            )
    connection.commit()


def print_completeness_report(connection: sqlite3.Connection, parsed_nodes: list[dict]) -> bool:
    all_passed = True

    db_node_ids = set(row[0] for row in connection.execute("SELECT node_id FROM curriculum_nodes"))
    doc_node_ids = set(node["node_id"] for node in parsed_nodes)

    missing_from_doc = db_node_ids - doc_node_ids
    if len(missing_from_doc) > 0:
        all_passed = False
        print(f"FAIL  nodes in DB but not in review doc: {sorted(missing_from_doc)}")

    missing_from_db = doc_node_ids - db_node_ids
    if len(missing_from_db) > 0:
        all_passed = False
        print(f"FAIL  nodes in review doc but not in DB: {sorted(missing_from_db)}")

    nodes_without_label = [node["node_id"] for node in parsed_nodes if not node["label"]]
    if len(nodes_without_label) > 0:
        all_passed = False
        print(f"FAIL  nodes with no Label parsed: {nodes_without_label}")

    nodes_without_subskills = [node["node_id"] for node in parsed_nodes if len(node["sub_skills"]) == 0]
    if len(nodes_without_subskills) > 0:
        all_passed = False
        print(f"FAIL  nodes with no sub-skills parsed: {nodes_without_subskills}")

    total_subskills = sum(len(node["sub_skills"]) for node in parsed_nodes)
    atomic = len([node for node in parsed_nodes if len(node["sub_skills"]) == 1])
    print(f"PASS  {len(doc_node_ids)} nodes parsed, all present in DB" if all_passed else "")
    print(f"INFO  {total_subskills} sub-skills total ({atomic} atomic nodes with a single sub-skill)")

    return all_passed


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    review_text = REVIEW_PATH.read_text(encoding="utf-8")
    parsed_nodes = parse_review(review_text)

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    apply_schema(connection)
    write_sublabels(connection, parsed_nodes)

    print(f"Loaded labels + sub-skills for {len(parsed_nodes)} nodes from {REVIEW_PATH}")
    print()
    all_passed = print_completeness_report(connection, parsed_nodes)
    print()
    print("Completeness report: PASS" if all_passed else "Completeness report: FAIL")
