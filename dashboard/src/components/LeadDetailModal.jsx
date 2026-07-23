import React, { useEffect, useState } from 'react';
import { X, Phone, DollarSign, MapPin, Calendar, Clock, Sparkles, MessageSquare, Bot, User, Wrench, ShieldAlert } from 'lucide-react';
import { fetchConversations, updateLeadStatus } from '../api';

export default function LeadDetailModal({ lead, onClose, onLeadUpdated }) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState(lead.status);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await fetchConversations(lead.id);
        setConversations(data);
      } catch (err) {
        console.error('Error fetching conversations:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [lead.id]);

  const handleStatusChange = async (newStatus) => {
    try {
      setSelectedStatus(newStatus);
      const updated = await updateLeadStatus(lead.id, newStatus);
      if (onLeadUpdated) onLeadUpdated(updated);
    } catch (e) {
      console.error(e);
    }
  };

  const formatPrice = (val) => {
    if (!val) return 'Flexible';
    return `$${val.toLocaleString()}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-[#0c1322] border border-indigo-500/30 rounded-3xl shadow-2xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-600 to-pink-500 flex items-center justify-center text-white font-bold">
              {lead.name.charAt(0)}
            </div>
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <span>{lead.name}</span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 font-normal">
                  Lead #{lead.id}
                </span>
              </h2>
              <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                <Phone className="w-3 h-3 text-slate-500" />
                <span>{lead.phone}</span>
                <span>•</span>
                <span>Captured: {new Date(lead.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Status Selector */}
            <select
              value={selectedStatus}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-xl text-xs font-semibold text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              <option value="new">Status: New</option>
              <option value="qualified">Status: Qualified</option>
              <option value="needs_followup">Status: Needs Follow-up</option>
              <option value="not_interested">Status: Not Interested</option>
            </select>

            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white rounded-xl bg-slate-800/80 hover:bg-slate-700 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Lead Qualification Parameters Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="glass-panel p-3.5 rounded-2xl border border-slate-800/80">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                <DollarSign className="w-3.5 h-3.5 text-indigo-400" />
                <span>Budget Range</span>
              </div>
              <p className="font-semibold text-sm text-indigo-300">
                {lead.budget_min ? `${formatPrice(lead.budget_min)} - ` : 'Up to '}
                {formatPrice(lead.budget_max)}
              </p>
            </div>

            <div className="glass-panel p-3.5 rounded-2xl border border-slate-800/80">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                <MapPin className="w-3.5 h-3.5 text-indigo-400" />
                <span>Location</span>
              </div>
              <p className="font-semibold text-sm text-slate-200">
                {lead.preferred_location || 'Not specified'}
              </p>
            </div>

            <div className="glass-panel p-3.5 rounded-2xl border border-slate-800/80">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                <Clock className="w-3.5 h-3.5 text-indigo-400" />
                <span>Timeline</span>
              </div>
              <p className="font-semibold text-sm text-slate-200">
                {lead.timeline || 'Not specified'}
              </p>
            </div>

            <div className="glass-panel p-3.5 rounded-2xl border border-slate-800/80">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>Financing Status</span>
              </div>
              <p className="font-semibold text-sm text-slate-200">
                {lead.financing_status || 'Guidance requested'}
              </p>
            </div>
          </div>

          {/* Conversations Section */}
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2 mb-3">
              <MessageSquare className="w-4 h-4 text-indigo-400" />
              <span>Voice Call History & Transcripts</span>
            </h3>

            {loading ? (
              <div className="text-center py-8 text-slate-400 text-sm">
                <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                Loading call transcripts...
              </div>
            ) : conversations.length === 0 ? (
              <div className="text-center py-8 glass-panel rounded-2xl border border-slate-800 text-sm text-slate-400">
                No voice calls recorded for this lead yet.
              </div>
            ) : (
              <div className="space-y-6">
                {conversations.map((conv) => (
                  <div key={conv.id} className="glass-panel rounded-2xl border border-slate-800 p-5 space-y-4">
                    {/* Call Header */}
                    <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800/80 text-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-200">Call Session #{conv.id}</span>
                        <span className="text-slate-500">•</span>
                        <span className="text-slate-400">{new Date(conv.created_at).toLocaleString()}</span>
                        <span className="text-slate-500">•</span>
                        <span className="text-slate-400 flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-500" />
                          {conv.duration_seconds}s duration
                        </span>
                      </div>

                      <div>
                        {conv.outcome === 'qualified' && (
                          <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-semibold">
                            Qualified
                          </span>
                        )}
                        {conv.outcome === 'escalated' && (
                          <span className="px-2.5 py-0.5 rounded-full bg-rose-500/15 text-rose-400 border border-rose-500/30 font-semibold flex items-center gap-1">
                            <ShieldAlert className="w-3 h-3" /> Escalated to Human
                          </span>
                        )}
                        {conv.outcome === 'dropped' && (
                          <span className="px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/30 font-semibold">
                            Dropped Early
                          </span>
                        )}
                        {conv.outcome === 'incomplete' && (
                          <span className="px-2.5 py-0.5 rounded-full bg-slate-500/15 text-slate-400 border border-slate-500/30 font-semibold">
                            Incomplete
                          </span>
                        )}
                      </div>
                    </div>

                    {/* AI Structured Summary */}
                    {conv.summary && (
                      <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-400 mb-2 uppercase tracking-wide">
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>AI Conversation Summary</span>
                        </div>
                        <div className="text-xs text-slate-300 whitespace-pre-line leading-relaxed">
                          {conv.summary}
                        </div>
                      </div>
                    )}

                    {/* Turn by turn Transcript */}
                    <div className="space-y-2.5">
                      <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                        Turn-by-Turn Transcript
                      </div>
                      <div className="max-h-72 overflow-y-auto space-y-2.5 pr-2">
                        {conv.transcript && conv.transcript.length > 0 ? (
                          conv.transcript.map((turn, idx) => (
                            <div
                              key={idx}
                              className={`p-3 rounded-xl text-xs leading-relaxed flex items-start gap-2.5 ${
                                turn.role === 'assistant'
                                  ? 'bg-slate-900/80 border border-indigo-500/20 text-slate-200'
                                  : turn.role === 'tool'
                                  ? 'bg-amber-950/20 border border-amber-500/20 text-amber-300'
                                  : 'bg-emerald-950/20 border border-emerald-500/20 text-emerald-200'
                              }`}
                            >
                              <div className="mt-0.5 flex-shrink-0">
                                {turn.role === 'assistant' ? (
                                  <Bot className="w-3.5 h-3.5 text-indigo-400" />
                                ) : turn.role === 'tool' ? (
                                  <Wrench className="w-3.5 h-3.5 text-amber-400" />
                                ) : (
                                  <User className="w-3.5 h-3.5 text-emerald-400" />
                                )}
                              </div>
                              <div className="flex-1">
                                <span className="font-bold mr-1.5 opacity-75">
                                  {turn.role === 'assistant' ? 'Riya:' : turn.role === 'tool' ? `Tool (${turn.name || 'exec'}):` : 'Caller:'}
                                </span>
                                <span>{turn.content}</span>
                              </div>
                            </div>
                          ))
                        ) : (
                          <p className="text-xs text-slate-500 italic">No transcript recorded for this turn.</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
