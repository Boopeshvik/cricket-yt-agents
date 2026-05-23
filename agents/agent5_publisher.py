import os
import json
import time
import tempfile
import httplib2
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from config.settings import (
    GMAIL_SENDER,
    SHEET_ID,
    DRIVE_VIDEOS_FOLDER_ID,
    DRIVE_SHORTS_FOLDER_ID
)
from utils.google_auth import get_google_services
import base64
from email.mime.text import MIMEText

LOG_FILE = "logs/agent5_publisher.log"


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line      = f"[{timestamp}] {message}"
    print(line)
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def read_upload_schedule(drive, sheets_service):
    log("Reading upload schedule from Google Sheet...")
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId = SHEET_ID,
            range         = "Sheet1!A2:H100"
        ).execute()

        rows   = result.get("values", [])
        schedule = []

        for row in rows:
            if len(row) < 8:
                continue
            schedule.append({
                "file_name"   : row[0].strip(),
                "title"       : row[1].strip(),
                "description" : row[2].strip(),
                "tags"        : [t.strip() for t in row[3].split(",")],
                "publish_date": row[4].strip(),
                "publish_time": row[5].strip(),
                "visibility"  : row[6].strip().lower(),
                "type"        : row[7].strip().lower()
            })

        log(f"Found {len(schedule)} scheduled uploads")
        return schedule

    except Exception as e:
        log(f"Error reading schedule: {e}")
        return []


def is_due(publish_date, publish_time):
    try:
        scheduled = datetime.strptime(
            f"{publish_date} {publish_time}",
            "%Y-%m-%d %H:%M"
        )
        return datetime.now() >= scheduled
    except Exception:
        return False


def find_file_in_drive(drive, file_name, folder_id):
    log(f"Searching for '{file_name}' in Drive...")
    try:
        response = drive.files().list(
            q         = f"name='{file_name}' and '{folder_id}' in parents and trashed=false",
            fields    = "files(id, name, mimeType, size)",
            pageSize  = 5
        ).execute()

        files = response.get("files", [])
        if files:
            log(f"Found file: {files[0]['name']} (ID: {files[0]['id']})")
            return files[0]
        else:
            log(f"File not found: {file_name}")
            return None

    except Exception as e:
        log(f"Error searching Drive: {e}")
        return None


def download_from_drive(drive, file_id, file_name):
    log(f"Downloading '{file_name}' from Drive...")
    try:
        tmp_path = os.path.join(tempfile.gettempdir(), file_name)
        request  = drive.files().get_media(fileId=file_id)

        with open(tmp_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                pct = int(status.progress() * 100)
                log(f"  Download progress: {pct}%")

        log(f"Download complete: {tmp_path}")
        return tmp_path

    except Exception as e:
        log(f"Error downloading file: {e}")
        return None


def upload_to_youtube(youtube, video_path, item):
    log(f"Uploading '{item['title']}' to YouTube...")
    try:
        # Determine if Short or regular video
        is_short = item["type"] == "short"

        body = {
            "snippet": {
                "title"      : item["title"],
                "description": item["description"],
                "tags"       : item["tags"],
                "categoryId" : "17"  # Sports category
            },
            "status": {
                "privacyStatus"         : item["visibility"],
                "selfDeclaredMadeForKids": False
            }
        }

        # Add #Shorts to title if it's a short
        if is_short and "#Shorts" not in item["title"]:
            body["snippet"]["title"] = item["title"] + " #Shorts"

        media = MediaFileUpload(
            video_path,
            mimetype    = "video/*",
            resumable   = True,
            chunksize   = 1024 * 1024 * 5  # 5MB chunks
        )

        request  = youtube.videos().insert(
            part = "snippet,status",
            body = body,
            media_body = media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                log(f"  Upload progress: {pct}%")

        video_id  = response["id"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        log(f"Upload complete! Video ID: {video_id}")
        log(f"URL: {video_url}")

        return video_id, video_url

    except Exception as e:
        log(f"Error uploading to YouTube: {e}")
        return None, None


def send_upload_notification(gmail, title, video_url, item_type):
    log("Sending upload notification email...")
    try:
        today   = datetime.now().strftime("%d %B %Y %H:%M")
        subject = f"✅ New {item_type.title()} Published — {title}"

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1a6b2e; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">BeyoondBoundariess</h1>
                <p style="color: #90EE90; margin: 5px 0;">Auto Publisher — Upload Confirmation</p>
            </div>
            <div style="padding: 20px; background: #f9f9f9;">
                <h2 style="color: #1a6b2e;">✅ {item_type.title()} Published Successfully!</h2>
                <p><strong>Title:</strong> {title}</p>
                <p><strong>Published at:</strong> {today}</p>
                <p><strong>Type:</strong> {item_type.title()}</p>
                <p><strong>URL:</strong> 
                    <a href="{video_url}" style="color: #1a6b2e;">{video_url}</a>
                </p>
                <div style="margin-top: 20px; padding: 15px; 
                            background: #e8f5e9; border-radius: 8px;">
                    <p style="margin: 0; color: #1a6b2e;">
                        Your video is now live on YouTube. 
                        Share it with your audience!
                    </p>
                </div>
            </div>
            <div style="padding: 15px; text-align: center; 
                        background: #1a6b2e; color: white;">
                <p style="margin: 0; font-size: 12px;">
                    Sent by BeyoondBoundariess Auto Publisher Agent
                </p>
            </div>
        </body>
        </html>
        """

        message            = __import__("email.mime.multipart", fromlist=["MIMEMultipart"]).MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"]    = GMAIL_SENDER
        message["To"]      = GMAIL_SENDER

        from email.mime.text import MIMEText
        message.attach(MIMEText(html, "html"))

        raw = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode("utf-8")

        gmail.users().messages().send(
            userId = "me",
            body   = {"raw": raw}
        ).execute()

        log("Notification email sent!")

    except Exception as e:
        log(f"Error sending notification: {e}")


def mark_as_uploaded(sheets_service, row_index):
    try:
        sheets_service.spreadsheets().values().update(
            spreadsheetId = SHEET_ID,
            range         = f"Sheet1!I{row_index + 2}",
            valueInputOption = "RAW",
            body          = {"values": [["UPLOADED"]]}
        ).execute()
        log(f"Row {row_index + 2} marked as UPLOADED in sheet")
    except Exception as e:
        log(f"Could not mark row as uploaded: {e}")


def run_agent5():
    log("=" * 50)
    log("Agent 5 — Auto Publisher Starting...")
    log("=" * 50)

    youtube, youtube_analytics, gmail, drive = get_google_services()

    # Build Sheets service
    from utils.google_auth import TOKEN_FILE, SCOPES
    import pickle
    with open(TOKEN_FILE, "rb") as token:
        creds = pickle.load(token)
    sheets = build("sheets", "v4", credentials=creds)

    # Read schedule
    schedule = read_upload_schedule(drive, sheets)

    if not schedule:
        log("No scheduled uploads found.")
        return

    uploaded_count = 0

    for index, item in enumerate(schedule):
        log(f"\nChecking: {item['file_name']}")

        # Skip if already uploaded
        if item.get("status") == "UPLOADED":
            log("  Already uploaded — skipping")
            continue

        # Check if due
        if not is_due(item["publish_date"], item["publish_time"]):
            log(f"  Not due yet — scheduled for {item['publish_date']} {item['publish_time']}")
            continue

        log(f"  Due for upload! Processing...")

        # Find correct folder
        folder_id = (
            DRIVE_VIDEOS_FOLDER_ID
            if item["type"] == "video"
            else DRIVE_SHORTS_FOLDER_ID
        )

        # Find file in Drive
        file_info = find_file_in_drive(drive, item["file_name"], folder_id)
        if not file_info:
            log(f"  File not found in Drive — skipping")
            continue

        # Download from Drive
        local_path = download_from_drive(drive, file_info["id"], item["file_name"])
        if not local_path:
            log(f"  Download failed — skipping")
            continue

        # Upload to YouTube
        video_id, video_url = upload_to_youtube(youtube, local_path, item)

        if video_id:
            # Send notification
            send_upload_notification(gmail, item["title"], video_url, item["type"])

            # Mark as uploaded in sheet
            mark_as_uploaded(sheets, index)

            uploaded_count += 1

        # Clean up temp file
        try:
            os.remove(local_path)
            log(f"  Temp file cleaned up")
        except Exception:
            pass

    log("=" * 50)
    log(f"Agent 5 completed! {uploaded_count} video(s) uploaded.")
    log("=" * 50)


if __name__ == "__main__":
    run_agent5()