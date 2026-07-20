from typing import Any, Dict, List, Optional
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.models import Lead, LeadStatus


async def save_lead(
    db: AsyncSession,
    name: str,
    phone: str,
    budget_min: Optional[float] = None,
    budget_max: Optional[float] = None,
    preferred_location: Optional[str] = None,
    bhk_preference: Optional[str] = None,
    timeline: Optional[str] = None,
    financing_status: Optional[str] = None,
    status: Optional[str] = None,
) -> Lead:
    """
    Persists or updates lead details. If a lead with the same phone exists,
    updates their preferences and details.
    """
    # Clean phone
    clean_phone = phone.strip() if phone else "+15550000000"
    
    # Check if lead exists
    stmt = select(Lead).where(Lead.phone == clean_phone)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()

    # Determine status: if budget, location, and timeline exist, it's qualified
    calculated_status = status or LeadStatus.NEW.value
    if budget_max and preferred_location and (timeline or financing_status):
        calculated_status = LeadStatus.QUALIFIED.value
    elif not status and (budget_max or preferred_location):
        calculated_status = LeadStatus.NEEDS_FOLLOWUP.value

    if lead:
        if name and name.strip() and name != "Prospective Buyer":
            lead.name = name.strip()
        if budget_min is not None:
            lead.budget_min = budget_min
        if budget_max is not None:
            lead.budget_max = budget_max
        if preferred_location:
            lead.preferred_location = preferred_location
        if bhk_preference:
            lead.bhk_preference = bhk_preference
        if timeline:
            lead.timeline = timeline
        if financing_status:
            lead.financing_status = financing_status
        lead.status = calculated_status
    else:
        lead = Lead(
            name=name.strip() if name and name.strip() else "Prospective Buyer",
            phone=clean_phone,
            budget_min=budget_min,
            budget_max=budget_max,
            preferred_location=preferred_location,
            bhk_preference=bhk_preference,
            timeline=timeline,
            financing_status=financing_status,
            status=calculated_status,
        )
        db.add(lead)

    await db.flush()
    await db.refresh(lead)
    return lead


async def get_leads(
    db: AsyncSession,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Lead]:
    stmt = select(Lead).options(selectinload(Lead.conversations)).order_by(Lead.created_at.desc())

    conditions = []
    if status and status.lower() != "all":
        conditions.append(Lead.status == status.lower())

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        conditions.append(
            or_(
                Lead.name.ilike(term),
                Lead.phone.ilike(term),
                Lead.preferred_location.ilike(term),
            )
        )

    if conditions:
        from sqlalchemy import and_
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_lead_by_id(db: AsyncSession, lead_id: int) -> Optional[Lead]:
    stmt = select(Lead).options(selectinload(Lead.conversations)).where(Lead.id == lead_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
