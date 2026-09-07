"""One-off fetch: export every transcript Doc in the Drive 'eval' folder to
/eval/ as plain text, for hand-labelling against Phase 3's extraction output.

Read-only against Drive; makes no Anthropic API calls. Safe to re-run --
each file is re-exported and overwritten, since eval inputs are expected to
be a small, hand-picked, occasionally-changing set rather than an
append-only log like the real ingest folder.
"""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from drive_client import (
    export_transcript_text,
    extract_transcript_body,
    find_folder_by_name,
    get_drive_service,
    list_transcripts,
)

EVAL_DIR = pathlib.Path("eval")


def safe_filename(title: str) -> str:
    lowered = title.lower()
    tokens = re.findall(r"[a-z0-9]+", lowered)
    return "_".join(tokens) + ".txt"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    service = get_drive_service()
    folder_id = find_folder_by_name(service, "eval")
    transcripts = list_transcripts(service, folder_id, page_size=100)

    if len(transcripts) == 0:
        print("No Docs found in the 'eval' Drive folder.")

    EVAL_DIR.mkdir(exist_ok=True)

    for transcript in transcripts:
        title = transcript["name"]
        drive_file_id = transcript["id"]
        created = transcript["createdTime"]

        try:
            raw_text = export_transcript_text(service, drive_file_id)
            body = extract_transcript_body(raw_text)
        except ValueError as error:
            print(f"{title!r}: FAILED to extract transcript body -- {error}")
            continue

        out_path = EVAL_DIR / safe_filename(title)
        out_path.write_text(body, encoding="utf-8")
        print(f"{title!r} (created {created}): saved {len(body)} chars -> {out_path}")
        print(f"    drive_file_id: {drive_file_id}")
