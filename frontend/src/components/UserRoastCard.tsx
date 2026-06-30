import { Quote, TrendingUp, TrendingDown } from 'lucide-react';

const GRADIENTS = [
  'from-indigo-600 to-purple-700',
  'from-orange-600 to-red-700',
  'from-pink-600 to-rose-700',
  'from-cyan-600 to-blue-700',
  'from-emerald-600 to-teal-700',
  'from-violet-600 to-indigo-700',
];

export default function UserRoastCard({ profile, stats }: { profile: any, stats: any }) {
  const gradient = GRADIENTS[Math.abs(hashStr(profile.name)) % GRADIENTS.length];

  return (
    <div className="card card-hover overflow-hidden">
      {/* Header strip */}
      <div className={`bg-gradient-to-r ${gradient} p-5 flex items-center gap-4`}>
        <div className="w-12 h-12 rounded-xl bg-black/30 flex items-center justify-center text-white font-black text-xl flex-shrink-0">
          {profile.name.substring(0, 2).toUpperCase()}
        </div>
        <div className="min-w-0">
          <p className="text-white/70 text-xs font-semibold uppercase tracking-widest truncate">The title says it all</p>
          <h3 className="text-white font-black text-lg leading-tight truncate" title={profile.name}>{profile.name}</h3>
          <div className="inline-block mt-1 px-2 py-0.5 bg-black/25 rounded-full text-[11px] text-white font-semibold tracking-wide">
            {profile.title}
          </div>
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* Personality Summary */}
        <p className="text-gray-300 text-[15px] leading-relaxed">{profile.personality_summary}</p>

        {/* Roast */}
        <div className="bg-red-500/5 border border-red-500/15 rounded-xl p-4">
          <p className="text-red-300 text-sm leading-relaxed italic">💀 {profile.roast}</p>
        </div>

        {/* Iconic Quote */}
        {profile.iconic_quote && (
          <div className="flex gap-3 bg-white/[0.03] border border-white/[0.06] rounded-xl p-4">
            <Quote className="w-4 h-4 text-gray-600 flex-shrink-0 mt-0.5" />
            <p className="text-gray-400 text-sm italic leading-relaxed">"{profile.iconic_quote}"</p>
          </div>
        )}

        {/* Stats Row */}
        {stats && (
          <div className="grid grid-cols-3 gap-2 pt-1">
            <MiniStat label="Messages" value={stats.total_messages} />
            <MiniStat label="Share" value={`${stats.share_pct}%`} />
            <MiniStat label="Late Night" value={`${stats.late_night_ratio_pct}%`} />
            <MiniStat label="Avg Length" value={`${stats.avg_msg_length_words}w`} />
            <MiniStat label="Initiations" value={stats.conversation_initiations} />
            <MiniStat label="Ghosted" value={stats.times_left_on_read} highlight={stats.times_left_on_read > 5} />
          </div>
        )}
      </div>
    </div>
  );
}

function MiniStat({ label, value, highlight = false }: { label: string, value: any, highlight?: boolean }) {
  return (
    <div className="bg-white/[0.03] border border-white/[0.05] rounded-lg p-2.5 text-center">
      <p className={`font-mono font-bold text-sm ${highlight ? 'text-red-400' : 'text-white'}`}>{value}</p>
      <p className="text-[10px] text-gray-600 uppercase tracking-wider mt-0.5">{label}</p>
    </div>
  );
}

function hashStr(str: string) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) hash = ((hash << 5) - hash) + str.charCodeAt(i);
  return hash;
}
