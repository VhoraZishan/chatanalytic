import { Zap } from 'lucide-react';

export default function RelationshipCard({ relationship }: { relationship: any }) {
  const [p1, p2] = relationship.persons || [];
  return (
    <div className="card card-hover p-6 space-y-4">
      {/* Names */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-bold text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-full truncate max-w-[130px]" title={p1}>{p1}</span>
        <Zap className="w-4 h-4 text-yellow-500 flex-shrink-0" />
        <span className="text-sm font-bold text-purple-300 bg-purple-500/10 border border-purple-500/20 px-3 py-1 rounded-full truncate max-w-[130px]" title={p2}>{p2}</span>
      </div>
      {/* Dynamic title */}
      <h4 className="text-white font-bold text-base">{relationship.dynamic_title}</h4>
      {/* Description */}
      <p className="text-gray-400 text-sm leading-relaxed">{relationship.description}</p>
      {/* Reply time note */}
      {relationship.reply_time_note && (
        <div className="bg-yellow-500/5 border border-yellow-500/15 rounded-lg px-4 py-3">
          <p className="text-yellow-300/80 text-xs font-mono">{relationship.reply_time_note}</p>
        </div>
      )}
    </div>
  );
}
