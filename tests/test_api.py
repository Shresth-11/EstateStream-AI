import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.database import init_db


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["agent"] == "Riya"


@pytest.mark.asyncio
async def test_get_properties():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Search properties in Downtown
        res = await client.get("/api/properties?location=Downtown")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0


@pytest.mark.asyncio
async def test_leads_crud():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create lead
        payload = {
            "name": "Marcus Vance",
            "phone": "+15558889999",
            "budget_min": 600000.0,
            "budget_max": 900000.0,
            "preferred_location": "West End",
            "bhk_preference": "3 BHK",
            "timeline": "Immediate",
            "financing_status": "Cash buyer",
            "status": "qualified",
        }
        res = await client.post("/api/leads", json=payload)
        assert res.status_code == 200
        lead_data = res.json()
        assert lead_data["name"] == "Marcus Vance"
        lead_id = lead_data["id"]

        # Get single lead
        res_single = await client.get(f"/api/leads/{lead_id}")
        assert res_single.status_code == 200
        assert res_single.json()["phone"] == "+15558889999"

        # List leads with status filter
        res_list = await client.get("/api/leads?status=qualified")
        assert res_list.status_code == 200
        assert any(l["id"] == lead_id for l in res_list.json())


@pytest.mark.asyncio
async def test_chat_endpoint_turn():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "session_id": "test-chat-turn-1",
            "message": "Hi, I am looking for a 2 BHK in Midtown around $450,000.",
            "caller_name": "David Miller",
            "caller_phone": "+15552223333",
        }
        res = await client.post("/api/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["reply"] is not None
        assert len(data["reply"]) > 0


@pytest.mark.asyncio
async def test_twilio_incoming_call_twiml():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/twilio/incoming-call")
        assert res.status_code == 200
        assert "text/xml" in res.headers["content-type"] or "application/xml" in res.headers["content-type"]
        assert "<Stream url=" in res.text
