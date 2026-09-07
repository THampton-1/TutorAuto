"""Google Drive access for the Meet Recordings folder.

Meet writes lesson transcripts into Drive as Google Docs, not text files.
Local folder sync (Drive for Desktop) produces .gdoc pointer files, not
content, so this module always goes through the Drive API and exports
each Doc with mimeType='text/plain'.
"""

import pathlib
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CREDENTIALS_PATH = pathlib.Path(".secrets/client_secret.json")
TOKEN_PATH = pathlib.Path(".secrets/token.json")


def get_credentials() -> Credentials:
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds is not None and creds.valid:
        return creds

    if creds is not None and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
        creds = flow.run_local_server(port=0)

    TOKEN_PATH.write_text(creds.to_json())
    return creds


def get_drive_service():
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


def find_folder_by_name(service, name: str) -> str:
    query = (
        f"name = '{name}' "
        "and mimeType = 'application/vnd.google-apps.folder' "
        "and trashed = false"
    )
    response = service.files().list(q=query, fields="files(id, name)").execute()
    folders = response.get("files", [])

    if len(folders) == 0:
        raise RuntimeError(f"No folder named {name!r} found in Drive.")
    if len(folders) > 1:
        raise RuntimeError(f"Multiple folders named {name!r} found; cannot disambiguate.")

    return folders[0]["id"]


def find_meet_recordings_folder(service) -> str:
    return find_folder_by_name(service, "Meet Recordings")


def list_transcripts(service, folder_id: str, page_size: int = 10) -> list[dict]:
    query = (
        f"'{folder_id}' in parents "
        "and mimeType = 'application/vnd.google-apps.document' "
        "and trashed = false"
    )
    response = service.files().list(
        q=query,
        fields="files(id, name, createdTime, modifiedTime)",
        orderBy="createdTime desc",
        pageSize=page_size,
    ).execute()
    return response.get("files", [])


def export_transcript_text(service, file_id: str) -> str:
    content = service.files().export(fileId=file_id, mimeType="text/plain").execute()
    return content.decode("utf-8")


def extract_transcript_body(raw_text: str) -> str:
    """Strip everything before the verbatim transcript.

    Meet produces two doc shapes. A "Notes by Gemini" doc leads with an
    AI-paraphrased summary, then a "📖 Transcript" heading, then a
    repeated mini-header (date/title/first timestamp), then the real
    speaker-labelled dialogue starting after a triple newline. A
    "Transcript"-only doc has no summary and no repeated mini-header: the
    plain word "Transcript" appears alone on its own line, immediately
    followed by dialogue. Either way the verbatim text is identical once
    isolated, so extraction downstream never has to know which button was
    clicked when recording.
    """
    emoji_marker = "\U0001F4D6 Transcript"
    marker_index = raw_text.find(emoji_marker)

    if marker_index != -1:
        remainder = raw_text[marker_index + len(emoji_marker):]
        gap_index = remainder.find("\r\n\r\n\r\n")
        if gap_index == -1:
            raise ValueError("Found a '📖 Transcript' heading but no header/body gap after it.")
        body = remainder[gap_index + len("\r\n\r\n\r\n"):]
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
