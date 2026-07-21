from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models import Conversation
from backend.schemas import ConversationCreate, ConversationOut
from backend.services.conversation_service import (
    create_conversation,
    get_conversation_by_id,
    get_conversations,
)

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.get("", response_model=List[ConversationOut])
async def list_conversations(
    lead_id: Optional[int] = Query(None, description="Filter by associated lead ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List recent conversations with transcripts and summaries."""
    return await get_conversations(db, lead_id=lead_id, limit=limit, offset=offset)


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full conversation transcript and details by ID."""
    conv = await get_conversation_by_id(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.post("", response_model=ConversationOut)
async def record_conversation(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Store a finished conversation record."""
    conv = await create_conversation(
        db,
        transcript=payload.transcript,
        lead_id=payload.lead_id,
        summary=payload.summary,
        outcome=payload.outcome.value if payload.outcome else None,
        duration_seconds=payload.duration_seconds,
    )
    return conv
