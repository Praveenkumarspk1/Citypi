"""
User Aggregate
"""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from ..entities.user import User, UserRole, UserStatus
from ..events import (
    UserDeactivated,
    UserEmailVerified,
    UserLoggedIn,
    UserProfileUpdated,
    UserRegistered,
    UserRoleChanged,
    UserStatusChanged,
)


@dataclass
class UserAggregate:
    """
    User aggregate root.
    Encapsulates user identity, profile, preferences, and behavior.
    """
    user: User
    _uncommitted_events: list = field(default_factory=list, init=False)

    @classmethod
    def create(
        cls,
        email: str,
        display_name: str | None = None,
        firebase_uid: str | None = None,
        google_id: str | None = None,
        password_hash: str | None = None,
        locale: str = "en",
        timezone: str = "UTC",
    ) -> "UserAggregate":
        """Create a new user aggregate"""
        user = User(
            id=uuid4(),
            email=email,
            display_name=display_name,
            firebase_uid=firebase_uid,
            google_id=google_id,
            password_hash=password_hash,
            locale=locale,
            timezone=timezone,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        aggregate = cls(user=user)
        aggregate._add_event(UserRegistered(
            user_id=user.id,
            email=user.email,
            firebase_uid=user.firebase_uid,
            google_id=user.google_id,
            timestamp=datetime.utcnow(),
        ))
        return aggregate

    def update_profile(
        self,
        display_name: str | None = None,
        avatar_url: str | None = None,
        locale: str | None = None,
        timezone: str | None = None,
    ) -> None:
        """Update user profile"""
        old_values = {
            "display_name": self.user.display_name,
            "avatar_url": self.user.avatar_url,
            "locale": self.user.locale,
            "timezone": self.user.timezone,
        }

        if display_name is not None:
            self.user.display_name = display_name
        if avatar_url is not None:
            self.user.avatar_url = avatar_url
        if locale is not None:
            self.user.locale = locale
        if timezone is not None:
            self.user.timezone = timezone

        self.user.updated_at = datetime.utcnow()

        new_values = {
            "display_name": self.user.display_name,
            "avatar_url": self.user.avatar_url,
            "locale": self.user.locale,
            "timezone": self.user.timezone,
        }

        self._add_event(UserProfileUpdated(
            user_id=self.user.id,
            old_values=old_values,
            new_values=new_values,
            timestamp=datetime.utcnow(),
        ))

    def verify_email(self) -> None:
        """Mark email as verified"""
        if not self.user.email_verified:
            self.user.email_verified = True
            self.user.updated_at = datetime.utcnow()
            self._add_event(UserEmailVerified(
                user_id=self.user.id,
                email=self.user.email,
                timestamp=datetime.utcnow(),
            ))

    def change_role(self, new_role: UserRole, changed_by: UUID) -> None:
        """Change user role (admin only)"""
        if self.user.role != new_role:
            old_role = self.user.role
            self.user.role = new_role
            self.user.updated_at = datetime.utcnow()
            self._add_event(UserRoleChanged(
                user_id=self.user.id,
                old_role=old_role,
                new_role=new_role,
                changed_by=changed_by,
                timestamp=datetime.utcnow(),
            ))

    def change_status(self, new_status: UserStatus, reason: str = "") -> None:
        """Change user status"""
        if self.user.status != new_status:
            old_status = self.user.status
            self.user.status = new_status
            self.user.updated_at = datetime.utcnow()
            self._add_event(UserStatusChanged(
                user_id=self.user.id,
                old_status=old_status,
                new_status=new_status,
                reason=reason,
                timestamp=datetime.utcnow(),
            ))

    def record_login(self) -> None:
        """Record user login"""
        self.user.last_login_at = datetime.utcnow()
        self.user.updated_at = datetime.utcnow()
        self._add_event(UserLoggedIn(
            user_id=self.user.id,
            timestamp=datetime.utcnow(),
        ))

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
            self.user.interests = interests
        if budget_level is not None:
            self.user.budget_level = budget_level
        if accessibility_needs is not None:
            self.user.accessibility_needs = accessibility_needs
        if dietary_restrictions is not None:
            self.user.dietary_restrictions = dietary_restrictions
        if preferred_transport_modes is not None:
            self.user.preferred_transport_modes = preferred_transport_modes

        self.user.updated_at = datetime.utcnow()
        self._add_event(UserProfileUpdated(
            user_id=self.user.id,
            old_values={},  # Could track old preferences
            new_values={
                "interests": self.user.interests,
                "budget_level": self.user.budget_level,
                "accessibility_needs": self.user.accessibility_needs,
                "dietary_restrictions": self.user.dietary_restrictions,
                "preferred_transport_modes": self.user.preferred_transport_modes,
            },
            timestamp=datetime.utcnow(),
        ))

    def deactivate(self, reason: str = "") -> None:
        """Deactivate user"""
        self.change_status(UserStatus.INACTIVE, reason)
        self._add_event(UserDeactivated(
            user_id=self.user.id,
            reason=reason,
            timestamp=datetime.utcnow(),
        ))

    def suspend(self, reason: str = "") -> None:
        """Suspend user"""
        self.change_status(UserStatus.SUSPENDED, reason)

    def activate(self) -> None:
        """Activate user"""
        self.change_status(UserStatus.ACTIVE)

    def soft_delete(self) -> None:
        """Soft delete user"""
        self.change_status(UserStatus.DELETED, "User requested deletion")

    def _add_event(self, event) -> None:
        """Add domain event to uncommitted events"""
        self._uncommitted_events.append(event)

    def get_uncommitted_events(self) -> list:
        """Get and clear uncommitted events"""
        events = self._uncommitted_events.copy()
        self._uncommitted_events.clear()
        return events

    def to_dict(self) -> dict:
        return {
            "user": self.user.to_dict(),
            "uncommitted_events_count": len(self._uncommitted_events),
        }
