"""
User Application Service
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from ...domain.entities.user import User, UserRole, UserStatus
from ...domain.events.domain_events import (
    UserCreatedEvent,
    UserDeletedEvent,
    UserEmailVerifiedEvent,
    UserLoggedInEvent,
    UserPreferencesUpdatedEvent,
    UserUpdatedEvent,
)
from ...domain.repositories.user_repository import UserRepository
from ..ports.cache import CachePort
from ..ports.event_publisher import EventPublisher
from ..ports.external_services import (
    AuthServicePort,
    CacheServicePort,
    NotificationServicePort,
)


class UserService:
    """Application service for user management"""

    def __init__(
        self,
        user_repository: UserRepository,
        cache: CachePort,
        auth: AuthServicePort,
        notification: NotificationServicePort,
        event_bus: EventPublisher,
    ):
        self.user_repository = user_repository
        self.cache = cache
        self.auth = auth
        self.notification = notification
        self.event_bus = event_bus

    async def create_user(
        self,
        email: str,
        display_name: str | None = None,
        firebase_uid: str | None = None,
        google_id: str | None = None,
        password: str | None = None,
        locale: str = "en",
        timezone: str = "UTC",
        interests: list[str] | None = None,
        budget_level: str = "moderate",
        accessibility_needs: list[str] | None = None,
        dietary_restrictions: list[str] | None = None,
        preferred_transport_modes: list[str] | None = None,
    ) -> User:
        """Create a new user"""
        existing = await self.user_repository.get_by_email(email)
        if existing:
            raise ValueError(f"User with email {email} already exists")

        if firebase_uid:
            existing = await self.user_repository.get_by_firebase_uid(firebase_uid)
            if existing:
                raise ValueError("User with Firebase UID already exists")

        if google_id:
            existing = await self.user_repository.get_by_google_id(google_id)
            if existing:
                raise ValueError("User with Google ID already exists")

        user = User(
            email=email,
            display_name=display_name,
            firebase_uid=firebase_uid,
            google_id=google_id,
            locale=locale,
            timezone=timezone,
            interests=interests or [],
            budget_level=budget_level,
            accessibility_needs=accessibility_needs or [],
            dietary_restrictions=dietary_restrictions or [],
            preferred_transport_modes=preferred_transport_modes or [],
        )

        if password:
            user.set_password(password)

        created_user = await self.user_repository.create(user)

        # Publish event
        event = UserCreatedEvent.create(created_user)
        await self.event_bus.publish(event)

        # Send welcome notification
        await self.notification.send_welcome_email(created_user.email, created_user.display_name)

        await self.cache.set(f"user:{created_user.id}", created_user)

        return created_user

    async def get_user(self, user_id: UUID) -> User | None:
        """Get user by ID"""
        cached = await self.cache.get(f"user:{user_id}")
        if cached:
            return cached

        user = await self.user_repository.get_by_id(user_id)
        if user:
            await self.cache.set(f"user:{user_id}", user)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email"""
        return await self.user_repository.get_by_email(email)

    async def get_user_by_firebase_uid(self, firebase_uid: str) -> User | None:
        """Get user by Firebase UID"""
        return await self.user_repository.get_by_firebase_uid(firebase_uid)

    async def get_user_by_google_id(self, google_id: str) -> User | None:
        """Get user by Google ID"""
        return await self.user_repository.get_by_google_id(google_id)

    async def update_profile(
        self,
        user_id: UUID,
        display_name: str | None = None,
        avatar_url: str | None = None,
        locale: str | None = None,
        timezone: str | None = None,
    ) -> User | None:
        """Update user profile"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None

        changes = {}
        if display_name is not None and display_name != user.display_name:
            changes["display_name"] = {"old": user.display_name, "new": display_name}
        if avatar_url is not None and avatar_url != user.avatar_url:
            changes["avatar_url"] = {"old": user.avatar_url, "new": avatar_url}
        if locale is not None and locale != user.locale:
            changes["locale"] = {"old": user.locale, "new": locale}
        if timezone is not None and timezone != user.timezone:
            changes["timezone"] = {"old": user.timezone, "new": timezone}

        user.update_profile(
            display_name=display_name,
            avatar_url=avatar_url,
            locale=locale,
            timezone=timezone,
        )

        updated_user = await self.user_repository.update(user)

        if changes:
            event = UserUpdatedEvent.create(updated_user, changes)
            await self.event_bus.publish(event)

        await self.cache.set(f"user:{user_id}", updated_user)

        return updated_user

    async def update_preferences(
        self,
        user_id: UUID,
        interests: list[str] | None = None,
        budget_level: str | None = None,
        accessibility_needs: list[str] | None = None,
        dietary_restrictions: list[str] | None = None,
        preferred_transport_modes: list[str] | None = None,
    ) -> User | None:
        """Update user preferences"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None

        changes = {}
        if interests is not None and interests != user.interests:
            changes["interests"] = {"old": user.interests, "new": interests}
        if budget_level is not None and budget_level != user.budget_level:
            changes["budget_level"] = {"old": user.budget_level, "new": budget_level}
        if accessibility_needs is not None and accessibility_needs != user.accessibility_needs:
            changes["accessibility_needs"] = {"old": user.accessibility_needs, "new": accessibility_needs}
        if dietary_restrictions is not None and dietary_restrictions != user.dietary_restrictions:
            changes["dietary_restrictions"] = {"old": user.dietary_restrictions, "new": dietary_restrictions}
        if preferred_transport_modes is not None and preferred_transport_modes != user.preferred_transport_modes:
            changes["preferred_transport_modes"] = {"old": user.preferred_transport_modes, "new": preferred_transport_modes}

        user.update_preferences(
            interests=interests,
            budget_level=budget_level,
            accessibility_needs=accessibility_needs,
            dietary_restrictions=dietary_restrictions,
            preferred_transport_modes=preferred_transport_modes,
        )

        updated_user = await self.user_repository.update(user)

        if changes:
            event = UserPreferencesUpdatedEvent.create(updated_user, changes)
            await self.event_bus.publish(event)

        await self.cache.set(f"user:{user_id}", updated_user)

        return updated_user

    async def verify_email(self, user_id: UUID) -> User | None:
        """Verify user email"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None

        user.verify_email()
        user.clear_email_verification_token()
        updated_user = await self.user_repository.update(user)

        event = UserEmailVerifiedEvent.create(updated_user)
        await self.event_bus.publish(event)

        await self.cache.set(f"user:{user_id}", updated_user)

        return updated_user

    async def forgot_password(self, email: str) -> bool:
        """Initiate password reset"""
        user = await self.user_repository.get_by_email(email)
        if not user:
            # Don't reveal if user exists for security
            return True

        user.generate_password_reset_token()
        await self.user_repository.update(user)

        # Send reset email
        await self.notification.send_password_reset_email(user.email, user.password_reset_token)

        return True

    async def resend_verification_email(self, email: str) -> bool:
        """Resend email verification"""
        user = await self.user_repository.get_by_email(email)
        if not user:
            return True

        if user.email_verified:
            return True

        user.generate_email_verification_token()
        await self.user_repository.update(user)

        # Send verification email
        await self.notification.send_verification_email(user.email, user.email_verification_token)

        return True

    async def reset_password(self, token: str, new_password: str) -> User | None:
        """Reset user password"""
        user = await self.user_repository.get_by_password_reset_token(token)
        if not user:
            return None

        if not user.verify_password_reset_token(token):
            return None

        user.set_password(new_password)
        user.clear_password_reset_token()
        updated_user = await self.user_repository.update(user)

        event = UserUpdatedEvent.create(updated_user, {"password_changed": True})
        await self.event_bus.publish(event)

        await self.cache.set(f"user:{updated_user.id}", updated_user)

        return updated_user

    async def authenticate(self, email: str, password: str) -> User | None:
        """Authenticate user"""
        user = await self.user_repository.get_by_email(email)
        if not user:
            return None

        if not user.verify_password(password):
            return None

        if not user.is_active():
            raise ValueError("Account is not active")

        user.record_login()
        updated_user = await self.user_repository.update(user)
        await self.user_repository.update_last_login(user.id)

        event = UserLoggedInEvent.create(updated_user)
        await self.event_bus.publish(event)

        await self.cache.set(f"user:{user.id}", updated_user)

        return updated_user

    async def create_access_token(self, user: User) -> str:
        """Create access token for user"""
        return await self.auth.create_access_token(
            subject=str(user.id),
            email=user.email,
            role=user.role.value,
        )

    async def create_refresh_token(self, user: User) -> str:
        """Create refresh token for user"""
        return await self.auth.create_refresh_token(subject=str(user.id))

    async def deactivate_user(self, user_id: UUID) -> User | None:
        """Deactivate user"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None

        user.deactivate()
        updated_user = await self.user_repository.update(user)

        event = UserUpdatedEvent.create(updated_user, {"status": {"old": "active", "new": "inactive"}})
        await self.event_bus.publish(event)

        await self.cache.set(f"user:{user_id}", updated_user)

        return updated_user

    async def suspend_user(self, user_id: UUID) -> User | None:
        """Suspend user"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None

        user.suspend()
        updated_user = await self.user_repository.update(user)

        event = UserUpdatedEvent.create(updated_user, {"status": {"old": user.status.value, "new": "suspended"}})
        await self.event_bus.publish(event)

        await self.cache.set(f"user:{user_id}", updated_user)

        return updated_user

    async def activate_user(self, user_id: UUID) -> User | None:
        """Activate user"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None

        user.activate()
        updated_user = await self.user_repository.update(user)

        event = UserUpdatedEvent.create(updated_user, {"status": {"old": user.status.value, "new": "active"}})
        await self.event_bus.publish(event)

        await self.cache.set(f"user:{user_id}", updated_user)

        return updated_user

    async def delete_user(self, user_id: UUID) -> bool:
        """Soft delete user"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False

        user.soft_delete()
        await self.user_repository.update(user)

        event = UserDeletedEvent.create(user)
        await self.event_bus.publish(event)

        await self.cache.delete(f"user:{user_id}")

        return True

    async def change_role(self, user_id: UUID, new_role: UserRole) -> User | None:
        """Change user role"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None

        old_role = user.role
        user.role = new_role
        user.updated_at = datetime.utcnow()

        updated_user = await self.user_repository.update(user)

        event = UserUpdatedEvent.create(updated_user, {"role": {"old": old_role.value, "new": new_role.value}})
        await self.event_bus.publish(event)

        await self.cache.set(f"user:{user_id}", updated_user)

        return updated_user

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role: UserRole | None = None,
        status: UserStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        """List users with pagination"""
        return await self.user_repository.list(
            page=page,
            page_size=page_size,
            role=role,
            status=status,
            search=search,
        )

    async def get_users_with_preferences(
        self,
        interests: list[str] | None = None,
        budget_level: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        """Get users matching preferences"""
        return await self.user_repository.get_users_with_preferences(
            interests=interests,
            budget_level=budget_level,
            page=page,
            page_size=page_size,
        )