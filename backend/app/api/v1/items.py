import math
import os
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import (
    APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
)
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_current_user_optional, get_db
from app.core.config import settings
from app.models.category import Category, Subcategory
from app.models.contact import ContactRequest
from app.models.item import FoundItem, ItemImage, ItemStatusHistory
from app.models.location import CampusLocation
from app.models.user import User
from app.schemas.item import (
    FoundItemCardOut, FoundItemDetailOut, FoundItemUpdate,
    ItemCategorySummary, ItemImageOut, ItemLocationSummary,
    ItemReporterSummary, ItemStatusHistoryOut, ItemStatusUpdate,
    ItemSubcategorySummary, PaginatedItemsOut
)

router = APIRouter(prefix="/items", tags=["Found Items"])

ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_FILE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def get_primary_image_path(item: FoundItem) -> Optional[str]:
    for img in item.images:
        if img.is_primary:
            return img.image_path
    if item.images:
        return item.images[0].image_path
    return None


@router.get("", response_model=PaginatedItemsOut)
def search_items(
    location_id: Optional[int] = Query(None, description="Campus Location ID"),
    category_id: Optional[int] = Query(None, description="Category ID"),
    subcategory_id: Optional[int] = Query(None, description="Subcategory ID"),
    q: Optional[str] = Query(None, description="Search keyword in title or description"),
    quantity: Optional[int] = Query(None, description="Filter by quantity"),
    date_from: Optional[datetime] = Query(None, description="Found date starting from"),
    date_to: Optional[datetime] = Query(None, description="Found date up to"),
    sort: str = Query("newest", pattern="^(newest|oldest|category|location)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    query = db.query(FoundItem).filter(FoundItem.status == "available")

    if location_id:
        query = query.filter(FoundItem.location_id == location_id)
    if category_id:
        query = query.filter(FoundItem.category_id == category_id)
    if subcategory_id:
        query = query.filter(FoundItem.subcategory_id == subcategory_id)
    if quantity:
        query = query.filter(FoundItem.quantity == quantity)
    if date_from:
        query = query.filter(FoundItem.found_at >= date_from)
    if date_to:
        query = query.filter(FoundItem.found_at <= date_to)
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                FoundItem.title.ilike(term),
                FoundItem.description.ilike(term),
                FoundItem.reference_code.ilike(term),
            )
        )

    # Sorting
    if sort == "newest":
        query = query.order_by(FoundItem.found_at.desc(), FoundItem.id.desc())
    elif sort == "oldest":
        query = query.order_by(FoundItem.found_at.asc(), FoundItem.id.asc())
    elif sort == "category":
        query = query.join(FoundItem.category).order_by(Category.name.asc(), FoundItem.found_at.desc())
    elif sort == "location":
        query = query.join(FoundItem.location).order_by(CampusLocation.name.asc(), FoundItem.found_at.desc())

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    items_page = query.offset((page - 1) * page_size).limit(page_size).all()

    card_list = []
    for item in items_page:
        card = FoundItemCardOut(
            id=item.id,
            reference_code=item.reference_code,
            title=item.title,
            description=item.description[:180] + ("..." if len(item.description) > 180 else ""),
            category=ItemCategorySummary.model_validate(item.category),
            subcategory=ItemSubcategorySummary.model_validate(item.subcategory) if item.subcategory else None,
            location=ItemLocationSummary.model_validate(item.location),
            found_at=item.found_at,
            quantity=item.quantity,
            condition=item.condition,
            status=item.status,
            created_at=item.created_at,
            primary_image=get_primary_image_path(item),
        )
        card_list.append(card)

    return PaginatedItemsOut(
        items=card_list,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{reference_code}", response_model=FoundItemDetailOut)
def get_item_detail(
    reference_code: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    item = db.query(FoundItem).filter(FoundItem.reference_code == reference_code).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with reference code '{reference_code}' was not found.",
        )

    is_owner = False
    if current_user and current_user.id == item.reporter_id:
        is_owner = True

    if item.status != "available" and not is_owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Found item listing not found.")

    contact_count = (
        db.query(ContactRequest).filter(ContactRequest.item_id == item.id).count()
        if is_owner
        else None
    )

    return FoundItemDetailOut(
        id=item.id,
        reference_code=item.reference_code,
        title=item.title,
        description=item.description,
        category=ItemCategorySummary.model_validate(item.category),
        subcategory=ItemSubcategorySummary.model_validate(item.subcategory) if item.subcategory else None,
        location=ItemLocationSummary.model_validate(item.location),
        reporter=ItemReporterSummary.model_validate(item.reporter),
        found_at=item.found_at,
        quantity=item.quantity,
        condition=item.condition,
        status=item.status,
        created_at=item.created_at,
        updated_at=item.updated_at,
        resolved_at=item.resolved_at,
        images=[ItemImageOut.model_validate(img) for img in item.images],
        contact_count=contact_count,
        is_owner=is_owner,
    )


@router.post("", response_model=FoundItemDetailOut, status_code=status.HTTP_201_CREATED)
async def create_found_item(
    title: str = Form(..., min_length=3, max_length=200),
    description: str = Form(..., min_length=10),
    category_id: int = Form(...),
    location_id: int = Form(...),
    found_at: str = Form(..., description="ISO 8601 string or YYYY-MM-DDTHH:MM"),
    quantity: int = Form(1, ge=1),
    subcategory_id: Optional[int] = Form(None),
    condition: Optional[str] = Form(None),
    image: UploadFile = File(..., description="At least one image is mandatory"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate category & location exist
    cat = db.query(Category).filter(Category.id == category_id, Category.is_active.is_(True)).first()
    if not cat:
        raise HTTPException(status_code=400, detail="Invalid or inactive Category selected.")
    
    loc = db.query(CampusLocation).filter(CampusLocation.id == location_id, CampusLocation.is_active.is_(True)).first()
    if not loc:
        raise HTTPException(status_code=400, detail="Invalid or inactive Campus Location selected.")

    if subcategory_id:
        sub = db.query(Subcategory).filter(
            Subcategory.id == subcategory_id,
            Subcategory.category_id == category_id,
            Subcategory.is_active.is_(True),
        ).first()
        if not sub:
            raise HTTPException(status_code=400, detail="Invalid Subcategory for the selected Category.")

    # Parse found_at
    try:
        found_datetime = datetime.fromisoformat(found_at.replace("Z", "+00:00"))
        # Strip timezone info if present to store clean naive UTC in MySQL
        found_datetime = found_datetime.replace(tzinfo=None)
    except Exception:
        try:
            found_datetime = datetime.strptime(found_at[:16], "%Y-%m-%dT%H:%M")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid date format for found_at. Use YYYY-MM-DDTHH:MM.")

    # Validate image file
    content_type = image.content_type
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type '{content_type}'. Allowed types: JPEG, PNG, WebP.",
        )

    file_bytes = await image.read()
    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )
    if len(file_bytes) < 100:
        raise HTTPException(status_code=400, detail="Uploaded file is empty or corrupted.")

    # Generate safe unique filename
    ext = ALLOWED_IMAGE_TYPES[content_type]
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    upload_rel_path = f"user_uploads/{safe_filename}"
    upload_abs_path = os.path.join(settings.UPLOAD_DIR, "user_uploads", safe_filename)
    os.makedirs(os.path.dirname(upload_abs_path), exist_ok=True)

    with open(upload_abs_path, "wb") as f:
        f.write(file_bytes)

    # Generate unique human-readable reference code
    year = datetime.utcnow().year
    count_today = db.query(FoundItem).count() + 1
    ref_code = f"FI-{year}-{count_today:06d}"
    while db.query(FoundItem).filter(FoundItem.reference_code == ref_code).first():
        count_today += 1
        ref_code = f"FI-{year}-{count_today:06d}"

    item = FoundItem(
        reference_code=ref_code,
        title=title.strip(),
        description=description.strip(),
        category_id=category_id,
        subcategory_id=subcategory_id,
        location_id=location_id,
        reporter_id=current_user.id,
        found_at=found_datetime,
        quantity=quantity,
        condition=condition.strip() if condition else None,
        status="available",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(item)
    db.flush()

    item_image = ItemImage(
        item_id=item.id,
        image_path=upload_rel_path,
        original_filename=image.filename or safe_filename,
        is_primary=True,
        uploaded_at=datetime.utcnow(),
    )
    db.add(item_image)
    db.commit()
    db.refresh(item)

    return FoundItemDetailOut(
        id=item.id,
        reference_code=item.reference_code,
        title=item.title,
        description=item.description,
        category=ItemCategorySummary.model_validate(item.category),
        subcategory=ItemSubcategorySummary.model_validate(item.subcategory) if item.subcategory else None,
        location=ItemLocationSummary.model_validate(item.location),
        reporter=ItemReporterSummary.model_validate(item.reporter),
        found_at=item.found_at,
        quantity=item.quantity,
        condition=item.condition,
        status=item.status,
        created_at=item.created_at,
        updated_at=item.updated_at,
        resolved_at=item.resolved_at,
        images=[ItemImageOut.model_validate(img) for img in item.images],
        contact_count=0,
        is_owner=True,
    )


@router.patch("/{item_id}", response_model=FoundItemDetailOut)
def update_item(
    item_id: int,
    item_in: FoundItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(FoundItem).filter(FoundItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    if item.reporter_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You can only edit your own listings.")

    target_category_id = item_in.category_id if item_in.category_id is not None else item.category_id
    if item_in.category_id is not None and not db.query(Category).filter(
        Category.id == item_in.category_id,
        Category.is_active.is_(True),
    ).first():
        raise HTTPException(status_code=400, detail="Invalid or inactive Category selected.")
    if item_in.location_id is not None and not db.query(CampusLocation).filter(
        CampusLocation.id == item_in.location_id,
        CampusLocation.is_active.is_(True),
    ).first():
        raise HTTPException(status_code=400, detail="Invalid or inactive Campus Location selected.")

    if "subcategory_id" in item_in.model_fields_set and item_in.subcategory_id is not None:
        subcategory = db.query(Subcategory).filter(
            Subcategory.id == item_in.subcategory_id,
            Subcategory.category_id == target_category_id,
            Subcategory.is_active.is_(True),
        ).first()
        if not subcategory:
            raise HTTPException(status_code=400, detail="Invalid Subcategory for the selected Category.")

    if item_in.title is not None:
        item.title = item_in.title.strip()
    if item_in.description is not None:
        item.description = item_in.description.strip()
    if item_in.category_id is not None:
        item.category_id = item_in.category_id
    if "subcategory_id" in item_in.model_fields_set:
        item.subcategory_id = item_in.subcategory_id
    elif item_in.category_id is not None and item.subcategory and item.subcategory.category_id != target_category_id:
        item.subcategory_id = None
    if item_in.location_id is not None:
        item.location_id = item_in.location_id
    if item_in.found_at is not None:
        item.found_at = item_in.found_at.replace(tzinfo=None)
    if item_in.quantity is not None:
        item.quantity = item_in.quantity
    if "condition" in item_in.model_fields_set:
        item.condition = item_in.condition.strip() if item_in.condition else None

    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)

    contact_count = db.query(ContactRequest).filter(ContactRequest.item_id == item.id).count()

    return FoundItemDetailOut(
        id=item.id,
        reference_code=item.reference_code,
        title=item.title,
        description=item.description,
        category=ItemCategorySummary.model_validate(item.category),
        subcategory=ItemSubcategorySummary.model_validate(item.subcategory) if item.subcategory else None,
        location=ItemLocationSummary.model_validate(item.location),
        reporter=ItemReporterSummary.model_validate(item.reporter),
        found_at=item.found_at,
        quantity=item.quantity,
        condition=item.condition,
        status=item.status,
        created_at=item.created_at,
        updated_at=item.updated_at,
        resolved_at=item.resolved_at,
        images=[ItemImageOut.model_validate(img) for img in item.images],
        contact_count=contact_count,
        is_owner=True,
    )


@router.patch("/{item_id}/status", response_model=FoundItemDetailOut)
def update_item_status(
    item_id: int,
    status_in: ItemStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(FoundItem).filter(FoundItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    if item.reporter_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You can only change status of your own listings.")

    new_status = status_in.status.lower()
    if new_status not in {"available", "returned", "removed"}:
        raise HTTPException(status_code=400, detail="Allowed status values: 'available', 'returned', 'removed'.")

    old_status = item.status
    if old_status == new_status:
        # No-op
        contact_count = db.query(ContactRequest).filter(ContactRequest.item_id == item.id).count()
        return FoundItemDetailOut(
            id=item.id,
            reference_code=item.reference_code,
            title=item.title,
            description=item.description,
            category=ItemCategorySummary.model_validate(item.category),
            subcategory=ItemSubcategorySummary.model_validate(item.subcategory) if item.subcategory else None,
            location=ItemLocationSummary.model_validate(item.location),
            reporter=ItemReporterSummary.model_validate(item.reporter),
            found_at=item.found_at,
            quantity=item.quantity,
            condition=item.condition,
            status=item.status,
            created_at=item.created_at,
            updated_at=item.updated_at,
            resolved_at=item.resolved_at,
            images=[ItemImageOut.model_validate(img) for img in item.images],
            contact_count=contact_count,
            is_owner=True,
        )

    # Transactional update
    item.status = new_status
    item.updated_at = datetime.utcnow()
    if new_status in {"returned", "removed"}:
        item.resolved_at = datetime.utcnow()
    else:
        item.resolved_at = None

    history = ItemStatusHistory(
        item_id=item.id,
        changed_by_user_id=current_user.id,
        old_status=old_status,
        new_status=new_status,
        note=status_in.note or f"Status changed from {old_status} to {new_status} by {current_user.full_name}",
        created_at=datetime.utcnow(),
    )
    db.add(history)
    db.commit()
    db.refresh(item)

    contact_count = db.query(ContactRequest).filter(ContactRequest.item_id == item.id).count()

    return FoundItemDetailOut(
        id=item.id,
        reference_code=item.reference_code,
        title=item.title,
        description=item.description,
        category=ItemCategorySummary.model_validate(item.category),
        subcategory=ItemSubcategorySummary.model_validate(item.subcategory) if item.subcategory else None,
        location=ItemLocationSummary.model_validate(item.location),
        reporter=ItemReporterSummary.model_validate(item.reporter),
        found_at=item.found_at,
        quantity=item.quantity,
        condition=item.condition,
        status=item.status,
        created_at=item.created_at,
        updated_at=item.updated_at,
        resolved_at=item.resolved_at,
        images=[ItemImageOut.model_validate(img) for img in item.images],
        contact_count=contact_count,
        is_owner=True,
    )


@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(FoundItem).filter(FoundItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    if item.reporter_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You can only remove your own listings.")

    old_status = item.status
    item.status = "removed"
    item.resolved_at = datetime.utcnow()
    item.updated_at = datetime.utcnow()

    history = ItemStatusHistory(
        item_id=item.id,
        changed_by_user_id=current_user.id,
        old_status=old_status,
        new_status="removed",
        note=f"Listing removed/archived by owner {current_user.full_name}",
        created_at=datetime.utcnow(),
    )
    db.add(history)
    db.commit()

    return {"message": "Listing successfully archived and removed from search.", "status": "removed"}
