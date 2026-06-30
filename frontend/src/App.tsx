import { useState } from 'react';
import UploadDropzone from './components/UploadDropzone';
import Dashboard from './components/Dashboard';

type Mode = 'dm' | 'group' | null;

function App() {
  const [chatId, setChatId] = useState<number | null>(null);
  const [mode, setMode] = useState<Mode>(null);

  const handleUploadComplete = (id: number, m: Mode) => {
    setChatId(id);
    setMode(m);
  };

  return (
    <div className="min-h-screen bg-[#080b14] text-gray-100 font-sans selection:bg-indigo-500/30">
      <header className="border-b border-white/[0.06] bg-[#080b14]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-black text-white text-sm shadow-lg shadow-indigo-500/25">
              CA
            </div>
            <span className="text-lg font-bold tracking-tight text-white">Chat Analytic</span>
            {mode && (
              <span className={`text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full ml-1
                ${mode === 'dm' ? 'bg-pink-500/15 text-pink-400' : 'bg-indigo-500/15 text-indigo-400'}`}>
                {mode === 'dm' ? 'DM' : 'Group'}
              </span>
            )}
          </div>
          {chatId && (
            <button
              onClick={() => { setChatId(null); setMode(null); }}
              className="text-sm text-gray-500 hover:text-white transition-colors"
            >
              ← Analyze Another Chat
            </button>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {!chatId
          ? <UploadDropzone onUploadComplete={handleUploadComplete} />
          : <Dashboard chatId={chatId} mode={mode} />
        }
      </main>
    </div>
  );
}

export default App;
