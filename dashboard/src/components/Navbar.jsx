import React from 'react';
import { PhoneCall, Mic, Users, Building2, Radio, Sparkles } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, onOpenVoiceTester }) {
  return (
    <header className="sticky top-0 z-40 bg-[#fbf8f3]/95 backdrop-blur-md border-b border-[#ede5da]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between py-3">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#d94336] flex items-center justify-center shadow-md shadow-[#d94336]/20 text-white">
            <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
              <path d="M12 2L2 12h3v8h6v-6h2v6h6v-8h3L12 2zm0 2.84L19.5 11h-1.5v7h-2v-6H8v6H6v-7H4.5L12 4.84z"/>
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-extrabold text-lg tracking-tight text-[#191512]">
                ESTATESTREAM <span className="text-[#d94336]">AI</span>
              </h1>
              <span className="hidden sm:inline-block text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-[#feece8] text-[#b83226] border border-[#fbd2ca]">
                Real-Time Voice AI
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-[#78716c]">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>Voice Agent: Riya</span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex items-center gap-1 bg-[#f4ede4] p-1 rounded-xl border border-[#e8dfd2]">
          <button
            onClick={() => setActiveTab('leads')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'leads'
                ? 'bg-[#ffffff] text-[#191512] shadow-sm'
                : 'text-[#6b635b] hover:text-[#191512] hover:bg-[#ffffff]/50'
            }`}
          >
            <Users className="w-3.5 h-3.5 text-[#d94336]" />
            <span>Buyer Leads</span>
          </button>

          <button
            onClick={() => setActiveTab('properties')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'properties'
                ? 'bg-[#ffffff] text-[#191512] shadow-sm'
                : 'text-[#6b635b] hover:text-[#191512] hover:bg-[#ffffff]/50'
            }`}
          >
            <Building2 className="w-3.5 h-3.5 text-[#d94336]" />
            <span>Inventory (22+)</span>
          </button>

          <button
            onClick={() => setActiveTab('conversations')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'conversations'
                ? 'bg-[#ffffff] text-[#191512] shadow-sm'
                : 'text-[#6b635b] hover:text-[#191512] hover:bg-[#ffffff]/50'
            }`}
          >
            <Radio className="w-3.5 h-3.5 text-[#d94336]" />
            <span>Call Logs</span>
          </button>
        </nav>

        {/* CTAs */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={onOpenVoiceTester}
            className="flex items-center gap-2 px-4 py-2.5 bg-[#d94336] hover:bg-[#c43529] text-white text-xs font-bold rounded-xl shadow-md shadow-[#d94336]/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <PhoneCall className="w-3.5 h-3.5" />
            <span>Test Live Voice Call</span>
          </button>

          <a
            href="/voice-test"
            target="_blank"
            rel="noreferrer"
            className="hidden lg:flex items-center gap-1.5 px-3 py-2.5 bg-[#ffffff] hover:bg-[#f4ede4] text-[#191512] text-xs font-semibold rounded-xl border border-[#ede5da] transition-all shadow-sm"
          >
            <Mic className="w-3.5 h-3.5 text-[#6b635b]" />
            <span>Mic Window</span>
          </a>
        </div>
      </div>
    </header>
  );
}
