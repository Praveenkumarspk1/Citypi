"""
SQLAlchemy Conversation Repository Implementation
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.conversation import Conversation, Message, MessageRole
from ....domain.repositories.base import FilterParams, PaginatedResult, PaginationParams, SortParams
from ....domain.repositories.conversation_repository import ConversationRepository
from ..models.conversation import ConversationModel, MessageModel


class SQLAlchemyConversationRepository(ConversationRepository):
    """SQLAlchemy implementation of Conversation repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Conversation | None:
        """Get conversation by ID"""
        stmt = select(ConversationModel).where(ConversationModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None

    async def get_by_ids(self, ids: list[UUID]) -> list[Conversation]:
        """Get multiple conversations by IDs"""
        stmt = select(ConversationModel).where(ConversationModel.id.in_(ids))
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_entity() for m in models]

    async def get_by_user_id(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Conversation]:
        """Get conversations by user ID"""
        stmt = select(ConversationModel).where(ConversationModel.user_id == user_id)
        count_stmt = select(func.count(ConversationModel.id)).where(ConversationModel.user_id == user_id)

        stmt = stmt.order_by(desc(ConversationModel.updated_at))

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        if pagination:
            stmt = stmt.offset((pagination.page - 1) * pagination.page_size)
            stmt = stmt.limit(pagination.page_size)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        items = [m.to_entity() for m in models]

        page = pagination.page if pagination else 1
        page_size = pagination.page_size if pagination else len(items)
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    async def get_with_messages(
        self,
        conversation_id: UUID,
        message_limit: int = 50,
    ) -> Conversation | None:
        """Get conversation with messages"""
        stmt = select(ConversationModel).where(ConversationModel.id == conversation_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        # Get messages
        msg_stmt = select(MessageModel).where(
            MessageModel.conversation_id == conversation_id
        ).order_by(MessageModel.created_at).limit(message_limit)

        msg_result = await self.session.execute(msg_stmt)
        messages = msg_result.scalars().all()

        entity = model.to_entity()
        entity.messages = [m.to_entity() for m in messages]
        return entity

    async def list(
        self,
        pagination: PaginationParams | None = None,
        sort: SortParams | None = None,
        filters: FilterParams | None = None,
    ) -> PaginatedResult[Conversation]:
        """List conversations with pagination, sorting, and filtering"""
        stmt = select(ConversationModel)
        count_stmt = select(func.count(ConversationModel.id))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(ConversationModel, key):
                    column = getattr(ConversationModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))

        if sort and hasattr(ConversationModel, sort.field):
            column = getattr(ConversationModel, sort.field)
            if sort.order.lower() == "desc":
                stmt = stmt.order_by(desc(column))
            else:
                stmt = stmt.order_by(asc(column))
        else:
            stmt = stmt.order_by(desc(ConversationModel.updated_at))

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        if pagination:
            stmt = stmt.offset((pagination.page - 1) * pagination.page_size)
            stmt = stmt.limit(pagination.page_size)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        items = [m.to_entity() for m in models]

        page = pagination.page if pagination else 1
        page_size = pagination.page_size if pagination else len(items)
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    async def add(self, entity: Conversation) -> Conversation:
        """Add a new conversation"""
        model = ConversationModel.from_entity(entity)
        self.session.add(model)
        await self.session.flush()
        return model.to_entity()

    async def update(self, entity: Conversation) -> Conversation:
        """Update an existing conversation"""
        stmt = select(ConversationModel).where(ConversationModel.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Conversation with id {entity.id} not found")

        for key, value in entity.__dict__.items():
            if hasattr(model, key) and key not in ('id', 'created_at'):
                setattr(model, key, value)

        model.updated_at = datetime.utcnow()
        await self.session.flush()
        return model.to_entity()

    async def delete(self, id: UUID) -> bool:
        """Delete a conversation"""
        stmt = select(ConversationModel).where(ConversationModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            await self.session.flush()
            return True
        return False

    async def exists(self, id: UUID) -> bool:
        """Check if conversation exists"""
        stmt = select(func.count(ConversationModel.id)).where(ConversationModel.id == id)
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def count(self, filters: FilterParams | None = None) -> int:
        """Count conversations with optional filters"""
        stmt = select(func.count(ConversationModel.id))

        if filters and filters.filters:
            conditions = []
            for key, value in filters.filters.items():
                if hasattr(ConversationModel, key):
                    column = getattr(ConversationModel, key)
                    if isinstance(value, list):
                        conditions.append(column.in_(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def add_message(self, conversation_id: UUID, message: Message) -> None:
        """Add message to conversation"""
        model = MessageModel.from_entity(message)
        self.session.add(model)

        # Update conversation's updated_at and message_count
        stmt = select(ConversationModel).where(ConversationModel.id == conversation_id)
        result = await self.session.execute(stmt)
        conv_model = result.scalar_one_or_none()

        if conv_model:
            conv_model.updated_at = datetime.utcnow()
            conv_model.message_count += 1

        await self.session.flush()

    async def update_message(self, message: Message) -> None:
        """Update a message"""
        stmt = select(MessageModel).where(MessageModel.id == message.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            for key, value in message.__dict__.items():
                if hasattr(model, key) and key not in ('id', 'created_at'):
                    setattr(model, key, value)
            await self.session.flush()

    async def get_unread_count(self, user_id: UUID) -> int:
        """Get unread message count for user"""
        stmt = select(func.count(MessageModel.id)).where(
            and_(
                MessageModel.conversation_id.in_(
                    select(ConversationModel.id).where(ConversationModel.user_id == user_id)
                ),
                MessageModel.role == MessageRole.ASSISTANT,
                not MessageModel.is_read
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
