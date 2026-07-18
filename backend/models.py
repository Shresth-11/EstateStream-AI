import enum
from datetime import datetime
from typing import Any, List, Optional
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.database import Base


class LeadStatus(str, enum.Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    NEEDS_FOLLOWUP = "needs_followup"
    NOT_INTERESTED = "not_interested"


class ConversationOutcome(str, enum.Enum):
    QUALIFIED = "qualified"
    DROPPED = "dropped"
    ESCALATED = "escalated"
    INCOMPLETE = "incomplete"


class Property(Base):
    """Real estate property listing."""
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    bhk_config: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # JSON type supports both PostgreSQL JSONB and SQLite JSON transparently
    amenities: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "location": self.location,
            "price": self.price,
            "bhk_config": self.bhk_config,
            "description": self.description,
            "amenities": self.amenities or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Lead(Base):
    """Prospective buyer qualified or contacted by the voice agent."""
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    budget_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    budget_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    preferred_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bhk_preference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    timeline: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    financing_status: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=LeadStatus.NEW.value, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="lead",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        conv_count = 0
        if "conversations" in self.__dict__ and self.conversations:
            conv_count = len(self.conversations)
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "budget_min": self.budget_min,
            "budget_max": self.budget_max,
            "preferred_location": self.preferred_location,
            "bhk_preference": self.bhk_preference,
            "timeline": self.timeline,
            "financing_status": self.financing_status,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "conversations_count": conv_count,
        }


class Conversation(Base):
    """Call session turn-by-turn logs and qualification summaries."""
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    lead_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("leads.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    transcript: Mapped[List[dict]] = mapped_column(JSON, nullable=False, default=list)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome: Mapped[str] = mapped_column(String(50), default=ConversationOutcome.INCOMPLETE.value, index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead: Mapped[Optional["Lead"]] = relationship("Lead", back_populates="conversations")

    def to_dict(self) -> dict:
        lead_dict = None
        if "lead" in self.__dict__ and self.lead:
            lead_dict = self.lead.to_dict()
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "transcript": self.transcript or [],
            "summary": self.summary,
            "outcome": self.outcome,
            "duration_seconds": self.duration_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "lead": lead_dict,
        }
