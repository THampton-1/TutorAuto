"""Load a transcribed curriculum spec into curriculum_nodes.

The source specs are scanned/screenshotted PDFs, not machine-readable
text, so there is no programmatic PDF parser here. Each spec is
transcribed once (by hand, cross-checked against the source images) into
a nodes.json file alongside the source images in /specs/. This script's
job is just to load that JSON into sqlite and independently verify
nothing was lost or duplicated during transcription.
"""

import json
import pathlib
import sqlite3
import sys

DB_PATH = pathlib.Path("data/lessons.db")
SCHEMA_PATH = pathlib.Path("scripts/schema.sql")

# Expected point counts per module, read directly off the spec's own
# numbering (the last point number in each module, e.g. N1..N16). This
# is an independent check against the source, not against our own
# transcription, so it actually catches a dropped or duplicated node.
EXPECTED_COUNTS = {
    "Number": 16,
    "Algebra": 25,
    "Ratio, proportion and rates of change": 16,
    "Geometry and measures": 25,
    "Probability": 9,
    "Statistics": 6,
}


def load_nodes(nodes_path: pathlib.Path) -> list[dict]:
    with open(nodes_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_nodes(connection: sqlite3.Connection, syllabus: str, nodes: list[dict]) -> None:
    for node in nodes:
        connection.execute(
            """
            INSERT INTO curriculum_nodes (node_id, syllabus, module, topic, spec_order, stretch_content)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(node_id) DO UPDATE SET
                syllabus = excluded.syllabus,
                module = excluded.module,
                topic = excluded.topic,
                spec_order = excluded.spec_order,
                stretch_content = excluded.stretch_content
            """,
            (
                node["node_id"],
                syllabus,
                node["module"],
                node["topic"],
                node["spec_order"],
                1 if node["stretch_content"] else 0,
            ),
        )
    connection.commit()


def print_completeness_report(nodes: list[dict], expected_counts: dict[str, int]) -> bool:
    all_passed = True

    node_ids = []
    for node in nodes:
        node_ids.append(node["node_id"])
    duplicate_ids = set(node_id for node_id in node_ids if node_ids.count(node_id) > 1)
    if len(duplicate_ids) > 0:
        all_passed = False
        print(f"FAIL  duplicate node_id(s) found: {sorted(duplicate_ids)}")

    for module_name, expected_count in expected_counts.items():
        module_nodes = [node for node in nodes if node["module"] == module_name]
        actual_count = len(module_nodes)
        status = "PASS" if actual_count == expected_count else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"{status}  {module_name}: expected {expected_count}, got {actual_count}")

        spec_orders = [node["spec_order"] for node in module_nodes]
        is_monotonic = all(spec_orders[i] < spec_orders[i + 1] for i in range(len(spec_orders) - 1))
        monotonic_status = "PASS" if is_monotonic else "FAIL"
        if not is_monotonic:
            all_passed = False
        print(f"{monotonic_status}  {module_name}: spec_order monotonic")

    stretch_count = len([node for node in nodes if node["stretch_content"]])
    print(f"INFO  {stretch_count} of {len(nodes)} nodes flagged as grade 7+ stretch content")

    return all_passed


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    nodes_path = pathlib.Path("specs/edexcel-gcse-higher-2015/nodes.json")
    nodes = load_nodes(nodes_path)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        connection.executescript(f.read())
    write_nodes(connection, syllabus="edexcel_gcse_higher", nodes=nodes)

    print(f"Wrote {len(nodes)} nodes to {DB_PATH}")
    print()
    all_passed = print_completeness_report(nodes, EXPECTED_COUNTS)
    print()
    print("Completeness report: PASS" if all_passed else "Completeness report: FAIL")
