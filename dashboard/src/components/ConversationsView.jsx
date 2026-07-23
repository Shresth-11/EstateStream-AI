import React, { useState, useEffect } from 'react';
import { Radio, Clock, ShieldAlert, CheckCircle2, User, ChevronDown, ChevronUp, Sparkles, MessageSquare } from 'lucide-react';
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
        return <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-xs font-semibold flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Qualified</span>;
      case 'escalated':
        return <span className="px-2.5 py-0.5 rounded-full bg-rose-500/15 text-rose-400 border border-rose-500/30 text-xs font-semibold flex items-center gap-1"><ShieldAlert className="w-3 h-3" /> Escalated</span>;
      case 'dropped':
        return <span className="px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/30 text-xs font-semibold">Dropped</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full bg-slate-500/15 text-slate-400 border border-slate-500/30 text-xs font-semibold">Incomplete</span>;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Call Sessions & Turn-by-Turn Logs</h2>
        <p className="text-sm text-slate-400">All inbound calls processed via Twilio Media Streams or WebRTC browser mic</p>
      </div>

      {loading ? (
        <div className="text-center py-16 text-slate-400">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p>Loading call history...</p>
        </div>
      ) : conversations.length === 0 ? (
        <div className="text-center py-16 glass-card rounded-2xl border border-slate-800">
          <Radio className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-300">No call sessions recorded yet</h3>
          <p className="text-sm text-slate-500 mt-1">Start a call using the Live Mic Tester to generate session records.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className="glass-card rounded-2xl border border-slate-800/80 overflow-hidden transition-all"
            >
              {/* Row Header */}
              <div
                onClick={() => toggleExpand(conv.id)}
                className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer hover:bg-slate-800/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-indigo-950/60 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                    <Radio className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-base text-white">Call #{conv.id}</h3>
                      {conv.lead && (
                        <span className="text-xs px-2 py-0.5 rounded-md bg-slate-800 text-indigo-300 font-medium border border-slate-700">
                          {conv.lead.name}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                      <span>{new Date(conv.created_at).toLocaleString()}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-500" />
                        {conv.duration_seconds}s
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {getOutcomeBadge(conv.outcome)}
                  <div className="text-slate-400 p-1">
                    {expandedId === conv.id ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                  </div>
                </div>
              </div>

              {/* Collapsible Details */}
              {expandedId === conv.id && (
                <div className="px-5 pb-5 pt-1 border-t border-slate-800/60 space-y-4">
                  {conv.summary && (
                    <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-400 mb-2 uppercase tracking-wide">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>AI Call Summary</span>
                      </div>
                      <div className="text-xs text-slate-300 whitespace-pre-line leading-relaxed">
                        {conv.summary}
                      </div>
                    </div>
                  )}

                  {/* Transcript */}
                  <div>
                    <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>Turn-by-Turn Transcript ({conv.transcript ? conv.transcript.length : 0} turns)</span>
                    </div>
                    <div className="max-h-60 overflow-y-auto space-y-2 pr-2">
                      {conv.transcript && conv.transcript.length > 0 ? (
                        conv.transcript.map((t, i) => (
                          <div
                            key={i}
                            className={`p-2.5 rounded-xl text-xs ${
                              t.role === 'assistant'
                                ? 'bg-indigo-950/30 border border-indigo-500/20 text-indigo-200'
                                : 'bg-emerald-950/30 border border-emerald-500/20 text-emerald-200'
                            }`}
                          >
                            <span className="font-bold mr-1.5 opacity-75">
                              {t.role === 'assistant' ? 'Riya:' : 'Caller:'}
                            </span>
                            <span>{t.content}</span>
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-slate-500 italic">No turns logged.</p>
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
