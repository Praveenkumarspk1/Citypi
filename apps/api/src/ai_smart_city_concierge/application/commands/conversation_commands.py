"""
Conversation Commands (CQRS Write Side)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from ...domain.entities.conversation import (
    Conversation,
    ConversationStatus,
    Message,
    MessageRole,
    MessageType,
)
from ...domain.events.domain_events import (
    ConversationArchivedEvent,
    ConversationDeletedEvent,
    ConversationMessageAddedEvent,
    ConversationStartedEvent,
    ConversationSummaryGeneratedEvent,
    ConversationUpdatedEvent,
)
from ...domain.value_objects.coordinates import Coordinates
from ..ports.event_publisher import EventPublisher
from ..ports.repositories import ConversationRepositoryPort


@dataclass
class StartConversationCommand:
    """Command to start a new conversation"""
    user_id: UUID
    title: str | None = None
    language: str = "en"
    location: Coordinates | None = None
    context: dict[str, Any] = None
    initial_message: str | None = None
    initial_message_type: MessageType = MessageType.TEXT

    def __post_init__(self):
        if self.context is None:
            self.context = {}


@dataclass
class AddMessageCommand:
    """Command to add a message to conversation"""
    conversation_id: UUID
    role: MessageRole
    content: str
    type: MessageType = MessageType.TEXT
    tokens: int = 0
    model: str | None = None
    processing_time_ms: int = 0
    attachments: list[dict[str, Any]] = None
    tool_calls: list[dict[str, Any]] = None
    tool_call_id: str | None = None
    context: dict[str, Any] = None
    location: Coordinates | None = None

    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.tool_calls is None:
            self.tool_calls = []
        if self.context is None:
            self.context = {}


@dataclass
class UpdateConversationCommand:
    """Command to update conversation"""
    conversation_id: UUID
    title: str | None = None
    language: str | None = None
    location: Coordinates | None = None
    context: dict[str, Any] | None = None
    status: ConversationStatus | None = None


@dataclass
class UpdateConversationSummaryCommand:
    """Command to update conversation summary"""
    conversation_id: UUID
    summary: str


@dataclass
class ArchiveConversationCommand:
    """Command to archive conversation"""
    conversation_id: UUID


@dataclass
class DeleteConversationCommand:
    """Command to delete conversation"""
    conversation_id: UUID


@dataclass
class ActivateConversationCommand:
    """Command to activate conversation"""
    conversation_id: UUID


class ConversationCommandHandler:
    """Handler for conversation commands"""

    def __init__(
        self,
        conversation_repository: ConversationRepositoryPortPort,
        event_publisher: EventPublisher,
    ):
        self.conversation_repository = conversation_repository
        self.event_publisher = event_publisher

    async def handle_start_conversation(self, command: StartConversationCommand) -> Conversation:
        """Handle start conversation command"""
        # Create conversation
        conversation = Conversation(
            user_id=command.user_id,
            title=command.title,
            language=command.language,
            location=command.location,
            context=command.context,
        )

        # Add initial message if provided
        if command.initial_message:
            conversation.add_user_message(
                content=command.initial_message,
                type=command.initial_message_type,
                location=command.location,
            )

        # Save
        created_conversation = await self.conversation_repository.create(conversation)

        # Publish event
        event = ConversationStartedEvent.create(created_conversation)
        await self.event_publisher.publish(event)

        return created_conversation

    async def handle_add_message(self, command: AddMessageCommand) -> Message:
        """Handle add message command"""
        conversation = await self.conversation_repository.get_by_id(command.conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {command.conversation_id} not found")

        if not conversation.is_active():
            raise ValueError("Cannot add message to inactive conversation")

        # Add message based on role
        if command.role == MessageRole.USER:
            message = conversation.add_user_message(
                content=command.content,
                type=command.type,
                location=command.location,
                tokens=command.tokens,
                model=command.model,
                processing_time_ms=command.processing_time_ms,
                attachments=command.attachments,
                context=command.context,
            )
        elif command.role == MessageRole.ASSISTANT:
            message = conversation.add_assistant_message(
                content=command.content,
                type=command.type,
                tokens=command.tokens,
                model=command.model,
                processing_time_ms=command.processing_time_ms,
                tool_calls=command.tool_calls,
                attachments=command.attachments,
                context=command.context,
            )
        elif command.role == MessageRole.SYSTEM:
            message = conversation.add_system_message(command.content)
        elif command.role == MessageRole.TOOL:
            message = conversation.add_tool_message(
                content=command.content,
                tool_call_id=command.tool_call_id,
                context=command.context,
            )
        else:
            raise ValueError(f"Unknown message role: {command.role}")

        # Update conversation in repository
        await self.conversation_repository.add_message(command.conversation_id, message)

        # Publish event
        event = ConversationMessageAddedEvent.create(conversation, message)
        await self.event_publisher.publish(event)

        return message

    async def handle_update_conversation(self, command: UpdateConversationCommand) -> Conversation:
        """Handle update conversation command"""
        conversation = await self.conversation_repository.get_by_id(command.conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {command.conversation_id} not found")

        # Track changes
        changes = {}
        if command.title is not None and command.title != conversation.title:
            changes["title"] = {"old": conversation.title, "new": command.title}
        if command.language is not None and command.language != conversation.language:
            changes["language"] = {"old": conversation.language, "new": command.language}
        if command.location is not None and command.location != conversation.location:
            changes["location"] = {"old": conversation.location.to_dict() if conversation.location else None, "new": command.location.to_dict()}
        if command.context is not None and command.context != conversation.context:
            changes["context"] = {"old": conversation.context, "new": command.context}
        if command.status is not None and command.status != conversation.status:
            changes["status"] = {"old": conversation.status.value, "new": command.status.value}

        # Update
        if command.title is not None:
            conversation.title = command.title
        if command.language is not None:
            conversation.language = command.language
        if command.location is not None:
            conversation.update_location(command.location)
        if command.context is not None:
            conversation.update_context(command.context)
        if command.status is not None:
            conversation.status = command.status

        conversation.updated_at = datetime.utcnow()

        updated_conversation = await self.conversation_repository.update(conversation)

        # Publish event
        if changes:
            event = ConversationUpdatedEvent.create(updated_conversation, changes)
            await self.event_publisher.publish(event)

        return updated_conversation

    async def handle_update_summary(self, command: UpdateConversationSummaryCommand) -> Conversation:
        """Handle update summary command"""
        conversation = await self.conversation_repository.get_by_id(command.conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {command.conversation_id} not found")

        conversation.update_summary(command.summary)
        updated_conversation = await self.conversation_repository.update(conversation)

        # Update in repository (optimized)
        await self.conversation_repository.update_summary(command.conversation_id, command.summary)

        # Publish event
        event = ConversationSummaryGeneratedEvent.create(updated_conversation, command.summary)
        await self.event_publisher.publish(event)

        return updated_conversation

    async def handle_archive(self, command: ArchiveConversationCommand) -> Conversation:
        """Handle archive conversation command"""
        conversation = await self.conversation_repository.get_by_id(command.conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {command.conversation_id} not found")

        conversation.archive()
        updated_conversation = await self.conversation_repository.update(conversation)

        # Publish event
        event = ConversationArchivedEvent.create(updated_conversation)
        await self.event_publisher.publish(event)

        return updated_conversation

    async def handle_delete(self, command: DeleteConversationCommand) -> bool:
        """Handle delete conversation command"""
        conversation = await self.conversation_repository.get_by_id(command.conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {command.conversation_id} not found")

        conversation.delete()
        await self.conversation_repository.update(conversation)

        # Publish event
        event = ConversationDeletedEvent.create(conversation)
        await self.event_publisher.publish(event)

        return True

    async def handle_activate(self, command: ActivateConversationCommand) -> Conversation:
        """Handle activate conversation command"""
        conversation = await self.conversation_repository.get_by_id(command.conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {command.conversation_id} not found")

        conversation.activate()
        updated_conversation = await self.conversation_repository.update(conversation)

        return updated_conversation
