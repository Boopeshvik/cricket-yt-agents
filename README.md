# 🏏 BeyoondBoundariess — AI Multi-Agent Workforce for YouTube

> **A five-agent AI system that automates end-to-end YouTube content production for a cricket channel.**  
> From analytics to publishing — fully orchestrated, fully autonomous.

🔗 **Live System:** [cricket-yt-agents.onrender.com](https://cricket-yt-agents.onrender.com/)  
📺 **YouTube Channel:** [BeyoondBoundariess](https://www.youtube.com/@BeyoondBoundariess)

---

## 🧠 Why I Built This

Running a YouTube channel manually is a second job. Research, scripting, thumbnail ideation, analytics review, scheduling — each takes hours. I wanted to explore whether a coordinated system of AI agents could take over the operational burden, freeing the creator to focus purely on judgment and quality.

This project is also my most direct demonstration of **multi-agent system design**: not one AI doing everything, but specialised agents with defined responsibilities, communicating through a shared orchestration layer.

---

## 🎯 The Problem It Solves

| Manual Process | AI Agent Solution |
|---|---|
| Hours reviewing YouTube Analytics | Analytics Agent pulls and summarises performance data automatically |
| Brainstorming video topics | Content Ideation Agent generates data-driven topic recommendations |
| Designing thumbnail concepts | Thumbnail Design Agent creates visual briefs based on top-performing patterns |
| Writing executive summaries | Reporting Agent generates weekly performance reports |
| Managing upload schedule | Auto-Publishing Agent handles scheduling and metadata |

**Result:** ~80% reduction in content preparation effort. End-to-end production cycles cut from several hours to under one hour.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Orchestration Layer                    │
│                  FastAPI + HTTP Routing                  │
└──────┬──────────┬──────────┬──────────┬─────────────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
  ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────┐
  │Analytics│ │Content │ │Thumbna-│ │Executi-│ │ Auto-   │
  │ Agent   │ │Ideation│ │il Agent│ │ve Rpt  │ │Publish  │
  │         │ │ Agent  │ │        │ │ Agent  │ │ Agent   │
  └────┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └────┬────┘
       │          │          │          │             │
       └──────────┴──────────┴──────────┴─────────────┘
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
       ┌────────────┐  ┌────────────┐  ┌────────────┐
       │ Claude AI  │  │ YouTube    │  │  Google    │
       │ (Anthropic)│  │ Data API   │  │  APIs      │
       └────────────┘  └────────────┘  └────────────┘
```

---

## 🤖 The Five Agents — Roles & Responsibilities

### 1. 📊 Analytics Agent
- Pulls channel performance data via YouTube Data API
- Identifies top-performing videos, drop-off patterns, and audience trends
- Outputs structured performance summary for other agents to use

### 2. 💡 Content Ideation Agent
- Receives analytics insights from Agent 1
- Uses Claude AI to generate topic recommendations based on what's performing
- Considers trending cricket events, seasonal relevance, and gap analysis
- Outputs a prioritised content brief

### 3. 🎨 Thumbnail Design Agent
- Analyses top-performing thumbnail patterns from analytics
- Generates creative briefs: layout, colour, text, imagery direction
- Outputs thumbnail concept ready for design execution

### 4. 📋 Executive Reporting Agent
- Aggregates outputs from all other agents
- Generates a weekly executive summary: performance, recommendations, next actions
- Formatted for quick review — decision-ready, not data-heavy

### 5. 🚀 Auto-Publishing Agent
- Handles video scheduling, metadata generation, and tag optimisation
- Coordinates with YouTube API for upload preparation
- Reduces manual publishing overhead to near zero

---

## 🔑 Key Technical Decisions

**Why HTTP POST instead of WebSockets?**  
Windows compatibility. During development, WebSocket connections caused persistent issues in the target deployment environment. HTTP POST with async handlers gave the same event-driven behaviour without the compatibility headaches — a pragmatic call that kept the project moving.

**Why FastAPI as the orchestration layer?**  
Lightweight, async-native, and easy to expose individual agent endpoints for testing and debugging. Each agent is callable independently, which made iteration much faster.

**Why separate agents rather than one large prompt?**  
Specialisation improves output quality. A single "do everything" prompt produces mediocre results across the board. Giving each agent a narrow, well-defined job — with its own system prompt and context — produces dramatically better outputs. This also mirrors how real teams work: specialists, not generalists, for each task.

**OAuth token management:**  
YouTube OAuth tokens stored as base64-encoded environment variables, decoded at runtime — keeping credentials secure without a secrets manager overhead for a solo project.

---

## ✨ Workflow in Action

```
1. Trigger: Weekly scheduled run (or manual via API)
2. Analytics Agent → fetches last 7 days of channel data
3. Content Ideation Agent → reads analytics, generates 5 topic briefs
4. Thumbnail Agent → generates 3 thumbnail concepts per topic
5. Reporting Agent → compiles everything into executive summary
6. Auto-Publishing Agent → schedules approved content, generates metadata
7. Output: Complete content plan + performance report, ready for review
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | Python, FastAPI |
| AI | Anthropic Claude API |
| Data | YouTube Data API v3, Google APIs |
| Auth | OAuth 2.0 (base64 token management) |
| Deployment | Render |
| Communication | HTTP POST (async) |

---

## 💡 What I Learned / Would Build Next

**Learned:**
- Multi-agent design is fundamentally a product problem: defining agent scope, handoffs, and failure modes requires the same thinking as designing a product feature set
- Agent specialisation dramatically outperforms monolithic prompts — the quality gap is significant
- Deployment environment constraints (Windows/OS compatibility) shape architecture decisions more than developers expect

**What I'd build next:**
- ⏰ Automated scheduler (cron-based trigger, currently manual)
- 🎙️ Script writing agent — full video script generated from the content brief
- 📈 A/B testing agent — comparing thumbnail and title performance across uploads
- 🌐 Dashboard UI — visual overview of all agent outputs in one place
- 🔗 Cross-platform agent — repurposing content for Instagram Reels and Twitter/X

---

## 🚀 Running Locally

```bash
git clone https://github.com/Boopeshvik/cricket-yt-agents.git
cd cricket-yt-agents

pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY=your_claude_api_key
export YOUTUBE_CLIENT_ID=your_youtube_client_id
export YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
export YOUTUBE_REFRESH_TOKEN_B64=base64_encoded_refresh_token

uvicorn main:app --reload
```

---

## 👤 About the Builder

Built by **Boopesh Vikram** — AI Product Leader and hands-on AI practitioner.  
📌 [boopeshvikram.com](https://www.boopeshvikram.com) · [LinkedIn](https://www.linkedin.com/in/boopeshvikram) · [GitHub](https://github.com/Boopeshvik)
