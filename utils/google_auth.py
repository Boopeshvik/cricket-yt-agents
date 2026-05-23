import os
import pickle
import base64
import tempfile
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

CREDENTIALS_FILE = "config/client_secrets.json"
TOKEN_FILE       = "config/token.pickle"


def get_credentials_file():
    """
    Returns path to client_secrets.json.
    On cloud (Render), reads from environment variable.
    On local, reads from file.
    """
    b64 = os.getenv("GOOGLE_CLIENT_SECRETS_B64")
    if b64:
        # Write to temp file
        tmp = tempfile.NamedTemporaryFile(
            delete = False,
            suffix = ".json",
            mode   = "wb"
        )
        tmp.write(base64.b64decode(b64))
        tmp.close()
        return tmp.name
    return CREDENTIALS_FILE


def get_token():
    """
    Returns credentials object.
    On cloud (Render), reads token from environment variable.
    On local, reads from token.pickle file.
    """
    b64 = os.getenv("GOOGLE_TOKEN_B64")
    if b64:
        return pickle.loads(base64.b64decode(b64))

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            return pickle.load(f)

    return None


def save_token(creds):
    """
    Saves token locally only.
    On cloud we don't save — token comes from env var.
    """
    if not os.getenv("GOOGLE_TOKEN_B64"):
        os.makedirs("config", exist_ok=True)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)


def get_google_services():
    creds = get_token()

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_token(creds)
        else:
            # This only works locally — not on cloud
            credentials_file = get_credentials_file()
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES
            )
            creds = flow.run_local_server(port=0)
            save_token(creds)

    youtube = build("youtube",          "v3", credentials=creds)
    youtube_analytics = build("youtubeAnalytics", "v2", credentials=creds)
    gmail   = build("gmail",            "v1", credentials=creds)
    drive   = build("drive",            "v3", credentials=creds)

    print("YouTube           → Connected ✅")
    print("YouTube Analytics → Connected ✅")
    print("Gmail             → Connected ✅")
    print("Drive             → Connected ✅")

    return youtube, youtube_analytics, gmail, drive