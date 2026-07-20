import json
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.models import Conversation, ConversationOutcome, Lead, LeadStatus
from backend.config import settings


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
        outcome=outcome or ConversationOutcome.INCOMPLETE.value,
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
    Generates structured summary and outcome assessment directly from transcript.
    Used for instant real-time post-call persistence or as fallback if OpenAI key is not provided.
    """
    if not transcript:
        return {
            "summary": "Call ended without conversation turns.",
            "outcome": ConversationOutcome.DROPPED.value,
            "key_details": {},
        }

    turns = [t.get("content", "") for t in transcript if t.get("role") in ["user", "assistant"]]
    full_text = " ".join(turns).lower()

    # Determine outcome
    outcome = ConversationOutcome.INCOMPLETE.value
    if "escalate" in full_text or "advisor" in full_text or "human" in full_text:
        outcome = ConversationOutcome.ESCALATED.value
    elif any(word in full_text for word in ["budget", "looking for", "schedule", "listing", "details saved", "follow-up"]):
        outcome = ConversationOutcome.QUALIFIED.value
    elif len(transcript) <= 2:
        outcome = ConversationOutcome.DROPPED.value

    # Extract bullet points
    bullets = [
        f"Session completed with {len(transcript)} total turn(s).",
    ]
    if "bhk" in full_text:
        bullets.append("Caller specified bedroom/BHK preferences.")
    if "budget" in full_text or "$" in full_text or "k" in full_text or "thousand" in full_text:
        bullets.append("Budget parameters discussed and verified against listings.")
    if outcome == ConversationOutcome.ESCALATED.value:
        bullets.append("Escalation triggered: Caller requested human representative / legal or tax advice.")
    elif outcome == ConversationOutcome.QUALIFIED.value:
        bullets.append("Lead successfully qualified with property search performed.")
    else:
        bullets.append("Call concluded before full qualification flow was completed.")

    summary_text = "\n".join([f"• {b}" for b in bullets])

    return {
        "summary": summary_text,
        "outcome": outcome,
    }


async def generate_llm_summary(transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Uses OpenAI GPT-4o if API key is present; otherwise falls back to the structured heuristic.
    """
    if not settings.OPENAI_API_KEY or not transcript:
        return generate_structured_summary_heuristic(transcript)

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = (
            "You are an executive real-estate assistant reviewing a voice call transcript.\n"
            "Analyze the following call transcript between the agent Riya and the prospective buyer.\n"
            "Return a JSON object with two fields:\n"
            "1. 'summary': A concise 3-4 bullet point summary (e.g. • Buyer looking for... • Budget: ... • Outcome: ...)\n"
            "2. 'outcome': Must be exactly one of: 'qualified', 'dropped', 'escalated', or 'incomplete'.\n\n"
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
            "outcome": parsed.get("outcome", ConversationOutcome.QUALIFIED.value),
        }
    except Exception as e:
        # Graceful fallback if network/API fails
        return generate_structured_summary_heuristic(transcript)
