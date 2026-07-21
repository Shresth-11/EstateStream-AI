import pytest
from backend.database import AsyncSessionLocal, init_db
from backend.services.property_service import search_properties
from backend.services.lead_service import save_lead, get_lead_by_id
from backend.models import LeadStatus, ConversationOutcome
from voice.agent import AgentSession
from voice.llm_client import MockLLMClient, ToolCall


@pytest.mark.asyncio
async def test_search_properties():
    await init_db()
    async with AsyncSessionLocal() as db:
        # Search for Downtown properties under $600k
        results = await search_properties(db, location="Downtown", budget_max=600000.0, bhk="2")
        assert isinstance(results, list)
        assert len(results) > 0
        for p in results:
            assert p["price"] <= 650000.0
            assert "downtown" in p["location"].lower()


@pytest.mark.asyncio
async def test_save_lead():
    await init_db()
    async with AsyncSessionLocal() as db:
        lead = await save_lead(
            db=db,
            name="Alice Walker",
            phone="+15554321098",
            budget_min=400000.0,
            budget_max=650000.0,
            preferred_location="Midtown",
            bhk_preference="2 BHK",
            timeline="2 months",
            financing_status="Pre-approved",
        )
        await db.commit()

        assert lead.id is not None
        assert lead.name == "Alice Walker"
        assert lead.phone == "+15554321098"
        assert lead.status == LeadStatus.QUALIFIED.value


@pytest.mark.asyncio
async def test_agent_turn_with_mock():
    await init_db()
    async with AsyncSessionLocal() as db:
        session = AgentSession(
            session_id="test-session-1",
            caller_phone="+15559876543",
            caller_name="Sarah Connor",
            llm_client=MockLLMClient(),
        )

        greeting = await session.get_initial_greeting()
        assert "Riya" in greeting

        # Turn 1: User asks for a 3 BHK in Downtown under $800k
        turn_1 = await session.process_user_turn(
            "I am looking for a 3 BHK in Downtown under $800,000.",
            db=db,
        )
        assert turn_1["reply"] is not None
        assert len(turn_1["tools_called"]) > 0
        assert turn_1["tools_called"][0]["name"] == "search_properties"
        assert "Downtown" in turn_1["reply"] or "match" in turn_1["reply"].lower()

        # Turn 2: User confirms and gives details
        turn_2 = await session.process_user_turn(
            "Yes please, my name is Sarah Connor, save my details.",
            db=db,
        )
        assert len(turn_2["tools_called"]) > 0
        assert turn_2["tools_called"][0]["name"] == "save_lead"
        assert session.captured_lead is not None
        assert session.captured_lead.name == "Sarah Connor"


@pytest.mark.asyncio
async def test_agent_escalation():
    await init_db()
    async with AsyncSessionLocal() as db:
        session = AgentSession(
            session_id="test-esc-session",
            caller_phone="+15550001111",
            caller_name="Demanding Caller",
            llm_client=MockLLMClient(),
        )
        res = await session.process_user_turn(
            "I demand to speak to a real person and a human broker right now!",
            db=db,
        )
        assert res["escalated"] is True
        assert res["call_ended"] is True
        assert "broker" in res["reply"].lower()
