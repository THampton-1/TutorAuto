"""Load a curriculum spec's nodes.json into curriculum_nodes.

Each spec is turned into a nodes.json file alongside its source in /specs/
once: the GCSE spec (screenshots) was transcribed by hand; the A-Level spec
(a real-text PDF) is extracted by extract_alevel_spec.py. This script's job
is just to load that JSON into sqlite and independently verify nothing was
lost or duplicated on the way.

Usage: python scripts/build_curriculum.py [syllabus]   (default: all)
"""

import json
import pathlib
import sqlite3
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from schema_migrate import apply_schema

DB_PATH = pathlib.Path("data/lessons.db")
SCHEMA_PATH = pathlib.Path("scripts/schema.sql")

# Expected point counts per module, read directly off the spec's own
# numbering (the last point number in each module, e.g. N1..N16). This
# is an independent check against the source, not against our own
# transcription, so it actually catches a dropped or duplicated node.
GCSE_EXPECTED_COUNTS = {
    "Number": 16,
    "Algebra": 25,
    "Ratio, proportion and rates of change": 16,
    "Geometry and measures": 25,
    "Probability": 9,
    "Statistics": 6,
}

# A-Level: last point number in each topic of the 9MA0 Issue 4 content
# tables (pages 15-42), confirmed against a second PDF text engine and the
# rendered pages (ADR-015).
ALEVEL_EXPECTED_COUNTS = {
    "Proof": 1,
    "Algebra and functions": 11,
    "Coordinate geometry in the (x, y) plane": 4,
    "Sequences and series": 6,
    "Trigonometry": 9,
    "Exponentials and logarithms": 7,
    "Differentiation": 6,
    "Integration": 8,
    "Numerical methods": 5,
    "Vectors": 5,
    "Statistical sampling": 1,
    "Data presentation and interpretation": 4,
    "Probability": 3,
    "Statistical distributions": 3,
    "Statistical hypothesis testing": 3,
    "Quantities and units in mechanics": 1,
    "Kinematics": 5,
    "Forces and Newton’s laws": 6,
    "Moments": 1,
}

SYLLABUSES = {
    "edexcel_gcse_higher": {
        "nodes_path": pathlib.Path("specs/edexcel-gcse-higher-2015/nodes.json"),
        "expected_counts": GCSE_EXPECTED_COUNTS,
    },
    "edexcel_alevel_maths": {
        "nodes_path": pathlib.Path("specs/edexcel-alevel-maths-2017/nodes.json"),
        "expected_counts": ALEVEL_EXPECTED_COUNTS,
    },
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

    # Nodes carrying a spec reference like "7.3" (A-Level) must number
    # 1, 2, 3, ... within each topic with no gaps -- a dropped point shows
    # up here even if a module count were mistyped.
    numbers_by_topic = {}
    for node in nodes:
        if "spec_ref" not in node:
            continue
        topic_number, point_number = node["spec_ref"].split(".")
        topic_key = node["node_id"][0] + topic_number
        if topic_key not in numbers_by_topic:
            numbers_by_topic[topic_key] = []
        numbers_by_topic[topic_key].append(int(point_number))
    for topic_key, numbers in numbers_by_topic.items():
        expected_numbers = list(range(1, len(numbers) + 1))
        if numbers != expected_numbers:
            all_passed = False
            print(f"FAIL  {topic_key}: points numbered {numbers}, expected {expected_numbers}")
    if len(numbers_by_topic) > 0 and all_passed:
        print(f"PASS  point numbering contiguous within all {len(numbers_by_topic)} topics")

    stretch_count = len([node for node in nodes if node["stretch_content"]])
    print(f"INFO  {stretch_count} of {len(nodes)} nodes flagged as grade 7+ stretch content")

    return all_passed


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    selected = list(SYLLABUSES)
    if len(sys.argv) > 1:
        if sys.argv[1] not in SYLLABUSES:
            print(f"Unknown syllabus {sys.argv[1]!r}; choose from {list(SYLLABUSES)}")
            sys.exit(1)
        selected = [sys.argv[1]]

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    apply_schema(connection)

    for syllabus in selected:
        config = SYLLABUSES[syllabus]
        nodes = load_nodes(config["nodes_path"])
        print(f"== {syllabus}")
        all_passed = print_completeness_report(nodes, config["expected_counts"])
        # Only a spec that passes its completeness report reaches the
        # database, so a half-extracted tree can never be loaded.
        if not all_passed:
            print("Completeness report: FAIL -- nothing written")
            continue
        write_nodes(connection, syllabus=syllabus, nodes=nodes)
        print(f"Completeness report: PASS -- wrote {len(nodes)} nodes to {DB_PATH}")
        print()
