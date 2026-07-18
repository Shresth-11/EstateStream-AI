from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.models import LeadStatus, ConversationOutcome


# --- Property Schemas ---
class PropertyBase(BaseModel):
    title: str
    location: str
    price: float
    bhk_config: str
    description: str
    amenities: List[str] = Field(default_factory=list)


class PropertyCreate(PropertyBase):
    pass


class PropertyOut(PropertyBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class PropertySearchQuery(BaseModel):
    location: Optional[str] = None
    budget_max: Optional[float] = None
    bhk: Optional[str] = None


# --- Lead Schemas ---
class LeadBase(BaseModel):
    name: str
    phone: str
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    preferred_location: Optional[str] = None
    bhk_preference: Optional[str] = None
    timeline: Optional[str] = None
    financing_status: Optional[str] = None
    status: LeadStatus = LeadStatus.NEW


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    preferred_location: Optional[str] = None
    bhk_preference: Optional[str] = None
    timeline: Optional[str] = None
    financing_status: Optional[str] = None
    status: Optional[LeadStatus] = None


class LeadOut(LeadBase):
    id: int
    created_at: Optional[datetime] = None
    conversations_count: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)


# --- Conversation Schemas ---
class ConversationBase(BaseModel):
    lead_id: Optional[int] = None
    transcript: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Optional[str] = None
    outcome: ConversationOutcome = ConversationOutcome.INCOMPLETE
    duration_seconds: int = 0


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    summary: Optional[str] = None
    outcome: Optional[ConversationOutcome] = None
    duration_seconds: Optional[int] = None
    transcript: Optional[List[Dict[str, Any]]] = None


class ConversationOut(ConversationBase):
    id: int
    created_at: Optional[datetime] = None
    lead: Optional[LeadOut] = None
    model_config = ConfigDict(from_attributes=True)


# --- Chat Interaction Schemas (for Phase 2 & Test Interfaces) ---
class ChatMessage(BaseModel):
    role: str # "user", "assistant", "system", "tool"
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: Optional[str] = "default-session"
    message: str
    caller_phone: Optional[str] = "+15551234567"
    caller_name: Optional[str] = "Prospective Buyer"


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tools_called: List[Dict[str, Any]] = Field(default_factory=list)
    lead_saved: Optional[Dict[str, Any]] = None
    call_ended: bool = False
    escalated: bool = False
