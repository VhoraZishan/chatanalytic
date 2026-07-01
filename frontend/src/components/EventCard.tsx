import { Quote, Flame, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

const EVENT_COLORS = [
  'border-orange-500/25 bg-orange-500/5',
  'border-red-500/25 bg-red-500/5',
  'border-yellow-500/25 bg-yellow-500/5',
  'border-pink-500/25 bg-pink-500/5',
  'border-purple-500/25 bg-purple-500/5',
];

const SIGNAL_META: Record<string, { label: string; color: string }> = {
  volume_spike:          { label: '📈 Volume Spike',          color: 'bg-orange-500/15 text-orange-300 border-orange-500/25' },
  velocity_spike:        { label: '⚡ Velocity Spike',        color: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/25' },
  turn_taking_collapse:  { label: '🗣 Monologue Alert',       color: 'bg-red-500/15 text-red-300 border-red-500/25' },
  response_compression:  { label: '🏓 Rapid-Fire Replies',   color: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/25' },
  topic_cluster:         { label: '🎯 Topic Cluster',         color: 'bg-purple-500/15 text-purple-300 border-purple-500/25' },
};

export default function EventCard({ event, index }: { event: any; index: number }) {
  const [showContext, setShowContext] = useState(false);
  const colorClass = EVENT_COLORS[index % EVENT_COLORS.length];
  const flameColors = ['text-orange-400', 'text-red-400', 'text-yellow-400', 'text-pink-400', 'text-purple-400'];
  const signals: string[] = event.signals || [];
  const preCtx: { sender: string; text: string }[] = event.pre_context || [];

  return (
    <div className={`card ${colorClass} p-6 space-y-4 card-hover`}>
      {/* Header row */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1 min-w-0">
          <p className="text-gray-500 text-xs font-mono">
            {event.date}{event.time_tag ? ` · ${event.time_tag}` : ''}
            {event.caps_detected && (
              <span className="ml-2 text-yellow-500 font-semibold">⚠ CAPS</span>
            )}
          </p>
          <h4 className="text-white font-bold text-lg">{event.event_title}</h4>
        </div>
        <Flame className={`w-5 h-5 flex-shrink-0 mt-1 ${flameColors[index % flameColors.length]}`} />
      </div>

      {/* Signal badges */}
      {signals.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {signals.map((sig) => {
            const meta = SIGNAL_META[sig] || { label: sig, color: 'bg-white/10 text-gray-400 border-white/10' };
            return (
              <span
                key={sig}
                className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${meta.color}`}
              >
                {meta.label}
              </span>
            );
          })}
        </div>
      )}

      {/* Summary */}
      <p className="text-gray-300 text-sm leading-relaxed">{event.summary}</p>

      {/* Pre-context toggle */}
      {preCtx.length > 0 && (
        <div>
          <button
            onClick={() => setShowContext((s) => !s)}
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            {showContext ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            {showContext ? 'Hide' : 'Show'} lead-up ({preCtx.length} msgs)
          </button>
          {showContext && (
            <div className="mt-3 space-y-1.5 border-l-2 border-white/10 pl-4">
              {preCtx.map((m, i) => (
                <p key={i} className="text-xs text-gray-500 leading-snug">
                  <span className="text-gray-400 font-semibold">{m.sender}:</span> {m.text}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Iconic moment quote */}
      {event.iconic_moment && (
        <div className="flex gap-3 bg-black/20 border border-white/5 rounded-xl p-4">
          <Quote className="w-4 h-4 text-gray-600 flex-shrink-0 mt-0.5" />
          <p className="text-gray-400 text-sm italic leading-relaxed">"{event.iconic_moment}"</p>
        </div>
      )}
    </div>
  );
}
