"""
SQLAlchemy User Model
"""
import uuid
from datetime import datetime

from ai_smart_city_concierge.domain.entities.user import UserRole, UserStatus
from ai_smart_city_concierge.infrastructure.config.database import Base
from sqlalchemy import JSON, Boolean, Column, DateTime, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class UserModel(Base):
    """SQLAlchemy model for User"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    locale = Column(String(10), default="en", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    firebase_uid = Column(String(128), unique=True, nullable=True, index=True)
    google_id = Column(String(128), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    email_verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Preferences (stored as JSON)
    interests = Column(JSON, default=list, nullable=False)
    budget_level = Column(String(20), default="moderate", nullable=False)
    accessibility_needs = Column(JSON, default=list, nullable=False)
    dietary_restrictions = Column(JSON, default=list, nullable=False)
    preferred_transport_modes = Column(JSON, default=list, nullable=False)

    # Relationships
    conversations = relationship("ConversationModel", back_populates="user", lazy="dynamic")
    itineraries = relationship("ItineraryModel", back_populates="user", lazy="dynamic")
    media = relationship("MediaModel", back_populates="user", lazy="dynamic")
    feedback = relationship("FeedbackModel", back_populates="user", lazy="dynamic")
    favorites = relationship("FavoriteModel", back_populates="user", lazy="dynamic")

    def to_entity(self):
        """Convert to domain entity"""
        from ai_smart_city_concierge.domain.entities.user import User
        return User(
            id=self.id,
            email=self.email,
            email_verified=self.email_verified,
            display_name=self.display_name,
            avatar_url=self.avatar_url,
            locale=self.locale,
            timezone=self.timezone,
            role=self.role,
            status=self.status,
            firebase_uid=self.firebase_uid,
            google_id=self.google_id,
            password_hash=self.password_hash,
            email_verification_token=self.email_verification_token,
            password_reset_token=self.password_reset_token,
            password_reset_expires=self.password_reset_expires,
            last_login_at=self.last_login_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            interests=self.interests or [],
            budget_level=self.budget_level,
            accessibility_needs=self.accessibility_needs or [],
            dietary_restrictions=self.dietary_restrictions or [],
            preferred_transport_modes=self.preferred_transport_modes or [],
        )

    @classmethod
    def from_entity(cls, entity):
        """Create model from domain entity"""
        return cls(
            id=entity.id,
            email=entity.email,
            email_verified=entity.email_verified,
            display_name=entity.display_name,
            avatar_url=entity.avatar_url,
            locale=entity.locale,
            timezone=entity.timezone,
            role=entity.role,
            status=entity.status,
            firebase_uid=entity.firebase_uid,
            google_id=entity.google_id,
            password_hash=entity.password_hash,
            email_verification_token=entity.email_verification_token,
            password_reset_token=entity.password_reset_token,
            password_reset_expires=entity.password_reset_expires,
            last_login_at=entity.last_login_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
            interests=entity.interests,
            budget_level=entity.budget_level,
            accessibility_needs=entity.accessibility_needs,
            dietary_restrictions=entity.dietary_restrictions,
            preferred_transport_modes=entity.preferred_transport_modes,
        )
