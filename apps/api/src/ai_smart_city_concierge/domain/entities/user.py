"""
User Domain Entity
"""
import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4


class UserRole(StrEnum):
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


@dataclass
class User:
    """
    User aggregate root.
    Contains core user identity and profile information.
    """
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    email_verified: bool = False
    display_name: str | None = None
    avatar_url: str | None = None
    locale: str = "en"
    timezone: str = "UTC"
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    firebase_uid: str | None = None
    google_id: str | None = None
    password_hash: str | None = None
    email_verification_token: str | None = None
    password_reset_token: str | None = None
    password_reset_expires: datetime | None = None
    last_login_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None

    # Preferences (embedded for quick access)
    interests: list[str] = field(default_factory=list)
    budget_level: str = "moderate"  # budget, moderate, luxury
    accessibility_needs: list[str] = field(default_factory=list)
    dietary_restrictions: list[str] = field(default_factory=list)
    preferred_transport_modes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate user after initialization"""
        if not self.email:
            raise ValueError("Email is required")
        if "@" not in self.email:
            raise ValueError("Invalid email format")
        if self.budget_level not in ("budget", "moderate", "luxury"):
            raise ValueError("Budget level must be budget, moderate, or luxury")

    def set_password(self, password: str) -> None:
        """Hash and set password"""
        salt = secrets.token_hex(16)
        self.password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() + ':' + salt
        self.updated_at = datetime.utcnow()

    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        if not self.password_hash:
            return False
        try:
            hash_part, salt = self.password_hash.split(':')
            computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
            return computed_hash == hash_part
        except (ValueError, AttributeError):
            return False

    def generate_email_verification_token(self) -> str:
        """Generate email verification token"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.updated_at = datetime.utcnow()
        return self.email_verification_token

    def generate_password_reset_token(self, expires_in_hours: int = 24) -> str:
        """Generate password reset token with expiration"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=expires_in_hours)
        self.updated_at = datetime.utcnow()
        return self.password_reset_token

    def verify_password_reset_token(self, token: str) -> bool:
        """Verify password reset token and check expiration"""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        if datetime.utcnow() > self.password_reset_expires:
            return False
        return self.password_reset_token == token

    def clear_password_reset_token(self) -> None:
        """Clear password reset token after use"""
        self.password_reset_token = None
        self.password_reset_expires = None
        self.updated_at = datetime.utcnow()

    def verify_email_token(self, token: str) -> bool:
        """Verify email verification token"""
        if not self.email_verification_token:
            return False
        return self.email_verification_token == token

    def clear_email_verification_token(self) -> None:
        """Clear email verification token after use"""
        self.email_verification_token = None
        self.updated_at = datetime.utcnow()

    def update_profile(
        self,
        display_name: str | None = None,
        avatar_url: str | None = None,
        locale: str | None = None,
        timezone: str | None = None,
    ) -> None:
        """Update user profile"""
        if display_name is not None:
            self.display_name = display_name
        if avatar_url is not None:
            self.avatar_url = avatar_url
        if locale is not None:
            self.locale = locale
        if timezone is not None:
            self.timezone = timezone
        self.updated_at = datetime.utcnow()

    def update_preferences(
        self,
        interests: list[str] | None = None,
        budget_level: str | None = None,
        accessibility_needs: list[str] | None = None,
        dietary_restrictions: list[str] | None = None,
        preferred_transport_modes: list[str] | None = None,
    ) -> None:
        """Update user preferences"""
        if interests is not None:
            self.interests = interests
        if budget_level is not None:
            if budget_level not in ("budget", "moderate", "luxury"):
                raise ValueError("Budget level must be budget, moderate, or luxury")
            self.budget_level = budget_level
        if accessibility_needs is not None:
            self.accessibility_needs = accessibility_needs
        if dietary_restrictions is not None:
            self.dietary_restrictions = dietary_restrictions
        if preferred_transport_modes is not None:
            self.preferred_transport_modes = preferred_transport_modes
        self.updated_at = datetime.utcnow()

    def verify_email(self) -> None:
        """Mark email as verified"""
        self.email_verified = True
        self.updated_at = datetime.utcnow()

    def record_login(self) -> None:
        """Record user login"""
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate user"""
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.utcnow()

    def suspend(self) -> None:
        """Suspend user"""
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate user"""
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def soft_delete(self) -> None:
        """Soft delete user"""
        self.status = UserStatus.DELETED
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE

    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN

    def is_premium(self) -> bool:
        """Check if user is premium"""
        return self.role in (UserRole.PREMIUM, UserRole.ADMIN)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "email": self.email,
            "email_verified": self.email_verified,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "locale": self.locale,
            "timezone": self.timezone,
            "role": self.role.value,
            "status": self.status.value,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "preferences": {
                "interests": self.interests,
                "budget_level": self.budget_level,
                "accessibility_needs": self.accessibility_needs,
                "dietary_restrictions": self.dietary_restrictions,
                "preferred_transport_modes": self.preferred_transport_modes,
            }
        }
