import React, { useState } from 'react';
import { Search, Filter, Phone, MapPin, DollarSign, Calendar, CheckCircle2, AlertCircle, Clock, FileText, ChevronRight } from 'lucide-react';

export default function LeadList({ leads, loading, onSelectLead, filterStatus, setFilterStatus, searchQuery, setSearchQuery, onStatusChange }) {
  const statusOptions = [
    { label: 'All Leads', value: 'all' },
    { label: 'Qualified', value: 'qualified', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
    { label: 'Needs Follow-up', value: 'needs_followup', color: 'bg-amber-500/10 text-amber-400 border-amber-500/30' },
    { label: 'New', value: 'new', color: 'bg-blue-500/10 text-blue-400 border-blue-500/30' },
    { label: 'Not Interested', value: 'not_interested', color: 'bg-slate-500/10 text-slate-400 border-slate-500/30' },
  ];

  const getStatusBadge = (status) => {
    switch (status) {
      case 'qualified':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"><CheckCircle2 className="w-3 h-3" /> Qualified</span>;
      case 'needs_followup':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30"><Clock className="w-3 h-3" /> Needs Follow-up</span>;
      case 'not_interested':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-500/15 text-slate-400 border border-slate-500/30">Not Interested</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/15 text-blue-400 border border-blue-500/30">New</span>;
    }
  };

  const formatPrice = (val) => {
    if (!val) return 'Flexible';
    return `$${val.toLocaleString()}`;
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Buyer Leads & Qualification</h2>
          <p className="text-sm text-slate-400">Captured and qualified in real-time by voice agent Riya</p>
        </div>

        {/* Search input */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search name, phone, location..."
            className="w-full pl-10 pr-4 py-2 bg-slate-900/80 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {statusOptions.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setFilterStatus(opt.value)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-medium border transition-all whitespace-nowrap ${
              filterStatus === opt.value
                ? 'bg-indigo-600 border-indigo-500 text-white shadow-md shadow-indigo-600/20'
                : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Leads Grid / Table */}
      {loading ? (
        <div className="text-center py-16 text-slate-400">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p>Loading buyer leads...</p>
        </div>
      ) : leads.length === 0 ? (
        <div className="text-center py-16 glass-card rounded-2xl border border-slate-800">
          <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-3 text-slate-400">
            <Filter className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-200">No leads found</h3>
          <p className="text-sm text-slate-400 mt-1 max-w-sm mx-auto">
            No leads match your current search and filter settings. Click "Live Mic Tester" to trigger a voice qualification call.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {leads.map((lead) => (
            <div
              key={lead.id}
              className="glass-card rounded-2xl p-5 border border-slate-800/80 hover:border-indigo-500/40 flex flex-col justify-between group"
            >
              <div>
                {/* Header: Name & Status */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div>
                    <h3 className="font-semibold text-base text-white group-hover:text-indigo-300 transition-colors">
                      {lead.name}
                    </h3>
                    <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-0.5">
                      <Phone className="w-3 h-3 text-slate-500" />
                      <span>{lead.phone}</span>
                    </div>
                  </div>
                  <div>{getStatusBadge(lead.status)}</div>
                </div>

                {/* Key Qualification Metrics */}
                <div className="space-y-2 py-2 border-y border-slate-800/60 my-3 text-xs">
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="flex items-center gap-1.5 text-slate-400">
                      <DollarSign className="w-3.5 h-3.5 text-indigo-400" />
                      Budget
                    </span>
                    <span className="font-semibold text-indigo-300">
                      {lead.budget_min ? `${formatPrice(lead.budget_min)} - ` : 'Up to '}
                      {formatPrice(lead.budget_max)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-slate-300">
                    <span className="flex items-center gap-1.5 text-slate-400">
                      <MapPin className="w-3.5 h-3.5 text-indigo-400" />
                      Location
                    </span>
                    <span className="font-medium text-slate-200">{lead.preferred_location || 'Not specified'}</span>
                  </div>

                  <div className="flex items-center justify-between text-slate-300">
                    <span className="flex items-center gap-1.5 text-slate-400">
                      <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                      Timeline
                    </span>
                    <span className="font-medium text-slate-200">{lead.timeline || 'Not specified'}</span>
                  </div>
                </div>

                {/* Badges: BHK & Financing */}
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {lead.bhk_preference && (
                    <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 text-[11px] font-medium border border-slate-700">
                      {lead.bhk_preference}
                    </span>
                  )}
                  {lead.financing_status && (
                    <span className="px-2 py-0.5 rounded-md bg-indigo-950/40 text-indigo-300 text-[11px] font-medium border border-indigo-800/40">
                      {lead.financing_status}
                    </span>
                  )}
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => onSelectLead(lead)}
                className="w-full mt-2 flex items-center justify-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800/90 hover:bg-indigo-600 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700/60 hover:border-indigo-500 transition-all group/btn"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>View Transcript & AI Summary</span>
                <ChevronRight className="w-3.5 h-3.5 transition-transform group-hover/btn:translate-x-0.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
