from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.models.contact import ContactRequest
from app.models.item import FoundItem, ItemImage
from app.models.user import User

router = APIRouter(prefix="/me", tags=["User Profile & Listings"])


@router.get("/items")
def get_my_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = (
        db.query(FoundItem)
        .filter(FoundItem.reporter_id == current_user.id)
        .order_by(FoundItem.created_at.desc())
        .all()
    )

    result = []
    for item in items:
        # Get primary image
        img_path = None
        for img in item.images:
            if img.is_primary:
                img_path = img.image_path
                break
        if not img_path and item.images:
            img_path = item.images[0].image_path

        contact_count = (
            db.query(func.count(ContactRequest.id))
            .filter(ContactRequest.item_id == item.id)
            .scalar()
            or 0
        )

        result.append(
            {
                "id": item.id,
                "reference_code": item.reference_code,
                "title": item.title,
                "description": item.description,
                "category": {
                    "id": item.category.id,
                    "name": item.category.name,
                    "slug": item.category.slug,
                },
                "subcategory": {
                    "id": item.subcategory.id,
                    "name": item.subcategory.name,
                    "slug": item.subcategory.slug,
                }
                if item.subcategory
                else None,
                "location": {
                    "id": item.location.id,
                    "name": item.location.name,
                    "building_or_area": item.location.building_or_area,
                },
                "found_at": item.found_at.isoformat(),
                "quantity": item.quantity,
                "condition": item.condition,
                "status": item.status,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
                "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
                "primary_image": img_path,
                "contact_count": contact_count,
            }
        )

    return result
