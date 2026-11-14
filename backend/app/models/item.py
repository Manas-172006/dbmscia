from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class FoundItem(Base):
    __tablename__ = "found_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reference_code = Column(String(30), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("campus_locations.id"), nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    found_at = Column(DateTime, nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    condition = Column(String(50), nullable=True)
    status = Column(String(20), default="available", nullable=False, index=True)  # available, returned, removed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_status_category_location", "status", "category_id", "location_id"),
    )

    # Relationships
    category = relationship("Category", back_populates="found_items")
    subcategory = relationship("Subcategory", back_populates="found_items")
    location = relationship("CampusLocation", back_populates="found_items")
    reporter = relationship("User", back_populates="found_items")
    images = relationship("ItemImage", back_populates="item", cascade="all, delete-orphan")
    contact_requests = relationship("ContactRequest", back_populates="item", cascade="all, delete-orphan")
    status_history = relationship("ItemStatusHistory", back_populates="item", cascade="all, delete-orphan")


class ItemImage(Base):
    __tablename__ = "item_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("found_items.id", ondelete="CASCADE"), nullable=False, index=True)
    image_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    item = relationship("FoundItem", back_populates="images")


class ItemStatusHistory(Base):
    __tablename__ = "item_status_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("found_items.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    old_status = Column(String(20), nullable=False)
    new_status = Column(String(20), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    item = relationship("FoundItem", back_populates="status_history")
    changed_by_user = relationship("User", back_populates="status_changes")
