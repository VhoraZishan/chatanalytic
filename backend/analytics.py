import os
import json
import statistics
from datetime import timedelta, datetime
from collections import defaultdict

try:
    from backend.database import get_db_connection
except ImportError:
    from database import get_db_connection


def _parse_dt(ts):
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    return ts


def run_analytics(chat_id: int) -> dict:
    with get_db_connection() as conn:
        participants = {}
        for row in conn.execute(
            "SELECT id, display_name FROM participants WHERE chat_id = ?", (chat_id,)
        ):
            participants[row["id"]] = row["display_name"]

        messages = []
        for row in conn.execute(
            """SELECT id, sender_id, timestamp, text, message_type
               FROM messages WHERE chat_id = ? ORDER BY timestamp ASC""",
            (chat_id,),
        ):
            messages.append(dict(row))

    if not messages:
        return {"error": "No messages found"}

    # ── 1. Per-User Stats ─────────────────────────────────────────────────────
    user_data = defaultdict(lambda: {
        "msg_count": 0, "word_count": 0, "media_count": 0,
        "late_night": 0, "initiations": 0, "ignored_count": 0,
        "hour_buckets": defaultdict(int),
    })

    for i, msg in enumerate(messages):
        sid = msg["sender_id"]
        if sid is None:
            continue
        ud = user_data[sid]
        ud["msg_count"] += 1
        if msg["message_type"] == "text" and msg["text"]:
            ud["word_count"] += len(msg["text"].split())
        elif msg["message_type"] == "media":
            ud["media_count"] += 1

        dt = _parse_dt(msg["timestamp"])
        if 0 <= dt.hour < 4:
            ud["late_night"] += 1
        ud["hour_buckets"][dt.hour] += 1

        if i > 0:
            prev = messages[i - 1]
            if prev["sender_id"] is not None:
                gap = dt - _parse_dt(prev["timestamp"])
                if gap >= timedelta(hours=2):
                    ud["initiations"] += 1

    for i in range(1, len(messages)):
        curr, prev = messages[i], messages[i - 1]
        if None in (curr["sender_id"], prev["sender_id"]):
            continue
        if curr["sender_id"] != prev["sender_id"]:
            gap = _parse_dt(curr["timestamp"]) - _parse_dt(prev["timestamp"])
            if gap >= timedelta(hours=6):
                user_data[prev["sender_id"]]["ignored_count"] += 1

    total_msgs = len(messages)
    user_profiles = {}
    for sid, data in user_data.items():
        if data["msg_count"] < 5:
            continue
        name = participants[sid]
        peak_hour = max(data["hour_buckets"], key=data["hour_buckets"].get, default=12)
        user_profiles[name] = {
            "total_messages": data["msg_count"],
            "share_pct": round(data["msg_count"] / total_msgs * 100, 1),
            "avg_msg_length_words": round(data["word_count"] / data["msg_count"], 1) if data["msg_count"] else 0,
            "media_sent": data["media_count"],
            "late_night_ratio_pct": round(data["late_night"] / data["msg_count"] * 100, 1) if data["msg_count"] else 0,
            "conversation_initiations": data["initiations"],
            "times_left_on_read": data["ignored_count"],
            "peak_hour": peak_hour,
        }

    # ── 2. Relationship Reply-Time Matrix ─────────────────────────────────────
    pair_reply_times = defaultdict(lambda: defaultdict(list))
    for i in range(1, len(messages)):
        curr, prev = messages[i], messages[i - 1]
        a_id, b_id = prev["sender_id"], curr["sender_id"]
        if None in (a_id, b_id) or a_id == b_id:
            continue
        gap = (_parse_dt(curr["timestamp"]) - _parse_dt(prev["timestamp"])).total_seconds()
        if 0 < gap < 10800:
            pair_reply_times[a_id][b_id].append(gap)

    relationship_matrix = []
    for a_id, replies in pair_reply_times.items():
        for b_id, times in replies.items():
            if len(times) < 3:
                continue
            avg_secs = statistics.mean(times)
            a_name = participants.get(a_id, "Unknown")
            b_name = participants.get(b_id, "Unknown")
            relationship_matrix.append({
                "person_a": a_name,
                "person_b": b_name,
                "description": f"{b_name} replies to {a_name} in avg {int(avg_secs // 60)} mins ({len(times)} replies)",
                "avg_reply_secs": round(avg_secs),
                "sample_count": len(times),
            })
    relationship_matrix.sort(key=lambda x: x["avg_reply_secs"])

    # ── 3. Hot Day Detection (24-hour buckets) ────────────────────────────────
    text_messages = [
        m for m in messages
        if m["message_type"] in ("text", "media") and m["text"] and m["sender_id"] is not None
    ]

    day_buckets = defaultdict(list)
    for m in text_messages:
        day_key = _parse_dt(m["timestamp"]).strftime("%Y-%m-%d")
        day_buckets[day_key].append(m)

    avg_day_density = len(text_messages) / max(len(day_buckets), 1)

    # Find top hot days (≥ 2x avg and at least 20 messages)
    hot_days = sorted(
        [(day, msgs) for day, msgs in day_buckets.items()
         if len(msgs) >= max(20, avg_day_density * 1.8)],
        key=lambda x: -len(x[1])
    )[:5]

    hot_moments = []
    for day, day_msgs in hot_days:
        dt_label = datetime.strptime(day, "%Y-%m-%d").strftime("%d %b %Y")
        # Spread 30 samples across the day
        step = max(1, len(day_msgs) // 30)
        sampled = day_msgs[::step][:30]
        hot_moments.append({
            "date": dt_label,
            "message_count": len(day_msgs),
            "sample_messages": [
                {"sender": participants.get(m["sender_id"], "?"), "text": m["text"][:200]}
                for m in sampled
            ],
        })

    # ── 4. Monthly Timeline ────────────────────────────────────────────────────
    month_counts = defaultdict(int)
    for m in messages:
        month_counts[_parse_dt(m["timestamp"]).strftime("%b %Y")] += 1

    seen_months, month_order = set(), []
    for m in messages:
        k = _parse_dt(m["timestamp"]).strftime("%b %Y")
        if k not in seen_months:
            seen_months.add(k)
            month_order.append(k)
    monthly_timeline = [{"month": k, "count": month_counts[k]} for k in month_order]

    # ── 5. Per-Person Balanced Message Sample ────────────────────────────────
    # Ensure EVERY participant gets represented — 15 msgs per person max
    per_person = defaultdict(list)
    for m in text_messages:
        name = participants.get(m["sender_id"], "?")
        per_person[name].append(m)

    llm_message_sample = []
    for name, msgs in per_person.items():
        step = max(1, len(msgs) // 15)
        sampled = msgs[::step][:15]
        for m in sampled:
            llm_message_sample.append({
                "sender": name,
                "text": m["text"][:200],
            })

    # Also add 20 chronologically recent messages for current-state context
    recent = [
        {"sender": participants.get(m["sender_id"], "?"), "text": m["text"][:200]}
        for m in text_messages[-20:]
    ]
    llm_message_sample.extend(recent)

    # ── 6. Final Payload ──────────────────────────────────────────────────────
    d1 = _parse_dt(messages[0]["timestamp"]).strftime("%d %b %Y")
    d2 = _parse_dt(messages[-1]["timestamp"]).strftime("%d %b %Y")

    return {
        "chat_id": chat_id,
        "total_messages": total_msgs,
        "date_range": f"{d1} → {d2}",
        "participants": list(user_profiles.keys()),
        "user_profiles": user_profiles,
        "relationship_matrix": relationship_matrix[:20],
        "hot_moments": hot_moments,
        "monthly_timeline": monthly_timeline,
        "llm_message_sample": llm_message_sample,
    }


if __name__ == "__main__":
    result = run_analytics(1)
    display = {k: v for k, v in result.items() if k != "llm_message_sample"}
    display["llm_message_sample_count"] = len(result.get("llm_message_sample", []))
    display["hot_days"] = [(hm["date"], hm["message_count"]) for hm in result.get("hot_moments", [])]
    print(json.dumps(display, indent=2))
