from typing import Any, Dict, List, Optional
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import Property


async def search_properties(
    db: AsyncSession,
    location: Optional[str] = None,
    budget_max: Optional[float] = None,
    bhk: Optional[str] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Searches properties matching criteria:
    - location: substring / case-insensitive search
    - budget_max: price <= budget_max (with a 10% flexible ceiling for close matches)
    - bhk: substring match on BHK config (e.g. '2' matches '2 BHK')
    """
    stmt = select(Property)
    conditions = []

    if location and location.strip():
        loc = location.strip().lower()
        conditions.append(Property.location.ilike(f"%{loc}%"))

    if budget_max and budget_max > 0:
        # Flexible tolerance allows catching listings slightly under or at ceiling
        max_allowed = budget_max * 1.05
        conditions.append(Property.price <= max_allowed)

    if bhk and bhk.strip():
        bhk_cleaned = bhk.strip().lower()
        # If user says "2" or "2 BHK" or "2 bedroom"
        digit = "".join([c for c in bhk_cleaned if c.isdigit()])
        if digit:
            conditions.append(Property.bhk_config.ilike(f"%{digit}%"))
        else:
            conditions.append(Property.bhk_config.ilike(f"%{bhk_cleaned}%"))

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # Order by price ascending
    stmt = stmt.order_by(Property.price.asc()).limit(limit)

    result = await db.execute(stmt)
    properties = result.scalars().all()

    return [p.to_dict() for p in properties]


async def get_all_properties(
    db: AsyncSession,
    limit: int = 100,
    offset: int = 0,
) -> List[Property]:
    stmt = select(Property).order_by(Property.id.asc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_property(db: AsyncSession, prop_data: dict) -> Property:
    prop = Property(**prop_data)
    db.add(prop)
    await db.flush()
    await db.refresh(prop)
    return prop
