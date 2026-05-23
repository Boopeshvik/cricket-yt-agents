import json
import os
from datetime import datetime
import anthropic
from config.settings import ANTHROPIC_API_KEY

DATA_FILE_IN  = "data/content_ideas.json"
DATA_FILE_OUT = "data/thumbnail_ideas.json"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

conversation_history = []


def load_content_ideas():
    if not os.path.exists(DATA_FILE_IN):
        print("No content ideas found. Run Agent 1 first.")
        return None
    with open(DATA_FILE_IN, "r", encoding="utf-8") as f:
        return json.load(f)


def build_system_prompt():
    return """You are the Visual Designer AI for a Tamil cricket YouTube channel called "BeyoondBoundariess".

Your job is to create detailed thumbnail concepts and design briefs for cricket videos.

YOUR DESIGN STYLE:
- Bold, high contrast thumbnails
- Cricket green (#1a6b2e) as primary brand color
- Large readable text that works on mobile
- Emotional faces or action shots as focal point
- Clean backgrounds that don't distract
- Yellow/gold accents for highlights

YOUR BEHAVIOUR RULES:
1. Generate specific, actionable design briefs
2. Include exact text overlay suggestions
3. Suggest specific colors with hex codes
4. Describe the main visual element clearly
5. Keep mobile viewing in mind — text must be readable on small screens
6. When team gives feedback, refine the design
7. Stand firm if your design reasoning is data-backed
8. Be conversational and collaborative

For each thumbnail provide:
- Main visual element (player, action, graphic)
- Background style
- Text overlay (title text on thumbnail)
- Color scheme with hex codes
- Mood/emotion to convey
- Canva or Photoshop tips
- AI image generation prompt (for tools like Midjourney or DALL-E)"""


def generate_thumbnails(content_ideas):
    print("Generating thumbnail concepts with Claude...")

    videos = content_ideas["content_plan"].get("video_ideas", [])
    shorts = content_ideas["content_plan"].get("short_ideas", [])

    all_items = []
    for v in videos[:5]:
        all_items.append({"type": "video", "title": v["title"], "concept": v["concept"]})
    for s in shorts[:5]:
        all_items.append({"type": "short", "title": s["title"], "concept": s["concept"]})

    items_text = ""
    for i, item in enumerate(all_items, 1):
        items_text += f"{i}. [{item['type'].upper()}] {item['title']}\n   Concept: {item['concept']}\n\n"

    prompt = f"""Generate detailed thumbnail design briefs for these cricket videos:

{items_text}

Respond in this exact JSON format:
{{
  "thumbnails": [
    {{
      "video_title"     : "exact title here",
      "type"            : "video or short",
      "main_visual"     : "describe the main image/photo to use",
      "background"      : "background style and color",
      "text_overlay"    : "exact text to put on thumbnail (short, punchy)",
      "color_scheme"    : {{
        "primary"   : "#hexcode",
        "secondary" : "#hexcode",
        "text"      : "#hexcode",
        "accent"    : "#hexcode"
      }},
      "mood"            : "emotion to convey",
      "canva_tips"      : "specific Canva design tips",
      "ai_image_prompt" : "detailed prompt for AI image generation"
    }}
  ]
}}

Make each thumbnail unique, bold and optimised for cricket fans on mobile."""

    response = client.messages.create(
        model     = "claude-sonnet-4-20250514",
        max_tokens= 4000,
        messages  = [{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text

    try:
        start    = response_text.find("{")
        end      = response_text.rfind("}") + 1
        json_str = response_text[start:end]
        return json.loads(json_str)
    except Exception as e:
        print(f"Could not parse JSON: {e}")
        return {"raw_response": response_text}


def save_thumbnail_ideas(ideas):
    output = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "thumbnails"  : ideas
    }
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE_OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Thumbnail ideas saved to {DATA_FILE_OUT}")


def print_thumbnails(ideas):
    thumbnails = ideas.get("thumbnails", [])
    print("\n" + "=" * 50)
    print("THUMBNAIL CONCEPTS — BEYOONDBOUNDARIESS")
    print("=" * 50)

    for i, t in enumerate(thumbnails, 1):
        print(f"\n{i}. {t['video_title']}")
        print(f"   Type       : {t['type'].upper()}")
        print(f"   Main Visual: {t['main_visual']}")
        print(f"   Text       : {t['text_overlay']}")
        print(f"   Mood       : {t['mood']}")
        print(f"   Colors     : Primary {t['color_scheme']['primary']} | Accent {t['color_scheme']['accent']}")
        print(f"   Canva Tips : {t['canva_tips']}")
        print(f"   AI Prompt  : {t['ai_image_prompt'][:80]}...")
    print("=" * 50)


def chat_with_designer(system_prompt, user_message):
    global conversation_history

    conversation_history.append({
        "role"   : "user",
        "content": user_message
    })

    response = client.messages.create(
        model     = "claude-sonnet-4-20250514",
        max_tokens= 2000,
        system    = system_prompt,
        messages  = conversation_history
    )

    reply = response.content[0].text

    conversation_history.append({
        "role"   : "assistant",
        "content": reply
    })

    return reply


def run_agent2():
    global conversation_history
    conversation_history = []

    print("=" * 50)
    print("Agent 2 — Visual Designer Starting...")
    print("=" * 50)

    content_ideas = load_content_ideas()
    if not content_ideas:
        return

    # Generate thumbnail concepts
    ideas = generate_thumbnails(content_ideas)

    if "thumbnails" in ideas:
        save_thumbnail_ideas(ideas)
        print_thumbnails(ideas)
    else:
        print("\nAgent 2 Response:")
        print(ideas.get("raw_response", "No response"))

    # Team chat with designer
    system_prompt = build_system_prompt()

    print("\n" + "=" * 50)
    print("TEAM CHAT WITH AGENT 2 — VISUAL DESIGNER")
    print("Ask for changes, new concepts or feedback.")
    print("Type 'save' to save latest designs.")
    print("Type 'exit' to finish.")
    print("=" * 50)

    while True:
        print()
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("\nAgent 2 session ended.")
            break

        if user_input.lower() == "save":
            save_response = chat_with_designer(
                system_prompt,
                "Give me the final updated thumbnail concepts in JSON format."
            )
            try:
                start = save_response.find("{")
                end   = save_response.rfind("}") + 1
                final = json.loads(save_response[start:end])
                save_thumbnail_ideas(final)
                print("Final designs saved!")
            except Exception:
                print("Could not parse. Try again.")
            continue

        reply = chat_with_designer(system_prompt, user_input)
        print(f"\nAgent 2: {reply}")

    print("\nAgent 2 completed!")
    return ideas


def run_agent2_auto():
    """
    UI version — runs without interactive chat.
    Generates thumbnail concepts and saves automatically.
    """
    global conversation_history
    conversation_history = []

    print("=" * 50)
    print("Agent 2 — Visual Designer (Auto Mode)...")
    print("=" * 50)

    content_ideas = load_content_ideas()
    if not content_ideas:
        return None

    ideas = generate_thumbnails(content_ideas)

    if "thumbnails" in ideas:
        save_thumbnail_ideas(ideas)
        print_thumbnails(ideas)
        print("Agent 2 completed successfully!")
        return ideas
    else:
        print("Agent 2 completed.")
        return None


if __name__ == "__main__":
    run_agent2()