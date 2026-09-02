"""
Conversation Queries (CQRS Read Side)
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ...domain.entities.conversation import ConversationStatus
from ..dto.response import ConversationResponse, MessageResponse, PaginatedResponse
from ..ports.repositories import ConversationRepositoryPort


@dataclass
class GetConversationQuery:
    """Query to get conversation by ID"""
    conversation_id: UUID
    include_messages: bool = False
    message_limit: int = 50
    message_offset: int = 0


@dataclass
class GetConversationsByUserQuery:
    """Query to get conversations by user"""
    user_id: UUID
    status: ConversationStatus | None = None
    page: int = 1
    page_size: int = 20


@dataclass
class GetActiveConversationsByUserQuery:
    """Query to get active conversations by user"""
    user_id: UUID
    limit: int = 10


@dataclass
class GetConversationMessagesQuery:
    """Query to get messages for a conversation"""
    conversation_id: UUID
    limit: int = 50
    offset: int = 0
    before: datetime | None = None


@dataclass
class GetConversationStatsQuery:
    """Query to get conversation statistics for user"""
    user_id: UUID


class ConversationQueryHandler:
    """Handler for conversation queries"""

    def __init__(self, conversation_repository: ConversationRepositoryPortPort):
        self.conversation_repository = conversation_repository

    async def handle_get_conversation(self, query: GetConversationQuery) -> ConversationResponse | None:
        """Handle get conversation query"""
        if query.include_messages:
            conversation = await self.conversation_repository.get_with_messages(
                query.conversation_id,
                message_limit=query.message_limit,
                message_offset=query.message_offset,
            )
        else:
            conversation = await self.conversation_repository.get_by_id(query.conversation_id)

        if not conversation:
            return None

        return ConversationResponse.from_entity(conversation, include_messages=query.include_messages)

    async def handle_get_conversations_by_user(self, query: GetConversationsByUserQuery) -> PaginatedResponse[ConversationResponse]:
        """Handle get conversations by user query"""
        from ..ports.repositories import PaginationParams

        pagination = PaginationParams(page=query.page, page_size=query.page_size)
        result = await self.conversation_repository.get_by_user(
            query.user_id,
            status=query.status,
            pagination=pagination,
        )

        return PaginatedResponse(
            items=[ConversationResponse.from_entity(conv) for conv in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            has_next=result.has_next,
            has_prev=result.has_prev,
        )

    async def handle_get_active_conversations_by_user(self, query: GetActiveConversationsByUserQuery) -> list[ConversationResponse]:
        """Handle get active conversations by user query"""
        conversations = await self.conversation_repository.get_active_by_user(query.user_id, query.limit)
        return [ConversationResponse.from_entity(conv) for conv in conversations]

    async def handle_get_conversation_messages(self, query: GetConversationMessagesQuery) -> list[MessageResponse]:
        """Handle get conversation messages query"""
        messages = await self.conversation_repository.get_messages(
            query.conversation_id,
            limit=query.limit,
            offset=query.offset,
            before=query.before,
        )
        return [MessageResponse.from_entity(msg) for msg in messages]

    async def handle_get_conversation_stats(self, query: GetConversationStatsQuery) -> dict:
        """Handle get conversation stats query"""
        return await self.conversation_repository.get_user_conversation_stats(query.user_id)
