import json
import os
import base64
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic
from config.settings import ANTHROPIC_API_KEY, GMAIL_SENDER, COFOUNDER_EMAIL
from utils.google_auth import get_google_services

DATA_FILE_ANALYTICS = "data/analytics_brief.json"
DATA_FILE_IDEAS     = "data/content_ideas.json"
REPORT_FILE         = "data/weekly_report.html"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def load_data():
    analytics = None
    ideas     = None

    if os.path.exists(DATA_FILE_ANALYTICS):
        with open(DATA_FILE_ANALYTICS, "r", encoding="utf-8") as f:
            analytics = json.load(f)
    else:
        print("No analytics brief found. Run Agent 3 first.")

    if os.path.exists(DATA_FILE_IDEAS):
        with open(DATA_FILE_IDEAS, "r", encoding="utf-8") as f:
            ideas = json.load(f)
    else:
        print("No content ideas found. Run Agent 1 first.")

    return analytics, ideas


def generate_report_html(analytics, ideas):
    print("Generating executive report with Claude...")

    # Extract all data
    channel      = analytics["channel_stats"]
    top_videos   = analytics["top_videos"]
    sentiment    = analytics["comment_analysis"]
    content_plan = ideas["content_plan"] if ideas else {}
    period       = analytics.get("period_stats", {})
    last7        = period.get("last_7_days",  {})
    last30       = period.get("last_30_days", {})

    # Real dates
    today       = datetime.now().strftime("%d %B %Y")
    next_monday = (datetime.now() + timedelta(days=(7 - datetime.now().weekday()))).strftime("%d %B %Y")

    # Format top videos
    top_videos_text = ""
    for i, v in enumerate(top_videos[:5], 1):
        top_videos_text += f"{i}. {v['title']} — {v['views']} views, {v['likes']} likes\n"

    # Format video ideas
    video_ideas_text = ""
    for i, v in enumerate(content_plan.get("video_ideas", [])[:3], 1):
        video_ideas_text += f"{i}. {v['title']} — Post at {v['best_time_to_post']}\n"

    prompt = f"""You are writing a weekly executive report for a Tamil cricket YouTube channel called "BeyoondBoundariess".

Report Date : {today}
Next Report : {next_monday}

OVERALL CHANNEL STATS:
- Subscribers  : {channel['subscribers']} (Goal: 1000)
- Total Views  : {channel['total_views']}
- Total Videos : {channel['total_videos']}
- Milestone    : {round((channel['subscribers'] / 1000) * 100)}% to 1000 subscribers

LAST 7 DAYS ({last7.get('from_date', 'N/A')} to {last7.get('to_date', 'N/A')}):
- Views              : {last7.get('views', 0)}
- Watch Hours        : {last7.get('watch_hours', 0)} hrs
- Subscribers Gained : {last7.get('subs_gained', 0)}
- Subscribers Lost   : {last7.get('subs_lost', 0)}
- Net Subscribers    : {last7.get('net_subs', 0)}
- Likes              : {last7.get('likes', 0)}

LAST 30 DAYS ({last30.get('from_date', 'N/A')} to {last30.get('to_date', 'N/A')}):
- Views              : {last30.get('views', 0)}
- Watch Hours        : {last30.get('watch_hours', 0)} hrs
- Subscribers Gained : {last30.get('subs_gained', 0)}
- Subscribers Lost   : {last30.get('subs_lost', 0)}
- Net Subscribers    : {last30.get('net_subs', 0)}
- Likes              : {last30.get('likes', 0)}

TOP PERFORMING VIDEOS:
{top_videos_text}

COMMENT SENTIMENT:
- Positive             : {sentiment['positive_pct']}%
- Negative             : {sentiment['negative_pct']}%
- Total Comments       : {sentiment['total_comments']}

UPCOMING CONTENT PLAN:
{video_ideas_text}

WEEKLY STRATEGY:
{content_plan.get('weekly_strategy', 'N/A')}

Write a professional but friendly executive report in HTML format.

The HTML should:
1. Have a clean professional design with cricket green color (#1a6b2e)
2. Use ONLY these real dates — Report Date: {today}, Next Report: {next_monday}
3. Include these sections:
   - Header with channel name and report date: {today}
   - Milestone progress bar showing {channel['subscribers']}/1000 subscribers
   - Overall channel stats card
   - Last 7 days performance table with dates {last7.get('from_date','N/A')} to {last7.get('to_date','N/A')}
   - Last 30 days performance table with dates {last30.get('from_date','N/A')} to {last30.get('to_date','N/A')}
   - Top 5 videos table
   - Upcoming content plan
   - 3 specific action items for this week
   - Footer showing next report date: {next_monday}
4. Be mobile friendly
5. Look like a real business report

Return ONLY the complete HTML code, nothing else."""

    response = client.messages.create(
        model     = "claude-sonnet-4-20250514",
        max_tokens= 4000,
        messages  = [{"role": "user", "content": prompt}]
    )

    return response.content[0].text


def save_report(html_content):
    os.makedirs("data", exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Report saved to {REPORT_FILE}")


def send_email(gmail_service, html_content):
    print(f"Sending report to {GMAIL_SENDER} and {COFOUNDER_EMAIL}...")

    today   = datetime.now().strftime("%d %b %Y")
    subject = f"BeyoondBoundariess — Weekly Report {today}"

    message            = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"]    = GMAIL_SENDER
    message["To"]      = f"{GMAIL_SENDER}, {COFOUNDER_EMAIL}"

    html_part = MIMEText(html_content, "html")
    message.attach(html_part)

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode("utf-8")

    try:
        gmail_service.users().messages().send(
            userId="me",
            body={"raw": raw_message}
        ).execute()
        print("Report sent successfully to both emails!")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def run_agent4(send_mail=True):
    print("=" * 50)
    print("Agent 4 — Executive Reporter Starting...")
    print("=" * 50)

    analytics, ideas = load_data()
    if not analytics:
        return

    html_content = generate_report_html(analytics, ideas)
    save_report(html_content)

    if send_mail:
        _, _, gmail, _ = get_google_services()
        success = send_email(gmail, html_content)

        if success:
            print("=" * 50)
            print("Weekly report sent successfully!")
            print(f"Sent to  : {GMAIL_SENDER}")
            print(f"Sent to  : {COFOUNDER_EMAIL}")
            print(f"Saved at : {REPORT_FILE}")
            print("=" * 50)
    else:
        print("Report generated and saved locally (email skipped)")

    print("Agent 4 completed!")


if __name__ == "__main__":
    run_agent4()