import React from 'react';
import { AlertCircle, Flame, Moon, Ghost } from 'lucide-react';

interface PatternProps {
  pattern_key: string;
  triggered: boolean;
  evidence: any;
  ai_commentary?: string;
}

const patternConfig: Record<string, { title: string, icon: React.ReactNode, color: string }> = {
  ghosting_period: {
    title: "The Phantom Zone (Ghosting)",
    icon: <Ghost className="w-5 h-5" />,
    color: "from-blue-500 to-cyan-500 text-cyan-400"
  },
  double_texting: {
    title: "Double Texting Champion",
    icon: <Flame className="w-5 h-5" />,
    color: "from-orange-500 to-red-500 text-orange-400"
  },
  late_night_spike: {
    title: "Midnight Owls",
    icon: <Moon className="w-5 h-5" />,
    color: "from-indigo-500 to-purple-500 text-indigo-400"
  }
};

export default function PatternCard({ pattern }: { pattern: PatternProps }) {
  const config = patternConfig[pattern.pattern_key] || {
    title: pattern.pattern_key.replace('_', ' ').toUpperCase(),
    icon: <AlertCircle className="w-5 h-5" />,
    color: "from-gray-500 to-gray-400 text-gray-300"
  };

  return (
    <div className="rounded-2xl bg-gray-900 border border-gray-800 overflow-hidden group hover:border-gray-700 transition-colors">
      <div className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center bg-gray-950 border border-gray-800 ${config.color.split(' ')[1]}`}>
            {config.icon}
          </div>
          <h3 className={`text-lg font-semibold text-transparent bg-clip-text bg-gradient-to-r ${config.color.split(' ').slice(0,2).join(' ')}`}>
            {config.title}
          </h3>
        </div>

        {pattern.ai_commentary ? (
          <p className="text-gray-300 leading-relaxed text-[15px] italic border-l-2 border-gray-700 pl-4 py-1 mb-6">
            "{pattern.ai_commentary}"
          </p>
        ) : (
          <p className="text-gray-500 italic mb-6">Generating AI roast...</p>
        )}

        <div className="bg-gray-950 rounded-xl p-4 border border-gray-800/50 text-sm">
          <div className="text-xs text-gray-500 uppercase tracking-wider font-semibold mb-2">Hard Evidence</div>
          
          {pattern.pattern_key === 'ghosting_period' && (
            <div className="space-y-3">
              <div className="flex justify-between items-center bg-gray-900 px-3 py-2 rounded-lg">
                <span className="text-gray-400">Time ghosted:</span>
                <span className="font-mono text-red-400 font-medium">{pattern.evidence.gap_days} days</span>
              </div>
            </div>
          )}

          {pattern.pattern_key === 'double_texting' && (
            <div className="space-y-3">
              <div className="flex justify-between items-center bg-gray-900 px-3 py-2 rounded-lg">
                <span className="text-gray-400">Offender:</span>
                <span className="font-medium text-orange-400">{pattern.evidence.offender}</span>
              </div>
              <div className="text-xs text-gray-500">Longest Streak: {pattern.evidence.example_streak?.length} messages</div>
            </div>
          )}

          {pattern.pattern_key === 'late_night_spike' && (
            <div className="space-y-3">
               <div className="flex justify-between items-center bg-gray-900 px-3 py-2 rounded-lg">
                <span className="text-gray-400">Night Owl:</span>
                <span className="font-medium text-indigo-400">{pattern.evidence.person}</span>
              </div>
              <div className="flex justify-between items-center bg-gray-900 px-3 py-2 rounded-lg mt-1">
                <span className="text-gray-400">Late night msgs:</span>
                <span className="font-mono text-gray-300">{pattern.evidence.late_night_ratio}%</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
