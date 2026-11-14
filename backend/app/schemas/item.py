from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ItemImageOut(BaseModel):
    id: int
    image_path: str
    original_filename: str
    is_primary: bool
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemCategorySummary(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class ItemSubcategorySummary(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class ItemLocationSummary(BaseModel):
    id: int
    name: str
    building_or_area: str

    model_config = ConfigDict(from_attributes=True)


class ItemReporterSummary(BaseModel):
    id: int
    full_name: str
    department: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FoundItemCardOut(BaseModel):
    id: int
    reference_code: str
    title: str
    description: str
    category: ItemCategorySummary
    subcategory: Optional[ItemSubcategorySummary] = None
    location: ItemLocationSummary
    found_at: datetime
    quantity: int
    condition: Optional[str] = None
    status: str
    created_at: datetime
    primary_image: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FoundItemDetailOut(BaseModel):
    id: int
    reference_code: str
    title: str
    description: str
    category: ItemCategorySummary
    subcategory: Optional[ItemSubcategorySummary] = None
    location: ItemLocationSummary
    reporter: ItemReporterSummary
    found_at: datetime
    quantity: int
    condition: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    images: List[ItemImageOut] = []
    contact_count: Optional[int] = None
    is_owner: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class PaginatedItemsOut(BaseModel):
    items: List[FoundItemCardOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class FoundItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    location_id: Optional[int] = None
    found_at: Optional[datetime] = None
    quantity: Optional[int] = Field(None, ge=1)
    condition: Optional[str] = None


class ItemStatusUpdate(BaseModel):
    status: str  # 'available', 'returned', 'removed'
    note: Optional[str] = None


class ItemStatusHistoryOut(BaseModel):
    id: int
    old_status: str
    new_status: str
    note: Optional[str] = None
    created_at: datetime
    changed_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
