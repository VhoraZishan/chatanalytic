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

    # ── 0. Pre-compute per-person average word count (for long-message anomaly) ──
    # Requires at least 5 messages from a sender to build a stable baseline
    person_word_samples = defaultdict(list)
    for m in messages:
        if m["sender"] != "SYSTEM" and m["type"] == "text" and m["text"]:
            wc = len(m["text"].split())
            if wc > 0:
                person_word_samples[m["sender"]].append(wc)

    person_avg_words = {
        s: statistics.mean(counts)
        for s, counts in person_word_samples.items()
        if len(counts) >= 5
    }

    # ── 1. Per-User Stats ──────────────────────────────────────────────────────
    user_data = defaultdict(lambda: {
        "msg_count": 0, "word_count": 0, "media_count": 0,
        "late_night": 0, "initiations": 0, "ignored_count": 0,
        "replied_to_count": 0,
        "hour_buckets": defaultdict(int),
        "initiation_hours": [],
        "active_days": set(),
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
        ud["active_days"].add(dt.date())

        if i > 0:
            prev = messages[i - 1]
            if prev["sender"] != "SYSTEM":
                gap = dt - _parse_dt(prev["timestamp"])
                if gap >= timedelta(hours=2):
                    ud["initiations"] += 1
                    ud["initiation_hours"].append(dt.hour)

    # Response rate: did a different sender reply within 4 hours?
    for i in range(len(messages) - 1):
        curr = messages[i]
        if curr["sender"] == "SYSTEM":
            continue
        curr_dt = _parse_dt(curr["timestamp"])
        for j in range(i + 1, min(i + 30, len(messages))):
            nxt = messages[j]
            if nxt["sender"] == "SYSTEM":
                continue
            if (_parse_dt(nxt["timestamp"]) - curr_dt).total_seconds() > 14400:
                break
            if nxt["sender"] != curr["sender"]:
                user_data[curr["sender"]]["replied_to_count"] += 1
                break

    # Times left on read: sent the last message before a long (6h+) silence
    for i in range(1, len(messages)):
        curr, prev = messages[i], messages[i - 1]
        if "SYSTEM" in (curr["sender"], prev["sender"]):
            continue
        if curr["sender"] != prev["sender"]:
            gap = _parse_dt(curr["timestamp"]) - _parse_dt(prev["timestamp"])
            if gap >= timedelta(hours=6):
                user_data[prev["sender"]]["ignored_count"] += 1

    def _peak_initiation_period(hours):
        if not hours:
            return "unknown"
        buckets = {
            "morning (6-11am)": 0,
            "afternoon (12-5pm)": 0,
            "evening (6-10pm)": 0,
            "late_night (11pm-5am)": 0,
        }
        for h in hours:
            if 6 <= h < 12:
                buckets["morning (6-11am)"] += 1
            elif 12 <= h < 18:
                buckets["afternoon (12-5pm)"] += 1
            elif 18 <= h < 23:
                buckets["evening (6-10pm)"] += 1
            else:
                buckets["late_night (11pm-5am)"] += 1
        return max(buckets, key=buckets.get)

    def _streak_stats(active_days_set):
        if not active_days_set:
            return 0, 0
        days = sorted(active_days_set)
        longest_streak = cur_streak = 1
        longest_gap = 0
        for k in range(1, len(days)):
            diff = (days[k] - days[k - 1]).days
            if diff == 1:
                cur_streak += 1
                longest_streak = max(longest_streak, cur_streak)
            else:
                cur_streak = 1
            longest_gap = max(longest_gap, diff)
        return longest_streak, longest_gap

    user_profiles = {}
    for sender, data in user_data.items():
        if data["msg_count"] < 5:
            continue
        peak_hour = max(data["hour_buckets"], key=data["hour_buckets"].get, default=12)
        longest_streak, longest_gap = _streak_stats(data["active_days"])
        user_profiles[sender] = {
            "total_messages": data["msg_count"],
            "share_pct": round(data["msg_count"] / total_msgs * 100, 1),
            "avg_msg_length_words": round(data["word_count"] / data["msg_count"], 1) if data["msg_count"] else 0,
            "media_sent": data["media_count"],
            "late_night_ratio_pct": round(data["late_night"] / data["msg_count"] * 100, 1) if data["msg_count"] else 0,
            "conversation_initiations": data["initiations"],
            "times_left_on_read": data["ignored_count"],
            "peak_hour": peak_hour,
            "response_rate_pct": round(data["replied_to_count"] / data["msg_count"] * 100, 1) if data["msg_count"] else 0,
            "peak_initiation_period": _peak_initiation_period(data["initiation_hours"]),
            "longest_active_streak_days": longest_streak,
            "longest_silence_days": longest_gap,
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

    # ── 3. Multi-Signal Hot Moment Detection ──────────────────────────────────
    text_messages = [
        m for m in messages
        if m["type"] in ("text", "media") and m["text"] and m["sender"] != "SYSTEM"
    ]

    if not text_messages:
        hot_moments = []
    else:
        t_start = _parse_dt(text_messages[0]["timestamp"])
        t_end = _parse_dt(text_messages[-1]["timestamp"])
        window_secs = 1800    # 30-min window
        step_secs   = 900     # slide every 15 min
        total_secs  = max((t_end - t_start).total_seconds(), 1)

        msg_offsets = [(_parse_dt(m["timestamp"]) - t_start).total_seconds() for m in text_messages]
        total_windows = max(1, int(total_secs // step_secs))
        baseline_density = len(text_messages) / max(total_windows, 1)

        def _caps_ratio(msgs):
            caps = sum(1 for m in msgs if m.get("text", "") and m["text"].isupper() and len(m["text"]) > 3)
            return caps / max(len(msgs), 1)

        def _avg_len(msgs):
            return statistics.mean([len(m.get("text", "")) for m in msgs]) if msgs else 0

        window_scores = []

        # --- 3a. Sliding window scoring ---
        for w in range(total_windows):
            w_start_sec = w * step_secs
            w_end_sec   = w_start_sec + window_secs

            win_msgs = [
                text_messages[idx]
                for idx, off in enumerate(msg_offsets)
                if w_start_sec <= off < w_end_sec
            ]

            if len(win_msgs) < 5:
                continue

            signals = []
            score   = 0

            sorted_win = sorted(win_msgs, key=lambda m: _parse_dt(m["timestamp"]))

            # Signal 1 – Volume spike
            vol_ratio = len(win_msgs) / max(baseline_density, 1)
            if vol_ratio >= 2.5:
                signals.append("volume_spike")
                score += min(vol_ratio / 2.5, 3.0)

            # Signal 2 – Velocity spike (>= 4 msgs in any 3-min stretch)
            for vi in range(len(sorted_win) - 3):
                burst_gap = (_parse_dt(sorted_win[vi + 3]["timestamp"]) - _parse_dt(sorted_win[vi]["timestamp"])).total_seconds()
                if burst_gap <= 180:
                    signals.append("velocity_spike")
                    score += 1.5
                    break

            # Signal 3 – Turn-taking collapse (same sender >= 4 consecutive)
            max_run = cur_run = 1
            for vi in range(1, len(sorted_win)):
                if sorted_win[vi]["sender"] == sorted_win[vi - 1]["sender"]:
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
                if sorted_win[vi]["sender"] != sorted_win[vi - 1]["sender"]:
                    g = (_parse_dt(sorted_win[vi]["timestamp"]) - _parse_dt(sorted_win[vi - 1]["timestamp"])).total_seconds()
                    if 0 < g < 300:
                        gaps.append(g)
            if gaps and statistics.mean(gaps) < 45:
                signals.append("response_compression")
                score += 1.3

            # Signal 5 – Topic cluster (short avg message length + high volume = rapid-fire pings)
            avg_l = _avg_len(win_msgs)
            if avg_l < 40 and len(win_msgs) >= 8:
                signals.append("topic_cluster")
                score += 1.0

            # Signal 6 – Long-message anomaly: someone sends a message far longer than their personal average
            for m in win_msgs:
                if m["type"] != "text":
                    continue
                avg_w = person_avg_words.get(m["sender"], 0)
                wc = len(m["text"].split())
                if avg_w > 0 and wc >= max(3.5 * avg_w, 20):
                    signals.append("long_message_anomaly")
                    score += 2.0
                    break

            # Signal 7 – Question cascade: a question triggers 2+ different people responding within 5 min
            for vi, m in enumerate(sorted_win):
                if m["type"] != "text" or not m["text"].strip().endswith("?"):
                    continue
                q_sender = m["sender"]
                q_dt = _parse_dt(m["timestamp"])
                responders = set()
                for vj in range(vi + 1, len(sorted_win)):
                    resp = sorted_win[vj]
                    if resp["sender"] == q_sender:
                        continue
                    if (_parse_dt(resp["timestamp"]) - q_dt).total_seconds() > 300:
                        break
                    responders.add(resp["sender"])
                if len(responders) >= 2:
                    signals.append("question_cascade")
                    score += 1.8
                    break

            # Media-flood filter: demote windows dominated by media shares (meme dumps)
            media_count_w = sum(1 for m in win_msgs if m["type"] == "media")
            media_ratio = media_count_w / max(len(win_msgs), 1)
            if media_ratio > 0.65:
                score *= 0.5
                signals.append("media_heavy")

            # Only record if there is at least one real (non-media-heavy) signal
            real_signals = [s for s in signals if s != "media_heavy"]
            if real_signals:
                window_scores.append({
                    "w_start_sec": w_start_sec,
                    "win_msgs":    win_msgs,
                    "signals":     list(dict.fromkeys(signals)),
                    "score":       round(score, 2),
                    "caps":        _caps_ratio(win_msgs) > 0.1,
                })

        # --- 3b. Standalone long-message anomaly events ---
        # Catches emotionally significant messages that sit in quiet windows
        for idx, m in enumerate(text_messages):
            if m["type"] != "text":
                continue
            avg_w = person_avg_words.get(m["sender"], 0)
            wc = len(m["text"].split())
            if avg_w > 0 and wc >= max(4.0 * avg_w, 30):
                m_off = msg_offsets[idx]
                already_covered = any(
                    ws["w_start_sec"] <= m_off < ws["w_start_sec"] + window_secs
                    for ws in window_scores
                )
                if not already_covered:
                    pre_ctx = text_messages[max(0, idx - 5):idx]
                    window_scores.append({
                        "w_start_sec": m_off,
                        "win_msgs":    [m],
                        "signals":     ["long_message_anomaly"],
                        "score":       2.5,
                        "caps":        False,
                        "_pre_ctx_override": pre_ctx,
                    })

        # --- 3c. Silence-then-burst detection ---
        # Someone disappears for 6+ hours then fires 3+ messages in 10 minutes
        per_person_msgs = defaultdict(list)
        for idx, m in enumerate(text_messages):
            per_person_msgs[m["sender"]].append((idx, m))

        for sender, pmsg_list in per_person_msgs.items():
            for k in range(1, len(pmsg_list)):
                prev_idx, prev_m = pmsg_list[k - 1]
                curr_idx, curr_m = pmsg_list[k]
                gap_secs = (_parse_dt(curr_m["timestamp"]) - _parse_dt(prev_m["timestamp"])).total_seconds()
                if gap_secs < 21600:  # less than 6 hours, skip
                    continue
                re_entry_dt = _parse_dt(curr_m["timestamp"])
                burst_msgs = [curr_m]
                for kk in range(k + 1, len(pmsg_list)):
                    _, bm = pmsg_list[kk]
                    if (_parse_dt(bm["timestamp"]) - re_entry_dt).total_seconds() <= 600:
                        burst_msgs.append(bm)
                    else:
                        break
                if len(burst_msgs) >= 3:
                    curr_off = msg_offsets[curr_idx]
                    already_covered = any(
                        ws["w_start_sec"] <= curr_off < ws["w_start_sec"] + window_secs
                        for ws in window_scores
                    )
                    if not already_covered:
                        pre_ctx = text_messages[max(0, curr_idx - 5):curr_idx]
                        window_scores.append({
                            "w_start_sec":    curr_off,
                            "win_msgs":       burst_msgs,
                            "signals":        ["silence_then_burst"],
                            "score":          2.0,
                            "caps":           False,
                            "_pre_ctx_override":  pre_ctx,
                            "_silence_hours":     round(gap_secs / 3600, 1),
                            "_re_entry_sender":   sender,
                        })

        # --- 3d. Select top 8, deduplicate overlapping windows ---
        window_scores.sort(key=lambda x: -x["score"])
        selected = []
        for ws in window_scores:
            overlap = any(
                abs(ws["w_start_sec"] - sel["w_start_sec"]) < step_secs * 2
                for sel in selected
            )
            if not overlap:
                selected.append(ws)
            if len(selected) >= 8:
                break

        # Sort selected chronologically by time offset for display
        selected.sort(key=lambda x: x["w_start_sec"])

        # --- 3e. Build hot_moments payload ---
        hot_moments = []
        for ws in selected:
            w_dt = t_start + timedelta(seconds=ws["w_start_sec"])
            date_label = w_dt.strftime("%d %b %Y")
            time_tag   = w_dt.strftime("%H:%M")

            win_msgs = ws["win_msgs"]
            step_s = max(1, len(win_msgs) // 25)
            sample = win_msgs[::step_s][:25]

            if "_pre_ctx_override" in ws:
                pre_ctx = ws["_pre_ctx_override"]
            else:
                first_off = ws["w_start_sec"]
                pre_ctx = [
                    text_messages[idx]
                    for idx, off in enumerate(msg_offsets)
                    if first_off - 600 <= off < first_off
                ][-5:]

            hm = {
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
            }
            if "_silence_hours" in ws:
                hm["silence_hours_before"] = ws["_silence_hours"]
                hm["re_entry_sender"] = ws["_re_entry_sender"]

            hot_moments.append(hm)

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

    # ── 5. Cluster-based Message Sample ──────────────────────────────────────
    # Group text_messages by sender to pick anchor points per person
    per_person_idx = defaultdict(list)
    for idx, m in enumerate(text_messages):
        per_person_idx[m["sender"]].append(idx)

    n_participants = len(per_person_idx)
    # Scale anchors per person inversely with group size so total clusters stay bounded
    anchors_per_person = max(3, min(8, 24 // max(n_participants, 1)))
    WINDOW_RADIUS = 4  # 4 messages before + 4 after anchor = up to 9-message clusters

    seen_cluster_centers = set()
    clusters = []

    for sender, p_indices in per_person_idx.items():
        step = max(1, len(p_indices) // anchors_per_person)
        anchor_indices = p_indices[::step][:anchors_per_person]

        for anchor_idx in anchor_indices:
            if anchor_idx in seen_cluster_centers:
                continue
            seen_cluster_centers.add(anchor_idx)

            start = max(0, anchor_idx - WINDOW_RADIUS)
            end   = min(len(text_messages), anchor_idx + WINDOW_RADIUS + 1)
            window = text_messages[start:end]

            anchor_dt = _parse_dt(text_messages[anchor_idx]["timestamp"])
            label = anchor_dt.strftime("%d %b %Y %H:%M")

            clusters.append({
                "label": label,
                "anchor_sender": sender,
                "messages": [
                    {"sender": m["sender"], "text": m["text"][:200]}
                    for m in window
                ]
            })

    # Sort chronologically and cap total to avoid token bloat
    clusters.sort(key=lambda c: c["label"])
    clusters = clusters[:40]

    # ── 6. Final Payload ──────────────────────────────────────────────────────
    d1 = _parse_dt(messages[0]["timestamp"]).strftime("%d %b %Y")
    d2 = _parse_dt(messages[-1]["timestamp"]).strftime("%d %b %Y")

    return {
        "chat_name":          chat_name,
        "chat_mode":          chat_mode,
        "total_messages":     total_msgs,
        "date_range":         f"{d1} → {d2}",
        "participants":       list(user_profiles.keys()),
        "user_profiles":      user_profiles,
        "relationship_matrix": relationship_matrix[:20],
        "hot_moments":        hot_moments,
        "monthly_timeline":   monthly_timeline,
        "llm_message_clusters": clusters,
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

    total_sent = 0
    total_words_sent = 0
    total_media_sent = 0
    total_late_night = 0
    total_initiations = 0
    total_ignored = 0
    total_replied_to = 0
    initiation_hours = []
    active_days_all = set()

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
                active_days_all.add(dt.date())

                if i > 0:
                    prev = messages[i - 1]
                    if prev["sender"] != "SYSTEM" and not is_target(prev["sender"]):
                        gap = dt - _parse_dt(prev["timestamp"])
                        if gap >= timedelta(hours=2):
                            total_initiations += 1
                            initiation_hours.append(dt.hour)

            if i > 0:
                prev = messages[i - 1]
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

        # Response rate for target
        for i in range(len(messages) - 1):
            curr = messages[i]
            if curr["sender"] == "SYSTEM" or not is_target(curr["sender"]):
                continue
            curr_dt = _parse_dt(curr["timestamp"])
            for j in range(i + 1, min(i + 30, len(messages))):
                nxt = messages[j]
                if nxt["sender"] == "SYSTEM":
                    continue
                if (_parse_dt(nxt["timestamp"]) - curr_dt).total_seconds() > 14400:
                    break
                if not is_target(nxt["sender"]):
                    total_replied_to += 1
                    break

        # Times target was left on read
        for i in range(1, len(messages)):
            curr, prev = messages[i], messages[i - 1]
            if "SYSTEM" in (curr["sender"], prev["sender"]):
                continue
            if is_target(prev["sender"]) and not is_target(curr["sender"]):
                gap = _parse_dt(curr["timestamp"]) - _parse_dt(prev["timestamp"])
                if gap >= timedelta(hours=6):
                    total_ignored += 1

        chat_summaries.append({
            "chat_name": chat_name,
            "chat_mode": chat_mode,
            "total_messages": chat_total,
            "messages_sent_by_you": chat_sent,
            "your_share_pct": round(chat_sent / chat_total * 100, 1) if chat_total else 0,
        })

    avg_reply_to_you = statistics.mean(reply_times_to_target) if reply_times_to_target else None
    avg_reply_by_you = statistics.mean(reply_times_by_target) if reply_times_by_target else None

    # Streak and initiation stats
    def _peak_initiation_period(hours):
        if not hours:
            return "unknown"
        buckets = {
            "morning (6-11am)": 0, "afternoon (12-5pm)": 0,
            "evening (6-10pm)": 0, "late_night (11pm-5am)": 0,
        }
        for h in hours:
            if 6 <= h < 12:
                buckets["morning (6-11am)"] += 1
            elif 12 <= h < 18:
                buckets["afternoon (12-5pm)"] += 1
            elif 18 <= h < 23:
                buckets["evening (6-10pm)"] += 1
            else:
                buckets["late_night (11pm-5am)"] += 1
        return max(buckets, key=buckets.get)

    def _streak_stats(active_days_set):
        if not active_days_set:
            return 0, 0
        days = sorted(active_days_set)
        longest_streak = cur_streak = 1
        longest_gap = 0
        for k in range(1, len(days)):
            diff = (days[k] - days[k - 1]).days
            if diff == 1:
                cur_streak += 1
                longest_streak = max(longest_streak, cur_streak)
            else:
                cur_streak = 1
            longest_gap = max(longest_gap, diff)
        return longest_streak, longest_gap

    longest_streak, longest_gap = _streak_stats(active_days_all)

    # Consolidated monthly timeline
    month_counts = defaultdict(int)
    for chat in chats:
        for m in chat["messages"]:
            month_counts[_parse_dt(m["timestamp"]).strftime("%b %Y")] += 1

    seen_months = sorted(list(month_counts.keys()), key=lambda x: datetime.strptime(x, "%b %Y"))
    monthly_timeline = [{"month": k, "count": month_counts[k]} for k in seen_months]

    # Wider conversation clips: 8 messages before + 8 after anchor = 17-message windows
    # Up to 5 clips per chat for better coverage
    chat_clips = []
    for chat in chats:
        messages = chat["messages"]
        chat_name = chat["chat_name"]

        target_indices = [idx for idx, m in enumerate(messages) if is_target(m["sender"])]
        if not target_indices:
            continue

        step = max(1, len(target_indices) // 5)
        selected_indices = target_indices[::step][:5]

        clips_for_this_chat = []
        for idx in selected_indices:
            start_win = max(0, idx - 8)
            end_win   = min(len(messages), idx + 9)
            window_msgs = messages[start_win:end_win]

            clips_for_this_chat.append({
                "clip_msgs": [
                    {"sender": m["sender"], "text": m["text"][:200], "type": m["type"]}
                    for m in window_msgs
                ]
            })

        chat_clips.append({
            "chat_name": chat_name,
            "clips": clips_for_this_chat,
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
            "times_left_on_read": total_ignored,
            "response_rate_pct": round(total_replied_to / total_sent * 100, 1) if total_sent else 0,
            "peak_initiation_period": _peak_initiation_period(initiation_hours),
            "longest_active_streak_days": longest_streak,
            "longest_silence_days": longest_gap,
            "avg_reply_time_to_you_mins": round(avg_reply_to_you / 60, 1) if avg_reply_to_you else None,
            "avg_reply_time_by_you_mins": round(avg_reply_by_you / 60, 1) if avg_reply_by_you else None,
        },
        "chat_clips": chat_clips,
    }
