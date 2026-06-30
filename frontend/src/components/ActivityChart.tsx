interface DataPoint { month: string; count: number; }

export default function ActivityChart({ data }: { data: DataPoint[] }) {
  if (!data || data.length === 0) return null;

  const max = Math.max(...data.map(d => d.count));

  return (
    <div className="card p-6">
      <p className="text-xs text-gray-500 uppercase tracking-widest font-semibold mb-4">Messages per Month</p>
      {/* Bars container — fixed height of 160px */}
      <div className="flex items-end gap-1.5" style={{ height: '160px' }}>
        {data.map((d, i) => {
          const heightPct = max > 0 ? (d.count / max) * 100 : 0;
          const isPeak = d.count === max;
          return (
            <div
              key={i}
              className="flex-1 flex flex-col justify-end items-center group relative"
              style={{ height: '100%' }}
            >
              {/* Tooltip */}
              <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-800 border border-gray-700 text-white text-[10px] font-mono px-2 py-0.5 rounded-md opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 pointer-events-none">
                {d.count.toLocaleString()}
              </div>
              {/* Bar */}
              <div
                className={`w-full rounded-t-sm transition-all duration-700 ${
                  isPeak
                    ? 'bg-gradient-to-t from-orange-600 to-red-500'
                    : 'bg-gradient-to-t from-indigo-800 to-indigo-500'
                }`}
                style={{ height: `${Math.max(heightPct, 2)}%` }}
              />
            </div>
          );
        })}
      </div>
      {/* X-axis labels */}
      <div className="flex gap-1.5 mt-3 border-t border-white/5 pt-3">
        {data.map((d, i) => (
          <div key={i} className="flex-1 text-center text-[9px] text-gray-600 leading-tight">
            {d.month.replace(' 20', "\n'")}
          </div>
        ))}
      </div>
      {/* Peak annotation */}
      <div className="mt-3 text-xs text-orange-400/70">
        🔥 Peak: {data.find(d => d.count === max)?.month} — {max.toLocaleString()} messages
      </div>
    </div>
  );
}
