import { Quote, Flame } from 'lucide-react';

const EVENT_COLORS = [
  'border-orange-500/25 bg-orange-500/5',
  'border-red-500/25 bg-red-500/5',
  'border-yellow-500/25 bg-yellow-500/5',
  'border-pink-500/25 bg-pink-500/5',
  'border-purple-500/25 bg-purple-500/5',
];

export default function EventCard({ event, index }: { event: any, index: number }) {
  const colorClass = EVENT_COLORS[index % EVENT_COLORS.length];
  const flameColors = ['text-orange-400', 'text-red-400', 'text-yellow-400', 'text-pink-400', 'text-purple-400'];

  return (
    <div className={`card ${colorClass} p-6 space-y-4 card-hover`}>
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1 min-w-0">
          <p className="text-gray-500 text-xs font-mono">{event.date}</p>
          <h4 className="text-white font-bold text-lg">{event.event_title}</h4>
        </div>
        <Flame className={`w-5 h-5 flex-shrink-0 mt-1 ${flameColors[index % flameColors.length]}`} />
      </div>

      <p className="text-gray-300 text-sm leading-relaxed">{event.summary}</p>

      {event.iconic_moment && (
        <div className="flex gap-3 bg-black/20 border border-white/5 rounded-xl p-4">
          <Quote className="w-4 h-4 text-gray-600 flex-shrink-0 mt-0.5" />
          <p className="text-gray-400 text-sm italic leading-relaxed">"{event.iconic_moment}"</p>
        </div>
      )}
    </div>
  );
}
