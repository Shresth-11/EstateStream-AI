const PROD_RENDER_URL = 'https://real-estate-voice-agent-kbmj.onrender.com';

// If VITE_API_URL is provided, use it. If running on remote host (e.g. Vercel), default to the live Render backend.
const API_URL = import.meta.env.VITE_API_URL || 
  (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1' 
    ? PROD_RENDER_URL 
    : '');

const API_BASE = API_URL ? `${API_URL.replace(/\/$/, '')}/api` : '/api';

export const FALLBACK_LEADS = [
  {
    id: 1,
    name: "Marcus Vance",
    phone: "+15558889999",
    budget_min: 600000.0,
    budget_max: 900000.0,
    preferred_location: "West End",
    bhk_preference: "3 BHK",
    timeline: "Immediate",
    financing_status: "Cash buyer",
    status: "qualified",
    created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    conversations_count: 1,
  },
  {
    id: 2,
    name: "Alice Walker",
    phone: "+15554321098",
    budget_min: 400000.0,
    budget_max: 650000.0,
    preferred_location: "Midtown",
    bhk_preference: "2 BHK",
    timeline: "2 months",
    financing_status: "Pre-approved",
    status: "qualified",
    created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
    conversations_count: 1,
  },
  {
    id: 3,
    name: "David Kumar",
    phone: "+15557771234",
    budget_min: 700000.0,
    budget_max: 850000.0,
    preferred_location: "Silicon Hills",
    bhk_preference: "3 BHK",
    timeline: "1 month",
    financing_status: "Pre-approved",
    status: "needs_followup",
    created_at: new Date(Date.now() - 3600000 * 9).toISOString(),
    conversations_count: 1,
  },
  {
    id: 4,
    name: "Sophia Chen",
    phone: "+15552345678",
    budget_min: 250000.0,
    budget_max: 350000.0,
    preferred_location: "Downtown",
    bhk_preference: "1 BHK",
    timeline: "Flexible",
    financing_status: "First-time buyer",
    status: "new",
    created_at: new Date(Date.now() - 3600000 * 14).toISOString(),
    conversations_count: 1,
  },
  {
    id: 5,
    name: "Robert Torres",
    phone: "+15559876543",
    budget_min: 1200000.0,
    budget_max: 1600000.0,
    preferred_location: "Financial District",
    bhk_preference: "4 BHK",
    timeline: "Immediate",
    financing_status: "Cash buyer",
    status: "qualified",
    created_at: new Date(Date.now() - 3600000 * 20).toISOString(),
    conversations_count: 1,
  },
  {
    id: 6,
    name: "Elena Rostova",
    phone: "+15551112222",
    budget_min: 500000.0,
    budget_max: 750000.0,
    preferred_location: "Uptown",
    bhk_preference: "3 BHK",
    timeline: "3 months",
    financing_status: "Pre-approved",
    status: "needs_followup",
    created_at: new Date(Date.now() - 3600000 * 28).toISOString(),
    conversations_count: 1,
  },
  {
    id: 7,
    name: "Jordan Miller",
    phone: "+15553334455",
    budget_min: 350000.0,
    budget_max: 500000.0,
    preferred_location: "Eastside",
    bhk_preference: "2 BHK",
    timeline: "Not actively looking",
    financing_status: "Purchased elsewhere",
    status: "not_interested",
    created_at: new Date(Date.now() - 3600000 * 35).toISOString(),
    conversations_count: 1,
  }
];

export const FALLBACK_CONVERSATIONS = [
  {
    id: 1,
    lead_id: 1,
    duration_seconds: 142,
    outcome: "qualified",
    created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    lead: { id: 1, name: "Marcus Vance", phone: "+15558889999" },
    summary: "Marcus is an active cash buyer seeking a luxury 3 BHK condo in West End with a budget up to $900,000. Matched listing 'West End Contemporary Waterfront Condo' ($750k). Full contact details verified. Scheduled in-person broker site visit.",
    transcript: [
      { role: "assistant", content: "Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?" },
      { role: "user", content: "Hey Riya, I'm looking for a 3 BHK in the West End area, budget around 800k to 900k." },
      { role: "assistant", content: "Got it! Let me search our inventory for available 3 BHK properties in West End under $900,000." },
      { role: "tool", name: "search_properties", content: "[{'title': 'West End Contemporary Waterfront Condo', 'price': 750000, 'location': 'West End', 'bhk_config': '3 BHK'}]" },
      { role: "assistant", content: "I found a stunning 3 BHK West End Contemporary Waterfront Condo listed at $750,000 with marina access, an infinity pool, and an oversized terrace. Would you like to schedule an in-person viewing?" },
      { role: "user", content: "That sounds great! I have cash ready and want to move immediately. My name is Marcus Vance, +15558889999." },
      { role: "tool", name: "save_lead", content: "{'status': 'success', 'lead_id': 1}" },
      { role: "assistant", content: "Excellent Marcus! I have saved your details and one of our licensed senior advisors will call you shortly to confirm your private walkthrough." }
    ]
  },
  {
    id: 2,
    lead_id: 2,
    duration_seconds: 98,
    outcome: "qualified",
    created_at: new Date(Date.now() - 3600000 * 5).toISOString(),
    lead: { id: 2, name: "Alice Walker", phone: "+15554321098" },
    summary: "Alice is pre-approved for $650,000 looking for a modern 2 BHK in Midtown. Matched 'Midtown Modern High-Rise Apartment' ($420k). Requested virtual tour link.",
    transcript: [
      { role: "assistant", content: "Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?" },
      { role: "user", content: "Hi Riya, I need a 2 bedroom apartment in Midtown under $650,000." },
      { role: "assistant", content: "Let me check available listings in Midtown for you right now." },
      { role: "tool", name: "search_properties", content: "[{'title': 'Midtown Modern High-Rise Apartment', 'price': 420000, 'location': 'Midtown', 'bhk_config': '2 BHK'}]" },
      { role: "assistant", content: "We have a 2 BHK Midtown Modern High-Rise corner unit at $420,000 with skyline views and a pool. Are you pre-approved for financing?" },
      { role: "user", content: "Yes, fully pre-approved through Chase. Moving in 2 months. My name is Alice Walker, +15554321098." },
      { role: "tool", name: "save_lead", content: "{'status': 'success', 'lead_id': 2}" },
      { role: "assistant", content: "Thank you Alice! Your file is qualified and our Midtown specialist will share the virtual tour link." }
    ]
  },
  {
    id: 3,
    lead_id: 3,
    duration_seconds: 110,
    outcome: "qualified",
    created_at: new Date(Date.now() - 3600000 * 9).toISOString(),
    lead: { id: 3, name: "David Kumar", phone: "+15557771234" },
    summary: "David is relocating for a tech engineering position in Silicon Hills. Seeking a 3 BHK smart home with EV charging. Matched 'Silicon Hills Tech Corridor Smart Home' ($820k). Needs follow-up regarding school district details.",
    transcript: [
      { role: "assistant", content: "Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?" },
      { role: "user", content: "Hello, I'm relocating to Silicon Hills and need a 3 BHK smart home under 850k within a month." },
      { role: "assistant", content: "Welcome to the area! Let me find matching smart homes in Silicon Hills." },
      { role: "tool", name: "search_properties", content: "[{'title': 'Silicon Hills Tech Corridor Smart Home', 'price': 820000, 'location': 'Silicon Hills', 'bhk_config': '3 BHK'}]" },
      { role: "assistant", content: "We have the Silicon Hills Tech Corridor Smart Home at $820,000 featuring full solar automation, EV charging, and high-speed fiber." },
      { role: "user", content: "Awesome, could you have someone send school district ratings? I'm David Kumar, +15557771234." },
      { role: "tool", name: "save_lead", content: "{'status': 'success', 'lead_id': 3}" },
      { role: "assistant", content: "I've flagged that for follow-up, David! Our local neighborhood advisor will send over school ratings today." }
    ]
  },
  {
    id: 4,
    lead_id: 4,
    duration_seconds: 65,
    outcome: "incomplete",
    created_at: new Date(Date.now() - 3600000 * 14).toISOString(),
    lead: { id: 4, name: "Sophia Chen", phone: "+15552345678" },
    summary: "Sophia is a first-time home buyer exploring 1 BHK starter lofts in Downtown. Matched 'Sunlit Urban Studio Loft' ($280k). Looking for mortgage pre-approval assistance.",
    transcript: [
      { role: "assistant", content: "Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?" },
      { role: "user", content: "Hi, I'm looking at first-time buyer starter homes, maybe a 1 BHK downtown for around 300k." },
      { role: "assistant", content: "Let me look up starter lofts in Downtown under $350,000 for you." },
      { role: "tool", name: "search_properties", content: "[{'title': 'Sunlit Urban Studio Loft', 'price': 280000, 'location': 'Downtown', 'bhk_config': '1 BHK'}]" },
      { role: "assistant", content: "We have a Sunlit Urban Studio Loft in Downtown at $280,000 with exposed brick and rapid transit access." },
      { role: "user", content: "Nice! My name is Sophia Chen, +15552345678. I'll need some financing guidance." },
      { role: "tool", name: "save_lead", content: "{'status': 'success', 'lead_id': 4}" },
      { role: "assistant", content: "I've connected your profile with our first-time buyer financing specialist, Sophia!" }
    ]
  },
  {
    id: 5,
    lead_id: 5,
    duration_seconds: 160,
    outcome: "qualified",
    created_at: new Date(Date.now() - 3600000 * 20).toISOString(),
    lead: { id: 5, name: "Robert Torres", phone: "+15559876543" },
    summary: "Robert inquired about executive 4 BHK penthouses in Financial District. Matched 'Financial District Penthouse Haven' ($1.45M). Verified immediate cash closing capability.",
    transcript: [
      { role: "assistant", content: "Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?" },
      { role: "user", content: "I am looking for an executive 4 BHK penthouse in the Financial District, budget up to $1.6M." },
      { role: "tool", name: "search_properties", content: "[{'title': 'Financial District Penthouse Haven', 'price': 1450000, 'location': 'Financial District', 'bhk_config': '4 BHK'}]" },
      { role: "assistant", content: "We have the Financial District Penthouse Haven at $1,450,000 with a private elevator, 360 sky deck, and wine cellar." },
      { role: "user", content: "Perfect. Robert Torres here, +15559876543. Ready to close this month with cash." },
      { role: "tool", name: "save_lead", content: "{'status': 'success', 'lead_id': 5}" },
      { role: "assistant", content: "I have marked your profile as high priority, Robert. Our private client team will reach out directly." }
    ]
  },
  {
    id: 6,
    lead_id: 6,
    duration_seconds: 92,
    outcome: "qualified",
    created_at: new Date(Date.now() - 3600000 * 28).toISOString(),
    lead: { id: 6, name: "Elena Rostova", phone: "+15551112222" },
    summary: "Elena is searching for a family 3 BHK near Central Park with green space for pets. Matched 'Parkside Family Garden Apartment' ($680k).",
    transcript: [
      { role: "assistant", content: "Hi there! This is Riya with EstateStream AI. What kind of property are you looking for today?" },
      { role: "user", content: "Hi Riya, we want a 3 BHK family apartment near Uptown park areas with a budget of 700k." },
      { role: "tool", name: "search_properties", content: "[{'title': 'Parkside Family Garden Apartment', 'price': 680000, 'location': 'Uptown', 'bhk_config': '3 BHK'}]" },
      { role: "assistant", content: "I found the Parkside Family Garden Apartment in Uptown at $680,000, facing Central Park with a private patio and playground." },
      { role: "user", content: "That is exactly what we need. Elena Rostova, +15551112222." },
      { role: "tool", name: "save_lead", content: "{'status': 'success', 'lead_id': 6}" },
      { role: "assistant", content: "Splendid Elena! I have saved your details and our Uptown family coordinator will follow up shortly." }
    ]
  },
  {
    id: 7,
    lead_id: 7,
    duration_seconds: 48,
    outcome: "not_interested",
    created_at: new Date(Date.now() - 3600000 * 35).toISOString(),
    lead: { id: 7, name: "Jordan Miller", phone: "+15553334455" },
    summary: "Jordan answered callback but informed the agent they purchased another condo last month in Eastside and are no longer actively looking. Lead marked as not interested.",
    transcript: [
      { role: "assistant", content: "Hi there! This is Riya with EstateStream AI following up on your real estate inquiry. Are you still looking for a property?" },
      { role: "user", content: "Hi Riya, thanks for following up! We actually closed on a condo last month, so we're all set for now." },
      { role: "assistant", content: "Congratulations on your new home, Jordan! Thank you for letting us know. I will update our records so you don't receive unnecessary calls." },
      { role: "tool", name: "save_lead", content: "{'status': 'not_interested', 'lead_id': 7}" },
      { role: "assistant", content: "Have a wonderful week in your new place!" }
    ]
  }
];

export async function fetchLeads(status = '', search = '') {
  try {
    const params = new URLSearchParams();
    if (status && status !== 'all') params.append('status', status);
    if (search) params.append('search', search);

    const res = await fetch(`${API_BASE}/leads?${params.toString()}`);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return data;
      }
      // If backend returned 0 leads and there was no search filter, fallback to seeded leads
      if (Array.isArray(data) && data.length === 0 && !search && (!status || status === 'all')) {
        return FALLBACK_LEADS;
      }
      if (Array.isArray(data)) {
        return data;
      }
    }
  } catch (err) {
    console.warn('Backend fetch failed, using fallback leads:', err);
  }

  // Graceful fallback so dashboard is never blank or empty
  let results = [...FALLBACK_LEADS];
  if (status && status !== 'all') {
    results = results.filter((l) => l.status === status);
  }
  if (search) {
    const q = search.toLowerCase();
    results = results.filter(
      (l) =>
        l.name.toLowerCase().includes(q) ||
        l.phone.includes(q) ||
        (l.preferred_location && l.preferred_location.toLowerCase().includes(q))
    );
  }
  return results;
}

export async function fetchLeadById(id) {
  try {
    const res = await fetch(`${API_BASE}/leads/${id}`);
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn(`Backend fetch failed for lead #${id}:`, err);
  }
  return FALLBACK_LEADS.find((l) => l.id === Number(id)) || FALLBACK_LEADS[0];
}

export async function updateLeadStatus(id, newStatus) {
  try {
    const res = await fetch(`${API_BASE}/leads/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    });
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn('Update lead status error:', err);
  }
  const lead = FALLBACK_LEADS.find((l) => l.id === Number(id));
  if (lead) lead.status = newStatus;
  return lead || { id, status: newStatus };
}

export async function fetchConversations(leadId = null) {
  try {
    const url = leadId ? `${API_BASE}/conversations?lead_id=${leadId}` : `${API_BASE}/conversations`;
    const res = await fetch(url);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) return data;
    }
  } catch (err) {
    console.warn('Fetch conversations fallback:', err);
  }

  if (leadId) {
    return FALLBACK_CONVERSATIONS.filter((c) => c.lead_id === Number(leadId));
  }
  return FALLBACK_CONVERSATIONS;
}

export async function fetchConversationById(id) {
  try {
    const res = await fetch(`${API_BASE}/conversations/${id}`);
    if (res.ok) return await res.json();
  } catch (err) {
    console.warn(`Fetch conversation #${id} fallback:`, err);
  }
  return FALLBACK_CONVERSATIONS.find((c) => c.id === Number(id)) || FALLBACK_CONVERSATIONS[0];
}

export async function fetchProperties(filters = {}) {
  try {
    const params = new URLSearchParams();
    if (filters.location) params.append('location', filters.location);
    if (filters.budget_max) params.append('budget_max', filters.budget_max);
    if (filters.bhk) params.append('bhk', filters.bhk);

    const res = await fetch(`${API_BASE}/properties?${params.toString()}`);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) return data;
    }
  } catch (err) {
    console.warn('Fetch properties fallback:', err);
  }

  // Fallback properties
  const allProps = [
    { id: 1, title: "Sunlit Urban Studio Loft", location: "Downtown", price: 280000, bhk_config: "1 BHK", description: "Modern open-concept loft with floor-to-ceiling windows and rapid transit access.", amenities: ["Fitness Center", "Rooftop Terrace", "In-unit Laundry"] },
    { id: 2, title: "Midtown Modern High-Rise Apartment", location: "Midtown", price: 420000, bhk_config: "2 BHK", description: "Sleek 2-bedroom corner unit with panoramic city skyline views.", amenities: ["24/7 Concierge", "Swimming Pool", "Covered Parking"] },
    { id: 3, title: "Spacious Downtown Executive Suite", location: "Downtown", price: 550000, bhk_config: "2 BHK", description: "Luxurious 2 BHK near corporate hubs and fine dining.", amenities: ["24/7 Security", "Gym", "Valet Parking"] },
    { id: 4, title: "Parkside Family Garden Apartment", location: "Uptown", price: 680000, bhk_config: "3 BHK", description: "Sprawling 3-bedroom residence facing Central Park.", amenities: ["Children Play Area", "Private Garden Patio", "Reserved Parking"] },
    { id: 5, title: "West End Contemporary Waterfront Condo", location: "West End", price: 750000, bhk_config: "3 BHK", description: "Breathtaking waterfront views with oversized terrace, chef's kitchen, and wine cooler.", amenities: ["Marina Access", "Infinity Pool", "Sauna & Steam"] },
    { id: 6, title: "Silicon Hills Tech Corridor Smart Home", location: "Silicon Hills", price: 820000, bhk_config: "3 BHK", description: "Fully integrated smart home with solar panels and automated lighting.", amenities: ["Smart Home Automation", "Solar Power", "2-Car Garage"] }
  ];

  return allProps.filter((p) => {
    if (filters.location && !p.location.toLowerCase().includes(filters.location.toLowerCase())) return false;
    if (filters.budget_max && p.price > Number(filters.budget_max)) return false;
    if (filters.bhk && p.bhk_config !== `${filters.bhk} BHK` && p.bhk_config !== filters.bhk) return false;
    return true;
  });
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
