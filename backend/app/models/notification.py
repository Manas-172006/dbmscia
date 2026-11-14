from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # 'new_contact_request', 'status_changed', etc.
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    related_item_id = Column(Integer, ForeignKey("found_items.id", ondelete="SET NULL"), nullable=True)
    related_contact_request_id = Column(Integer, ForeignKey("contact_requests.id", ondelete="SET NULL"), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="notifications")
