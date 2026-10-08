import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))

import pytest
from drive_client import extract_transcript_body

NOTES_BY_GEMINI_DOC = (
    "Notes\r\n"
    "Jul 28, 2026\r\n"
    "Fake lesson\r\n"
    "Summary\r\n"
    "Covered some fake topics.\r\n"
    "\r\n"
    "Next steps\r\n"
    "* Do fake homework.\r\n"
    "\r\n"
    "Give feedback, including how helpful the notes were for your needs.\r\n"
    "\U0001F4D6 Transcript\r\n"
    "Jul 28, 2026\r\n"
    "Fake lesson - Transcript\r\n"
    "00:00:15\r\n"
    "\r\n"
    "\r\n"
    "Teacher Name: Hello.\r\n"
    "Student Name: Hi there.\r\n"
)

TRANSCRIPT_ONLY_DOC = (
    "Fake lesson - Transcript\r\n"
    "Attendees\r\n"
    "Student Name, Teacher Name\r\n"
    "Transcript\r\n"
    "Student Name: Hi, we're good.\r\n"
    "Teacher Name: Hello, how are you?\r\n"
)


def test_extracts_body_from_notes_by_gemini_doc():
    body = extract_transcript_body(NOTES_BY_GEMINI_DOC)
    assert body == "Teacher Name: Hello.\r\nStudent Name: Hi there."


def test_extracts_body_from_transcript_only_doc():
    body = extract_transcript_body(TRANSCRIPT_ONLY_DOC)
    assert body == "Student Name: Hi, we're good.\r\nTeacher Name: Hello, how are you?"


def test_raises_when_no_transcript_heading_present():
    with pytest.raises(ValueError):
        extract_transcript_body("Just some random doc text with no heading at all.\r\n")


def test_extracts_body_when_dialogue_follows_emoji_heading_directly():
    # Since the 2026-09-08 fix, the body starts at the first "Speaker: "
    # line -- no blank-line gap after the heading is required.
    doc = "\U0001F4D6 Transcript\r\nTeacher Name: Hello.\r\n"
    assert extract_transcript_body(doc) == "Teacher Name: Hello."


def test_raises_when_emoji_heading_has_no_dialogue_or_timestamp_after_it():
    broken_doc = "\U0001F4D6 Transcript\r\n\r\nno speaker lines here\r\n"
    with pytest.raises(ValueError):
        extract_transcript_body(broken_doc)


def test_falls_back_to_first_timestamp_when_no_speaker_labels():
    # Shape of the real 2026-09-14 Gabriel doc: Meet produced no speaker labels.
    doc = (
        "Summary text.\r\n\U0001F4D6 Transcript\r\nSep 14, 2026\r\n"
        "lesson: Gabriel - Transcript\r\n00:00:01\r\n\r\n\r\n"
        "a line parallel perpendicular. Huh?\r\n\r\n00:00:20\r\n\r\nAnd then you can do five.\r\n"
    )
    body = extract_transcript_body(doc)
    assert body.startswith("00:00:01")
    assert "lesson: Gabriel - Transcript" not in body
    assert body.endswith("And then you can do five.")
