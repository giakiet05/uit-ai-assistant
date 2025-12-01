import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ...shared.config.database import Base


class User(Base):
    __tablename__ = "users"

    # Core fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users

    # Provider fields for social login (e.g., Google)
    provider = Column(String, default="local", nullable=False) # 'local', 'google'
    provider_id = Column(String, unique=True, nullable=True, index=True)

    # Status fields
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String, default="user", nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True) # For soft deletes

    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="owner")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"