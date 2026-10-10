import pathlib
import sqlite3
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))

from build_sublabels import parse_review, print_completeness_report

ALEVEL_DOC = """
### P7.3  *(AS part)*
- **Label:** Applications of differentiation
- **AS:** all except points of inflection
- **⚠ Grain check:** merge if you like
- **Sub-skills:**
  - Tangents & normals
  - Points of inflection
- **Spec:** Apply differentiation to find gradients, tangents and normals

### P10.1
- **Label:** Vectors in 2D & 3D
- **Sub-skills:**
  - Vectors in 2D
- **Spec:** *(typed)* Use vectors in two dimensions and in three dimensions
"""


def test_parse_reads_dotted_alevel_ids_and_ignores_note_lines():
    nodes = parse_review(ALEVEL_DOC)
    assert [node["node_id"] for node in nodes] == ["P7.3", "P10.1"]
    assert nodes[0]["label"] == "Applications of differentiation"
    assert nodes[0]["sub_skills"] == ["Tangents & normals", "Points of inflection"]
    assert nodes[1]["sub_skills"] == ["Vectors in 2D"]


def test_parse_still_reads_gcse_ids():
    nodes = parse_review("### N8  *(stretch)*\n- **Label:** Surds\n- **Sub-skills:**\n  - Simplifying surds\n- **Spec:** x\n")
    assert nodes[0]["node_id"] == "N8"


def make_two_syllabus_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE curriculum_nodes (node_id TEXT PRIMARY KEY, syllabus TEXT)")
    for node_id, syllabus in [("N8", "gcse"), ("P7.3", "alevel"), ("P10.1", "alevel"), ("S2.1", "alevel")]:
        connection.execute("INSERT INTO curriculum_nodes VALUES (?, ?)", (node_id, syllabus))
    return connection


def test_completeness_ignores_other_syllabuses_but_catches_missing_nodes():
    connection = make_two_syllabus_connection()
    # The doc has P7.3 and P10.1; S2.1 (same syllabus) is missing, N8 (GCSE) is not its business.
    assert print_completeness_report(connection, parse_review(ALEVEL_DOC)) is False
    connection.execute("DELETE FROM curriculum_nodes WHERE node_id = 'S2.1'")
    assert print_completeness_report(connection, parse_review(ALEVEL_DOC)) is True
