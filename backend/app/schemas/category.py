from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class SubcategoryOut(BaseModel):
    id: int
    category_id: int
    name: str
    slug: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool
    subcategories: List[SubcategoryOut] = []

    model_config = ConfigDict(from_attributes=True)
