import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LeadList from './components/LeadList';
import LeadDetailModal from './components/LeadDetailModal';
import PropertyCatalog from './components/PropertyCatalog';
import ConversationsView from './components/ConversationsView';
import VoiceTestModal from './components/VoiceTestModal';
import { fetchLeads } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('leads');
  const [leads, setLeads] = useState([]);
  const [loadingLeads, setLoadingLeads] = useState(true);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLead, setSelectedLead] = useState(null);
  const [isVoiceTesterOpen, setIsVoiceTesterOpen] = useState(false);

  const loadLeads = async () => {
    try {
      setLoadingLeads(true);
      const data = await fetchLeads(filterStatus, searchQuery);
      setLeads(data);
    } catch (err) {
      console.error('Failed to load leads:', err);
    } finally {
      setLoadingLeads(false);
    }
  };

  useEffect(() => {
    loadLeads();
  }, [filterStatus, searchQuery]);

  const handleLeadUpdated = (updatedLead) => {
    setLeads((prev) => prev.map((l) => (l.id === updatedLead.id ? updatedLead : l)));
    setSelectedLead(updatedLead);
  };

  return (
    <div className="min-h-screen bg-[#070a12] text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenVoiceTester={() => setIsVoiceTesterOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'leads' && (
          <LeadList
            leads={leads}
            loading={loadingLeads}
            onSelectLead={(lead) => setSelectedLead(lead)}
            filterStatus={filterStatus}
            setFilterStatus={setFilterStatus}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
          />
        )}

        {activeTab === 'properties' && <PropertyCatalog />}

        {activeTab === 'conversations' && (
          <ConversationsView onSelectLead={(lead) => setSelectedLead(lead)} />
        )}
      </main>

      {/* Lead Detail / Transcript Modal */}
      {selectedLead && (
        <LeadDetailModal
          lead={selectedLead}
          onClose={() => setSelectedLead(null)}
          onLeadUpdated={handleLeadUpdated}
        />
      )}

      {/* Voice Pipeline Test Modal */}
      <VoiceTestModal
        isOpen={isVoiceTesterOpen}
        onClose={() => setIsVoiceTesterOpen(false)}
        onCallCompleted={() => loadLeads()}
      />
    </div>
  );
}
