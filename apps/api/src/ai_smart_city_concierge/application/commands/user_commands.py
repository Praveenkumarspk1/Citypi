"""
User Commands (CQRS Write Side)
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ...domain.entities.user import User, UserRole
from ...domain.events.domain_events import (
    UserCreatedEvent,
    UserDeletedEvent,
    UserEmailVerifiedEvent,
    UserLoggedInEvent,
    UserPreferencesUpdatedEvent,
    UserUpdatedEvent,
)
from ..ports.event_publisher import EventPublisher
from ..ports.repositories import UserRepositoryPort


@dataclass
class CreateUserCommand:
    """Command to create a new user"""
    email: str
    display_name: str | None = None
    firebase_uid: str | None = None
    google_id: str | None = None
    password: str | None = None
    locale: str = "en"
    timezone: str = "UTC"
    interests: list[str] = None
    budget_level: str = "moderate"
    accessibility_needs: list[str] = None
    dietary_restrictions: list[str] = None
    preferred_transport_modes: list[str] = None

    def __post_init__(self):
        if self.interests is None:
            self.interests = []
        if self.accessibility_needs is None:
            self.accessibility_needs = []
        if self.dietary_restrictions is None:
            self.dietary_restrictions = []
        if self.preferred_transport_modes is None:
            self.preferred_transport_modes = []


@dataclass
class UpdateUserProfileCommand:
    """Command to update user profile"""
    user_id: UUID
    display_name: str | None = None
    avatar_url: str | None = None
    locale: str | None = None
    timezone: str | None = None


@dataclass
class UpdateUserPreferencesCommand:
    """Command to update user preferences"""
    user_id: UUID
    interests: list[str] | None = None
    budget_level: str | None = None
    accessibility_needs: list[str] | None = None
    dietary_restrictions: list[str] | None = None
    preferred_transport_modes: list[str] | None = None


@dataclass
class VerifyUserEmailCommand:
    """Command to verify user email"""
    user_id: UUID


@dataclass
class ForgotPasswordCommand:
    """Command to initiate password reset"""
    email: str


@dataclass
class ResendVerificationEmailCommand:
    """Command to resend email verification"""
    email: str


@dataclass
class ResetPasswordCommand:
    """Command to reset user password"""
    token: str
    new_password: str


@dataclass
class RecordUserLoginCommand:
    """Command to record user login"""
    user_id: UUID
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass
class UserLoginCommand:
    """Command to authenticate user login"""
    email: str
    password: str
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass
class DeactivateUserCommand:
    """Command to deactivate user"""
    user_id: UUID


@dataclass
class SuspendUserCommand:
    """Command to suspend user"""
    user_id: UUID


@dataclass
class ActivateUserCommand:
    """Command to activate user"""
    user_id: UUID


@dataclass
class DeleteUserCommand:
    """Command to soft delete user"""
    user_id: UUID


@dataclass
class ChangeUserRoleCommand:
    """Command to change user role"""
    user_id: UUID
    new_role: UserRole


class UserCommandHandler:
    """Handler for user commands"""

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        event_publisher: EventPublisher,
    ):
        self.user_repository = user_repository
        self.event_publisher = event_publisher

    async def handle_create_user(self, command: CreateUserCommand) -> User:
        """Handle create user command"""
        # Check if user already exists
        existing = await self.user_repository.get_by_email(command.email)
        if existing:
            raise ValueError(f"User with email {command.email} already exists")

        if command.firebase_uid:
            existing = await self.user_repository.get_by_firebase_uid(command.firebase_uid)
            if existing:
                raise ValueError("User with Firebase UID already exists")

        if command.google_id:
            existing = await self.user_repository.get_by_google_id(command.google_id)
            if existing:
                raise ValueError("User with Google ID already exists")

        # Create user
        user = User(
            email=command.email,
            display_name=command.display_name,
            firebase_uid=command.firebase_uid,
            google_id=command.google_id,
            locale=command.locale,
            timezone=command.timezone,
            interests=command.interests,
            budget_level=command.budget_level,
            accessibility_needs=command.accessibility_needs,
            dietary_restrictions=command.dietary_restrictions,
            preferred_transport_modes=command.preferred_transport_modes,
        )

        # Set password if provided
        if command.password:
            user.set_password(command.password)

        # Save
        created_user = await self.user_repository.create(user)

        # Publish event
        event = UserCreatedEvent.create(created_user)
        await self.event_publisher.publish(event)

        return created_user

    async def handle_update_profile(self, command: UpdateUserProfileCommand) -> User:
        """Handle update profile command"""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise ValueError(f"User {command.user_id} not found")

        # Track changes
        changes = {}
        if command.display_name is not None and command.display_name != user.display_name:
            changes["display_name"] = {"old": user.display_name, "new": command.display_name}
        if command.avatar_url is not None and command.avatar_url != user.avatar_url:
            changes["avatar_url"] = {"old": user.avatar_url, "new": command.avatar_url}
        if command.locale is not None and command.locale != user.locale:
            changes["locale"] = {"old": user.locale, "new": command.locale}
        if command.timezone is not None and command.timezone != user.timezone:
            changes["timezone"] = {"old": user.timezone, "new": command.timezone}

        # Update
        user.update_profile(
            display_name=command.display_name,
            avatar_url=command.avatar_url,
            locale=command.locale,
            timezone=command.timezone,
        )

        updated_user = await self.user_repository.update(user)

        # Publish event
        if changes:
            event = UserUpdatedEvent.create(updated_user, changes)
            await self.event_publisher.publish(event)

        return updated_user

    async def handle_update_preferences(self, command: UpdateUserPreferencesCommand) -> User:
        """Handle update preferences command"""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise ValueError(f"User {command.user_id} not found")

        # Track changes
        changes = {}
        if command.interests is not None and command.interests != user.interests:
            changes["interests"] = {"old": user.interests, "new": command.interests}
        if command.budget_level is not None and command.budget_level != user.budget_level:
            changes["budget_level"] = {"old": user.budget_level, "new": command.budget_level}
        if command.accessibility_needs is not None and command.accessibility_needs != user.accessibility_needs:
            changes["accessibility_needs"] = {"old": user.accessibility_needs, "new": command.accessibility_needs}
        if command.dietary_restrictions is not None and command.dietary_restrictions != user.dietary_restrictions:
            changes["dietary_restrictions"] = {"old": user.dietary_restrictions, "new": command.dietary_restrictions}
        if command.preferred_transport_modes is not None and command.preferred_transport_modes != user.preferred_transport_modes:
            changes["preferred_transport_modes"] = {"old": user.preferred_transport_modes, "new": command.preferred_transport_modes}

        # Update
        user.update_preferences(
            interests=command.interests,
            budget_level=command.budget_level,
            accessibility_needs=command.accessibility_needs,
            dietary_restrictions=command.dietary_restrictions,
            preferred_transport_modes=command.preferred_transport_modes,
        )

        updated_user = await self.user_repository.update(user)

        # Publish event
        if changes:
            event = UserPreferencesUpdatedEvent.create(updated_user, changes)
            await self.event_publisher.publish(event)

        return updated_user

    async def handle_verify_email(self, command: VerifyUserEmailCommand) -> User:
        """Handle verify email command"""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise ValueError(f"User {command.user_id} not found")

        user.verify_email()
        updated_user = await self.user_repository.update(user)

        # Publish event
        event = UserEmailVerifiedEvent.create(updated_user)
        await self.event_publisher.publish(event)

        return updated_user

    async def handle_forgot_password(self, command: ForgotPasswordCommand) -> bool:
        """Handle forgot password command"""
        user = await self.user_repository.get_by_email(command.email)
        if not user:
            # Don't reveal if user exists for security
            return True

        # Generate password reset token
        user.generate_password_reset_token()
        await self.user_repository.update(user)

        # TODO: Send email with reset link
        # For now, we just generate the token

        return True

    async def handle_resend_verification_email(self, command: ResendVerificationEmailCommand) -> bool:
        """Handle resend verification email command"""
        user = await self.user_repository.get_by_email(command.email)
        if not user:
            # Don't reveal if user exists for security
            return True

        if user.email_verified:
            # User already verified, no need to resend
            return True

        # Generate new email verification token
        user.generate_email_verification_token()
        await self.user_repository.update(user)

        # TODO: Send email with verification link
        # For now, we just generate the token

        return True

    async def handle_reset_password(self, command: ResetPasswordCommand) -> User:
        """Handle reset password command"""
        user = await self.user_repository.get_by_password_reset_token(command.token)
        if not user:
            raise ValueError("Invalid or expired reset token")

        if not user.verify_password_reset_token(command.token):
            raise ValueError("Invalid or expired reset token")

        # Set new password
        user.set_password(command.new_password)
        user.clear_password_reset_token()
        updated_user = await self.user_repository.update(user)

        # Publish event
        event = UserUpdatedEvent.create(updated_user, {"password_changed": True})
        await self.event_publisher.publish(event)

        return updated_user

    async def handle_verify_email(self, command: VerifyUserEmailCommand) -> User:
        """Handle verify email command"""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise ValueError(f"User {command.user_id} not found")

        user.verify_email()
        user.clear_email_verification_token()
        updated_user = await self.user_repository.update(user)

        # Publish event
        event = UserEmailVerifiedEvent.create(updated_user)
        await self.event_publisher.publish(event)

        return updated_user

    async def handle_record_login(self, command: RecordUserLoginCommand) -> User:
        """Handle record login command"""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise ValueError(f"User {command.user_id} not found")

        user.record_login()
        updated_user = await self.user_repository.update(user)

        # Update last login in repository
        await self.user_repository.update_last_login(command.user_id)

        # Publish event
        event = UserLoggedInEvent.create(
            updated_user,
            ip_address=command.ip_address,
            user_agent=command.user_agent,
        )
        await self.event_publisher.publish(event)

        return updated_user

    async def handle_login(self, command: UserLoginCommand) -> User | None:
        """Handle user login - verify credentials and return user"""
        user = await self.user_repository.get_by_email(command.email)
        if not user:
            return None

        if not user.verify_password(command.password):
            return None

        if not user.is_active():
            raise ValueError("Account is not active")

        # Record login
        user.record_login()
        updated_user = await self.user_repository.update(user)
        await self.user_repository.update_last_login(command.user_id)

        # Publish event
        event = UserLoggedInEvent.create(
            updated_user,
            ip_address=command.ip_address,
            user_agent=command.user_agent,
        )
        await self.event_publisher.publish(event)

        return updated_user

    async def handle_deactivate(self, command: DeactivateUserCommand) -> User:
        """Handle deactivate user command"""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise ValueError(f"User {command.user_id} not found")

        user.deactivate()
        updated_user = await self.user_repository.update(user)

        # Publish event
        event = UserUpdatedEvent.create(updated_user, {"status": {"old": "active", "new": "inactive"}})
        await self.event_publisher.publish(event)

        return updated_user

    async def handle_suspend(self, command: SuspendUserCommand) -> User:
        """Handle suspend user command"""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise ValueError(f"User {command.user_id} not found")

        user.suspend()
        updated_user = await self.user_repository.update(user)

        # Publish event
        event = UserUpdatedEvent.create(updated_user, {"status": {"old": user.status.value, "new": "suspended"}})
        await self.event_publisher.publish(event)

        return updated_user

    async def handle_activate(self, command: ActivateUserCommand) -> User:
        """Handle activate user command"""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise ValueError(f"User {command.user_id} not found")

        user.activate()
        updated_user = await self.user_repository.update(user)

        # Publish event
        event = UserUpdatedEvent.create(updated_user, {"status": {"old": user.status.value, "new": "active"}})
        await self.event_publisher.publish(event)

        return updated_user

    async def handle_delete(self, command: DeleteUserCommand) -> bool:
        """Handle delete user command"""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise ValueError(f"User {command.user_id} not found")

        user.soft_delete()
        await self.user_repository.update(user)

        # Publish event
        event = UserDeletedEvent.create(user)
        await self.event_publisher.publish(event)

        return True

    async def handle_change_role(self, command: ChangeUserRoleCommand) -> User:
        """Handle change role command"""
        user = await self.user_repository.get_by_id(command.user_id)
        if not user:
            raise ValueError(f"User {command.user_id} not found")

        old_role = user.role
        user.role = command.new_role
        user.updated_at = datetime.utcnow()

        updated_user = await self.user_repository.update(user)

        # Publish event
        event = UserUpdatedEvent.create(updated_user, {"role": {"old": old_role.value, "new": command.new_role.value}})
        await self.event_publisher.publish(event)

        return updated_user
