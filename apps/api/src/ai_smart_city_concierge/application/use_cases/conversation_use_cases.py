"""
Conversation Application Use Cases
"""
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ...domain.entities.conversation import Conversation, Message, MessageRole
from ...domain.repositories.base import PaginatedResult, PaginationParams
from ...domain.repositories.conversation_repository import ConversationRepository


@dataclass
class CreateConversationRequest:
    """Request to create a conversation"""
    user_id: UUID
    title: str | None = None
    context: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class SendMessageRequest:
    """Request to send a message"""
    conversation_id: UUID
    role: MessageRole
    content: str
    metadata: dict[str, Any] | None = None
    tokens: int | None = None
    model: str | None = None


@dataclass
class UpdateConversationRequest:
    """Request to update a conversation"""
    title: str | None = None
    context: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    is_archived: bool | None = None
    is_pinned: bool | None = None


class ConversationUseCases:
    """Conversation Application Use Cases"""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
    ):
        self.conversation_repository = conversation_repository

    async def create_conversation(self, request: CreateConversationRequest) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            user_id=request.user_id,
            title=request.title,
            context=request.context or {},
            metadata=request.metadata or {},
        )

        return await self.conversation_repository.add(conversation)

    async def get_conversation(self, conversation_id: UUID) -> Conversation | None:
        """Get conversation by ID"""
        return await self.conversation_repository.get_by_id(conversation_id)

    async def get_conversation_with_messages(
        self,
        conversation_id: UUID,
        message_limit: int = 50,
    ) -> Conversation | None:
        """Get conversation with messages"""
        return await self.conversation_repository.get_with_messages(
            conversation_id=conversation_id,
            message_limit=message_limit,
        )

    async def get_user_conversations(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Conversation]:
        """Get conversations for a user"""
        return await self.conversation_repository.get_by_user_id(
            user_id=user_id,
            pagination=pagination,
        )

    async def update_conversation(
        self,
        conversation_id: UUID,
        request: UpdateConversationRequest,
    ) -> Conversation | None:
        """Update a conversation"""
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            return None

        if request.title is not None:
            conversation.title = request.title
        if request.context is not None:
            conversation.context = request.context
        if request.metadata is not None:
            conversation.metadata = request.metadata
        if request.is_archived is not None:
            conversation.is_archived = request.is_archived
        if request.is_pinned is not None:
            conversation.is_pinned = request.is_pinned

        return await self.conversation_repository.update(conversation)

    async def delete_conversation(self, conversation_id: UUID) -> bool:
        """Delete a conversation"""
        return await self.conversation_repository.delete(conversation_id)

    async def send_message(self, request: SendMessageRequest) -> Message:
        """Send a message in a conversation"""
        message = Message(
            conversation_id=request.conversation_id,
            role=request.role,
            content=request.content,
            metadata=request.metadata or {},
            tokens=request.tokens,
            model=request.model,
        )

        await self.conversation_repository.add_message(
            conversation_id=request.conversation_id,
            message=message,
        )

        return message

    async def get_unread_count(self, user_id: UUID) -> int:
        """Get unread message count for user"""
        return await self.conversation_repository.get_unread_count(user_id)

    async def mark_messages_read(self, conversation_id: UUID) -> None:
        """Mark all messages in conversation as read"""
        conversation = await self.conversation_repository.get_with_messages(conversation_id)
        if conversation:
            for message in conversation.messages:
                if message.role == MessageRole.ASSISTANT and not message.is_read:
                    message.is_read = True
                    await self.conversation_repository.update_message(message)

    async def generate_ai_response(
        self,
        conversation_id: UUID,
        user_message: str,
        system_prompt: str | None = None,
    ) -> Message:
        """Generate AI response for a conversation"""
        # Get conversation with history
        conversation = await self.conversation_repository.get_with_messages(conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")

        # Add user message
        user_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=user_message,
        )
        await self.conversation_repository.add_message(conversation_id, user_msg)

        # Generate AI response using service
        ai_response = await self.conversation_service.generate_response(
            conversation=conversation,
            user_message=user_message,
            system_prompt=system_prompt,
        )

        # Add AI message
        ai_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=ai_response.content,
            metadata=ai_response.metadata,
            tokens=ai_response.tokens,
            model=ai_response.model,
        )
        await self.conversation_repository.add_message(conversation_id, ai_msg)

        return ai_msg

    async def get_conversation_summary(self, conversation_id: UUID) -> str | None:
        """Get conversation summary"""
        conversation = await self.conversation_repository.get_with_messages(conversation_id)
        if not conversation:
            return None

        return await self.conversation_service.generate_summary(conversation)

    async def search_conversations(
        self,
        user_id: UUID,
        query: str,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Conversation]:
        """Search conversations by content"""
        return await self.conversation_service.search_conversations(
            user_id=user_id,
            query=query,
            pagination=pagination,
        )
