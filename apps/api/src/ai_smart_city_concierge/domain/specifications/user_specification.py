"""
User Specifications - Specification pattern for User queries
"""
from dataclasses import dataclass, field
from datetime import datetime

from ..entities.user import User, UserRole, UserStatus
from ..repositories.base import Specification


class UserSpecification(Specification[User]):
    """Base User specification"""
    pass


@dataclass(frozen=True)
class UserRoleSpecification(UserSpecification):
    """Specification for users by role"""
    role: UserRole

    def is_satisfied_by(self, user: User) -> bool:
        return user.role == self.role


@dataclass(frozen=True)
class UserStatusSpecification(UserSpecification):
    """Specification for users by status"""
    status: UserStatus

    def is_satisfied_by(self, user: User) -> bool:
        return user.status == self.status


@dataclass(frozen=True)
class UserActiveSpecification(UserSpecification):
    """Specification for active users"""
    def is_satisfied_by(self, user: User) -> bool:
        return user.status == UserStatus.ACTIVE


@dataclass(frozen=True)
class UserVerifiedSpecification(UserSpecification):
    """Specification for verified users"""
    required: bool = True

    def is_satisfied_by(self, user: User) -> bool:
        return user.is_verified == self.required


@dataclass(frozen=True)
class UserEmailVerifiedSpecification(UserSpecification):
    """Specification for users with verified email"""
    required: bool = True

    def is_satisfied_by(self, user: User) -> bool:
        return user.email_verified == self.required


@dataclass(frozen=True)
class UserPhoneVerifiedSpecification(UserSpecification):
    """Specification for users with verified phone"""
    required: bool = True

    def is_satisfied_by(self, user: User) -> bool:
        return user.phone_verified == self.required


@dataclass(frozen=True)
class UserCreatedAfterSpecification(UserSpecification):
    """Specification for users created after date"""
    date: datetime

    def is_satisfied_by(self, user: User) -> bool:
        return user.created_at >= self.date


@dataclass(frozen=True)
class UserCreatedBeforeSpecification(UserSpecification):
    """Specification for users created before date"""
    date: datetime

    def is_satisfied_by(self, user: User) -> bool:
        return user.created_at <= self.date


@dataclass(frozen=True)
class UserLastLoginAfterSpecification(UserSpecification):
    """Specification for users who logged in after date"""
    date: datetime

    def is_satisfied_by(self, user: User) -> bool:
        return user.last_login_at is not None and user.last_login_at >= self.date


@dataclass(frozen=True)
class UserLastLoginBeforeSpecification(UserSpecification):
    """Specification for users who logged in before date"""
    date: datetime

    def is_satisfied_by(self, user: User) -> bool:
        return user.last_login_at is not None and user.last_login_at <= self.date


@dataclass(frozen=True)
class UserNeverLoggedInSpecification(UserSpecification):
    """Specification for users who never logged in"""
    def is_satisfied_by(self, user: User) -> bool:
        return user.last_login_at is None


@dataclass(frozen=True)
class UserEmailSpecification(UserSpecification):
    """Specification for users by email domain or exact email"""
    email: str | None = None
    domain: str | None = None

    def is_satisfied_by(self, user: User) -> bool:
        if self.email and user.email.lower() == self.email.lower():
            return True
        if self.domain and user.email.lower().endswith(f"@{self.domain.lower()}"):
            return True
        return False


@dataclass(frozen=True)
class UserNameSearchSpecification(UserSpecification):
    """Specification for text search in user name"""
    query: str

    def is_satisfied_by(self, user: User) -> bool:
        query_lower = self.query.lower()
        full_name = f"{user.first_name} {user.last_name}".lower()
        return (query_lower in full_name or
                query_lower in user.first_name.lower() or
                query_lower in user.last_name.lower() or
                (user.username and query_lower in user.username.lower()))


@dataclass(frozen=True)
class UserHasPreferencesSpecification(UserSpecification):
    """Specification for users with specific preferences"""
    preference_keys: list[str] = field(default_factory=list)
    match_all: bool = False

    def is_satisfied_by(self, user: User) -> bool:
        if not user.preferences:
            return False
        if self.match_all:
            return all(key in user.preferences for key in self.preference_keys)
        return any(key in user.preferences for key in self.preference_keys)


@dataclass(frozen=True)
class UserLanguageSpecification(UserSpecification):
    """Specification for users by preferred language"""
    language: str

    def is_satisfied_by(self, user: User) -> bool:
        return user.preferences.get("language") == self.language


@dataclass(frozen=True)
class UserCurrencySpecification(UserSpecification):
    """Specification for users by preferred currency"""
    currency: str

    def is_satisfied_by(self, user: User) -> bool:
        return user.preferences.get("currency") == self.currency


@dataclass(frozen=True)
class UserTimezoneSpecification(UserSpecification):
    """Specification for users by timezone"""
    timezone: str

    def is_satisfied_by(self, user: User) -> bool:
        return user.preferences.get("timezone") == self.timezone


@dataclass(frozen=True)
class UserAccessibilityNeedsSpecification(UserSpecification):
    """Specification for users with accessibility needs"""
    needs: list[str] = field(default_factory=list)
    match_all: bool = False

    def is_satisfied_by(self, user: User) -> bool:
        if not user.accessibility_needs:
            return False
        if self.match_all:
            return all(need in user.accessibility_needs for need in self.needs)
        return any(need in user.accessibility_needs for need in self.needs)


@dataclass(frozen=True)
class UserTravelStyleSpecification(UserSpecification):
    """Specification for users by travel style"""
    style: str  # budget, luxury, adventure, cultural, etc.

    def is_satisfied_by(self, user: User) -> bool:
        return user.preferences.get("travel_style") == self.style


@dataclass(frozen=True)
class UserBudgetLevelSpecification(UserSpecification):
    """Specification for users by budget level"""
    level: str  # low, medium, high

    def is_satisfied_by(self, user: User) -> bool:
        return user.preferences.get("budget_level") == self.level


@dataclass(frozen=True)
class UserNotificationEnabledSpecification(UserSpecification):
    """Specification for users with notifications enabled"""
    notification_type: str  # email, push, sms
    enabled: bool = True

    def is_satisfied_by(self, user: User) -> bool:
        notifications = user.preferences.get("notifications", {})
        return notifications.get(self.notification_type, False) == self.enabled


@dataclass(frozen=True)
class UserHasItinerariesSpecification(UserSpecification):
    """Specification for users who have itineraries"""
    min_count: int = 1

    def is_satisfied_by(self, user: User) -> bool:
        return user.itinerary_count >= self.min_count


@dataclass(frozen=True)
class UserHasFavoritesSpecification(UserSpecification):
    """Specification for users who have favorites"""
    min_count: int = 1

    def is_satisfied_by(self, user: User) -> bool:
        return user.favorites_count >= self.min_count


@dataclass(frozen=True)
class UserHasReviewsSpecification(UserSpecification):
    """Specification for users who have written reviews"""
    min_count: int = 1

    def is_satisfied_by(self, user: User) -> bool:
        return user.reviews_count >= self.min_count


# Composite specifications for common query patterns
class UserSpecifications:
    """Factory for common User specification combinations"""

    @staticmethod
    def active_users() -> UserSpecification:
        """Get all active users"""
        return UserActiveSpecification()

    @staticmethod
    def verified_users() -> UserSpecification:
        """Get all verified users"""
        return UserVerifiedSpecification()

    @staticmethod
    def admin_users() -> UserSpecification:
        """Get all admin users"""
        return UserRoleSpecification(UserRole.ADMIN)

    @staticmethod
    def premium_users() -> UserSpecification:
        """Get all premium users"""
        return UserRoleSpecification(UserRole.PREMIUM)

    @staticmethod
    def new_users(days: int = 7) -> UserSpecification:
        """Get users created in the last N days"""
        from datetime import datetime, timedelta
        return UserCreatedAfterSpecification(datetime.utcnow() - timedelta(days=days))

    @staticmethod
    def recently_active_users(days: int = 30) -> UserSpecification:
        """Get users who logged in recently"""
        from datetime import datetime, timedelta
        return UserLastLoginAfterSpecification(datetime.utcnow() - timedelta(days=days))

    @staticmethod
    def inactive_users(days: int = 90) -> UserSpecification:
        """Get users who haven't logged in for N days"""
        from datetime import datetime, timedelta
        return (UserLastLoginBeforeSpecification(datetime.utcnow() - timedelta(days=days)) |
                UserNeverLoggedInSpecification())

    @staticmethod
    def users_by_email_domain(domain: str) -> UserSpecification:
        """Get users by email domain"""
        return UserEmailSpecification(domain=domain)

    @staticmethod
    def users_with_accessibility_needs(needs: list[str]) -> UserSpecification:
        """Get users with specific accessibility needs"""
        return UserAccessibilityNeedsSpecification(needs=needs)

    @staticmethod
    def budget_travelers() -> UserSpecification:
        """Get budget-conscious travelers"""
        return UserBudgetLevelSpecification("low")

    @staticmethod
    def luxury_travelers() -> UserSpecification:
        """Get luxury travelers"""
        return UserBudgetLevelSpecification("high")

    @staticmethod
    def adventure_travelers() -> UserSpecification:
        """Get adventure travelers"""
        return UserTravelStyleSpecification("adventure")

    @staticmethod
    def cultural_travelers() -> UserSpecification:
        """Get cultural travelers"""
        return UserTravelStyleSpecification("cultural")

    @staticmethod
    def users_with_notifications(notification_type: str = "push") -> UserSpecification:
        """Get users with specific notifications enabled"""
        return UserNotificationEnabledSpecification(notification_type)

    @staticmethod
    def active_content_creators() -> UserSpecification:
        """Get users who create content (itineraries, reviews)"""
        return (UserHasItinerariesSpecification(1) |
                UserHasReviewsSpecification(1)) & UserActiveSpecification()

    @staticmethod
    def engaged_users(min_itineraries: int = 3, min_favorites: int = 5) -> UserSpecification:
        """Get highly engaged users"""
        return (UserHasItinerariesSpecification(min_itineraries) &
                UserHasFavoritesSpecification(min_favorites) &
                UserActiveSpecification())

    @staticmethod
    def search_users(query: str) -> UserSpecification:
        """Search users by name/username"""
        return UserNameSearchSpecification(query) & UserActiveSpecification()
