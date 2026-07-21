from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models import Lead, LeadStatus
from backend.schemas import LeadCreate, LeadOut, LeadUpdate
from backend.services.lead_service import get_lead_by_id, get_leads, save_lead

router = APIRouter(prefix="/api/leads", tags=["Leads"])


@router.get("", response_model=List[LeadOut])
async def list_leads(
    status: Optional[str] = Query(None, description="Filter by status ('all', 'new', 'qualified', 'needs_followup', 'not_interested')"),
    search: Optional[str] = Query(None, description="Search term across name, phone, preferred_location"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all leads with optional status filter and text search."""
    return await get_leads(db, status=status, search=search, limit=limit, offset=offset)


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a single lead by ID."""
    lead = await get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("", response_model=LeadOut)
async def create_or_update_lead(
    payload: LeadCreate,
    db: AsyncSession = Depends(get_db),
):
    """Manually persist or update a lead."""
    lead = await save_lead(
        db,
        name=payload.name,
        phone=payload.phone,
        budget_min=payload.budget_min,
        budget_max=payload.budget_max,
        preferred_location=payload.preferred_location,
        bhk_preference=payload.bhk_preference,
        timeline=payload.timeline,
        financing_status=payload.financing_status,
        status=payload.status.value if payload.status else None,
    )
    return lead


@router.patch("/{lead_id}", response_model=LeadOut)
async def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update specific fields of an existing lead."""
    lead = await get_lead_by_id(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if payload.name is not None:
        lead.name = payload.name
    if payload.phone is not None:
        lead.phone = payload.phone
    if payload.budget_min is not None:
        lead.budget_min = payload.budget_min
    if payload.budget_max is not None:
        lead.budget_max = payload.budget_max
    if payload.preferred_location is not None:
        lead.preferred_location = payload.preferred_location
    if payload.bhk_preference is not None:
        lead.bhk_preference = payload.bhk_preference
    if payload.timeline is not None:
        lead.timeline = payload.timeline
    if payload.financing_status is not None:
        lead.financing_status = payload.financing_status
    if payload.status is not None:
        lead.status = payload.status.value

    await db.commit()
    await db.refresh(lead)
    return lead
