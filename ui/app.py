import json
import os
import asyncio
import threading
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="BeyoondBoundariess Agent System")

app.mount("/static", StaticFiles(directory="ui/static"), name="static")
templates = Jinja2Templates(directory="ui/templates")


def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def run_agent_in_thread(agent_id):
    if agent_id == "3":
        from agents.agent3_analytics import run_agent3
        run_agent3()
    elif agent_id == "1":
        from agents.agent1_creative import run_agent1_auto
        run_agent1_auto()
    elif agent_id == "2":
        from agents.agent2_designer import run_agent2_auto
        run_agent2_auto()
    elif agent_id == "4":
        from agents.agent4_reporter import run_agent4
        run_agent4()
    elif agent_id == "5":
        from agents.agent5_publisher import run_agent5
        run_agent5()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    analytics  = load_json("data/analytics_brief.json")
    ideas      = load_json("data/content_ideas.json")
    raw_thumbs = load_json("data/thumbnail_ideas.json")

    thumbnails = None
    if raw_thumbs:
        thumb_list = raw_thumbs.get("thumbnails", [])
        if isinstance(thumb_list, dict):
            thumb_list = thumb_list.get("thumbnails", [])
        thumbnails = {
            "generated_at": raw_thumbs.get("generated_at", ""),
            "thumbnails"  : thumb_list
        }

    return templates.TemplateResponse(
        request = request,
        name    = "dashboard.html",
        context = {
            "analytics" : analytics,
            "ideas"     : ideas,
            "thumbnails": thumbnails
        }
    )


@app.get("/api/analytics")
async def get_analytics():
    data = load_json("data/analytics_brief.json")
    if data:
        return JSONResponse(content=data)
    return JSONResponse(content={"error": "No analytics data found"}, status_code=404)


@app.get("/api/ideas")
async def get_ideas():
    data = load_json("data/content_ideas.json")
    if data:
        return JSONResponse(content=data)
    return JSONResponse(content={"error": "No content ideas found"}, status_code=404)


@app.get("/api/thumbnails")
async def get_thumbnails():
    data = load_json("data/thumbnail_ideas.json")
    if data:
        return JSONResponse(content=data)
    return JSONResponse(content={"error": "No thumbnail ideas found"}, status_code=404)


@app.get("/api/report")
async def get_report():
    path = "data/weekly_report.html"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content="<p style='padding:20px;font-family:sans-serif;color:#64748b'>No report generated yet.</p>"
    )


@app.post("/api/run-agent/{agent_id}")
async def run_agent_http(agent_id: str):
    try:
        result = {"done": False, "error": None}

        def thread_target():
            try:
                run_agent_in_thread(agent_id)
                result["done"] = True
            except Exception as e:
                import traceback
                result["error"] = traceback.format_exc()

        thread = threading.Thread(target=thread_target)
        thread.start()
        thread.join(timeout=300)

        if result["error"]:
            return JSONResponse(content={"status": "error", "detail": result["error"]})
        return JSONResponse(content={
            "status" : "success",
            "agent"  : agent_id,
            "message": f"Agent {agent_id} completed successfully!"
        })

    except Exception as e:
        import traceback
        return JSONResponse(content={"status": "error", "detail": traceback.format_exc()})


@app.get("/api/test-agent/{agent_id}")
async def test_agent(agent_id: str):
    try:
        result = {"done": False, "error": None}

        def thread_target():
            try:
                run_agent_in_thread(agent_id)
                result["done"] = True
            except Exception as e:
                import traceback
                result["error"] = traceback.format_exc()

        thread = threading.Thread(target=thread_target)
        thread.start()
        thread.join(timeout=300)

        if result["error"]:
            return JSONResponse(content={"status": "error", "detail": result["error"]})
        return JSONResponse(content={
            "status" : "success",
            "agent"  : agent_id,
            "message": f"Agent {agent_id} completed successfully"
        })

    except Exception as e:
        import traceback
        return JSONResponse(content={"status": "error", "detail": traceback.format_exc()})


@app.get("/api/debug-performance")
async def debug_performance():
    try:
        from utils.google_auth import get_google_services
        from agents.agent3_analytics import fetch_channel_stats

        youtube, youtube_analytics, gmail, drive = get_google_services()
        channel_stats = fetch_channel_stats(youtube)
        channel_id    = channel_stats["channel_id"]

        today    = datetime.now().strftime("%Y-%m-%d")
        day30ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        response = youtube_analytics.reports().query(
            ids       = f"channel=={channel_id}",
            startDate = day30ago,
            endDate   = today,
            metrics   = "views,estimatedMinutesWatched,subscribersGained,averageViewDuration,averageViewPercentage",
            dimensions= "day"
        ).execute()

        return JSONResponse(content={
            "channel_id"    : channel_id,
            "date_range"    : f"{day30ago} to {today}",
            "row_count"     : len(response.get("rows", [])),
            "column_headers": response.get("columnHeaders", []),
            "first_3_rows"  : response.get("rows", [])[:3],
        })

    except Exception as e:
        import traceback
        return JSONResponse(content={"error": traceback.format_exc()})


@app.websocket("/ws/agent/{agent_id}")
async def run_agent_ws(websocket: WebSocket, agent_id: str):
    await websocket.accept()
    try:
        await websocket.send_text(f"Starting Agent {agent_id}...")

        result = {"done": False, "error": None}

        def thread_target():
            try:
                run_agent_in_thread(agent_id)
                result["done"] = True
            except Exception as e:
                import traceback
                result["error"] = traceback.format_exc()

        thread = threading.Thread(target=thread_target)
        thread.start()

        while thread.is_alive():
            await asyncio.sleep(2)
            try:
                await websocket.send_text(f"Agent {agent_id} still running...")
            except Exception:
                break

        thread.join()

        if result["error"]:
            await websocket.send_text(f"ERROR::{result['error']}")
        else:
            await websocket.send_text(f"DONE::Agent {agent_id} completed successfully!")

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(f"ERROR::{str(e)}")


@app.post("/api/handoff/agent1-to-agent2")
async def handoff_to_agent2(request: Request):
    try:
        ideas = load_json("data/content_ideas.json")
        if not ideas:
            return JSONResponse(content={"error": "No content ideas found. Run Agent 1 first."})

        plan     = ideas.get("content_plan", {})
        videos   = plan.get("video_ideas",  [])
        shorts   = plan.get("short_ideas",  [])
        strategy = plan.get("weekly_strategy", "")

        video_list = "\n".join([f"{i+1}. {v['title']}" for i, v in enumerate(videos[:5])])
        short_list = "\n".join([f"{i+1}. {s['title']}" for i, s in enumerate(shorts[:5])])

        handoff_message = f"""Agent 1 has finalized the content plan. Here are the approved ideas:

VIDEO IDEAS:
{video_list}

SHORT IDEAS:
{short_list}

WEEKLY STRATEGY:
{strategy}

Please generate detailed thumbnail concepts for each of these videos and shorts."""

        from agents.agent2_designer import chat_with_designer, build_system_prompt
        system_prompt = build_system_prompt()
        reply         = chat_with_designer(system_prompt, handoff_message)

        return JSONResponse(content={
            "status" : "success",
            "reply"  : reply,
            "message": "Content plan sent to Agent 2 successfully!"
        })

    except Exception as e:
        import traceback
        return JSONResponse(content={"error": traceback.format_exc()})


@app.get("/api/benchmarks")
async def get_benchmarks():
    data = load_json("data/benchmarks.json")
    if data:
        return JSONResponse(content=data)
    defaults = {
        "video": {
            "impressions"       : 0,
            "views"             : 2000,
            "ctr"               : 0,
            "avg_view_duration" : 300,
            "audience_retention": 40.0,
            "watch_hours"       : 35,
            "subs_gained"       : 15,
            "returning_viewers" : 0
        },
        "short": {
            "impressions"       : 0,
            "views"             : 5000,
            "ctr"               : 0,
            "avg_view_duration" : 30,
            "audience_retention": 60.0,
            "watch_hours"       : 20,
            "subs_gained"       : 5,
            "returning_viewers" : 0
        }
    }
    return JSONResponse(content=defaults)


@app.post("/api/benchmarks")
async def save_benchmarks(request: Request):
    body = await request.json()
    os.makedirs("data", exist_ok=True)
    with open("data/benchmarks.json", "w") as f:
        json.dump(body, f, indent=2)
    return JSONResponse(content={"status": "saved"})


@app.post("/api/performance")
async def get_performance(request: Request):
    body         = await request.json()
    start_date   = body.get("start_date")
    end_date     = body.get("end_date")
    content_type = body.get("content_type", "video")

    try:
        from utils.google_auth import get_google_services
        from agents.agent3_analytics import (
            fetch_channel_stats,
            fetch_individual_video_metrics
        )

        youtube, youtube_analytics, gmail, drive = get_google_services()
        channel_stats = fetch_channel_stats(youtube)
        channel_id    = channel_stats["channel_id"]

        # Fetch individual video metrics (max 10 to avoid timeout)
        max_videos = body.get("max_videos", 10)

        # Fetch individual video metrics
        individual = fetch_individual_video_metrics(
            youtube, youtube_analytics, channel_id,
            start_date, end_date, content_type,
            max_videos=max_videos
        )


        # Calculate averages from individual video data
        num_videos = len(individual) if individual else 1

        def avg(key):
            vals = [v[key] for v in individual if v.get(key, 0) > 0]
            return round(sum(vals) / len(vals), 1) if vals else 0

        avg_duration_sec = avg("avg_view_duration_sec")
        mins = int(avg_duration_sec // 60)
        secs = int(avg_duration_sec % 60)

        consolidated = {
            "impressions"          : 0,
            "views"                : avg("views"),
            "ctr"                  : 0,
            "avg_view_duration_sec": avg_duration_sec,
            "avg_view_duration_fmt": f"{mins}:{secs:02d}",
            "audience_retention"   : avg("audience_retention"),
            "watch_hours"          : avg("watch_hours"),
            "subs_gained"          : avg("subs_gained"),
            "returning_viewers"    : 0,
            "from_date"            : start_date,
            "to_date"              : end_date,
            "content_type"         : content_type,
            "num_videos"           : num_videos
        }

        return JSONResponse(content={
            "status"      : "success",
            "consolidated": consolidated,
            "individual"  : individual,
            "start_date"  : start_date,
            "end_date"    : end_date,
            "content_type": content_type,
            "num_videos"  : num_videos
        })

    except Exception as e:
        import traceback
        return JSONResponse(content={
            "status": "error",
            "detail": traceback.format_exc()
        })


@app.post("/api/chat/agent1")
async def chat_agent1(request: Request):
    body    = await request.json()
    message = body.get("message", "")

    from agents.agent1_creative import (
        chat_with_agent1,
        build_system_prompt,
        load_analytics_brief,
        try_parse_ideas,
        save_content_ideas
    )

    brief = load_analytics_brief()
    if not brief:
        return JSONResponse(content={"error": "Run Agent 3 first"})

    system_prompt = build_system_prompt(brief)
    reply         = chat_with_agent1(system_prompt, message)

    ideas = try_parse_ideas(reply)
    if ideas:
        save_content_ideas(ideas)

    return JSONResponse(content={"reply": reply})


@app.post("/api/chat/agent2")
async def chat_agent2(request: Request):
    body    = await request.json()
    message = body.get("message", "")

    from agents.agent2_designer import (
        chat_with_designer,
        build_system_prompt
    )

    system_prompt = build_system_prompt()
    reply         = chat_with_designer(system_prompt, message)

    return JSONResponse(content={"reply": reply})