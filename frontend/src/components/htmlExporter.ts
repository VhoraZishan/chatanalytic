export function exportToHTML(data: any) {
  const roast = data.ai_roast || {};
  const profiles = data.user_profiles || {};
  const isDM = data.chat_mode === 'dm';
  const isEgo = data.chat_mode === 'ego';
  const isGroup = !isDM && !isEgo;
  const targetName = data.user_aliases?.[0] || 'Target';
  const title = roast.chat_title || (isDM ? 'DM Analysis' : isEgo ? `${targetName}'s Profile` : 'Group Chat Analysis');

  const GRADIENTS = [
    'linear-gradient(135deg, #4f46e5, #7c3aed)',
    'linear-gradient(135deg, #ea580c, #dc2626)',
    'linear-gradient(135deg, #db2777, #e11d48)',
    'linear-gradient(135deg, #0891b2, #2563eb)',
    'linear-gradient(135deg, #059669, #0d9488)',
    'linear-gradient(135deg, #7c3aed, #4f46e5)',
  ];

  function hashStr(str: string) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) hash = ((hash << 5) - hash) + str.charCodeAt(i);
    return hash;
  }

  // --- Monthly timeline bars ---
  const maxTimelineCount = Math.max(...(data.monthly_timeline || []).map((d: any) => d.count), 1);
  const timelineBarsHTML = (data.monthly_timeline || []).map((d: any) => {
    const heightPct = (d.count / maxTimelineCount) * 100;
    const isPeak = d.count === maxTimelineCount;
    return `
      <div class="flex-1 flex flex-col justify-end items-center group relative h-full">
        <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-800 border border-gray-700 text-white text-[10px] font-mono px-2 py-0.5 rounded-md opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 pointer-events-none">
          ${d.count.toLocaleString()}
        </div>
        <div class="w-full flex items-end h-full">
          <div class="w-full rounded-t-sm transition-all duration-700 ${isPeak ? 'bg-gradient-to-t from-orange-600 to-red-500' : 'bg-gradient-to-t from-indigo-800 to-indigo-500'}" style="height: ${Math.max(heightPct, 2)}%"></div>
        </div>
      </div>
    `;
  }).join('');

  const timelineLabelsHTML = (data.monthly_timeline || []).map((d: any) => `
    <div class="flex-1 text-center text-[9px] text-gray-600 leading-tight">
      ${d.month.replace(' 20', "<br>'")}
    </div>
  `).join('');

  // --- User Profiles (Group/DM mode only) ---
  const userProfilesHTML = (!isEgo ? (isDM ? roast.person_profiles : roast.user_profiles || []).map((ur: any) => {
    const stats = profiles[ur.name] || {};
    const grad = GRADIENTS[Math.abs(hashStr(ur.name)) % GRADIENTS.length];
    const summary = isDM ? ur.personality_in_this_chat : ur.personality_summary;

    return `
      <div class="card overflow-hidden card-hover">
        <div class="p-5 flex items-center gap-4" style="background: ${grad}">
          <div class="w-12 h-12 rounded-xl bg-black/30 flex items-center justify-center text-white font-black text-xl flex-shrink-0">
            ${ur.name.substring(0, 2).toUpperCase()}
          </div>
          <div class="min-w-0">
            <p class="text-white/70 text-xs font-semibold uppercase tracking-widest truncate">The title says it all</p>
            <h3 class="text-white font-black text-lg leading-tight truncate" title="${ur.name}">${ur.name}</h3>
            <div class="inline-block mt-1 px-2 py-0.5 bg-black/25 rounded-full text-[11px] text-white font-semibold tracking-wide">
              ${ur.title}
            </div>
          </div>
        </div>
        <div class="p-5 space-y-5">
          <p class="text-gray-300 text-[15px] leading-relaxed">${summary || ''}</p>
          <div class="bg-red-500/5 border border-red-500/15 rounded-xl p-4">
            <p class="text-red-300 text-sm leading-relaxed italic">💀 ${ur.roast}</p>
          </div>
          ${ur.iconic_quote ? `
            <div class="flex gap-3 bg-white/[0.03] border border-white/[0.06] rounded-xl p-4">
              <svg class="w-4 h-4 text-gray-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z"/></svg>
              <p class="text-gray-400 text-sm italic leading-relaxed">"${ur.iconic_quote}"</p>
            </div>
          ` : ''}
          ${stats.total_messages ? `
            <div class="grid grid-cols-3 gap-2 pt-1">
              <div class="bg-white/[0.03] border border-white/[0.05] rounded-lg p-2 text-center">
                <p class="font-mono font-bold text-sm text-white">${stats.total_messages}</p>
                <p class="text-[10px] text-gray-600 uppercase tracking-wider mt-0.5">Messages</p>
              </div>
              <div class="bg-white/[0.03] border border-white/[0.05] rounded-lg p-2 text-center">
                <p class="font-mono font-bold text-sm text-white">${stats.share_pct}%</p>
                <p class="text-[10px] text-gray-600 uppercase tracking-wider mt-0.5">Share</p>
              </div>
              <div class="bg-white/[0.03] border border-white/[0.05] rounded-lg p-2 text-center">
                <p class="font-mono font-bold text-sm text-white">${stats.late_night_ratio_pct}%</p>
                <p class="text-[10px] text-gray-600 uppercase tracking-wider mt-0.5">Late Night</p>
              </div>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }).join('') : '');

  // --- Relationship Web (Group mode) ---
  const relationshipMapHTML = (isGroup && roast.relationship_map || []).map((rel: any) => `
    <div class="card p-6 space-y-4">
      <div class="flex items-center gap-3">
        <span class="text-sm font-bold text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-full truncate">${rel.persons?.[0] || ''}</span>
        <span class="text-yellow-500">⚡</span>
        <span class="text-sm font-bold text-purple-300 bg-purple-500/10 border border-purple-500/20 px-3 py-1 rounded-full truncate">${rel.persons?.[1] || ''}</span>
      </div>
      <h4 class="text-white font-bold text-base">${rel.dynamic_title}</h4>
      <p class="text-gray-400 text-sm leading-relaxed">${rel.description}</p>
      ${rel.reply_time_note ? `
        <div class="bg-yellow-500/5 border border-yellow-500/15 rounded-lg px-4 py-3">
          <p class="text-yellow-300/80 text-xs font-mono">${rel.reply_time_note}</p>
        </div>
      ` : ''}
    </div>
  `).join('');

  // --- Relationship Dynamics (DM mode) ---
  const relationshipDynamicsHTML = isDM && roast.relationship_dynamics ? Object.entries(roast.relationship_dynamics).map(([key, val]: [string, any]) => {
    const labels: Record<string, string> = {
      who_initiates_more: '📨 Who Initiates',
      reply_asymmetry: '⏱ Reply Asymmetry',
      attachment_read: '🧠 Attachment Read',
      the_tension: '🔥 The Tension',
    };
    return `
      <div class="card p-5 space-y-2">
        <h4 class="text-xs font-bold uppercase tracking-widest text-gray-500">${labels[key] || key}</h4>
        <p class="text-gray-300 text-sm leading-relaxed">${val}</p>
      </div>
    `;
  }).join('') : '';


  // --- Social Circles Breakdown (Ego mode) ---
  const socialCirclesHTML = (isEgo && data.chat_summaries || []).map((summary: any) => `
    <div class="card p-5 space-y-3">
      <div class="flex items-center justify-between gap-3">
        <h4 class="text-white font-bold text-base truncate">${summary.chat_name}</h4>
        <span class="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full ${summary.chat_mode === 'dm' ? 'bg-pink-500/15 text-pink-400' : 'bg-indigo-500/15 text-indigo-400'}">
          ${summary.chat_mode === 'dm' ? 'DM' : 'Group'}
        </span>
      </div>
      <div class="grid grid-cols-2 gap-2 text-xs">
        <div class="bg-black/20 p-2 rounded-lg border border-white/5">
          <p class="text-gray-500">Sent by ${targetName}</p>
          <p class="text-white font-bold font-mono text-sm mt-0.5">${summary.messages_sent_by_you}</p>
        </div>
        <div class="bg-black/20 p-2 rounded-lg border border-white/5">
          <p class="text-gray-500">Share %</p>
          <p class="text-white font-bold font-mono text-sm mt-0.5">${summary.your_share_pct}%</p>
        </div>
      </div>
    </div>
  `).join('');

  const EVENT_COLORS = [
    'border-orange-500/25 bg-orange-500/5',
    'border-red-500/25 bg-red-500/5',
    'border-yellow-500/25 bg-yellow-500/5',
    'border-pink-500/25 bg-pink-500/5',
    'border-purple-500/25 bg-purple-500/5',
  ];
  const flameColors = ['text-orange-400', 'text-red-400', 'text-yellow-400', 'text-pink-400', 'text-purple-400'];

  const SIGNAL_LABELS: Record<string, string> = {
    volume_spike:         '📈 Volume Spike',
    velocity_spike:       '⚡ Velocity Spike',
    turn_taking_collapse: '🗣 Monologue Alert',
    response_compression: '🏓 Rapid-Fire Replies',
    topic_cluster:        '🎯 Topic Cluster',
  };
  const SIGNAL_COLORS: Record<string, string> = {
    volume_spike:         'background:rgba(249,115,22,0.15);color:#fdba74;border:1px solid rgba(249,115,22,0.25)',
    velocity_spike:       'background:rgba(234,179,8,0.15);color:#fde047;border:1px solid rgba(234,179,8,0.25)',
    turn_taking_collapse: 'background:rgba(239,68,68,0.15);color:#fca5a5;border:1px solid rgba(239,68,68,0.25)',
    response_compression: 'background:rgba(6,182,212,0.15);color:#67e8f9;border:1px solid rgba(6,182,212,0.25)',
    topic_cluster:        'background:rgba(139,92,246,0.15);color:#c4b5fd;border:1px solid rgba(139,92,246,0.25)',
  };

  const eventsHTML = (roast.hot_moment_summaries || []).map((ev: any, idx: number) => {
    const colorClass = EVENT_COLORS[idx % EVENT_COLORS.length];
    const flameColor = flameColors[idx % flameColors.length];
    const signals: string[] = ev.signals || [];
    const preCtx: any[] = ev.pre_context || [];
    const signalBadges = signals.map(sig => {
      const lbl = SIGNAL_LABELS[sig] || sig;
      const style = SIGNAL_COLORS[sig] || 'background:rgba(255,255,255,0.05);color:#9ca3af;border:1px solid rgba(255,255,255,0.1)';
      return `<span style="${style};font-size:11px;font-weight:600;padding:2px 10px;border-radius:9999px;display:inline-block;margin:2px 2px 2px 0">${lbl}</span>`;
    }).join('');
    const preCtxHTML = preCtx.length ? `
      <details style="margin-top:8px">
        <summary style="cursor:pointer;font-size:12px;color:#6b7280">Show lead-up (${preCtx.length} msgs)</summary>
        <div style="margin-top:8px;border-left:2px solid rgba(255,255,255,0.08);padding-left:12px">
          ${preCtx.map((m: any) => `<p style="font-size:12px;color:#6b7280;margin:4px 0"><span style="color:#9ca3af;font-weight:600">${m.sender}:</span> ${m.text}</p>`).join('')}
        </div>
      </details>` : '';
    return `
      <div class="card ${colorClass} p-6 space-y-4 border">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px">
          <div style="min-width:0">
            <p style="color:#6b7280;font-size:12px;font-family:monospace">${ev.date}${ev.time_tag ? ` · ${ev.time_tag}` : ''}${ev.caps_detected ? ' ⚠ CAPS' : ''}</p>
            <h4 style="color:white;font-weight:700;font-size:18px;margin-top:4px">${ev.event_title}</h4>
          </div>
          <span class="${flameColor}" style="font-size:20px;flex-shrink:0">🔥</span>
        </div>
        ${signalBadges ? `<div style="display:flex;flex-wrap:wrap;gap:4px">${signalBadges}</div>` : ''}
        <p style="color:#d1d5db;font-size:14px;line-height:1.6">${ev.summary}</p>
        ${preCtxHTML}
        ${ev.iconic_moment ? `
          <div style="display:flex;gap:12px;background:rgba(0,0,0,0.2);border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:16px">
            <svg style="width:16px;height:16px;color:#4b5563;flex-shrink:0;margin-top:2px" fill="currentColor" viewBox="0 0 24 24"><path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z"/></svg>
            <p style="color:#9ca3af;font-size:14px;font-style:italic;line-height:1.6">"${ev.iconic_moment}"</p>
          </div>
        ` : ''}
      </div>
    `;
  }).join('');

  // Assemble full HTML document template
  const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title} | Chat Analytic</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body {
      font-family: 'Inter', sans-serif;
      background-color: #080b14;
      color: #e2e8f0;
      -webkit-font-smoothing: antialiased;
    }
    h1, h2, h3, h4 {
      font-family: 'Space Grotesk', sans-serif;
    }
    .card {
      background: rgba(15, 20, 35, 0.8);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 20px;
      backdrop-filter: blur(8px);
    }
    .card-hover:hover {
      border-color: rgba(99,102,241,0.3);
      transform: translateY(-2px);
      transition: all 0.2s ease;
    }
  </style>
</head>
<body class="py-12 px-4 max-w-5xl mx-auto space-y-16">

  <!-- Header / Cover -->
  <div class="text-center space-y-3">
    <p class="text-gray-500 text-sm font-mono">${data.date_range}</p>
    <h2 class="text-4xl md:text-5xl font-black text-white leading-tight">
      ${title}
    </h2>
    <p class="text-gray-500 text-sm">
      ${isEgo 
        ? `${targetName}'s Profile across ${data.chat_summaries?.length} chats`
        : data.participants?.join(' · ')
      }
    </p>
    
    <div class="flex justify-center gap-4 pt-4 flex-wrap text-sm">
      <div class="flex items-center gap-2 bg-white/[0.04] border border-white/[0.08] px-5 py-2.5 rounded-full">
        <span class="font-mono font-bold text-white">
          ${(isEgo ? data.total_messages_analyzed : data.total_messages)?.toLocaleString()}
        </span>
        <span class="text-gray-500 text-xs">Total Messages</span>
      </div>
      ${!isEgo ? `
        <div class="flex items-center gap-2 bg-white/[0.04] border border-white/[0.08] px-5 py-2.5 rounded-full">
          <span class="font-mono font-bold text-white">${data.participants?.length}</span>
          <span class="text-gray-500 text-xs">Participants</span>
        </div>
      ` : `
        <div class="flex items-center gap-2 bg-white/[0.04] border border-white/[0.08] px-5 py-2.5 rounded-full">
          <span class="font-mono font-bold text-white">${data.chat_summaries?.length}</span>
          <span class="text-gray-500 text-xs">Circles Analyzed</span>
        </div>
      `}
      <div class="flex items-center gap-2 bg-white/[0.04] border border-white/[0.08] px-5 py-2.5 rounded-full">
        <span class="font-mono font-bold text-white">${data.monthly_timeline?.length}</span>
        <span class="text-gray-500 text-xs">Months Active</span>
      </div>
    </div>
  </div>

  <!-- Activity Timeline Graph -->
  ${data.monthly_timeline?.length > 0 ? `
    <div class="space-y-5">
      <h3 class="text-2xl font-bold text-white">Activity Timeline</h3>
      <div class="card p-6">
        <p class="text-xs text-gray-500 uppercase tracking-widest font-semibold mb-4">Messages per Month</p>
        <div class="flex items-end gap-1.5" style="height: 160px">
          ${timelineBarsHTML}
        </div>
        <div class="flex gap-1.5 mt-3 border-t border-white/5 pt-3">
          ${timelineLabelsHTML}
        </div>
      </div>
    </div>
  ` : ''}

  <!-- Ego Mode Layout -->
  ${isEgo ? `
    <!-- What They Actually Think of Target -->
    ${roast.ego_essence ? `
      <div class="space-y-5">
        <h3 class="text-2xl font-bold text-white">What People Think of ${targetName}</h3>
        <div class="card p-8 space-y-4">
          <p class="text-gray-300 text-xl leading-relaxed font-medium">${roast.ego_essence}</p>
          ${roast.compatibility_verdict ? `
            <div class="flex items-center gap-3 pt-2 border-t border-white/5">
              <span class="text-amber-400">♥</span>
              <p class="text-amber-300 font-semibold text-lg italic">${roast.compatibility_verdict}</p>
            </div>
          ` : ''}
        </div>
      </div>
    ` : ''}

    <!-- Ego Roast Card -->
    ${roast.roast ? `
      <div class="space-y-5">
        <h3 class="text-2xl font-bold text-white">The Verdict 💀</h3>
        <div class="card p-8 md:p-12 relative overflow-hidden border-red-500/20 bg-red-500/5">
          <p class="text-xl md:text-2xl font-semibold text-white leading-relaxed italic">
            "${roast.roast}"
          </p>
          ${roast.verdict ? `<p style="margin-top:16px;color:#fca5a5;font-weight:600;font-style:italic;font-size:16px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.08)">💀 ${roast.verdict}</p>` : ''}
          ${roast.iconic_quote ? `
            <div class="mt-6 flex gap-3 bg-black/20 border border-white/5 rounded-xl p-4">
              <span class="text-gray-600 text-lg">“</span>
              <p class="text-gray-400 text-sm italic leading-relaxed">"${roast.iconic_quote}"</p>
            </div>
          ` : ''}
        </div>
      </div>
    ` : ''}

    <!-- Psychological Profile -->
    ${roast.personality_summary ? `
      <div class="space-y-5">
        <h3 class="text-2xl font-bold text-white">Psychological Profile</h3>
        <div class="card p-8 space-y-6">
          <p class="text-gray-300 leading-relaxed text-lg">${roast.personality_summary}</p>
          
          ${data.ego_stats ? `
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-white/5 text-center text-xs">
              <div class="bg-white/[0.03] border border-white/[0.05] rounded-xl p-3">
                <p class="font-mono font-bold text-sm text-white">${data.ego_stats.total_messages_sent}</p>
                <p class="text-[10px] text-gray-500 uppercase tracking-wider mt-0.5">Total Sent</p>
              </div>
              <div class="bg-white/[0.03] border border-white/[0.05] rounded-xl p-3">
                <p class="font-mono font-bold text-sm text-white">${data.ego_stats.overall_share_pct}%</p>
                <p class="text-[10px] text-gray-500 uppercase tracking-wider mt-0.5">Share</p>
              </div>
              <div class="bg-white/[0.03] border border-white/[0.05] rounded-xl p-3">
                <p class="font-mono font-bold text-sm text-white">${data.ego_stats.avg_message_length_words} words</p>
                <p class="text-[10px] text-gray-500 uppercase tracking-wider mt-0.5">Avg Length</p>
              </div>
              <div class="bg-white/[0.03] border border-white/[0.05] rounded-xl p-3">
                <p class="font-mono font-bold text-sm text-white">${data.ego_stats.late_night_ratio_pct}%</p>
                <p class="text-[10px] text-gray-500 uppercase tracking-wider mt-0.5">Late Night</p>
              </div>
              <div class="bg-white/[0.03] border border-white/[0.05] rounded-xl p-3">
                <p class="font-mono font-bold text-sm text-white">${data.ego_stats.conversation_initiations}</p>
                <p class="text-[10px] text-gray-500 uppercase tracking-wider mt-0.5">Initiations</p>
              </div>
              <div class="bg-white/[0.03] border border-white/[0.05] rounded-xl p-3">
                <p class="font-mono font-bold text-sm text-white">${data.ego_stats.avg_reply_time_to_you_mins ? `${data.ego_stats.avg_reply_time_to_you_mins}m` : 'N/A'}</p>
                <p class="text-[10px] text-gray-500 uppercase tracking-wider mt-0.5">Reply to ${targetName}</p>
              </div>
              <div class="bg-white/[0.03] border border-white/[0.05] rounded-xl p-3">
                <p class="font-mono font-bold text-sm text-white">${data.ego_stats.avg_reply_time_by_you_mins ? `${data.ego_stats.avg_reply_time_by_you_mins}m` : 'N/A'}</p>
                <p class="text-[10px] text-gray-500 uppercase tracking-wider mt-0.5">Reply by ${targetName}</p>
              </div>
            </div>
          ` : ''}
        </div>
      </div>
    ` : ''}



    <!-- Social Circles Breakdown -->
    ${socialCirclesHTML ? `
      <div class="space-y-5">
        <h3 class="text-2xl font-bold text-white">Social Circles Breakdown</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          ${socialCirclesHTML}
        </div>
      </div>
    ` : ''}

    <!-- Dynamics Summary -->
    ${roast.dynamics_summary ? `
      <div class="space-y-5">
        <h3 class="text-2xl font-bold text-white">Social Dynamics Readout</h3>
        <div class="card p-6">
          <p class="text-gray-300 leading-relaxed text-[15px]">${roast.dynamics_summary}</p>
        </div>
      </div>
    ` : ''}

  ` : `
    <!-- DM or Group Mode Layout -->
    ${isDM ? `
      <!-- Relationship Essence -->
      ${roast.relationship_essence ? `
        <div class="space-y-5">
          <h3 class="text-2xl font-bold text-white">What Is This?</h3>
          <div class="card p-8 space-y-4">
            <p class="text-gray-300 text-xl leading-relaxed font-medium">${roast.relationship_essence}</p>
            ${roast.compatibility_verdict ? `
              <div style="display:flex;align-items:center;gap:12px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.05)">
                <span style="color:#f472b6">♥</span>
                <p style="color:#f9a8d4;font-weight:600;font-size:18px;font-style:italic">${roast.compatibility_verdict}</p>
              </div>
            ` : ''}
            ${roast.verdict ? `
              <div style="display:flex;align-items:center;gap:12px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.05)">
                <span style="color:#f87171">💀</span>
                <p style="color:#fca5a5;font-weight:600;font-style:italic">${roast.verdict}</p>
              </div>
            ` : ''}
          </div>
        </div>
      ` : ''}

      <!-- The Two Of You (DM Profiles) -->
      <div class="space-y-5">
        <h3 class="text-2xl font-bold text-white">The Two Of You 🔍</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          ${userProfilesHTML}
        </div>
      </div>

      <!-- Relationship Dynamics -->
      ${relationshipDynamicsHTML ? `
        <div class="space-y-5">
          <h3 class="text-2xl font-bold text-white">The Dynamics ⚡</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${relationshipDynamicsHTML}
          </div>
        </div>
      ` : ''}


    ` : `
      <!-- GROUP MODE Conditional Sections -->
      <!-- Group Essence -->
      ${roast.group_essence ? `
        <div class="space-y-5">
          <h3 class="text-2xl font-bold text-white">What This Group Actually Is</h3>
          <div class="card p-8">
            <p class="text-gray-300 text-xl leading-relaxed font-medium">${roast.group_essence}</p>
          </div>
        </div>
      ` : ''}

      <!-- Group Roast -->
      ${roast.group_roast ? `
        <div class="space-y-5">
          <h3 class="text-2xl font-bold text-white">The Group Verdict 💀</h3>
          <div class="card p-8 md:p-12 relative overflow-hidden" style="border-color: rgba(236,72,153,0.2); box-shadow: 0 0 40px rgba(236, 72, 153, 0.1);">
            <p class="text-xl md:text-2xl font-semibold text-white leading-relaxed relative z-10 italic">
              "${roast.group_roast}"
            </p>
            ${roast.verdict ? `<p style="margin-top:16px;color:#fca5a5;font-weight:600;font-style:italic;font-size:16px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.08)">💀 ${roast.verdict}</p>` : ''}
          </div>
        </div>
      ` : ''}

      <!-- The Suspects (Group Profiles) -->
      <div class="space-y-5">
        <h3 class="text-2xl font-bold text-white">The Suspects 🔍</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          ${userProfilesHTML}
        </div>
      </div>

      <!-- Relationship Map -->
      ${relationshipMapHTML ? `
        <div class="space-y-5">
          <h3 class="text-2xl font-bold text-white">The Dynamics ⚡</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
            ${relationshipMapHTML}
          </div>
        </div>
      ` : ''}
    `}
  `}

  <!-- Notable Events (Both Modes, skipped in Ego Mode as we don't extract events there) -->
  ${(!isEgo && eventsHTML) ? `
    <div class="space-y-5">
      <h3 class="text-2xl font-bold text-white">Notable Events 🔥</h3>
      <div class="space-y-4">
        ${eventsHTML}
      </div>
    </div>
  ` : ''}

  <!-- The Story So Far (chapter_narrative) -->
  ${roast.chapter_narrative?.length > 0 ? `
    <div class="space-y-5">
      <h3 class="text-2xl font-bold text-white">The Story So Far 📖</h3>
      <div style="position:relative">
        <div style="position:absolute;left:20px;top:0;bottom:0;width:1px;background:rgba(255,255,255,0.05)" class="hidden sm:block"></div>
        <div class="space-y-4">
          ${(roast.chapter_narrative as any[]).map((ch: any) => {
            const emojis: Record<string, string> = { setup: '🌱', rising: '📈', peak: '🔥', aftermath: '🌅' };
            const colors: Record<string, { badge: string; border: string; text: string }> = {
              setup:    { badge: 'color:#34d399', border: 'border-color:rgba(52,211,153,0.25);background:rgba(52,211,153,0.07)', text: 'color:#34d399' },
              rising:   { badge: 'color:#fbbf24', border: 'border-color:rgba(251,191,36,0.25);background:rgba(251,191,36,0.07)',  text: 'color:#fbbf24' },
              peak:     { badge: 'color:#f87171', border: 'border-color:rgba(248,113,113,0.25);background:rgba(248,113,113,0.07)', text: 'color:#f87171' },
              aftermath:{ badge: 'color:#818cf8', border: 'border-color:rgba(129,140,248,0.25);background:rgba(129,140,248,0.07)', text: 'color:#818cf8' },
            };
            const c = colors[ch.phase] || { badge: 'color:#9ca3af', border: 'border-color:rgba(255,255,255,0.08);background:rgba(255,255,255,0.03)', text: 'color:#9ca3af' };
            return `
              <div style="display:flex;gap:16px;align-items:flex-start">
                <div style="flex-shrink:0;width:40px;height:40px;border-radius:50%;background:rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.1);display:flex;align-items:center;justify-content:center;font-size:18px;position:relative;z-index:1">${emojis[ch.phase] || '📌'}</div>
                <div class="card" style="flex:1;padding:20px;border:1px solid;${c.border}">
                  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                    <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;${c.text}">${ch.phase}</span>
                    <span style="color:white;font-weight:700;font-size:14px">${ch.title}</span>
                  </div>
                  <p style="color:#9ca3af;font-size:14px;line-height:1.6">${ch.description}</p>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    </div>
  ` : ''}

  <!-- Footer Info -->
  <div class="text-center pt-8 border-t border-white/5 text-xs text-gray-600">
    Generated by Chat Analytic. Statically archived for offline viewing.
  </div>

</body>
</html>
`;

  // Trigger browser download of offline HTML report
  const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", `${title.toLowerCase().replace(/\s+/g, '-')}-report.html`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
