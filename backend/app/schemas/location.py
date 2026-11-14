from typing import Optional
from pydantic import BaseModel, ConfigDict


class CampusLocationOut(BaseModel):
    id: int
    name: str
    building_or_area: str
    description: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
