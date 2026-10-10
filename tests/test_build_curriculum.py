import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))

from build_curriculum import print_completeness_report

GOOD_NODES = [
    {"node_id": "X1", "module": "Fake", "spec_order": 1, "stretch_content": False, "topic": "a"},
    {"node_id": "X2", "module": "Fake", "spec_order": 2, "stretch_content": True, "topic": "b"},
]
GOOD_EXPECTED = {"Fake": 2}


def test_passes_when_counts_and_order_are_correct():
    assert print_completeness_report(GOOD_NODES, GOOD_EXPECTED) is True


def test_fails_when_a_node_is_missing():
    incomplete = [GOOD_NODES[0]]
    assert print_completeness_report(incomplete, GOOD_EXPECTED) is False


def test_fails_on_duplicate_node_id():
    duplicated = [
        {"node_id": "X1", "module": "Fake", "spec_order": 1, "stretch_content": False, "topic": "a"},
        {"node_id": "X1", "module": "Fake", "spec_order": 2, "stretch_content": False, "topic": "b"},
    ]
    assert print_completeness_report(duplicated, {"Fake": 2}) is False


def test_fails_when_spec_order_is_not_monotonic():
    out_of_order = [
        {"node_id": "X1", "module": "Fake", "spec_order": 2, "stretch_content": False, "topic": "a"},
        {"node_id": "X2", "module": "Fake", "spec_order": 1, "stretch_content": False, "topic": "b"},
    ]
    assert print_completeness_report(out_of_order, GOOD_EXPECTED) is False


def test_fails_on_a_gap_in_spec_point_numbering():
    gapped = [
        {"node_id": "P7.1", "spec_ref": "7.1", "module": "Diff", "spec_order": 1, "stretch_content": False, "topic": "a"},
        {"node_id": "P7.3", "spec_ref": "7.3", "module": "Diff", "spec_order": 2, "stretch_content": False, "topic": "b"},
    ]
    assert print_completeness_report(gapped, {"Diff": 2}) is False
