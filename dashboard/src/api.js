const API_URL = import.meta.env.VITE_API_URL || '';
const API_BASE = API_URL ? `${API_URL}/api` : '/api';

export async function fetchLeads(status = '', search = '') {
  const params = new URLSearchParams();
  if (status && status !== 'all') params.append('status', status);
  if (search) params.append('search', search);

  const res = await fetch(`${API_BASE}/leads?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch leads');
  return res.json();
}

export async function fetchLeadById(id) {
  const res = await fetch(`${API_BASE}/leads/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch lead #${id}`);
  return res.json();
}

export async function updateLeadStatus(id, newStatus) {
  const res = await fetch(`${API_BASE}/leads/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: newStatus }),
  });
  if (!res.ok) throw new Error('Failed to update lead');
  return res.json();
}

export async function fetchConversations(leadId = null) {
  const url = leadId ? `${API_BASE}/conversations?lead_id=${leadId}` : `${API_BASE}/conversations`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch conversations');
  return res.json();
}

export async function fetchConversationById(id) {
  const res = await fetch(`${API_BASE}/conversations/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch conversation #${id}`);
  return res.json();
}

export async function fetchProperties(filters = {}) {
  const params = new URLSearchParams();
  if (filters.location) params.append('location', filters.location);
  if (filters.budget_max) params.append('budget_max', filters.budget_max);
  if (filters.bhk) params.append('bhk', filters.bhk);

  const res = await fetch(`${API_BASE}/properties?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch properties');
  return res.json();
}

export async function sendChatMessage(message, sessionId, callerName, callerPhone) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      message: message,
      caller_name: callerName || 'Web User',
      caller_phone: callerPhone || '+15551234567',
    }),
  });
  if (!res.ok) throw new Error('Failed to communicate with agent');
  return res.json();
}
