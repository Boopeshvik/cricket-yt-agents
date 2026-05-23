import json
import os
from datetime import datetime, timedelta
from utils.google_auth import get_google_services

DATA_FILE = "data/analytics_brief.json"


def fetch_channel_stats(youtube):
    print("Fetching channel statistics...")
    response = youtube.channels().list(
        part="statistics,snippet",
        mine=True
    ).execute()

    channel = response["items"][0]
    stats   = channel["statistics"]

    return {
        "channel_name" : channel["snippet"]["title"],
        "channel_id"   : channel["id"],
        "subscribers"  : int(stats.get("subscriberCount", 0)),
        "total_views"  : int(stats.get("viewCount", 0)),
        "total_videos" : int(stats.get("videoCount", 0)),
        "fetched_at"   : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def fetch_period_stats(youtube_analytics, channel_id):
    print("Fetching 7 day and 30 day stats...")

    today    = datetime.now().strftime("%Y-%m-%d")
    day7ago  = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    day30ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    def get_stats(start_date, end_date):
        try:
            response = youtube_analytics.reports().query(
                ids        = f"channel=={channel_id}",
                startDate  = start_date,
                endDate    = end_date,
                metrics    = "views,estimatedMinutesWatched,subscribersGained,subscribersLost,likes",
                dimensions = "day",
            ).execute()

            rows        = response.get("rows", [])
            total_views = sum(r[1] for r in rows)
            total_watch = sum(r[2] for r in rows)
            subs_gained = sum(r[3] for r in rows)
            subs_lost   = sum(r[4] for r in rows)
            total_likes = sum(r[5] for r in rows)

            return {
                "views"       : int(total_views),
                "watch_hours" : round(total_watch / 60, 1),
                "subs_gained" : int(subs_gained),
                "subs_lost"   : int(subs_lost),
                "net_subs"    : int(subs_gained - subs_lost),
                "likes"       : int(total_likes),
                "from_date"   : start_date,
                "to_date"     : end_date
            }
        except Exception as e:
            print(f"Could not fetch period stats: {e}")
            return {
                "views"       : 0,
                "watch_hours" : 0,
                "subs_gained" : 0,
                "subs_lost"   : 0,
                "net_subs"    : 0,
                "likes"       : 0,
                "from_date"   : start_date,
                "to_date"     : end_date
            }

    return {
        "last_7_days"  : get_stats(day7ago,  today),
        "last_30_days" : get_stats(day30ago, today)
    }


def fetch_top_videos(youtube):
    print("Fetching top 10 videos...")
    response = youtube.search().list(
        part="snippet",
        forMine=True,
        type="video",
        order="viewCount",
        maxResults=10
    ).execute()

    videos = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title    = item["snippet"]["title"]
        date     = item["snippet"]["publishedAt"][:10]

        stats_response = youtube.videos().list(
            part="statistics",
            id=video_id
        ).execute()

        if stats_response["items"]:
            s = stats_response["items"][0]["statistics"]
            videos.append({
                "video_id" : video_id,
                "title"    : title,
                "published": date,
                "views"    : int(s.get("viewCount",    0)),
                "likes"    : int(s.get("likeCount",    0)),
                "comments" : int(s.get("commentCount", 0))
            })

    return videos


def fetch_recent_comments(youtube):
    print("Fetching recent comments...")

    channel_response = youtube.channels().list(
        part="id",
        mine=True
    ).execute()

    channel_id = channel_response["items"][0]["id"]

    response = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        type="video",
        order="date",
        maxResults=5
    ).execute()

    all_comments = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title    = item["snippet"]["title"]

        try:
            comments_response = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=10,
                order="time"
            ).execute()

            for c in comments_response.get("items", []):
                text = c["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                all_comments.append({
                    "video_title": title,
                    "comment"    : text
                })
            print(f"  Got {len(comments_response.get('items', []))} comments from: {title[:40]}...")

        except Exception as e:
            print(f"  Skipped: {title[:40]}... ({str(e)[:50]})")

    return all_comments[:50]


def analyse_comments(comments):
    print("Analysing comments...")
    positive_words = ["super", "great", "excellent", "good", "best",
                      "love", "amazing", "nice", "perfect", "நன்றி",
                      "அருமை", "சூப்பர்", "வாழ்க", "மிகவும்"]

    negative_words = ["bad", "worst", "boring", "hate", "dislike",
                      "மோசம்", "கஷ்டம்"]

    request_words  = ["please", "make video", "cover", "explain",
                      "பண்ணுங்க", "சொல்லுங்க", "வேணும்"]

    positive = 0
    negative = 0
    requests = []

    for c in comments:
        text = c["comment"].lower()
        if any(w in text for w in positive_words):
            positive += 1
        if any(w in text for w in negative_words):
            negative += 1
        if any(w in text for w in request_words):
            requests.append(c["comment"])

    total = len(comments) if comments else 1
    return {
        "total_comments" : len(comments),
        "positive_pct"   : round((positive / total) * 100),
        "negative_pct"   : round((negative / total) * 100),
        "viewer_requests": requests[:5]
    }


def save_brief(brief):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(brief, f, indent=2, ensure_ascii=False)
    print(f"Brief saved to {DATA_FILE}")


def run_agent3():
    print("=" * 50)
    print("Agent 3 — Analytics Manager Starting...")
    print("=" * 50)

    youtube, youtube_analytics, gmail, drive = get_google_services()

    channel_stats = fetch_channel_stats(youtube)
    channel_id    = channel_stats["channel_id"]
    period_stats  = fetch_period_stats(youtube_analytics, channel_id)
    top_videos    = fetch_top_videos(youtube)
    comments      = fetch_recent_comments(youtube)
    sentiment     = analyse_comments(comments)

    brief = {
        "generated_at"    : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "next_run_hours"  : 72,
        "channel_stats"   : channel_stats,
        "period_stats"    : period_stats,
        "top_videos"      : top_videos,
        "comment_analysis": sentiment,
        "recent_comments" : comments[:10]
    }

    save_brief(brief)

    print("=" * 50)
    print(f"Channel      : {channel_stats['channel_name']}")
    print(f"Subscribers  : {channel_stats['subscribers']}")
    print(f"Total Views  : {channel_stats['total_views']}")
    print(f"Top Video    : {top_videos[0]['title'] if top_videos else 'N/A'}")
    print(f"Comments     : {sentiment['total_comments']} analysed")
    print(f"Sentiment    : {sentiment['positive_pct']}% positive")
    print(f"Requests     : {len(sentiment['viewer_requests'])} viewer requests found")
    print(f"Last 7 days  : {period_stats['last_7_days']['views']} views, {period_stats['last_7_days']['net_subs']} net subs")
    print(f"Last 30 days : {period_stats['last_30_days']['views']} views, {period_stats['last_30_days']['net_subs']} net subs")
    print("=" * 50)
    print("Agent 3 completed successfully!")

    return brief


if __name__ == "__main__":
    run_agent3()