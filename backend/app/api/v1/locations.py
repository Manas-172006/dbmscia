from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.location import CampusLocation
from app.schemas.location import CampusLocationOut

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("", response_model=List[CampusLocationOut])
def get_locations(db: Session = Depends(get_db)):
    locations = (
        db.query(CampusLocation)
        .filter(CampusLocation.is_active.is_(True))
        .order_by(CampusLocation.name.asc())
        .all()
    )
    return [CampusLocationOut.model_validate(loc) for loc in locations]
