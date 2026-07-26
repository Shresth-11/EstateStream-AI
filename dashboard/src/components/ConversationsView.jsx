import React, { useState, useEffect } from 'react';
import { Radio, Clock, ShieldAlert, CheckCircle2, ChevronDown, ChevronUp, Sparkles, MessageSquare } from 'lucide-react';
import { fetchConversations } from '../api';

export default function ConversationsView({ onSelectLead }) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await fetchConversations();
      setConversations(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const getOutcomeBadge = (outcome) => {
    switch (outcome) {
      case 'qualified':
        return <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold flex items-center gap-1"><CheckCircle2 className="w-3 h-3 text-emerald-600" /> Qualified</span>;
      case 'escalated':
        return <span className="px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 text-xs font-bold flex items-center gap-1"><ShieldAlert className="w-3 h-3 text-rose-600" /> Escalated</span>;
      case 'dropped':
        return <span className="px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 text-xs font-bold">Dropped</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full bg-stone-100 text-stone-600 border border-stone-200 text-xs font-bold">Incomplete</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-extrabold text-[#191512] tracking-tight">Call Sessions & Turn Logs</h2>
        <p className="text-xs text-[#6b635b] mt-0.5">Every call ingested via Twilio Media Streams or browser microphone</p>
      </div>

      {loading ? (
        <div className="text-center py-20 text-[#6b635b]">
          <div className="w-8 h-8 border-2 border-[#d94336] border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm font-medium">Loading session history...</p>
        </div>
      ) : conversations.length === 0 ? (
        <div className="text-center py-16 masal-card p-8 border border-[#ede5da]">
          <Radio className="w-12 h-12 text-[#a8a29e] mx-auto mb-3" />
          <h3 className="text-base font-bold text-[#191512]">No calls recorded yet</h3>
          <p className="text-xs text-[#6b635b] mt-1">Start a call using the Live Voice Call tester to record sessions.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className="masal-card overflow-hidden transition-all"
            >
              {/* Row Header */}
              <div
                onClick={() => toggleExpand(conv.id)}
                className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer hover:bg-[#fbf8f3] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[#feece8] border border-[#fbd2ca] flex items-center justify-center text-[#d94336]">
                    <Radio className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-extrabold text-base text-[#191512]">Call #{conv.id}</h3>
                      {conv.lead && (
                        <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#f4ede4] text-[#191512] font-semibold border border-[#e8dfd2]">
                          {conv.lead.name}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-[#78716c] mt-0.5 font-medium">
                      <span>{new Date(conv.created_at).toLocaleString()}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-[#a8a29e]" />
                        {conv.duration_seconds}s
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {getOutcomeBadge(conv.outcome)}
                  <div className="text-[#a8a29e] p-1">
                    {expandedId === conv.id ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                  </div>
                </div>
              </div>

              {/* Collapsible Details */}
              {expandedId === conv.id && (
                <div className="px-5 pb-5 pt-2 border-t border-[#ede5da] space-y-4 bg-[#fdfbf9]">
                  {conv.summary && (
                    <div className="p-4 rounded-xl bg-[#fff9f5] border border-[#fed7aa]">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-[#c2410c] mb-2 uppercase tracking-wide">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>AI Call Summary</span>
                      </div>
                      <div className="text-xs text-[#431407] whitespace-pre-line leading-relaxed font-medium">
                        {conv.summary}
                      </div>
                    </div>
                  )}

                  {/* Transcript */}
                  <div>
                    <div className="text-xs font-bold text-[#78716c] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>Full Turn Transcript ({conv.transcript ? conv.transcript.length : 0} turns)</span>
                    </div>
                    <div className="max-h-60 overflow-y-auto space-y-2 pr-2">
                      {conv.transcript && conv.transcript.length > 0 ? (
                        conv.transcript.map((t, i) => (
                          <div
                            key={i}
                            className={`p-2.5 rounded-xl text-xs ${
                              t.role === 'assistant'
                                ? 'bg-[#fff5f3] border border-[#fbd2ca] text-[#191512]'
                                : 'bg-[#ffffff] border border-[#ede5da] text-[#191512]'
                            }`}
                          >
                            <span className="font-bold mr-1.5 text-[#d94336]">
                              {t.role === 'assistant' ? 'Riya:' : 'Caller:'}
                            </span>
                            <span>{t.content}</span>
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-[#78716c] italic">No turns logged.</p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
