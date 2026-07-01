import os
import json
from google import genai


def generate_report_commentary(analytics_payload: dict, chat_mode: str = "group") -> dict:
    """
    Sends a curated, token-efficient payload to Gemini.
    Gemini reads real messages to do language/personality understanding.
    Python already handled all the math.
    Returns structured JSON with group roast, user profiles, events, and timeline.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not set.")
        return {}

    client = genai.Client(api_key=api_key)

    # ---- Build a lean payload for the LLM ----
    stats_for_llm = {k: v for k, v in analytics_payload.items() if k != "llm_message_sample"}
    message_sample = analytics_payload.get("llm_message_sample", [])

    # Format hot moment samples inline (readable, token-efficient)
    hot_moments_readable = []
    for hm in analytics_payload.get("hot_moments", []):
        signals_str = ", ".join(hm.get("signals", [])) or "general_spike"
        time_str = hm.get("time_tag", "")
        caps_str = " [CAPS DETECTED]" if hm.get("caps_detected") else ""
        pre_ctx = hm.get("pre_context", [])
        pre_text = "\n".join(f"  BEFORE [{m['sender']}]: {m['text']}" for m in pre_ctx)
        msgs_text = "\n".join(
            f"  [{m['sender']}]: {m['text']}"
            for m in hm.get("sample_messages", [])
        )
        block = f"[{hm['date']} {time_str} — {hm['message_count']} msgs | signals: {signals_str}{caps_str}]"
        if pre_text:
            block += f"\nLEAD-UP:\n{pre_text}"
        block += f"\nBURST:\n{msgs_text}"
        hot_moments_readable.append(block)

    # Format evenly spread sample (no media/system msgs)
    spread_sample_text = "\n".join(
        f"[{m['sender']}]: {m['text']}"
        for m in message_sample
    )

    data_block = f"""
---
BEHAVIORAL STATS:
{json.dumps(stats_for_llm, indent=2)}

---
REAL MESSAGES (evenly spread across full timeline):
{spread_sample_text}

---
HOT MOMENTS (most explosive bursts of activity):
{"---".join(hot_moments_readable)}
"""

    if chat_mode == "ego":
        clips_text_list = []
        for chat_clip in analytics_payload.get("chat_clips", []):
            chat_name = chat_clip["chat_name"]
            for idx, clip in enumerate(chat_clip["clips"]):
                clip_lines = []
                for m in clip["clip_msgs"]:
                    if m["type"] == "media":
                        clip_lines.append(f"  {m['sender']}: <Media omitted>")
                    else:
                        clip_lines.append(f"  {m['sender']}: {m['text']}")
                clips_text_list.append(f"[{chat_name} - Conversation Sample #{idx+1}]:\n" + "\n".join(clip_lines))
        clips_text = "\n\n".join(clips_text_list)
        
        prompt = f"""
You are a savage, no-holds-barred AI social profiling analyst. Your job is to brutally analyze the target user's messaging behavior, language style, and social standing across multiple chats, and invent a hilarious, cutting social profile.

You are profiling the user who goes by the names: {analytics_payload.get("user_aliases")}

WRITING STYLE REQUIREMENT: Write the entire analysis strictly in the third person. Refer to the analyzed user by their name/alias (e.g. Zishan) instead of using "you" or "your". The analysis must talk *about* them in the third person to keep the report completely anonymous.

LANGUAGE NOTE: Messages may be in Gujarati, Hindi, English, or mixed Hinglish. Read and understand them all natively. Pay close attention to their tone, slangs, Gujaratiness, Hinglish expressions, abbreviations, and overall texting style.

MEDIA NOTE: The chats have no actual images/videos, represented as `<Media omitted>`. Factor this in! 

TONE: Brutally honest. Savage. Psychological profiling. Name specific behavioral habits (e.g. overyapping, needy response times, double texting, Gujarati slangs). Quote real messages from their samples.

---
EGO STATS (overall metrics for this user):
{json.dumps(analytics_payload.get("ego_stats"), indent=2)}

---
CHAT SUMMARIES (how they participate in different chats):
{json.dumps(analytics_payload.get("chat_summaries"), indent=2)}

---
CHRONOLOGICAL CONVERSATION CLIPS (to see how they interact back-and-forth):
{clips_text}

---
OUTPUT THIS EXACT JSON (raw JSON only, absolutely no markdown fences or backticks):

{{
  "chat_title": "A short savage title for this user's social identity. Max 6 words. e.g. 'The Group Chat Main Character', 'The Needy Double-Texter Who Thinks They Are Cool'.",
  "ego_essence": "2-3 sentences. What is this user's general vibe across their chats? Who do they think they are vs who they actually are?",
  "compatibility_verdict": "One sentence summary of their relationship standing. e.g. 'Highly responsive, but gets left on read because they yap too much.'",
  "personality_summary": "3-4 sentences. A detailed, savage psychological profile of their text communication patterns based on the quotes and reply speeds.",
  "roast": "2-3 sentences of pure roast targeting their text behaviors, referencing real quotes from what they sent.",
  "iconic_quote": "The single most representative verbatim quote sent by them from the samples that shows their essence.",
  "flags": [
    {{
      "type": "red",
      "behavior": "A specific texting habit e.g., 'Aggressive Double-Texting'",
      "proof": "Evidence from their quotes or behavior."
    }}
  ],
  "dynamics_summary": "A 2-3 sentence analysis of their response time matrix. Do they chase people? Do they ignore people?",
  "verdict": "One brutal final verdict sentence about this person's overall messaging persona across these chats.",
  "chapter_narrative": [
    {{
      "phase": "setup",
      "title": "Short catchy title for the opening chapter (e.g. 'The Arrival')",
      "description": "2-3 sentences on the early phase of their messaging history in these chats."
    }},
    {{
      "phase": "rising",
      "title": "Title for their rising/active phase",
      "description": "2-3 sentences on when things picked up."
    }},
    {{
      "phase": "peak",
      "title": "Title for their peak activity / most chaotic period",
      "description": "2-3 sentences on their most intense period."
    }},
    {{
      "phase": "aftermath",
      "title": "Title for what happened after the peak",
      "description": "2-3 sentences on the current state or wind-down."
    }}
  ]
}}
"""
    elif chat_mode == "dm":
        prompt = f"""
You are a savage, no-holds-barred relationship analyst — like a therapist who has zero filter and has read every single message in this 1-on-1 private conversation.

LANGUAGE NOTE: Messages may be in Gujarati, Hindi, English, or mixed Hinglish. Read and understand them all natively.

MEDIA NOTE: The chat has no actual images/videos, represented as `<Media omitted>`. Factor this in! If someone posts `<Media omitted>` and others react, analyze the reaction to deduce what they shared (e.g. memes, documents, scheduling screenshots) and roast accordingly.

TONE: Brutally honest. Savage. But also insightful. Name actual patterns you see. Quote real messages. Dig into the subtext — what's NOT being said, who's chasing, who's comfortable being ignored.
{data_block}
OUTPUT THIS EXACT JSON (raw JSON only, absolutely no markdown fences or backticks):

{{
  "chat_title": "A short punchy title for this relationship/dynamic. Max 6 words. e.g. 'The Situationship That Refuses to Die', 'Two People Avoiding the Obvious'.",
  "relationship_essence": "2-3 sentences. What IS this relationship? Friends? Situationship? Colleagues? What's the actual vibe based on reading the messages?",
  "compatibility_verdict": "One punchy verdict sentence. e.g. 'Emotionally compatible but terrified of admitting it.' or 'One person is a wall, the other is throwing themselves at it.'",
  "person_profiles": [
    {{
      "name": "Exact name from stats",
      "title": "Their role in this dynamic. e.g. 'The Emotionally Unavailable One', 'The Overthinker Who Texts First'",
      "personality_in_this_chat": "2-3 sentences on how they show up in this specific conversation. What's their energy, their patterns?",
      "roast": "2 sentences. A targeted roast based on something they actually said or did.",
      "iconic_quote": "A verbatim quote that captures them perfectly."
    }}
  ],
  "relationship_dynamics": {{
    "who_initiates_more": "Name + 1-2 sentences on who starts conversations more and what it implies.",
    "reply_asymmetry": "Based on the reply-time matrix: who replies faster and what it says about who cares more.",
    "attachment_read": "2-3 sentences on the attachment dynamic you observe — are they anxious/avoidant? secure? one-sided?",
    "the_tension": "What's the underlying tension or unspoken thing in this chat? 2 sentences."
  }},
  "red_flags": [
    "A specific behavior or pattern you noticed that's a red flag, with a real example."
  ],
  "green_flags": [
    "A genuinely positive pattern or moment you noticed."
  ],
  "hot_moment_summaries": [
    {{
      "date": "Same date string as provided",
      "time_tag": "Same time_tag as provided (HH:MM)",
      "event_title": "What happened here? Make it a punchy headline.",
      "summary": "2-3 sentences on what actually happened. Reference the lead-up context if relevant.",
      "iconic_moment": "Best quote or exchange from this moment."
    }}
  ],
  "verdict": "One brutal, specific final verdict on this relationship — what IS it, really, at its core?",
  "chapter_narrative": [
    {{
      "phase": "setup",
      "title": "Short catchy title for the opening chapter of this relationship",
      "description": "2-3 sentences on how this all started."
    }},
    {{
      "phase": "rising",
      "title": "Title for when things started heating up",
      "description": "2-3 sentences on the escalation."
    }},
    {{
      "phase": "peak",
      "title": "Title for the peak / most chaotic period",
      "description": "2-3 sentences on the most intense moments."
    }},
    {{
      "phase": "aftermath",
      "title": "Title for where things stand now",
      "description": "2-3 sentences on the current state of this dynamic."
    }}
  ]
}}
"""
    else:
        prompt = f"""
You are a savage, no-holds-barred AI chat analyst — think brutally honest friend who has read every single message.

LANGUAGE NOTE: Messages may be in Gujarati, Hindi, English, or mixed Hinglish. Read and understand them all natively.

MEDIA NOTE: The chat has no actual images/videos, represented as `<Media omitted>`. Factor this in! If someone posts `<Media omitted>` and others react, analyze the reaction to deduce what they shared (e.g. memes, documents, scheduling screenshots) and roast accordingly.

TONE: Absolutely savage. Nothing held back. Roast them like you know them personally. Reference specific things they actually said. Use real quotes. Be specific, not generic.
{data_block}
OUTPUT THIS EXACT JSON (raw JSON only, absolutely no markdown fences or backticks):

{{
  "chat_title": "A short, punchy, creative name that captures the essence of this specific group. NOT generic. Based on what they actually talk about and who they are. Max 6 words. Examples: 'The Placement Season Survivors', 'The Chaos Architects Anonymous', 'Functioning Adults (Barely)'.",
  "group_essence": "2-3 sentences describing what this group actually IS. What do they talk about, what's the energy, are they a team/friend group/study group? Based purely on reading the messages.",
  "group_roast": "3-4 sentences. A savage, specific roast of the entire group dynamic. Name names. Reference specific things people said or did.",
  "user_profiles": [
    {{
      "name": "Exact name from stats",
      "title": "A brutal, creative, specific title. Max 7 words. Must be earned by their actual behavior.",
      "personality_summary": "2-3 sentences. What kind of person are they in THIS group? What role do they play? How do others react to them?",
      "roast": "2-3 sentences of pure, targeted roast. Reference something they actually said or a pattern you noticed.",
      "iconic_quote": "A verbatim quote from their messages that perfectly captures their personality. Must be a real message from the sample."
    }}
  ],
  "relationship_map": [
    {{
      "persons": ["Name1", "Name2"],
      "dynamic_title": "A creative title for this dynamic e.g. 'The Workhorse and The Passenger'",
      "description": "2 sentences on the actual dynamic between them based on how they communicate with each other.",
      "reply_time_note": "Reference the reply matrix: who replies faster to whom and what it says about the relationship."
    }}
  ],
  "hot_moment_summaries": [
    {{
      "date": "Same date string as provided",
      "time_tag": "Same time_tag as provided (HH:MM)",
      "event_title": "A catchy name for this drama/event",
      "summary": "2-3 sentences on what actually happened. Be specific. Reference the lead-up context if it tells you why it happened.",
      "iconic_moment": "The single best quote or exchange from this event that captures the chaos."
    }}
  ],
  "verdict": "One savage, specific final verdict on this group — what is this group, really, in 1-2 sentences?",
  "chapter_narrative": [
    {{
      "phase": "setup",
      "title": "Catchy title for the group's origin / early days",
      "description": "2-3 sentences on how the group started and what the early vibe was."
    }},
    {{
      "phase": "rising",
      "title": "Title for when the group really got going",
      "description": "2-3 sentences on the most active, chaotic, or eventful phase."
    }},
    {{
      "phase": "peak",
      "title": "Title for the group's peak drama / peak activity",
      "description": "2-3 sentences on the wildest period. Name names if relevant."
    }},
    {{
      "phase": "aftermath",
      "title": "Title for where the group stands today",
      "description": "2-3 sentences on the current state. Is it dying? Thriving? On life support?"
    }}
  ]
}}
"""


    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = response.text.strip()

        # Strip any accidental markdown fences
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        return json.loads(text.strip())
    except Exception as e:
        print(f"LLM Error: {e}")
        return {}


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    from analytics import run_analytics
    print("Running analytics...")
    payload = run_analytics(1)
    print(f"Hot moments: {len(payload.get('hot_moments', []))}, Sample msgs: {len(payload.get('llm_message_sample', []))}")

    print("Generating deep roast...")
    result = generate_report_commentary(payload)

    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(result, indent=2, ensure_ascii=False))
