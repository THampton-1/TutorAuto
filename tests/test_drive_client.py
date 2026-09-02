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


def test_raises_when_emoji_heading_has_no_header_body_gap():
    broken_doc = "\U0001F4D6 Transcript\r\nTeacher Name: Hello.\r\n"
    with pytest.raises(ValueError):
        extract_transcript_body(broken_doc)
