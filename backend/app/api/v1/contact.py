from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.models.contact import ContactRequest
from app.models.item import FoundItem, ItemImage
from app.models.notification import Notification
from app.models.user import User
from app.schemas.contact import (
    ContactItemBrief, ContactRequestCreate, ContactRequestOut,
    ContactRequestStatusUpdate, ContactUserBrief
)
from app.schemas.notification import NotificationOut

router = APIRouter(tags=["Contact & Enquiries"])


def get_item_primary_image(item: FoundItem) -> str:
    for img in item.images:
        if img.is_primary:
            return img.image_path
    if item.images:
        return item.images[0].image_path
    return ""


def format_contact_request(req: ContactRequest) -> ContactRequestOut:
    return ContactRequestOut(
        id=req.id,
        item_id=req.item_id,
        item=ContactItemBrief(
            id=req.item.id,
            reference_code=req.item.reference_code,
            title=req.item.title,
            status=req.item.status,
            primary_image=get_item_primary_image(req.item),
        ),
        sender=ContactUserBrief(
            id=req.sender.id,
            full_name=req.sender.full_name,
            department=req.sender.department,
        ),
        recipient=ContactUserBrief(
            id=req.recipient.id,
            full_name=req.recipient.full_name,
            department=req.recipient.department,
        ),
        message=req.message,
        status=req.status,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


@router.post("/items/{item_id}/contact", response_model=ContactRequestOut, status_code=status.HTTP_201_CREATED)
def create_contact_request(
    item_id: int,
    req_in: ContactRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(FoundItem).filter(FoundItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Found item listing not found.")
    
    if item.status != "available":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot contact reporter for this item because its status is '{item.status}'.",
        )

    if item.reporter_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot submit a contact request for your own found item listing.",
        )

    contact_req = ContactRequest(
        item_id=item.id,
        sender_id=current_user.id,
        recipient_id=item.reporter_id,
        message=req_in.message.strip(),
        status="new",
    )
    db.add(contact_req)
    db.flush()

    # Create notification for listing owner
    notif = Notification(
        user_id=item.reporter_id,
        type="new_contact_request",
        title=f"New enquiry on '{item.title[:35]}...'",
        message=f"{current_user.full_name} sent a contact enquiry regarding your listing {item.reference_code}.",
        related_item_id=item.id,
        related_contact_request_id=contact_req.id,
        is_read=False,
    )
    db.add(notif)
    db.commit()
    db.refresh(contact_req)

    return format_contact_request(contact_req)


@router.get("/me/contact-requests/sent", response_model=List[ContactRequestOut])
def get_sent_contact_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    requests = (
        db.query(ContactRequest)
        .filter(ContactRequest.sender_id == current_user.id)
        .order_by(ContactRequest.created_at.desc())
        .all()
    )
    return [format_contact_request(r) for r in requests]


@router.get("/me/contact-requests/received", response_model=List[ContactRequestOut])
def get_received_contact_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    requests = (
        db.query(ContactRequest)
        .filter(ContactRequest.recipient_id == current_user.id)
        .order_by(ContactRequest.created_at.desc())
        .all()
    )
    return [format_contact_request(r) for r in requests]


@router.patch("/contact-requests/{request_id}/status", response_model=ContactRequestOut)
def update_contact_request_status(
    request_id: int,
    status_in: ContactRequestStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = db.query(ContactRequest).filter(ContactRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Contact request not found.")

    if req.recipient_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the listing recipient can update request status.")

    new_st = status_in.status.lower()
    if new_st not in {"new", "read", "closed"}:
        raise HTTPException(status_code=400, detail="Allowed status values: 'new', 'read', 'closed'.")

    req.status = new_st
    db.commit()
    db.refresh(req)

    return format_contact_request(req)


@router.get("/me/notifications", response_model=List[NotificationOut])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notifs = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return [NotificationOut.model_validate(n) for n in notifs]


@router.patch("/me/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return NotificationOut.model_validate(notif)


@router.patch("/me/notifications/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False)
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read."}
