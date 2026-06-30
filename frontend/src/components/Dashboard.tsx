import { useEffect, useState } from 'react';
import { Loader2, Skull, MessageSquare, Users, CalendarDays, Flame, Heart, AlertTriangle, CheckCircle } from 'lucide-react';
import UserRoastCard from './UserRoastCard';
import RelationshipCard from './RelationshipCard';
import EventCard from './EventCard';
import ActivityChart from './ActivityChart';

type Mode = 'dm' | 'group' | null;

export default function Dashboard({ chatId, mode }: { chatId: number, mode: Mode }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/report/${chatId}`);
        if (!res.ok) throw new Error('Failed to fetch report');
        setData(await res.json());
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [chatId]);

  if (loading) return (
    <div className="flex flex-col items-center justify-center py-40 gap-5">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-2 border-indigo-500/20 animate-ping absolute inset-0" />
        <Loader2 className="w-16 h-16 text-indigo-500 animate-spin relative z-10" />
      </div>
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white mb-2">Gemini is reading your chats...</h2>
        <p className="text-gray-500">Analyzing personalities, detecting drama, writing roasts. ~15 seconds.</p>
      </div>
    </div>
  );

  if (error || !data) return (
    <div className="text-center py-20 text-red-400 space-y-2">
      <p className="text-xl font-bold">Something went wrong</p>
      <p className="text-sm opacity-70">{error || 'Could not load'}</p>
    </div>
  );

  const roast = data.ai_roast || {};
  const profiles = data.user_profiles || {};
  const isDM = (data.chat_mode || mode) === 'dm';

  return (
    <div className="max-w-5xl mx-auto space-y-16 pb-20 animate-in fade-in duration-500">

      {/* ── Cover ── */}
      <div className="text-center pt-4 space-y-3">
        <p className="text-gray-500 text-sm font-mono">{data.date_range}</p>
        <h2 className="text-4xl md:text-5xl font-black text-white leading-tight">
          {roast.chat_title || (isDM ? 'DM Analysis' : 'Group Chat Analysis')}
        </h2>
        <p className="text-gray-500 text-sm">{data.participants?.join(' · ')}</p>
        <div className="flex justify-center gap-4 pt-4 flex-wrap">
          <Stat icon={<MessageSquare className="w-4 h-4" />} value={data.total_messages?.toLocaleString()} label="Total Messages" />
          <Stat icon={<Users className="w-4 h-4" />} value={data.participants?.length} label="Participants" />
          <Stat icon={<CalendarDays className="w-4 h-4" />} value={data.monthly_timeline?.length} label="Months Active" />
          <Stat icon={<Flame className="w-4 h-4" />} value={roast.hot_moment_summaries?.length || 0} label="Notable Events" />
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
          {/* Relationship Essence */}
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
      {!isDM && (
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

      {/* ── Timeline Narrative (both modes) ── */}
      {roast.group_timeline_narrative && (
        <Section title={isDM ? 'The Full Story 📖' : 'The Full Story 📖'}>
          <div className="card p-8">
            <p className="text-gray-300 leading-relaxed text-lg">{roast.group_timeline_narrative}</p>
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
