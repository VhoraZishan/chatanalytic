import { useState, useCallback } from 'react';
import { UploadCloud, Loader2, ShieldCheck, Zap, Quote, MessageCircle, Users } from 'lucide-react';

type Mode = 'dm' | 'group' | null;

interface Props {
  onUploadComplete: (chatId: number, mode: Mode) => void;
}

export default function UploadDropzone({ onUploadComplete }: Props) {
  const [mode, setMode] = useState<Mode>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async (file: File) => {
    if (!file.name.endsWith('.txt')) {
      setError('Please upload a .txt file exported from WhatsApp.');
      return;
    }
    setIsUploading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('chat_mode', mode!);
    try {
      const res = await fetch('http://127.0.0.1:8000/upload', { method: 'POST', body: formData });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail || 'Upload failed'); }
      const data = await res.json();
      onUploadComplete(data.chat_id, mode);
    } catch (err: any) {
      setError(err.message || 'An error occurred.');
    } finally {
      setIsUploading(false);
    }
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.[0]) handleUpload(e.dataTransfer.files[0]);
  }, [mode]);

  return (
    <div className="min-h-[calc(100vh-72px)] flex flex-col items-center justify-center py-16 px-4">
      {/* Hero */}
      <div className="text-center mb-12 max-w-3xl">
        <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold uppercase tracking-widest px-4 py-2 rounded-full mb-6">
          <Zap className="w-3 h-3" /> AI-Powered Chat Roasting
        </div>
        <h1 className="text-5xl md:text-7xl font-black tracking-tight mb-5 leading-[1.05]">
          Your chat,<br />
          <span className="text-gradient-fire">brutally exposed.</span>
        </h1>
        <p className="text-gray-400 text-lg leading-relaxed">
          Drop your WhatsApp export. We'll read every message and roast everyone involved.
        </p>
      </div>

      {/* Step 1: Mode selector */}
      <div className="w-full max-w-2xl mb-6">
        <p className="text-gray-500 text-xs uppercase tracking-widest font-semibold text-center mb-4">
          Step 1 — What kind of chat is this?
        </p>
        <div className="grid grid-cols-2 gap-4">
          <ModeCard
            selected={mode === 'dm'}
            onClick={() => setMode('dm')}
            icon={<MessageCircle className="w-7 h-7" />}
            title="DM / Personal Chat"
            desc="1-on-1 conversation. Get a relationship analysis: who's more invested, attachment styles, red flags, compatibility verdict."
            gradient="from-pink-600 to-rose-700"
          />
          <ModeCard
            selected={mode === 'group'}
            onClick={() => setMode('group')}
            icon={<Users className="w-7 h-7" />}
            title="Group Chat"
            desc="3+ people. Get personality roasts, group dynamics, toxic pairings, notable events, and a full group verdict."
            gradient="from-indigo-600 to-violet-700"
          />
        </div>
      </div>

      {/* Step 2: Drop Zone — only shown after mode is selected */}
      {mode && (
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onDrop}
          className={`w-full max-w-2xl rounded-3xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center gap-5 p-10 text-center relative overflow-hidden
            ${isDragging
              ? 'border-indigo-500 bg-indigo-500/10 glow-indigo'
              : 'border-white/10 bg-white/[0.02] hover:border-white/20'
            }`}
        >
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-transparent to-pink-500/5 pointer-events-none" />

          <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all
            ${isDragging ? 'bg-indigo-500/20 border border-indigo-500/40' : 'bg-white/5 border border-white/10'}`}>
            {isUploading
              ? <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
              : <UploadCloud className={`w-8 h-8 ${isDragging ? 'text-indigo-400' : 'text-gray-500'}`} />
            }
          </div>

          <div className="relative z-10">
            <h3 className="text-lg font-semibold text-white mb-1">
              {isUploading ? 'Parsing your chat...' : 'Step 2 — Drop your WhatsApp .txt here'}
            </h3>
            <p className="text-gray-500 text-sm">
              Export from WhatsApp → Chat Settings → Export Chat (Without Media)
            </p>
          </div>

          {!isUploading && (
            <div className="relative z-10">
              <input
                type="file" accept=".txt"
                onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
                className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
              />
              <div className="px-7 py-2.5 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-colors cursor-pointer text-sm">
                Browse Files
              </div>
            </div>
          )}

          {error && (
            <div className="px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm relative z-10 w-full">
              {error}
            </div>
          )}
        </div>
      )}

      {/* Feature pills */}
      <div className="flex flex-wrap justify-center gap-3 mt-10">
        {[
          { icon: <ShieldCheck className="w-4 h-4" />, text: '100% Local — data never leaves your machine' },
          { icon: <Zap className="w-4 h-4" />, text: 'Reads actual messages in any language' },
          { icon: <Quote className="w-4 h-4" />, text: 'Real quotes, real roasts, real events' },
        ].map((f, i) => (
          <div key={i} className="flex items-center gap-2 text-sm text-gray-500 bg-white/[0.03] border border-white/[0.06] px-4 py-2 rounded-full">
            <span className="text-indigo-500">{f.icon}</span> {f.text}
          </div>
        ))}
      </div>
    </div>
  );
}

function ModeCard({ selected, onClick, icon, title, desc, gradient }: any) {
  return (
    <button
      onClick={onClick}
      className={`text-left p-6 rounded-2xl border-2 transition-all duration-200 relative overflow-hidden group
        ${selected
          ? `border-transparent bg-gradient-to-br ${gradient} shadow-xl shadow-indigo-500/20`
          : 'border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.05]'
        }`}
    >
      <div className={`w-12 h-12 rounded-xl mb-4 flex items-center justify-center transition-all
        ${selected ? 'bg-white/20 text-white' : 'bg-white/[0.06] text-gray-400 group-hover:text-gray-300'}`}>
        {icon}
      </div>
      <h3 className={`font-bold text-base mb-2 ${selected ? 'text-white' : 'text-gray-300'}`}>{title}</h3>
      <p className={`text-sm leading-relaxed ${selected ? 'text-white/70' : 'text-gray-500'}`}>{desc}</p>
      {selected && (
        <div className="absolute top-3 right-3 w-5 h-5 rounded-full bg-white/30 flex items-center justify-center">
          <div className="w-2.5 h-2.5 rounded-full bg-white" />
        </div>
      )}
    </button>
  );
}
