import json
import os
from datetime import datetime
import anthropic
from config.settings import ANTHROPIC_API_KEY

DATA_FILE_IN  = "data/analytics_brief.json"
DATA_FILE_OUT = "data/content_ideas.json"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# This holds the full conversation history with the team
conversation_history = []


def load_analytics_brief():
    if not os.path.exists(DATA_FILE_IN):
        print("No analytics brief found. Run Agent 3 first.")
        return None
    with open(DATA_FILE_IN, "r", encoding="utf-8") as f:
        return json.load(f)


def build_system_prompt(brief):
    channel_stats = brief["channel_stats"]
    top_videos    = brief["top_videos"]
    sentiment     = brief["comment_analysis"]
    comments      = brief["recent_comments"]

    top_videos_text = ""
    for i, v in enumerate(top_videos[:5], 1):
        top_videos_text += f"{i}. {v['title']} — {v['views']} views, {v['likes']} likes\n"

    comments_text = ""
    for c in comments[:5]:
        comments_text += f"- {c['comment']}\n"

    requests_text = ""
    for r in sentiment.get("viewer_requests", []):
        requests_text += f"- {r}\n"
    if not requests_text:
        requests_text = "No specific requests found"

    system_prompt = f"""You are the Creative Head AI for a Tamil cricket YouTube channel called "BeyoondBoundariess" with {channel_stats['subscribers']} subscribers.

Your job is to help the team create the best cricket content strategy possible.

You have access to the latest channel analytics:

CHANNEL PERFORMANCE:
- Subscribers : {channel_stats['subscribers']}
- Total Views  : {channel_stats['total_views']}
- Total Videos : {channel_stats['total_videos']}

TOP PERFORMING VIDEOS:
{top_videos_text}

RECENT VIEWER COMMENTS:
{comments_text}

VIEWER REQUESTS:
{requests_text}

COMMENT SENTIMENT:
- Positive: {sentiment['positive_pct']}%
- Negative: {sentiment['negative_pct']}%

YOUR BEHAVIOUR RULES:
1. All titles and content must be in ENGLISH only
2. Focus on cricket — CSK, IPL 2025, player analysis, match reviews
3. When team members suggest ideas, evaluate them honestly
4. If a suggestion is good, accept it and improve it further
5. If a suggestion is bad, explain clearly WHY with data from analytics
6. Stand firm on decisions backed by data — don't just agree to please
7. Always back your reasoning with channel performance data
8. Be conversational, direct and collaborative like a real creative head
9. Keep the channel goal in mind — grow from {channel_stats['subscribers']} to 10,000 subscribers

When asked to generate a content plan, respond in this JSON format:
{{
  "video_ideas": [
    {{
      "title": "Video title here",
      "concept": "Brief concept explanation",
      "why_it_will_work": "Reason based on analytics",
      "best_time_to_post": "Day and time in IST",
      "estimated_views": "Low/Medium/High",
      "duration": "8-12 mins"
    }}
  ],
  "short_ideas": [
    {{
      "title": "Short title here",
      "concept": "60 second concept",
      "hook": "Opening 3 seconds hook",
      "best_time_to_post": "Day and time in IST"
    }}
  ],
  "topics_to_avoid": ["topic1", "topic2"],
  "weekly_strategy": "Overall strategy in 2-3 sentences"
}}

For normal conversation, just reply naturally without JSON."""

    return system_prompt


def chat_with_agent1(system_prompt, user_message):
    global conversation_history

    # Add user message to history
    conversation_history.append({
        "role"   : "user",
        "content": user_message
    })

    # Send full conversation to Claude
    response = client.messages.create(
        model     = "claude-sonnet-4-20250514",
        max_tokens= 4000,
        system    = system_prompt,
        messages  = conversation_history
    )

    assistant_reply = response.content[0].text

    # Add Claude's reply to history
    conversation_history.append({
        "role"   : "assistant",
        "content": assistant_reply
    })

    return assistant_reply


def try_parse_ideas(response_text):
    try:
        start    = response_text.find("{")
        end      = response_text.rfind("}") + 1
        json_str = response_text[start:end]
        return json.loads(json_str)
    except Exception:
        return None


def save_content_ideas(ideas):
    output = {
        "generated_at"  : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "next_run_hours": 72,
        "content_plan"  : ideas
    }
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE_OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nContent ideas saved to {DATA_FILE_OUT}")


def print_ideas(ideas):
    if not ideas:
        return

    print("\n" + "=" * 50)
    print("CONTENT PLAN — BEYOONDBOUNDARIESS")
    print("=" * 50)

    print("\n VIDEO IDEAS:")
    print("-" * 40)
    for i, v in enumerate(ideas.get("video_ideas", []), 1):
        print(f"\n{i}. {v['title']}")
        print(f"   Concept : {v['concept']}")
        print(f"   Why     : {v['why_it_will_work']}")
        print(f"   Post at : {v['best_time_to_post']}")
        print(f"   Expected: {v['estimated_views']} views")

    print("\n SHORT IDEAS:")
    print("-" * 40)
    for i, s in enumerate(ideas.get("short_ideas", []), 1):
        print(f"\n{i}. {s['title']}")
        print(f"   Concept : {s['concept']}")
        print(f"   Hook    : {s['hook']}")
        print(f"   Post at : {s['best_time_to_post']}")

    print("\n TOPICS TO AVOID:")
    for t in ideas.get("topics_to_avoid", []):
        print(f"   - {t}")

    print(f"\n WEEKLY STRATEGY:")
    print(f"   {ideas.get('weekly_strategy', '')}")
    print("=" * 50)


def run_agent1():
    global conversation_history
    conversation_history = []

    print("=" * 50)
    print("Agent 1 — Creative Head Starting...")
    print("=" * 50)

    brief = load_analytics_brief()
    if not brief:
        return

    system_prompt = build_system_prompt(brief)

    # Step 1 — Auto generate initial content plan
    print("Generating initial content plan...")
    initial_message = """Generate a content plan for the next 3 days for BeyoondBoundariess. 
Give 5 video ideas and 5 short ideas based on the analytics data you have."""

    response = chat_with_agent1(system_prompt, initial_message)

    # Try to parse and display as structured plan
    ideas = try_parse_ideas(response)
    if ideas:
        save_content_ideas(ideas)
        print_ideas(ideas)
    else:
        print("\nAgent 1 Response:")
        print(response)

    # Step 2 — Open team conversation
    print("\n" + "=" * 50)
    print("TEAM CHAT WITH AGENT 1")
    print("Type your suggestions, feedback or questions.")
    print("Type 'save' to save latest ideas.")
    print("Type 'exit' to finish.")
    print("=" * 50)

    while True:
        print()
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("\nAgent 1 session ended.")
            break

        if user_input.lower() == "save":
            # Ask Agent 1 to give final plan as JSON
            save_response = chat_with_agent1(
                system_prompt,
                "Give me the final updated content plan in JSON format based on our discussion."
            )
            final_ideas = try_parse_ideas(save_response)
            if final_ideas:
                save_content_ideas(final_ideas)
                print("Final plan saved!")
            else:
                print("Could not parse final plan. Try again.")
            continue

        # Normal team conversation
        reply = chat_with_agent1(system_prompt, user_input)
        print(f"\nAgent 1: {reply}")

    print("\nAgent 1 completed!")
    return ideas


def run_agent1_auto():
    """
    UI version — runs without interactive chat.
    Generates content plan and saves automatically.
    """
    global conversation_history
    conversation_history = []

    print("=" * 50)
    print("Agent 1 — Creative Head (Auto Mode)...")
    print("=" * 50)

    brief = load_analytics_brief()
    if not brief:
        return None

    system_prompt = build_system_prompt(brief)

    print("Generating content plan...")
    initial_message = """Generate a content plan for the next 3 days for BeyoondBoundariess.
Give 5 video ideas and 5 short ideas based on the analytics data you have."""

    response = chat_with_agent1(system_prompt, initial_message)

    ideas = try_parse_ideas(response)
    if ideas:
        save_content_ideas(ideas)
        print_ideas(ideas)
        print("Agent 1 completed successfully!")
        return ideas
    else:
        print("Agent 1 completed.")
        return None


if __name__ == "__main__":
    run_agent1()