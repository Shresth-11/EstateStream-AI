from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models import Property
from backend.schemas import PropertyOut
from backend.services.property_service import get_all_properties, search_properties

router = APIRouter(prefix="/api/properties", tags=["Properties"])


@router.get("", response_model=List[PropertyOut])
async def list_properties(
    location: Optional[str] = Query(None, description="Filter by location/area"),
    budget_max: Optional[float] = Query(None, description="Max budget ceiling"),
    bhk: Optional[str] = Query(None, description="BHK configuration (e.g. '2', '3 BHK')"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List or search properties with optional filtering."""
    if location or budget_max or bhk:
        results = await search_properties(db, location=location, budget_max=budget_max, bhk=bhk, limit=limit)
        return results
    return await get_all_properties(db, limit=limit, offset=offset)


@router.get("/{property_id}", response_model=PropertyOut)
async def get_property(
    property_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single property listing by ID."""
    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop
