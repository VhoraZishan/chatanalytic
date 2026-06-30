import json
import statistics
from datetime import timedelta, datetime
from collections import defaultdict

def _parse_dt(ts):
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    return ts

def run_analytics(chat_data: dict) -> dict:
    """
    Runs in-memory analytics over the parsed message dictionary.
    No SQLite database connections are used.
    """
    messages = chat_data["messages"]
    chat_mode = chat_data["chat_mode"]
    chat_name = chat_data["chat_name"]

    if not messages:
        return {"error": "No messages found"}

    total_msgs = len(messages)

    # ── 1. Per-User Stats ─────────────────────────────────────────────────────
    user_data = defaultdict(lambda: {
        "msg_count": 0, "word_count": 0, "media_count": 0,
        "late_night": 0, "initiations": 0, "ignored_count": 0,
        "hour_buckets": defaultdict(int),
    })

    for i, msg in enumerate(messages):
        sender = msg["sender"]
        if sender == "SYSTEM":
            continue
        ud = user_data[sender]
        ud["msg_count"] += 1
        
        if msg["type"] == "text" and msg["text"]:
            ud["word_count"] += len(msg["text"].split())
        elif msg["type"] == "media":
            ud["media_count"] += 1

        dt = _parse_dt(msg["timestamp"])
        if 0 <= dt.hour < 4:
            ud["late_night"] += 1
        ud["hour_buckets"][dt.hour] += 1

        if i > 0:
            prev = messages[i - 1]
            if prev["sender"] != "SYSTEM":
                gap = dt - _parse_dt(prev["timestamp"])
                if gap >= timedelta(hours=2):
                    ud["initiations"] += 1

    for i in range(1, len(messages)):
        curr, prev = messages[i], messages[i - 1]
        if "SYSTEM" in (curr["sender"], prev["sender"]):
            continue
        if curr["sender"] != prev["sender"]:
            gap = _parse_dt(curr["timestamp"]) - _parse_dt(prev["timestamp"])
            if gap >= timedelta(hours=6):
                user_data[prev["sender"]]["ignored_count"] += 1

    user_profiles = {}
    for sender, data in user_data.items():
        if data["msg_count"] < 5:
            continue
        peak_hour = max(data["hour_buckets"], key=data["hour_buckets"].get, default=12)
        user_profiles[sender] = {
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
        a_name, b_name = prev["sender"], curr["sender"]
        if "SYSTEM" in (a_name, b_name) or a_name == b_name:
            continue
        gap = (_parse_dt(curr["timestamp"]) - _parse_dt(prev["timestamp"])).total_seconds()
        if 0 < gap < 10800:
            pair_reply_times[a_name][b_name].append(gap)

    relationship_matrix = []
    for a_name, replies in pair_reply_times.items():
        for b_name, times in replies.items():
            if len(times) < 3:
                continue
            avg_secs = statistics.mean(times)
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
        if m["type"] in ("text", "media") and m["text"] and m["sender"] != "SYSTEM"
    ]

    day_buckets = defaultdict(list)
    for m in text_messages:
        day_key = _parse_dt(m["timestamp"]).strftime("%Y-%m-%d")
        day_buckets[day_key].append(m)

    avg_day_density = len(text_messages) / max(len(day_buckets), 1)

    hot_days = sorted(
        [(day, msgs) for day, msgs in day_buckets.items()
         if len(msgs) >= max(20, avg_day_density * 1.8)],
        key=lambda x: -len(x[1])
    )[:5]

    hot_moments = []
    for day, day_msgs in hot_days:
        dt_label = datetime.strptime(day, "%Y-%m-%d").strftime("%d %b %Y")
        step = max(1, len(day_msgs) // 30)
        sampled = day_msgs[::step][:30]
        hot_moments.append({
            "date": dt_label,
            "message_count": len(day_msgs),
            "sample_messages": [
                {"sender": m["sender"], "text": m["text"][:200]}
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
    per_person = defaultdict(list)
    for m in text_messages:
        per_person[m["sender"]].append(m)

    llm_message_sample = []
    for name, msgs in per_person.items():
        step = max(1, len(msgs) // 15)
        sampled = msgs[::step][:15]
        for m in sampled:
            llm_message_sample.append({
                "sender": name,
                "text": m["text"][:200],
            })

    recent = [
        {"sender": m["sender"], "text": m["text"][:200]}
        for m in text_messages[-20:]
    ]
    llm_message_sample.extend(recent)

    # ── 6. Final Payload ──────────────────────────────────────────────────────
    d1 = _parse_dt(messages[0]["timestamp"]).strftime("%d %b %Y")
    d2 = _parse_dt(messages[-1]["timestamp"]).strftime("%d %b %Y")

    return {
        "chat_name": chat_name,
        "chat_mode": chat_mode,
        "total_messages": total_msgs,
        "date_range": f"{d1} → {d2}",
        "participants": list(user_profiles.keys()),
        "user_profiles": user_profiles,
        "relationship_matrix": relationship_matrix[:20],
        "hot_moments": hot_moments,
        "monthly_timeline": monthly_timeline,
        "llm_message_sample": llm_message_sample,
    }
