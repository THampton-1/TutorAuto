"""Google Drive access for the Meet Recordings folder.

Meet writes lesson transcripts into Drive as Google Docs, not text files.
Local folder sync (Drive for Desktop) produces .gdoc pointer files, not
content, so this module always goes through the Drive API and exports
each Doc with mimeType='text/plain'.
"""

import pathlib
import re
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CREDENTIALS_PATH = pathlib.Path(".secrets/client_secret.json")
TOKEN_PATH = pathlib.Path(".secrets/token.json")

# How many times each Drive request is retried (with growing pauses) when
# the network drops or Drive answers 5xx/429. A laptop waking from sleep
# mid-request turns into a short wait instead of a failed refresh.
DRIVE_RETRIES = 4


def get_credentials(interactive: bool = True) -> Credentials:
    """Load Drive credentials, refreshing or (if allowed) re-logging in.

    interactive=False is for the nightly scheduled refresh: nobody is at
    the keyboard, so opening a browser login would hang the job forever
    instead of failing. It raises instead, and the failure lands in the
    refresh log and on the index page.
    """
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds is not None and creds.valid:
        return creds

    if creds is not None and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not interactive:
        raise RuntimeError(
            "Drive login needed and this is a non-interactive run. "
            "Run `python scripts/drive_client.py` once by hand to log in again."
        )
    else:
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
        creds = flow.run_local_server(port=0)

    TOKEN_PATH.write_text(creds.to_json())
    return creds


def get_drive_service(interactive: bool = True):
    creds = get_credentials(interactive)
    return build("drive", "v3", credentials=creds)


def find_folder_by_name(service, name: str) -> str:
    query = (
        f"name = '{name}' "
        "and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    response = service.files().list(q=query, fields="files(id, name)").execute(num_retries=DRIVE_RETRIES)
    folders = response.get("files", [])

    if len(folders) == 0:
        raise RuntimeError(f"No folder named {name!r} found in Drive.")
    if len(folders) > 1:
        raise RuntimeError(f"Multiple folders named {name!r} found; cannot disambiguate.")

    return folders[0]["id"]


def find_meet_recordings_folder(service) -> str:
    return find_folder_by_name(service, "Meet Recordings")


def find_google_meet_folder(service) -> str:
    return find_folder_by_name(service, "Google Meet")


def list_subfolders(service, folder_id: str) -> list[dict]:
    query = (
        f"'{folder_id}' in parents "
        "and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    all_folders = []
    page_token = None
    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name)",
            pageSize=100,
            pageToken=page_token,
        ).execute(num_retries=DRIVE_RETRIES)
        all_folders.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if page_token is None:
            break
    return all_folders


def list_all_meet_transcripts(service) -> list[dict]:
    """List every transcript Doc Meet has written, wherever it put it.

    Up to roughly August 2026, Meet dropped every Doc straight into
    "Meet Recordings". After that it switched to one subfolder per meeting
    under "Google Meet" (e.g. "Lesson: Twins - 2026/10/01 18:02 BST/"),
    with "Meet Recordings" left behind as just one of those subfolders.
    So: look in "Google Meet" itself plus every direct subfolder of it.
    Only one level deep -- Meet has never nested further than that.

    One Drive call per subfolder, so this grows by one call per meeting
    (~10/week). Fine for years at Drive's quota; worth batching the
    folder IDs into fewer queries if it ever feels slow.
    """
    google_meet_id = find_google_meet_folder(service)
    folder_ids = [google_meet_id]
    for subfolder in list_subfolders(service, google_meet_id):
        folder_ids.append(subfolder["id"])

    all_files = []
    seen_ids = set()
    for folder_id in folder_ids:
        for transcript in list_transcripts(service, folder_id):
            if transcript["id"] in seen_ids:
                continue
            seen_ids.add(transcript["id"])
            all_files.append(transcript)

    all_files.sort(key=created_time_of, reverse=True)
    return all_files


def created_time_of(transcript: dict) -> str:
    return transcript["createdTime"]


def list_transcripts(service, folder_id: str, page_size: int = 100) -> list[dict]:
    """List every transcript Doc in the folder, following nextPageToken.

    page_size is only the per-request page size, not a cap on the total --
    the Drive API returns at most page_size files per call and a
    nextPageToken when more remain. The first version of this function
    treated page_size as a total-results cap (no pagination loop), which
    silently dropped every file past the first page on any folder bigger
    than that -- caught 2026-09-08 when a real, older Twins lesson never
    appeared in ingest.py's output despite matching its alias correctly.
    """
    query = (
        f"'{folder_id}' in parents "
        "and mimeType = 'application/vnd.google-apps.document' "
        "and trashed = false"
    )
    all_files = []
    page_token = None
    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, createdTime, modifiedTime)",
            orderBy="createdTime desc",
            pageSize=page_size,
            pageToken=page_token,
        ).execute(num_retries=DRIVE_RETRIES)
        all_files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if page_token is None:
            break
    return all_files


def export_transcript_text(service, file_id: str) -> str:
    content = service.files().export(fileId=file_id, mimeType="text/plain").execute(num_retries=DRIVE_RETRIES)
    return content.decode("utf-8")


DIALOGUE_LINE_PATTERN = re.compile(
    r"^[A-Z][a-zA-Z'-]+(?: [A-Z][a-zA-Z'-]+){0,3}: ",
    re.MULTILINE,
)

TIMESTAMP_LINE_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2}\s*$", re.MULTILINE)


def extract_transcript_body(raw_text: str) -> str:
    """Strip everything before the verbatim transcript.

    Meet produces two doc shapes. A "Notes by Gemini" doc leads with an
    AI-paraphrased summary, then a "📖 Transcript" heading, then a
    repeated mini-header (date/title/first timestamp), then the real
    speaker-labelled dialogue. A "Transcript"-only doc has no summary and
    no repeated mini-header: the plain word "Transcript" appears alone on
    its own line, immediately followed by dialogue. Either way the
    verbatim text is identical once isolated, so extraction downstream
    never has to know which button was clicked when recording.

    The mini-header's blank-line padding before the "Notes by Gemini"
    dialogue starts is NOT consistent across recordings -- some have
    several blank lines and an inline timestamp, some have none, so this
    locates the first genuine "Speaker Name: " line instead of counting
    newlines. (A naive "gap of blank lines" heuristic was tried first and
    silently truncated real transcripts to a few hundred characters on any
    recording where dialogue turns weren't blank-line-separated -- caught
    2026-09-08 comparing a live ingest against its raw Drive export.)
    """
    emoji_marker = "\U0001F4D6 Transcript"
    marker_index = raw_text.find(emoji_marker)

    if marker_index != -1:
        remainder = raw_text[marker_index + len(emoji_marker):]
        dialogue_match = DIALOGUE_LINE_PATTERN.search(remainder)
        if dialogue_match is not None:
            body = remainder[dialogue_match.start():]
            return body.strip()
        # Some recordings have no speaker labels at all -- Meet couldn't tell
        # the voices apart (seen 2026-09-14, Gabriel: timestamped blocks of
        # unattributed speech). The text is still the real lesson, so start
        # at the first "00:00:01"-style timestamp line, which is where the
        # mini-header ends. Extraction copes; it just can't attribute quotes.
        timestamp_match = TIMESTAMP_LINE_PATTERN.search(remainder)
        if timestamp_match is None:
            raise ValueError(
                "Found a '📖 Transcript' heading but neither speaker-labelled dialogue "
                "nor a timestamp line after it."
            )
        body = remainder[timestamp_match.start():]
        return body.strip()

    lines = raw_text.split("\r\n")
    heading_line_number = -1
    for line_number in range(len(lines)):
        if lines[line_number].strip() == "Transcript":
            heading_line_number = line_number
            break

    if heading_line_number == -1:
        raise ValueError("No transcript heading found in this document.")

    body_lines = lines[heading_line_number + 1:]
    return "\r\n".join(body_lines).strip()


if __name__ == "__main__":
    # Windows consoles default stdout to cp1252, which cannot encode most
    # maths notation (°, π, ×, √, smart quotes) that shows up in transcripts.
    sys.stdout.reconfigure(encoding="utf-8")

    service = get_drive_service()
    folder_id = find_meet_recordings_folder(service)
    transcripts = list_transcripts(service, folder_id, page_size=1)

    if len(transcripts) == 0:
        print("No transcripts found in the Meet Recordings folder.")
    else:
        transcript = transcripts[0]
        raw_text = export_transcript_text(service, transcript["id"])
        body = extract_transcript_body(raw_text)
        print("Title:", transcript["name"])
        print("Created:", transcript["createdTime"])
        print()
        print(body[:500])
