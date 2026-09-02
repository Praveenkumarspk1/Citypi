"""
Conversation Application Service
"""
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
from ...domain.repositories.conversation_repository import ConversationRepository
from ...domain.services.conversation_manager import ConversationManager
from ...domain.specifications.conversation_specification import (
    ConversationActiveSpecification,
    ConversationArchivedSpecification,
    ConversationUserSpecification,
)
from ..ports.cache import CachePort
from ..ports.event_publisher import EventPublisher
from ..ports.external_services import LLMServicePort, EmbeddingServicePort, VectorDBServicePort


class ConversationService:
    """Application service for conversation management"""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        conversation_manager: ConversationManager,
        llm_service: LLMServicePort,
        embedding_service: EmbeddingServicePort,
        vector_db: VectorDBServicePort,
        cache: CachePort,
        event_bus: EventPublisher,
    ):
        self.conversation_repository = conversation_repository
        self.conversation_manager = conversation_manager
        self.llm_service = llm_service
        self.embedding_service = embedding_service
        self.vector_db = vector_db
        self.cache = cache
        self.event_bus = event_bus

    async def start_conversation(
        self,
        user_id: UUID,
        title: str | None = None,
        language: str = "en",
        location: Any = None,
        context: dict[str, Any] | None = None,
        initial_message: str | None = None,
        initial_message_type: MessageType = MessageType.TEXT,
    ) -> Conversation:
        """Start a new conversation"""
        conversation = Conversation(
            user_id=user_id,
            title=title,
            language=language,
            location=location,
            context=context or {},
        )

        if initial_message:
            conversation.add_user_message(
                content=initial_message,
                type=initial_message_type,
                location=location,
            )

        created_conversation = await self.conversation_repository.create(conversation)

        # Publish domain event
        event = ConversationStartedEvent.create(created_conversation)
        await self.event_bus.publish(event)

        # Cache the conversation
        await self.cache.set(f"conversation:{created_conversation.id}", created_conversation)

        return created_conversation

    async def add_message(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        type: MessageType = MessageType.TEXT,
        tokens: int = 0,
        model: str | None = None,
        processing_time_ms: int = 0,
        attachments: list[dict[str, Any]] | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        tool_call_id: str | None = None,
        context: dict[str, Any] | None = None,
        location: Any = None,
    ) -> Message:
        """Add a message to conversation"""
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if not conversation.is_active():
            raise ValueError("Cannot add message to inactive conversation")

        # Add message based on role
        if role == MessageRole.USER:
            message = conversation.add_user_message(
                content=content,
                type=type,
                location=location,
                tokens=tokens,
                model=model,
                processing_time_ms=processing_time_ms,
                attachments=attachments or [],
                context=context or {},
            )
        elif role == MessageRole.ASSISTANT:
            message = conversation.add_assistant_message(
                content=content,
                type=type,
                tokens=tokens,
                model=model,
                processing_time_ms=processing_time_ms,
                tool_calls=tool_calls or [],
                attachments=attachments or [],
                context=context or {},
            )
        elif role == MessageRole.SYSTEM:
            message = conversation.add_system_message(content)
        elif role == MessageRole.TOOL:
            message = conversation.add_tool_message(
                content=content,
                tool_call_id=tool_call_id,
                context=context or {},
            )
        else:
            raise ValueError(f"Unknown message role: {role}")

        # Update conversation in repository
        await self.conversation_repository.add_message(conversation_id, message)

        # Publish domain event
        event = ConversationMessageAddedEvent.create(conversation, message)
        await self.event_bus.publish(event)

        # Update cache
        await self.cache.set(f"conversation:{conversation_id}", conversation)

        return message

    async def get_conversation(self, conversation_id: UUID) -> Conversation | None:
        """Get conversation by ID"""
        # Try cache first
        cached = await self.cache.get(f"conversation:{conversation_id}")
        if cached:
            return cached

        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if conversation:
            await self.cache.set(f"conversation:{conversation_id}", conversation)
        return conversation

    async def get_user_conversations(
        self,
        user_id: UUID,
        status: ConversationStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Conversation], int]:
        """Get conversations for a user with pagination"""
        spec = ConversationUserSpecification(user_id)
        if status:
            if status == ConversationStatus.ACTIVE:
                spec = spec & ConversationActiveSpecification()
            elif status == ConversationStatus.ARCHIVED:
                spec = spec & ConversationArchivedSpecification()

        return await self.conversation_repository.find(
            specification=spec,
            page=page,
            page_size=page_size,
        )

    async def update_conversation(
        self,
        conversation_id: UUID,
        title: str | None = None,
        language: str | None = None,
        location: Any = None,
        context: dict[str, Any] | None = None,
        status: ConversationStatus | None = None,
    ) -> Conversation | None:
        """Update conversation"""
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            return None

        changes = {}
        if title is not None and title != conversation.title:
            changes["title"] = {"old": conversation.title, "new": title}
        if language is not None and language != conversation.language:
            changes["language"] = {"old": conversation.language, "new": language}
        if location is not None and location != conversation.location:
            changes["location"] = {
                "old": conversation.location.to_dict() if conversation.location else None,
                "new": location.to_dict() if location else None,
            }
        if context is not None and context != conversation.context:
            changes["context"] = {"old": conversation.context, "new": context}
        if status is not None and status != conversation.status:
            changes["status"] = {"old": conversation.status.value, "new": status.value}

        if title is not None:
            conversation.title = title
        if language is not None:
            conversation.language = language
        if location is not None:
            conversation.update_location(location)
        if context is not None:
            conversation.update_context(context)
        if status is not None:
            conversation.status = status

        conversation.updated_at = datetime.utcnow()

        updated_conversation = await self.conversation_repository.update(conversation)

        if changes:
            event = ConversationUpdatedEvent.create(updated_conversation, changes)
            await self.event_bus.publish(event)

        await self.cache.set(f"conversation:{conversation_id}", updated_conversation)

        return updated_conversation

    async def update_summary(self, conversation_id: UUID, summary: str) -> Conversation | None:
        """Update conversation summary"""
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            return None

        conversation.update_summary(summary)
        updated_conversation = await self.conversation_repository.update(conversation)
        await self.conversation_repository.update_summary(conversation_id, summary)

        event = ConversationSummaryGeneratedEvent.create(updated_conversation, summary)
        await self.event_bus.publish(event)

        await self.cache.set(f"conversation:{conversation_id}", updated_conversation)

        return updated_conversation

    async def archive_conversation(self, conversation_id: UUID) -> Conversation | None:
        """Archive conversation"""
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            return None

        conversation.archive()
        updated_conversation = await self.conversation_repository.update(conversation)

        event = ConversationArchivedEvent.create(updated_conversation)
        await self.event_bus.publish(event)

        await self.cache.set(f"conversation:{conversation_id}", updated_conversation)

        return updated_conversation

    async def delete_conversation(self, conversation_id: UUID) -> bool:
        """Delete conversation"""
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            return False

        conversation.delete()
        await self.conversation_repository.update(conversation)

        event = ConversationDeletedEvent.create(conversation)
        await self.event_bus.publish(event)

        await self.cache.delete(f"conversation:{conversation_id}")

        return True

    async def activate_conversation(self, conversation_id: UUID) -> Conversation | None:
        """Activate conversation"""
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            return None

        conversation.activate()
        updated_conversation = await self.conversation_repository.update(conversation)

        await self.cache.set(f"conversation:{conversation_id}", updated_conversation)

        return updated_conversation

    async def generate_ai_response(
        self,
        conversation_id: UUID,
        user_message: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> Message:
        """Generate AI response for conversation"""
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Prepare messages for LLM
        messages = conversation.get_messages_for_llm(max_messages=20)

        # Add system context if available
        if conversation.context:
            system_content = f"Context: {conversation.context}"
            messages.insert(0, {"role": "system", "content": system_content})

        # Call LLM
        response = await self.llm_service.chat_completion(
            messages=messages,
            tools=tools,
            temperature=0.7,
        )

        # Add assistant message
        assistant_message = conversation.add_assistant_message(
            content=response.content,
            tokens=response.tokens,
            model=response.model,
            processing_time_ms=response.processing_time_ms,
            tool_calls=response.tool_calls or [],
        )

        await self.conversation_repository.add_message(conversation_id, assistant_message)
        await self.cache.set(f"conversation:{conversation_id}", conversation)

        event = ConversationMessageAddedEvent.create(conversation, assistant_message)
        await self.event_bus.publish(event)

        return assistant_message