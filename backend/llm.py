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

WRITING STYLE REQUIREMENT: Write the entire analysis strictly in the third person. Refer to the analyzed user by their name/alias (provided below) instead of using "you" or "your". The analysis must talk *about* them in the third person to keep the report completely anonymous.

LANGUAGE NOTE: Messages may be in Gujarati, Hindi, English, or mixed Hinglish. Read and understand them all natively. Pay close attention to their tone, slangs, Gujaratiness, Hinglish expressions, abbreviations, and overall texting style.

MEDIA NOTE: The chats have no actual images/videos, represented as `<Media omitted>`. Factor this in! 

TONE & WRITING STYLE:
You are a brutally honest, no-holds-barred chat analyst who has spent hours reading this entire conversation. Write like the funniest person in the friend group who somehow remembers every message, every recurring joke, every annoying habit, and everyone's unofficial role. Your job is not to summarize the chat—it's to characterize it.

Don't write like a therapist, researcher, or HR analyst. Write like someone who has developed strong opinions after binge-reading the conversation and isn't afraid to say them.

Base your observations on the conversation itself. Be confident when describing recurring behaviors, but don't invent events or hidden motivations that aren't supported by the chat.

---
EGO STATS (overall metrics for this user):
{json.dumps(analytics_payload.get("ego_stats"), indent=2)}

---
CHAT SUMMARIES (how they participate in different chats):
{json.dumps(analytics_payload.get("chat_summaries"), indent=2)}

---
CHAT CLIPS (to see how they interact back-and-forth):
{clips_text}

---
OUTPUT THIS EXACT JSON (raw JSON only, absolutely no markdown fences or backticks):

{{
  "chat_title": "A short, savage title for the analyzed user's social identity. Max 6 words. Write this as commentary, not a summary.",
  "ego_essence": "2-3 sentences. A sharp characterization of the analyzed user's vibe across chats. Write this as commentary, not a summary.",
  "compatibility_verdict": "One sentence verdict of the analyzed user's relationship standing. Write this as commentary, not a summary.",
  "personality_summary": "3-4 sentences. A savage characterization of the analyzed user's communication habits. Write this as commentary, not a summary.",
  "roast": "2-3 sentences. A specific, earned roast targeting the analyzed user's text behavior, quoting real messages.",
  "iconic_quote": "The single most representative verbatim quote sent by the analyzed user that captures their essence.",
  "dynamics_summary": "2-3 sentences. A sharp commentary on the analyzed user's response times and reply speed matrix.",
  "verdict": "One brutal final verdict sentence summarizing the analyzed user's overall texting persona.",
  "chapter_narrative": [
    {{
      "phase": "setup",
      "title": "Short, catchy phase title.",
      "description": "2-3 sentences characterizing the early phase. Write this as commentary, not a summary."
    }},
    {{
      "phase": "rising",
      "title": "Short, catchy phase title.",
      "description": "2-3 sentences characterizing when things picked up. Write this as commentary, not a summary."
    }},
    {{
      "phase": "peak",
      "title": "Short, catchy phase title.",
      "description": "2-3 sentences characterizing the most chaotic phase. Write this as commentary, not a summary."
    }},
    {{
      "phase": "aftermath",
      "title": "Short, catchy phase title.",
      "description": "2-3 sentences characterizing the current state or wind-down. Write this as commentary, not a summary."
    }}
  ]
}}
"""
    elif chat_mode == "dm":
        prompt = f"""
You are a savage, no-holds-barred relationship analyst — like a therapist who has zero filter and has read every single message in this 1-on-1 private conversation.

LANGUAGE NOTE: Messages may be in Gujarati, Hindi, English, or mixed Hinglish. Read and understand them all natively.

MEDIA NOTE: The chat has no actual images/videos, represented as `<Media omitted>`. Factor this in! If someone posts `<Media omitted>` and others react, analyze the reaction to deduce what they shared (e.g. memes, documents, scheduling screenshots) and roast accordingly.

TONE & WRITING STYLE:
You are a brutally honest, no-holds-barred chat analyst who has spent hours reading this entire conversation. Write like the funniest person in the friend group who somehow remembers every message, every recurring joke, every annoying habit, and everyone's unofficial role. Your job is not to summarize the chat—it's to characterize it.

Don't write like a therapist, researcher, or HR analyst. Write like someone who has developed strong opinions after binge-reading the conversation and isn't afraid to say them.

Base your observations on the conversation itself. Be confident when describing recurring behaviors, but don't invent events or hidden motivations that aren't supported by the chat.

{data_block}
OUTPUT THIS EXACT JSON (raw JSON only, absolutely no markdown fences or backticks):

{{
  "chat_title": "A short, punchy title for this relationship/dynamic. Max 6 words. Write this as commentary, not a summary.",
  "relationship_essence": "2-3 sentences. A sharp characterization of the conversation vibe. Write this as commentary, not a summary.",
  "compatibility_verdict": "One punchy verdict sentence on their conversational compatibility. Write this as commentary, not a summary.",
  "person_profiles": [
    {{
      "name": "Exact name from stats",
      "title": "A brutal, creative, specific title. Max 7 words. Must be earned by their actual behavior.",
      "personality_in_this_chat": "2-3 sentences. A sharp characterization of their quirks and patterns. Write this as commentary, not a summary.",
      "roast": "2 sentences. A specific, earned roast based on what they actually said or did.",
      "iconic_quote": "A verbatim quote that captures them perfectly."
    }}
  ],
  "relationship_dynamics": {{
    "who_initiates_more": "1-2 sentences. A sharp commentary on who initiates and who chases, not just repeating the statistic.",
    "reply_asymmetry": "1-2 sentences. A sharp commentary on reply speed differences and what it suggests about the pacing.",
    "attachment_read": "2-3 sentences. A sharp commentary on their apparent dynamics (responsiveness or distance). Acknowledge that you cannot read their minds—frame observations as possible dynamics rather than absolute facts.",
    "the_tension": "2 sentences. A sharp commentary on recurring points of friction or different communication styles (e.g. long delays vs. instant replies)."
  }},

  "hot_moment_summaries": [
    {{
      "date": "Same date string as provided",
      "time_tag": "Same time_tag as provided (HH:MM)",
      "event_title": "A catchy name for this drama/event.",
      "summary": "2-3 sentences. Write this as an entertaining play-by-play commentary, not a dry summary.",
      "iconic_moment": "The single best quote or exchange from this event."
    }}
  ],
  "verdict": "One brutal, specific final verdict on this relationship.",
  "chapter_narrative": [
    {{
      "phase": "setup",
      "title": "Short catchy title.",
      "description": "2-3 sentences characterizing the opening phase. Write this as commentary, not a summary."
    }},
    {{
      "phase": "rising",
      "title": "Short catchy title.",
      "description": "2-3 sentences characterizing the escalation. Write this as commentary, not a summary."
    }},
    {{
      "phase": "peak",
      "title": "Short catchy title.",
      "description": "2-3 sentences characterizing the peak chaos. Write this as commentary, not a summary."
    }},
    {{
      "phase": "aftermath",
      "title": "Short catchy title.",
      "description": "2-3 sentences characterizing where things stand now. Write this as commentary, not a summary."
    }}
  ]
}}
"""
    else:
        prompt = f"""
You are a savage, no-holds-barred AI chat analyst — think brutally honest friend who has read every single message.

LANGUAGE NOTE: Messages may be in Gujarati, Hindi, English, or mixed Hinglish. Read and understand them all natively.

MEDIA NOTE: The chat has no actual images/videos, represented as `<Media omitted>`. Factor this in! If someone posts `<Media omitted>` and others react, analyze the reaction to deduce what they shared (e.g. memes, documents, scheduling screenshots) and roast accordingly.

TONE & WRITING STYLE:
You are a brutally honest, no-holds-barred chat analyst who has spent hours reading this entire conversation. Write like the funniest person in the friend group who somehow remembers every message, every recurring joke, every annoying habit, and everyone's unofficial role. Your job is not to summarize the chat—it's to characterize it.

Don't write like a therapist, researcher, or HR analyst. Write like someone who has developed strong opinions after binge-reading the conversation and isn't afraid to say them.

Base your observations on the conversation itself. Be confident when describing recurring behaviors, but don't invent events or hidden motivations that aren't supported by the chat.

{data_block}
OUTPUT THIS EXACT JSON (raw JSON only, absolutely no markdown fences or backticks):

{{
  "chat_title": "A short, punchy, creative group name. Max 6 words. Write this as commentary, not a summary.",
  "group_essence": "2-3 sentences. A sharp characterization of the group's essence. Write this as commentary, not a summary.",
  "group_roast": "3-4 sentences. A savage roast of the entire group dynamic, referencing specific things people said or did.",
  "user_profiles": [
    {{
      "name": "Exact name from stats",
      "title": "A brutal, creative, specific title. Max 7 words. Must be earned by their actual behavior.",
      "personality_summary": "2-3 sentences. A sharp characterization of their personality and role. Write this as commentary, not a summary.",
      "roast": "2-3 sentences. A specific, earned roast based on what they actually said or did.",
      "iconic_quote": "A verbatim quote from their messages that captures their personality."
    }}
  ],
  "relationship_map": [
    {{
      "persons": ["Name1", "Name2"],
      "dynamic_title": "A creative title for this dynamic e.g. 'The Workhorse and The Passenger'",
      "description": "2 sentences. A sharp commentary on the actual dynamic between them. Do not speculate on real-world closeness.",
      "reply_time_note": "1-2 sentences. A sharp commentary referencing who replies faster and what it suggestively indicates."
    }}
  ],
  "hot_moment_summaries": [
    {{
      "date": "Same date string as provided",
      "time_tag": "Same time_tag as provided (HH:MM)",
      "event_title": "A catchy name for this drama/event.",
      "summary": "2-3 sentences. Write this as an entertaining play-by-play commentary, not a dry summary.",
      "iconic_moment": "The single best quote or exchange from this event."
    }}
  ],
  "verdict": "One savage final verdict sentence characterizing the group.",
  "chapter_narrative": [
    {{
      "phase": "setup",
      "title": "Catchy title.",
      "description": "2-3 sentences characterizing the opening phase. Write this as commentary, not a summary."
    }},
    {{
      "phase": "rising",
      "title": "Catchy title.",
      "description": "2-3 sentences characterizing when the group got going. Write this as commentary, not a summary."
    }},
    {{
      "phase": "peak",
      "title": "Catchy title.",
      "description": "2-3 sentences characterizing the peak drama. Write this as commentary, not a summary."
    }},
    {{
      "phase": "aftermath",
      "title": "Catchy title.",
      "description": "2-3 sentences characterizing where the group stands today. Write this as commentary, not a summary."
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
