"""One-off runner: fire the real extraction call (ingest.py's call_extraction)
against a single transcript already saved in /eval/, without touching
lessons.db. Prints structured coverage rows for side-by-side comparison
against a hand-written or Gemini-generated answer.

Usage: python scripts/eval_extract.py eval/<filename>.txt

Reads ANTHROPIC_API_KEY from the environment if set, otherwise falls back to
.secrets/anthropic_api_key (gitignored, one line, no quotes) -- this keeps
the key out of shell history and out of the conversation transcript.
"""

import os
import pathlib
import sqlite3
import sys

import anthropic

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ingest import call_extraction, load_valid_nodes, resolve_student

DB_PATH = pathlib.Path("data/lessons.db")
KEY_FILE = pathlib.Path(".secrets/TutorScan2- API Key.txt")


def load_api_key() -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise RuntimeError(
        f"No API key found. Set ANTHROPIC_API_KEY or write the key to {KEY_FILE}."
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) != 2:
        print("Usage: python scripts/eval_extract.py eval/<filename>.txt")
        sys.exit(1)

    transcript_path = pathlib.Path(sys.argv[1])
    transcript_body = transcript_path.read_text(encoding="utf-8")

    connection = sqlite3.connect(DB_PATH)

    student_id, reason = resolve_student(connection, transcript_path.stem)
    if student_id is None:
        print(f"Could not resolve student from filename: {reason}")
        sys.exit(1)

    syllabus = connection.execute(
        "SELECT syllabus FROM students WHERE student_id = ?", (student_id,)
    ).fetchone()[0]
    nodes = load_valid_nodes(connection, syllabus)

    client = anthropic.Anthropic(api_key=load_api_key())
    coverage = call_extraction(client, transcript_body, nodes)

    node_lookup = {node["node_id"]: node for node in nodes}

    print(f"student: {student_id} | syllabus: {syllabus} | {len(coverage)} coverage row(s)\n")
    for event in coverage:
        if event["node_id"] == "unmatched":
            print(f"[UNMATCHED] {event['raw_label']!r} -- status: {event['status']}")
        else:
            node = node_lookup[event["node_id"]]
            print(f"{event['node_id']} -- {node['module']}: {node['topic']}")
            print(f"    status: {event['status']}")
        print(f"    quote: {event['evidence_quote']!r}")
        print()
