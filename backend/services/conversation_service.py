import json
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.models import Conversation, ConversationOutcome, Lead, LeadStatus, normalize_outcome
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


async def create_conversation(
    db: AsyncSession,
    transcript: List[Dict[str, Any]],
    lead_id: Optional[int] = None,
    summary: Optional[str] = None,
    outcome: Optional[str] = None,
    duration_seconds: int = 0,
) -> Conversation:
    """Creates a conversation record linked to an optional lead."""
    conv = Conversation(
        lead_id=lead_id,
        transcript=transcript or [],
        summary=summary,
        outcome=normalize_outcome(outcome),
        duration_seconds=duration_seconds,
    )
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    return conv


async def get_conversations(
    db: AsyncSession,
    lead_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Conversation]:
    stmt = select(Conversation).options(selectinload(Conversation.lead)).order_by(Conversation.created_at.desc())
    if lead_id:
        stmt = stmt.where(Conversation.lead_id == lead_id)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_conversation_by_id(db: AsyncSession, conv_id: int) -> Optional[Conversation]:
    stmt = select(Conversation).options(selectinload(Conversation.lead)).where(Conversation.id == conv_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def generate_structured_summary_heuristic(transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Rule-based summary used when no OpenAI key is configured or the LLM call fails.
    Only the CALLER's words drive the outcome; Riya's own scripted phrases
    ("looking for", "advisor") used to mark every call as qualified/escalated.
    """
    user_turns = [t.get("content", "") for t in transcript if t.get("role") == "user"]
    real_user_turns = [u for u in user_turns if u and u.strip() not in ("[silence]", "SILENCE_TIMEOUT")]

    if not real_user_turns:
        return {
            "summary": "• Caller connected but did not speak.\n• No qualification data captured.",
            "outcome": ConversationOutcome.DROPPED.value,
        }

    caller_text = " ".join(real_user_turns).lower()
    bullets = [f"Caller spoke {len(real_user_turns)} time(s)."]
    if any(w in caller_text for w in ["bhk", "bedroom", "bed "]):
        bullets.append("Caller specified a bedroom/BHK preference.")
    if any(w in caller_text for w in ["$", "budget", "k ", "thousand", "million", "lakh", "crore"]):
        bullets.append("Budget was discussed.")
    if any(w in caller_text for w in ["not interested", "already bought", "purchased another", "no thanks"]):
        outcome = ConversationOutcome.NOT_INTERESTED.value
    else:
        outcome = ConversationOutcome.INCOMPLETE.value
    return {"summary": "\n".join(f"• {b}" for b in bullets), "outcome": outcome}


def resolve_outcome(summary_outcome: Optional[str], escalated: bool, lead_captured: bool, has_user_speech: bool) -> str:
    """
    Hard facts from the session outrank the summarizer's opinion:
    escalation > no speech (dropped) > lead captured (qualified) > summarizer.
    """
    if escalated:
        return ConversationOutcome.ESCALATED.value
    if not has_user_speech:
        return ConversationOutcome.DROPPED.value
    if lead_captured:
        return ConversationOutcome.QUALIFIED.value
    out = normalize_outcome(summary_outcome)
    # Without a saved lead the call cannot be "qualified" or "escalated".
    if out in (ConversationOutcome.QUALIFIED.value, ConversationOutcome.ESCALATED.value):
        return ConversationOutcome.INCOMPLETE.value
    return out


async def persist_session(db: AsyncSession, agent, duration_seconds: int) -> Conversation:
    """Single post-call persistence path shared by browser WS, Twilio WS and text chat."""
    transcript = agent.get_transcript()
    has_user_speech = any(
        t.get("role") == "user" and t.get("content", "").strip() not in ("", "[silence]", "SILENCE_TIMEOUT")
        for t in transcript
    )
    summary_info = await generate_llm_summary(transcript) if has_user_speech else generate_structured_summary_heuristic(transcript)
    outcome = resolve_outcome(
        summary_info.get("outcome"),
        escalated=agent.escalated,
        lead_captured=agent.captured_lead is not None,
        has_user_speech=has_user_speech,
    )
    summary = summary_info.get("summary") or ""
    if isinstance(summary, list):  # LLM sometimes returns bullets as a JSON array
        summary = "\n".join(f"• {b}" for b in summary)
    if agent.escalated and agent.escalation_reason:
        summary = f"{summary}\n• Escalated: {agent.escalation_reason}".strip()
    return await create_conversation(
        db=db,
        transcript=transcript,
        lead_id=agent.captured_lead.id if agent.captured_lead else None,
        summary=summary,
        outcome=outcome,
        duration_seconds=max(int(duration_seconds), 1),
    )


async def generate_llm_summary(transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Uses OpenAI GPT-4o if API key is present; otherwise falls back to the structured heuristic.
    """
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("your_") or not transcript:
        return generate_structured_summary_heuristic(transcript)

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY, timeout=20.0, max_retries=1)
        
        prompt = (
            "You are an executive real-estate assistant reviewing a voice call transcript.\n"
            "Analyze the following call transcript between the agent Riya and the prospective buyer.\n"
            "Return a JSON object with two fields:\n"
            "1. 'summary': A single string containing a concise 3-4 bullet point summary (e.g. • Buyer looking for... • Budget: ... • Outcome: ...)\n"
            "2. 'outcome': Must be exactly one of: 'qualified', 'dropped', 'escalated', 'incomplete', or 'not_interested'.\n\n"
            f"Transcript:\n{json.dumps(transcript, indent=2)}"
        )
        
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        parsed = json.loads(response.choices[0].message.content)
        return {
            "summary": parsed.get("summary", ""),
            "outcome": normalize_outcome(parsed.get("outcome")),
        }
    except Exception as e:
        logger.warning(f"LLM summary failed, using heuristic: {e}")
        # Graceful fallback if network/API fails
        return generate_structured_summary_heuristic(transcript)
