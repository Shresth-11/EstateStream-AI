import time
from typing import Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas import ChatRequest, ChatResponse
from backend.services.conversation_service import create_conversation, generate_llm_summary
from backend.models import ConversationOutcome
from voice.agent import AgentSession

router = APIRouter(prefix="/api/chat", tags=["Text Chat Agent"])

# In-memory active chat sessions
active_chat_sessions: Dict[str, AgentSession] = {}
session_start_times: Dict[str, float] = {}


@router.post("", response_model=ChatResponse)
async def chat_with_agent(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Text-based qualification chat endpoint.
    Processes user turns, triggers function calling against PostgreSQL/SQLite,
    and saves the conversation record on conclusion.
    """
    session_id = payload.session_id or "default"
    
    if session_id not in active_chat_sessions:
        session = AgentSession(
            session_id=session_id,
            caller_phone=payload.caller_phone or "+15551234567",
            caller_name=payload.caller_name or "Prospective Buyer",
        )
        # Pre-seed initial greeting in conversation
        await session.get_initial_greeting()
        active_chat_sessions[session_id] = session
        session_start_times[session_id] = time.time()
    else:
        session = active_chat_sessions[session_id]

    turn_result = await session.process_user_turn(
        user_text=payload.message,
        db=db,
    )

    # If call ended or escalated, persist conversation and clean up session
    if turn_result["call_ended"]:
        duration = int(time.time() - session_start_times.get(session_id, time.time()))
        transcript = session.get_transcript()
        
        # Determine outcome
        outcome = ConversationOutcome.QUALIFIED.value if turn_result.get("lead_saved") else ConversationOutcome.INCOMPLETE.value
        if turn_result.get("escalated"):
            outcome = ConversationOutcome.ESCALATED.value

        summary_data = await generate_llm_summary(transcript)
        lead_id = session.captured_lead.id if session.captured_lead else None

        await create_conversation(
            db=db,
            transcript=transcript,
            lead_id=lead_id,
            summary=summary_data.get("summary"),
            outcome=summary_data.get("outcome", outcome),
            duration_seconds=max(duration, 15),
        )

        # Remove from active sessions
        active_chat_sessions.pop(session_id, None)
        session_start_times.pop(session_id, None)

    return ChatResponse(
        session_id=session_id,
        reply=turn_result["reply"],
        tools_called=turn_result["tools_called"],
        lead_saved=turn_result.get("lead_saved"),
        call_ended=turn_result["call_ended"],
        escalated=turn_result["escalated"],
    )
