import { Skull, MessageSquare, Users, CalendarDays, Heart, AlertTriangle, CheckCircle, Download } from 'lucide-react';
import UserRoastCard from './UserRoastCard';
import RelationshipCard from './RelationshipCard';
import EventCard from './EventCard';
import ActivityChart from './ActivityChart';
import { exportToHTML } from './htmlExporter';

type Mode = 'dm' | 'group' | 'ego' | null;

export default function Dashboard({ reportData, mode }: { reportData: any, mode: Mode }) {
  const data = reportData;
  const roast = data.ai_roast || {};
  const profiles = data.user_profiles || {};
  const chatMode = data.chat_mode || mode;
  const isDM = chatMode === 'dm';
  const isEgo = chatMode === 'ego';
  const isGroup = !isDM && !isEgo;
  const targetName = data.user_aliases?.[0] || 'Target';

  return (
    <div className="max-w-5xl mx-auto space-y-16 pb-20 animate-in fade-in duration-500">

      {/* ── Cover ── */}
      <div className="text-center pt-4 space-y-3">
        <p className="text-gray-500 text-sm font-mono">{data.date_range}</p>
        <h2 className="text-4xl md:text-5xl font-black text-white leading-tight">
          {roast.chat_title || (isDM ? 'DM Analysis' : isEgo ? 'User Profile' : 'Group Chat Analysis')}
        </h2>
        <p className="text-gray-500 text-sm">
          {isEgo 
            ? `${targetName}'s Profile across ${data.chat_summaries?.length} chats`
            : data.participants?.join(' · ')
          }
        </p>
        <div className="flex justify-center gap-4 pt-4 flex-wrap">
          <Stat icon={<MessageSquare className="w-4 h-4" />} value={(isEgo ? data.total_messages_analyzed : data.total_messages)?.toLocaleString()} label="Total Messages" />
          {!isEgo && <Stat icon={<Users className="w-4 h-4" />} value={data.participants?.length} label="Participants" />}
          <Stat icon={<CalendarDays className="w-4 h-4" />} value={data.monthly_timeline?.length} label="Months Active" />
        </div>
        <div className="pt-4">
          <button
            onClick={() => exportToHTML(data)}
            className="px-6 py-2.5 rounded-full bg-white/5 border border-white/10 hover:bg-white/10 text-white font-semibold transition-all text-xs flex items-center gap-2 mx-auto cursor-pointer hover:border-white/20"
          >
            <Download className="w-4.5 h-4.5 text-indigo-400" /> Export Offline Report (HTML)
          </button>
        </div>
      </div>

      {/* ── Activity Chart ── */}
      {data.monthly_timeline?.length > 0 && (
        <Section title="Activity Timeline">
          <ActivityChart data={data.monthly_timeline} />
        </Section>
      )}

      {/* ════════════════════════════════════════
          DM MODE SECTIONS
      ════════════════════════════════════════ */}
      {isDM && (
        <>
          {/* DM Relationship Essence + Verdict */}
          {roast.relationship_essence && (
            <Section title="What Is This?">
              <div className="card p-8 space-y-4">
                <p className="text-gray-300 text-xl leading-relaxed font-medium">{roast.relationship_essence}</p>
                {roast.compatibility_verdict && (
                  <div className="flex items-center gap-3 pt-2 border-t border-white/5">
                    <Heart className="w-5 h-5 text-pink-400 flex-shrink-0" />
                    <p className="text-pink-300 font-semibold text-lg italic">{roast.compatibility_verdict}</p>
                  </div>
                )}
                {roast.verdict && (
                  <div className="flex items-center gap-3 pt-2 border-t border-white/5">
                    <Skull className="w-5 h-5 text-red-400 flex-shrink-0" />
                    <p className="text-red-300 font-semibold italic">{roast.verdict}</p>
                  </div>
                )}
              </div>
            </Section>
          )}

          {/* DM Person Profiles */}
          {roast.person_profiles?.length > 0 && (
            <Section title="The Two Of You 🔍">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {roast.person_profiles.map((ur: any) => {
                  const u = profiles[ur.name];
                  return <UserRoastCard key={ur.name} profile={{ ...ur, personality_summary: ur.personality_in_this_chat }} stats={u} />;
                })}
              </div>
            </Section>
          )}

          {/* Relationship Dynamics */}
          {roast.relationship_dynamics && (
            <Section title="The Dynamics ⚡">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(roast.relationship_dynamics).map(([key, val]: [string, any]) => {
                  const labels: Record<string, string> = {
                    who_initiates_more: '📨 Who Initiates',
                    reply_asymmetry: '⏱ Reply Asymmetry',
                    attachment_read: '🧠 Attachment Read',
                    the_tension: '🔥 The Tension',
                  };
                  return (
                    <div key={key} className="card p-5 space-y-2">
                      <h4 className="text-xs font-bold uppercase tracking-widest text-gray-500">{labels[key] || key}</h4>
                      <p className="text-gray-300 text-sm leading-relaxed">{val}</p>
                    </div>
                  );
                })}
              </div>
            </Section>
          )}

          {/* Red / Green Flags */}
          {(roast.red_flags?.length > 0 || roast.green_flags?.length > 0) && (
            <Section title="Flags 🚩">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {roast.red_flags?.length > 0 && (
                  <div className="card p-6 border-red-500/20 space-y-3">
                    <h4 className="flex items-center gap-2 text-red-400 font-bold text-sm uppercase tracking-widest">
                      <AlertTriangle className="w-4 h-4" /> Red Flags
                    </h4>
                    <ul className="space-y-3">
                      {roast.red_flags.map((f: string, i: number) => (
                        <li key={i} className="text-sm text-gray-400 leading-relaxed flex gap-2">
                          <span className="text-red-500 flex-shrink-0 mt-0.5">🚩</span> {f}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {roast.green_flags?.length > 0 && (
                  <div className="card p-6 border-emerald-500/20 space-y-3">
                    <h4 className="flex items-center gap-2 text-emerald-400 font-bold text-sm uppercase tracking-widest">
                      <CheckCircle className="w-4 h-4" /> Green Flags
                    </h4>
                    <ul className="space-y-3">
                      {roast.green_flags.map((f: string, i: number) => (
                        <li key={i} className="text-sm text-gray-400 leading-relaxed flex gap-2">
                          <span className="text-emerald-500 flex-shrink-0 mt-0.5">✅</span> {f}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Section>
          )}
        </>
      )}

      {/* ════════════════════════════════════════
          GROUP MODE SECTIONS
      ════════════════════════════════════════ */}
      {isGroup && (
        <>
          {/* Group Essence */}
          {roast.group_essence && (
            <Section title="What This Group Actually Is">
              <div className="card p-8">
                <p className="text-gray-300 text-xl leading-relaxed font-medium">{roast.group_essence}</p>
              </div>
            </Section>
          )}

          {/* Group Verdict */}
          {roast.group_roast && (
            <Section title="The Group Verdict 💀">
              <div className="card p-8 md:p-12 relative overflow-hidden glow-pink" style={{ borderColor: 'rgba(236,72,153,0.2)' }}>
                <div className="absolute -top-8 -right-8 opacity-5"><Skull className="w-48 h-48" /></div>
                <p className="text-xl md:text-2xl font-semibold text-white leading-relaxed relative z-10 italic">
                  "{roast.group_roast}"
                </p>
                {roast.verdict && (
                  <p className="mt-4 text-red-300 font-semibold italic text-base relative z-10 border-t border-white/10 pt-4">
                    💀 {roast.verdict}
                  </p>
                )}
              </div>
            </Section>
          )}

          {/* The Suspects */}
          {roast.user_profiles?.length > 0 && (
            <Section title="The Suspects 🔍">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {roast.user_profiles.map((ur: any) => (
                  <UserRoastCard key={ur.name} profile={ur} stats={profiles[ur.name]} />
                ))}
              </div>
            </Section>
          )}

          {/* Relationship Map */}
          {roast.relationship_map?.length > 0 && (
            <Section title="The Dynamics ⚡">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {roast.relationship_map.map((rel: any, i: number) => (
                  <RelationshipCard key={i} relationship={rel} />
                ))}
              </div>
            </Section>
          )}
        </>
      )}

      {/* ════════════════════════════════════════
          EGO MODE SECTIONS
      ════════════════════════════════════════ */}
      {isEgo && (
        <>
          {/* What they think of target */}
          {roast.ego_essence && (
            <Section title={`What People Think of ${targetName}`}>
              <div className="card p-8 space-y-4">
                <p className="text-gray-300 text-xl leading-relaxed font-medium">{roast.ego_essence}</p>
                {roast.compatibility_verdict && (
                  <div className="flex items-center gap-3 pt-2 border-t border-white/5">
                    <Heart className="w-5 h-5 text-amber-400 flex-shrink-0" />
                    <p className="text-amber-300 font-semibold text-lg italic">{roast.compatibility_verdict}</p>
                  </div>
                )}
              </div>
            </Section>
          )}

          {/* Core Roast Card */}
          {roast.roast && (
            <Section title="The Verdict 💀">
              <div className="card p-8 md:p-12 relative overflow-hidden border-red-500/20 glow-red">
                <div className="absolute -top-8 -right-8 opacity-5"><Skull className="w-48 h-48" /></div>
                <p className="text-xl md:text-2xl font-semibold text-white leading-relaxed relative z-10 italic">
                  "{roast.roast}"
                </p>
                {roast.iconic_quote && (
                  <div className="mt-6 flex gap-3 bg-black/20 border border-white/5 rounded-xl p-4">
                    <span className="text-gray-600 text-lg flex-shrink-0">“</span>
                    <p className="text-gray-400 text-sm italic leading-relaxed">"${roast.iconic_quote}"</p>
                  </div>
                )}
              </div>
            </Section>
          )}

          {/* Psychological Profile */}
          {roast.personality_summary && (
            <Section title="Psychological Profile">
              <div className="card p-8 space-y-6">
                <p className="text-gray-300 leading-relaxed text-lg">{roast.personality_summary}</p>
                
                {data.ego_stats && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-white/5">
                    <MiniStat label="Total Sent" value={data.ego_stats.total_messages_sent} />
                    <MiniStat label="Share" value={`${data.ego_stats.overall_share_pct}%`} />
                    <MiniStat label="Avg Length" value={`${data.ego_stats.avg_message_length_words} words`} />
                    <MiniStat label="Late Night" value={`${data.ego_stats.late_night_ratio_pct}%`} />
                    <MiniStat label="Initiations" value={data.ego_stats.conversation_initiations} />
                    <MiniStat label={`Reply to ${targetName}`} value={data.ego_stats.avg_reply_time_to_you_mins ? `${data.ego_stats.avg_reply_time_to_you_mins}m` : 'N/A'} />
                    <MiniStat label={`Reply by ${targetName}`} value={data.ego_stats.avg_reply_time_by_you_mins ? `${data.ego_stats.avg_reply_time_by_you_mins}m` : 'N/A'} />
                  </div>
                )}
              </div>
            </Section>
          )}

          {/* Flags */}
          {roast.flags?.length > 0 && (
            <Section title="Flags 🚩">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {roast.flags.map((f: any, i: number) => {
                  const isRed = typeof f === 'object' 
                    ? f.type === 'red' 
                    : String(f).toLowerCase().includes('red');
                  
                  const behavior = typeof f === 'object' 
                    ? f.behavior 
                    : f;
                    
                  const proof = typeof f === 'object' 
                    ? f.proof 
                    : '';

                  return (
                    <div 
                      key={i} 
                      className={`card p-5 border ${isRed ? 'border-red-500/20 bg-red-500/5 glow-red' : 'border-emerald-500/20 bg-emerald-500/5 glow-indigo'}`}
                    >
                      <h4 className={`text-sm font-bold uppercase tracking-wider ${isRed ? 'text-red-400' : 'text-emerald-400'}`}>
                        {isRed ? '🚩 Red Flag' : '✅ Green Flag'}: {behavior}
                      </h4>
                      {proof && (
                        <p className="text-gray-400 text-sm leading-relaxed mt-2 italic">
                          "{proof}"
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </Section>
          )}

          {/* Social Circles Breakdown */}
          {data.chat_summaries?.length > 0 && (
            <Section title="Social Circles Breakdown">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.chat_summaries.map((summary: any, i: number) => (
                  <div key={i} className="card p-5 space-y-3">
                    <div className="flex items-center justify-between gap-3">
                      <h4 className="text-white font-bold text-base truncate">{summary.chat_name}</h4>
                      <span className={`text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full
                        ${summary.chat_mode === 'dm' ? 'bg-pink-500/15 text-pink-400' : 'bg-indigo-500/15 text-indigo-400'}`}>
                        {summary.chat_mode === 'dm' ? 'DM' : 'Group'}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-black/20 p-2 rounded-lg border border-white/5">
                        <p className="text-gray-500">Sent by {targetName}</p>
                        <p className="text-white font-bold font-mono text-sm mt-0.5">{summary.messages_sent_by_you}</p>
                      </div>
                      <div className="bg-black/20 p-2 rounded-lg border border-white/5">
                        <p className="text-gray-500">Share %</p>
                        <p className="text-white font-bold font-mono text-sm mt-0.5">{summary.your_share_pct}%</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Dynamics Summary */}
          {roast.dynamics_summary && (
            <Section title="Social Dynamics Readout">
              <div className="card p-6">
                <p className="text-gray-300 leading-relaxed text-[15px]">{roast.dynamics_summary}</p>
              </div>
            </Section>
          )}
        </>
      )}

      {/* ── Notable Events (both modes) ── */}
      {roast.hot_moment_summaries?.length > 0 && (
        <Section title="Notable Events 🔥">
          <div className="space-y-4">
            {roast.hot_moment_summaries.map((ev: any, i: number) => (
              <EventCard key={i} event={ev} index={i} />
            ))}
          </div>
        </Section>
      )}

      {/* ── The Story So Far (chapter_narrative) ── */}
      {roast.chapter_narrative?.length > 0 && (
        <Section title="The Story So Far 📖">
          <div className="relative">
            {/* Vertical spine */}
            <div className="absolute left-5 top-0 bottom-0 w-px bg-white/5 hidden sm:block" />
            <div className="space-y-4">
              {roast.chapter_narrative.map((ch: any, i: number) => {
                const phaseEmoji: Record<string, string> = {
                  setup: '🌱', rising: '📈', peak: '🔥', aftermath: '🌅',
                };
                const phaseColor: Record<string, string> = {
                  setup:    'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
                  rising:   'text-amber-400   bg-amber-500/10   border-amber-500/20',
                  peak:     'text-red-400     bg-red-500/10     border-red-500/20',
                  aftermath:'text-indigo-400  bg-indigo-500/10  border-indigo-500/20',
                };
                const colClass = phaseColor[ch.phase] || 'text-gray-400 bg-white/5 border-white/10';
                return (
                  <div key={i} className="flex gap-4">
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-black/40 border border-white/10 flex items-center justify-center text-base z-10">
                      {phaseEmoji[ch.phase] || '📌'}
                    </div>
                    <div className={`card flex-1 p-5 border ${colClass.split(' ').slice(1).join(' ')}`}>
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`text-[10px] font-bold uppercase tracking-widest ${colClass.split(' ')[0]}`}>
                          {ch.phase}
                        </span>
                        <span className="text-white font-bold text-sm">{ch.title}</span>
                      </div>
                      <p className="text-gray-400 text-sm leading-relaxed">{ch.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </Section>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string, children: React.ReactNode }) {
  return (
    <div className="space-y-5">
      <h3 className="text-2xl font-bold text-white">{title}</h3>
      {children}
    </div>
  );
}

function Stat({ icon, value, label }: any) {
  return (
    <div className="flex items-center gap-2 bg-white/[0.04] border border-white/[0.08] px-5 py-2.5 rounded-full">
      <span className="text-indigo-400">{icon}</span>
      <span className="font-mono font-bold text-white">{value}</span>
      <span className="text-gray-500 text-sm">{label}</span>
    </div>
  );
}

function MiniStat({ label, value }: { label: string, value: any }) {
  return (
    <div className="bg-white/[0.03] border border-white/[0.05] rounded-xl p-3 text-center">
      <p className="font-mono font-bold text-sm text-white">{value}</p>
      <p className="text-[10px] text-gray-500 uppercase tracking-wider mt-0.5">{label}</p>
    </div>
  );
}
