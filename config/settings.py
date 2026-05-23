import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY       = os.getenv("ANTHROPIC_API_KEY")
YOUTUBE_CLIENT_SECRETS  = os.getenv("YOUTUBE_CLIENT_SECRETS")
GMAIL_SENDER            = os.getenv("GMAIL_SENDER")
COFOUNDER_EMAIL         = os.getenv("COFOUNDER_EMAIL")
CHANNEL_NAME            = os.getenv("CHANNEL_NAME", "Tamil Cricket Channel")
SUBSCRIBER_COUNT        = int(os.getenv("SUBSCRIBER_COUNT", 950))
DRIVE_VIDEOS_FOLDER     = os.getenv("DRIVE_VIDEOS_FOLDER", "Cricket Videos")
DRIVE_SHORTS_FOLDER     = os.getenv("DRIVE_SHORTS_FOLDER", "Cricket Shorts")
SHEET_ID                = os.getenv("SHEET_ID")
DRIVE_VIDEOS_FOLDER_ID  = os.getenv("DRIVE_VIDEOS_FOLDER_ID")
DRIVE_SHORTS_FOLDER_ID  = os.getenv("DRIVE_SHORTS_FOLDER_ID")