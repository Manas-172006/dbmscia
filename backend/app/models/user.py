from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(191), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)  # 'user' or 'admin'
    phone = Column(String(50), nullable=True)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    found_items = relationship("FoundItem", back_populates="reporter", cascade="all, delete-orphan")
    sent_requests = relationship(
        "ContactRequest",
        foreign_keys="ContactRequest.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan"
    )
    received_requests = relationship(
        "ContactRequest",
        foreign_keys="ContactRequest.recipient_id",
        back_populates="recipient",
        cascade="all, delete-orphan"
    )
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    status_changes = relationship("ItemStatusHistory", back_populates="changed_by_user")
    audit_logs = relationship("AdminAuditLog", back_populates="admin_user")
