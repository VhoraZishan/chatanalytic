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

    # ── 3. Multi-Signal Hot Moment Detection ─────────────────────────────────
    text_messages = [
        m for m in messages
        if m["type"] in ("text", "media") and m["text"] and m["sender"] != "SYSTEM"
    ]

    # --- 3a. Sliding 30-minute windows every 15 minutes ---
    if not text_messages:
        hot_moments = []
    else:
        t_start = _parse_dt(text_messages[0]["timestamp"])
        t_end   = _parse_dt(text_messages[-1]["timestamp"])
        window_secs  = 1800   # 30-min window
        step_secs    = 900    # slide every 15 min
        total_secs   = max((t_end - t_start).total_seconds(), 1)

        # Pre-index messages by second-offset for fast windowing
        msg_offsets = [(_parse_dt(m["timestamp"]) - t_start).total_seconds() for m in text_messages]
        total_windows = max(1, int(total_secs // step_secs))

        # Global baseline: avg messages per 30-min window
        baseline_density = len(text_messages) / max(total_windows, 1)

        # --- Signal helpers ---
        def _caps_ratio(msgs):
            caps = sum(1 for m in msgs if m.get("text","") and m["text"].isupper() and len(m["text"]) > 3)
            return caps / max(len(msgs), 1)

        def _unique_senders(msgs):
            return len({m["sender"] for m in msgs})

        def _avg_len(msgs):
            return statistics.mean([len(m.get("text","")) for m in msgs]) if msgs else 0

        window_scores = []

        pointer_start = 0
        for w in range(total_windows):
            w_start_sec = w * step_secs
            w_end_sec   = w_start_sec + window_secs

            # Collect messages in this window
            win_msgs = []
            for idx, off in enumerate(msg_offsets):
                if w_start_sec <= off < w_end_sec:
                    win_msgs.append(text_messages[idx])

            if len(win_msgs) < 5:
                continue

            signals = []
            score   = 0

            # Signal 1 – Volume spike
            vol_ratio = len(win_msgs) / max(baseline_density, 1)
            if vol_ratio >= 2.5:
                signals.append("volume_spike")
                score += min(vol_ratio / 2.5, 3.0)

            # Signal 2 – Velocity spike (>= 4 msgs within any 3-min stretch)
            sorted_win = sorted(win_msgs, key=lambda m: _parse_dt(m["timestamp"]))
            for vi in range(len(sorted_win) - 3):
                burst_gap = (_parse_dt(sorted_win[vi+3]["timestamp"]) - _parse_dt(sorted_win[vi]["timestamp"])).total_seconds()
                if burst_gap <= 180:
                    signals.append("velocity_spike")
                    score += 1.5
                    break

            # Signal 3 – Turn-taking collapse (same sender >=4 consecutive)
            max_run = 1
            cur_run = 1
            for vi in range(1, len(sorted_win)):
                if sorted_win[vi]["sender"] == sorted_win[vi-1]["sender"]:
                    cur_run += 1
                    max_run = max(max_run, cur_run)
                else:
                    cur_run = 1
            if max_run >= 4:
                signals.append("turn_taking_collapse")
                score += 1.2

            # Signal 4 – Response compression (avg reply gap < 45s)
            gaps = []
            for vi in range(1, len(sorted_win)):
                if sorted_win[vi]["sender"] != sorted_win[vi-1]["sender"]:
                    g = (_parse_dt(sorted_win[vi]["timestamp"]) - _parse_dt(sorted_win[vi-1]["timestamp"])).total_seconds()
                    if 0 < g < 300:
                        gaps.append(g)
            if gaps and statistics.mean(gaps) < 45:
                signals.append("response_compression")
                score += 1.3

            # Signal 5 – Topic cluster (short avg message length = rapid-fire pings)
            avg_l = _avg_len(win_msgs)
            if avg_l < 40 and len(win_msgs) >= 8:
                signals.append("topic_cluster")
                score += 1.0

            if signals:
                caps = _caps_ratio(win_msgs) > 0.1
                window_scores.append({
                    "w_start_sec": w_start_sec,
                    "win_msgs":    win_msgs,
                    "signals":     list(dict.fromkeys(signals)),  # dedupe, preserve order
                    "score":       round(score, 2),
                    "caps":        caps,
                })

        # --- 3b. Merge overlapping windows and pick top 6 ---
        window_scores.sort(key=lambda x: -x["score"])

        selected = []
        for ws in window_scores:
            overlap = any(
                abs(ws["w_start_sec"] - sel["w_start_sec"]) < step_secs * 2
                for sel in selected
            )
            if not overlap:
                selected.append(ws)
            if len(selected) >= 6:
                break

        # --- 3c. Build hot_moments payload ---
        hot_moments = []
        for ws in selected:
            w_dt = t_start + timedelta(seconds=ws["w_start_sec"])
            date_label = w_dt.strftime("%d %b %Y")
            time_tag   = w_dt.strftime("%H:%M")

            win_msgs = ws["win_msgs"]
            # Sample up to 25 msgs from the window for LLM context
            step_s = max(1, len(win_msgs) // 25)
            sample = win_msgs[::step_s][:25]

            # Pre-context: 5 messages before the window
            first_off = ws["w_start_sec"]
            pre_ctx = [
                text_messages[idx]
                for idx, off in enumerate(msg_offsets)
                if first_off - 600 <= off < first_off
            ][-5:]

            hot_moments.append({
                "date":          date_label,
                "time_tag":      time_tag,
                "message_count": len(win_msgs),
                "signals":       ws["signals"],
                "signal_score":  ws["score"],
                "caps_detected": ws["caps"],
                "pre_context": [
                    {"sender": m["sender"], "text": m["text"][:150]}
                    for m in pre_ctx
                ],
                "sample_messages": [
                    {"sender": m["sender"], "text": m["text"][:200]}
                    for m in sample
                ],
            })

        # Sort chronologically for display
        hot_moments.sort(key=lambda x: x["date"])

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

def run_ego_analytics(chats: list[dict], user_aliases: list[str]) -> dict:
    """
    Aggregates stats across multiple chats to profile a specific target user.
    Uses chronological clips of back-and-forth conversation surrounding target user messages.
    """
    aliases = [a.lower().strip() for a in user_aliases if a.strip()]
    if not aliases:
        return {"error": "No user aliases provided"}
        
    def is_target(name):
        return name.lower().strip() in aliases
        
    total_messages_all = 0
    chat_summaries = []
    
    # Aggregated stats for target user
    total_sent = 0
    total_words_sent = 0
    total_media_sent = 0
    total_late_night = 0
    total_initiations = 0
    total_ignored = 0
    
    reply_times_to_target = []
    reply_times_by_target = []
    
    for chat in chats:
        messages = chat["messages"]
        chat_name = chat["chat_name"]
        chat_mode = chat["chat_mode"]
        
        chat_sent = 0
        chat_total = len(messages)
        total_messages_all += chat_total
        
        for i, m in enumerate(messages):
            sender = m["sender"]
            if sender == "SYSTEM":
                continue
            
            sender_is_target = is_target(sender)
            
            if sender_is_target:
                chat_sent += 1
                total_sent += 1
                if m["type"] == "text" and m["text"]:
                    total_words_sent += len(m["text"].split())
                elif m["type"] == "media":
                    total_media_sent += 1
                    
                dt = _parse_dt(m["timestamp"])
                if 0 <= dt.hour < 4:
                    total_late_night += 1
                    
                if i > 0:
                    prev = messages[i-1]
                    if prev["sender"] != "SYSTEM" and not is_target(prev["sender"]):
                        gap = dt - _parse_dt(prev["timestamp"])
                        if gap >= timedelta(hours=2):
                            total_initiations += 1
            
            if i > 0:
                prev = messages[i-1]
                curr = messages[i]
                sender_a, sender_b = prev["sender"], curr["sender"]
                if "SYSTEM" in (sender_a, sender_b) or sender_a == sender_b:
                    continue
                
                gap_secs = (_parse_dt(curr["timestamp"]) - _parse_dt(prev["timestamp"])).total_seconds()
                if 0 < gap_secs < 10800:
                    if is_target(sender_a) and not is_target(sender_b):
                        reply_times_to_target.append(gap_secs)
                    elif not is_target(sender_a) and is_target(sender_b):
                        reply_times_by_target.append(gap_secs)
                        
        chat_summaries.append({
            "chat_name": chat_name,
            "chat_mode": chat_mode,
            "total_messages": chat_total,
            "messages_sent_by_you": chat_sent,
            "your_share_pct": round(chat_sent / chat_total * 100, 1) if chat_total else 0
        })

    avg_reply_to_you = statistics.mean(reply_times_to_target) if reply_times_to_target else None
    avg_reply_by_you = statistics.mean(reply_times_by_target) if reply_times_by_target else None

    # Consolidated timeline
    month_counts = defaultdict(int)
    for chat in chats:
        for m in chat["messages"]:
            month_counts[_parse_dt(m["timestamp"]).strftime("%b %Y")] += 1
            
    seen_months = sorted(list(month_counts.keys()), key=lambda x: datetime.strptime(x, "%b %Y"))
    monthly_timeline = [{"month": k, "count": month_counts[k]} for k in seen_months]

    # Sample chronological clips around target user messages
    chat_clips = []
    for chat in chats:
        messages = chat["messages"]
        chat_name = chat["chat_name"]
        
        # Find indices of messages sent by target user
        target_indices = [idx for idx, m in enumerate(messages) if is_target(m["sender"])]
        
        if not target_indices:
            continue
            
        # Select up to 3 spread indices (start, middle, end)
        step = max(1, len(target_indices) // 3)
        selected_indices = target_indices[::step][:3]
        
        clips_for_this_chat = []
        for idx in selected_indices:
            start_win = max(0, idx - 3)
            end_win = min(len(messages), idx + 4)
            window_msgs = messages[start_win:end_win]
            
            clips_for_this_chat.append({
                "clip_msgs": [
                    {"sender": m["sender"], "text": m["text"][:200], "type": m["type"]}
                    for m in window_msgs
                ]
            })
            
        chat_clips.append({
            "chat_name": chat_name,
            "clips": clips_for_this_chat
        })

    return {
        "chat_mode": "ego",
        "user_aliases": user_aliases,
        "total_messages_analyzed": total_messages_all,
        "monthly_timeline": monthly_timeline,
        "chat_summaries": chat_summaries,
        "ego_stats": {
            "total_messages_sent": total_sent,
            "overall_share_pct": round(total_sent / total_messages_all * 100, 1) if total_messages_all else 0,
            "avg_message_length_words": round(total_words_sent / total_sent, 1) if total_sent else 0,
            "media_sent": total_media_sent,
            "late_night_ratio_pct": round(total_late_night / total_sent * 100, 1) if total_sent else 0,
            "conversation_initiations": total_initiations,
            "avg_reply_time_to_you_mins": round(avg_reply_to_you / 60, 1) if avg_reply_to_you else None,
            "avg_reply_time_by_you_mins": round(avg_reply_by_you / 60, 1) if avg_reply_by_you else None,
        },
        "chat_clips": chat_clips
    }




