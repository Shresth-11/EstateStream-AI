import React from 'react';
import { Search, Filter, Phone, MapPin, DollarSign, Calendar, CheckCircle2, Clock, FileText, ChevronRight, PhoneCall, Sparkles } from 'lucide-react';

export default function LeadList({
  leads,
  loading,
  onSelectLead,
  filterStatus,
  setFilterStatus,
  searchQuery,
  setSearchQuery,
  onOpenVoiceTester,
}) {
  const statusOptions = [
    { label: 'All Leads', value: 'all' },
    { label: 'Qualified', value: 'qualified' },
    { label: 'Needs Follow-up', value: 'needs_followup' },
    { label: 'New', value: 'new' },
    { label: 'Not Interested', value: 'not_interested' },
  ];

  const getStatusBadge = (status) => {
    switch (status) {
      case 'qualified':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Qualified
          </span>
        );
      case 'needs_followup':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3 h-3 text-amber-600" /> Needs Follow-up
          </span>
        );
      case 'not_interested':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-stone-100 text-stone-600 border border-stone-200">
            Not Interested
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-50 text-sky-700 border border-sky-200">
            New Lead
          </span>
        );
    }
  };

  const formatPrice = (val) => {
    if (!val) return 'Flexible';
    return `$${val.toLocaleString()}`;
  };

  return (
    <div className="space-y-8">
      {/* Editorial Hero Section (Inspired by Masal.ai) */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#ffffff] via-[#fbf8f3] to-[#f4ede4] border border-[#ede5da] p-8 sm:p-10 shadow-sm">
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#feece8] border border-[#fbd2ca] text-[#b83226] text-xs font-bold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Voice Calling For Real Estate</span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-[#191512] tracking-tight leading-[1.15]">
            Never miss another <br />
            <span className="text-[#d94336]">qualified lead.</span>
          </h2>

          <p className="text-base text-[#6b635b] leading-relaxed max-w-2xl font-normal">
            Riya calls every buyer within 30 seconds, qualifies budget and preferred location in natural conversation, searches real inventory, and saves verified records straight into your CRM.
          </p>

          {/* Floating Pill Badges */}
          <div className="flex flex-wrap gap-2.5 pt-2">
            <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#ffffff] border border-[#ede5da] text-xs font-semibold text-[#191512] shadow-sm">
              <span className="w-2 h-2 rounded-full bg-[#d94336]"></span>
              30-second callback
            </span>
            <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#ffffff] border border-[#ede5da] text-xs font-semibold text-[#191512] shadow-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              Auto-matches database inventory
            </span>
            <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#ffffff] border border-[#ede5da] text-xs font-semibold text-[#191512] shadow-sm">
              <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
              Zero hallucinations guarantee
            </span>
          </div>
        </div>
      </section>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          {statusOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setFilterStatus(opt.value)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                filterStatus === opt.value
                  ? 'bg-[#d94336] text-white shadow-md shadow-[#d94336]/20'
                  : 'bg-[#ffffff] border border-[#ede5da] text-[#6b635b] hover:text-[#191512] hover:bg-[#f4ede4]'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[#78716c]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search name, phone, location..."
            className="w-full pl-10 pr-4 py-2 bg-[#ffffff] border border-[#ede5da] rounded-xl text-xs font-medium text-[#191512] placeholder-[#78716c] focus:outline-none focus:border-[#d94336] shadow-sm"
          />
        </div>
      </div>

      {/* Leads Grid */}
      {loading ? (
        <div className="text-center py-20 text-[#6b635b]">
          <div className="w-8 h-8 border-2 border-[#d94336] border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm font-medium">Loading buyer records...</p>
        </div>
      ) : leads.length === 0 ? (
        <div className="text-center py-16 masal-card rounded-2xl p-8 border border-[#ede5da]">
          <div className="w-12 h-12 rounded-full bg-[#feece8] flex items-center justify-center mx-auto mb-3 text-[#d94336]">
            <Filter className="w-5 h-5" />
          </div>
          <h3 className="text-base font-bold text-[#191512]">No leads match your filter</h3>
          <p className="text-xs text-[#6b635b] mt-1 max-w-sm mx-auto">
            Try adjusting your search criteria or click "Test Live Voice Call" to simulate an inbound buyer conversation.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {leads.map((lead) => (
            <div
              key={lead.id}
              className="masal-card p-6 flex flex-col justify-between group"
            >
              <div>
                {/* Header: Name & Status */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div>
                    <h3 className="font-extrabold text-base text-[#191512] group-hover:text-[#d94336] transition-colors">
                      {lead.name}
                    </h3>
                    <div className="flex items-center gap-1.5 text-xs text-[#78716c] mt-0.5">
                      <Phone className="w-3 h-3 text-[#a8a29e]" />
                      <span>{lead.phone}</span>
                    </div>
                  </div>
                  <div>{getStatusBadge(lead.status)}</div>
                </div>

                {/* Qualification Parameters */}
                <div className="space-y-2.5 py-3 border-y border-[#ede5da] my-3 text-xs">
                  <div className="flex items-center justify-between text-[#191512]">
                    <span className="flex items-center gap-1.5 text-[#78716c] font-medium">
                      <DollarSign className="w-3.5 h-3.5 text-[#d94336]" />
                      Budget
                    </span>
                    <span className="font-bold text-[#191512]">
                      {lead.budget_min ? `${formatPrice(lead.budget_min)} - ` : 'Up to '}
                      {formatPrice(lead.budget_max)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[#191512]">
                    <span className="flex items-center gap-1.5 text-[#78716c] font-medium">
                      <MapPin className="w-3.5 h-3.5 text-[#d94336]" />
                      Location
                    </span>
                    <span className="font-semibold text-[#191512]">{lead.preferred_location || 'Flexible'}</span>
                  </div>

                  <div className="flex items-center justify-between text-[#191512]">
                    <span className="flex items-center gap-1.5 text-[#78716c] font-medium">
                      <Calendar className="w-3.5 h-3.5 text-[#d94336]" />
                      Timeline
                    </span>
                    <span className="font-medium text-[#44403c]">{lead.timeline || 'Immediate'}</span>
                  </div>
                </div>

                {/* Badges */}
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {lead.bhk_preference && (
                    <span className="px-2.5 py-1 rounded-md bg-[#f4ede4] text-[#191512] text-[11px] font-semibold border border-[#e8dfd2]">
                      {lead.bhk_preference}
                    </span>
                  )}
                  {lead.financing_status && (
                    <span className="px-2.5 py-1 rounded-md bg-[#feece8] text-[#b83226] text-[11px] font-semibold border border-[#fbd2ca]">
                      {lead.financing_status}
                    </span>
                  )}
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => onSelectLead(lead)}
                className="w-full mt-2 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-[#fbf8f3] hover:bg-[#d94336] text-[#191512] hover:text-white text-xs font-bold border border-[#ede5da] hover:border-[#d94336] transition-all group/btn shadow-xs"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>View Full Transcript & Summary</span>
                <ChevronRight className="w-3.5 h-3.5 transition-transform group-hover/btn:translate-x-0.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
