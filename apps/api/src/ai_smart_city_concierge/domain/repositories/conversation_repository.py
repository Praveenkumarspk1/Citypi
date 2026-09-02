"""
Conversation Repository Interface
"""
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from ..entities.conversation import Conversation, ConversationStatus, Message
from .base import BaseRepository, PaginatedResult, PaginationParams


class ConversationRepository(BaseRepository[Conversation, UUID], ABC):
    """Conversation repository interface"""

    @abstractmethod
    async def get_by_user(
        self,
        user_id: UUID,
        status: ConversationStatus | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Conversation]:
        """Get conversations by user"""
        pass

    @abstractmethod
    async def get_active_by_user(self, user_id: UUID, limit: int = 10) -> list[Conversation]:
        """Get active conversations for user"""
        pass

    @abstractmethod
    async def get_with_messages(
        self,
        conversation_id: UUID,
        message_limit: int | None = None,
        message_offset: int = 0,
    ) -> Conversation | None:
        """Get conversation with messages"""
        pass

    @abstractmethod
    async def add_message(self, conversation_id: UUID, message: Message) -> None:
        """Add message to conversation"""
        pass

    @abstractmethod
    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0,
        before: datetime | None = None,
    ) -> list[Message]:
        """Get messages for conversation"""
        pass

    @abstractmethod
    async def get_message_count(self, conversation_id: UUID) -> int:
        """Get total message count for conversation"""
        pass

    @abstractmethod
    async def update_summary(self, conversation_id: UUID, summary: str) -> None:
        """Update conversation summary"""
        pass

    @abstractmethod
    async def update_context(self, conversation_id: UUID, context: dict) -> None:
        """Update conversation context"""
        pass

    @abstractmethod
    async def update_location(self, conversation_id: UUID, location: dict) -> None:
        """Update conversation location context"""
        pass

    @abstractmethod
    async def archive_old_conversations(self, days: int = 90) -> int:
        """Archive conversations older than specified days"""
        pass

    @abstractmethod
    async def get_user_conversation_stats(self, user_id: UUID) -> dict:
        """Get conversation statistics for user"""
        pass
