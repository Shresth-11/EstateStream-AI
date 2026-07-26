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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#191512]/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-[#ffffff] border border-[#ede5da] rounded-3xl shadow-2xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-[#ede5da] flex items-center justify-between bg-[#fbf8f3]">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-[#d94336] flex items-center justify-center text-white font-extrabold text-base shadow-sm">
              {lead.name.charAt(0)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-extrabold text-[#191512]">
                  {lead.name}
                </h2>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#f4ede4] text-[#6b635b] font-semibold border border-[#e8dfd2]">
                  Lead #{lead.id}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-[#78716c] mt-0.5 font-medium">
                <Phone className="w-3 h-3 text-[#a8a29e]" />
                <span>{lead.phone}</span>
                <span>•</span>
                <span>Created {new Date(lead.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Status Selector */}
            <select
              value={selectedStatus}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="px-3.5 py-2 bg-[#ffffff] border border-[#ede5da] rounded-xl text-xs font-bold text-[#191512] focus:outline-none focus:border-[#d94336] cursor-pointer shadow-xs"
            >
              <option value="new">Status: New</option>
              <option value="qualified">Status: Qualified</option>
              <option value="needs_followup">Status: Needs Follow-up</option>
              <option value="not_interested">Status: Not Interested</option>
            </select>

            <button
              onClick={onClose}
              className="p-2 text-[#78716c] hover:text-[#191512] rounded-xl bg-[#f4ede4] hover:bg-[#ede4d8] transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Lead Qualification Parameters Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-[#fbf8f3] p-4 rounded-2xl border border-[#ede5da]">
              <div className="flex items-center gap-1.5 text-xs text-[#78716c] mb-1 font-medium">
                <DollarSign className="w-3.5 h-3.5 text-[#d94336]" />
                <span>Budget Range</span>
              </div>
              <p className="font-extrabold text-sm text-[#191512]">
                {lead.budget_min ? `${formatPrice(lead.budget_min)} - ` : 'Up to '}
                {formatPrice(lead.budget_max)}
              </p>
            </div>

            <div className="bg-[#fbf8f3] p-4 rounded-2xl border border-[#ede5da]">
              <div className="flex items-center gap-1.5 text-xs text-[#78716c] mb-1 font-medium">
                <MapPin className="w-3.5 h-3.5 text-[#d94336]" />
                <span>Location</span>
              </div>
              <p className="font-extrabold text-sm text-[#191512]">
                {lead.preferred_location || 'Not specified'}
              </p>
            </div>

            <div className="bg-[#fbf8f3] p-4 rounded-2xl border border-[#ede5da]">
              <div className="flex items-center gap-1.5 text-xs text-[#78716c] mb-1 font-medium">
                <Clock className="w-3.5 h-3.5 text-[#d94336]" />
                <span>Timeline</span>
              </div>
              <p className="font-extrabold text-sm text-[#191512]">
                {lead.timeline || 'Immediate'}
              </p>
            </div>

            <div className="bg-[#fbf8f3] p-4 rounded-2xl border border-[#ede5da]">
              <div className="flex items-center gap-1.5 text-xs text-[#78716c] mb-1 font-medium">
                <Sparkles className="w-3.5 h-3.5 text-[#d94336]" />
                <span>Financing Status</span>
              </div>
              <p className="font-extrabold text-sm text-[#191512]">
                {lead.financing_status || 'Pre-approved'}
              </p>
            </div>
          </div>

          {/* Conversations Section */}
          <div className="space-y-4">
            <h3 className="text-base font-extrabold text-[#191512] flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-[#d94336]" />
              <span>Voice Qualification History & Full Transcript</span>
            </h3>

            {loading ? (
              <div className="text-center py-8 text-[#6b635b] text-sm">
                <div className="w-6 h-6 border-2 border-[#d94336] border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                Loading conversation transcript...
              </div>
            ) : conversations.length === 0 ? (
              <div className="text-center py-8 bg-[#fbf8f3] rounded-2xl border border-[#ede5da] text-xs text-[#6b635b]">
                No voice calls recorded for this lead yet.
              </div>
            ) : (
              <div className="space-y-5">
                {conversations.map((conv) => (
                  <div key={conv.id} className="bg-[#ffffff] rounded-2xl border border-[#ede5da] p-5 space-y-4 shadow-sm">
                    {/* Call Header */}
                    <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#ede5da] text-xs">
                      <div className="flex items-center gap-2 font-medium text-[#78716c]">
                        <span className="font-bold text-[#191512]">Call #{conv.id}</span>
                        <span>•</span>
                        <span>{new Date(conv.created_at).toLocaleString()}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {conv.duration_seconds}s
                        </span>
                      </div>

                      <div>
                        {conv.outcome === 'qualified' && (
                          <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold">
                            Qualified
                          </span>
                        )}
                        {conv.outcome === 'escalated' && (
                          <span className="px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 text-xs font-bold flex items-center gap-1">
                            <ShieldAlert className="w-3 h-3" /> Escalated to Human
                          </span>
                        )}
                        {conv.outcome === 'dropped' && (
                          <span className="px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 text-xs font-bold">
                            Dropped
                          </span>
                        )}
                        {conv.outcome === 'incomplete' && (
                          <span className="px-2.5 py-0.5 rounded-full bg-stone-100 text-stone-600 border border-stone-200 text-xs font-bold">
                            Incomplete
                          </span>
                        )}
                      </div>
                    </div>

                    {/* AI Structured Summary */}
                    {conv.summary && (
                      <div className="p-4 rounded-xl bg-[#fff9f5] border border-[#fed7aa]">
                        <div className="flex items-center gap-1.5 text-xs font-extrabold text-[#c2410c] mb-2 uppercase tracking-wide">
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>AI Conversation Summary</span>
                        </div>
                        <div className="text-xs text-[#431407] whitespace-pre-line leading-relaxed font-medium">
                          {conv.summary}
                        </div>
                      </div>
                    )}

                    {/* Turn-by-Turn Transcript */}
                    <div className="space-y-2">
                      <div className="text-xs font-bold text-[#78716c] uppercase tracking-wider mb-2">
                        Turn-by-Turn Transcript
                      </div>
                      <div className="max-h-72 overflow-y-auto space-y-2.5 pr-2">
                        {conv.transcript && conv.transcript.length > 0 ? (
                          conv.transcript.map((turn, idx) => (
                            <div
                              key={idx}
                              className={`p-3.5 rounded-xl text-xs leading-relaxed flex items-start gap-2.5 ${
                                turn.role === 'assistant'
                                  ? 'bg-[#fff5f3] border border-[#fbd2ca] text-[#191512]'
                                  : turn.role === 'tool'
                                  ? 'bg-[#fef3c7] border border-[#fde68a] text-[#92400e]'
                                  : 'bg-[#fbf8f3] border border-[#ede5da] text-[#191512]'
                              }`}
                            >
                              <div className="mt-0.5 flex-shrink-0">
                                {turn.role === 'assistant' ? (
                                  <Bot className="w-4 h-4 text-[#d94336]" />
                                ) : turn.role === 'tool' ? (
                                  <Wrench className="w-4 h-4 text-[#d97706]" />
                                ) : (
                                  <User className="w-4 h-4 text-[#6b635b]" />
                                )}
                              </div>
                              <div className="flex-1">
                                <span className="font-bold mr-1.5 opacity-80">
                                  {turn.role === 'assistant' ? 'Riya:' : turn.role === 'tool' ? `Tool (${turn.name || 'exec'}):` : 'Caller:'}
                                </span>
                                <span className="font-normal">{turn.content}</span>
                              </div>
                            </div>
                          ))
                        ) : (
                          <p className="text-xs text-[#78716c] italic">No turns logged.</p>
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
