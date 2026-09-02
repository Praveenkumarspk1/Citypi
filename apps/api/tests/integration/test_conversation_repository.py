 """
Integration tests for ConversationRepository
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from ai_smart_city_concierge.infrastructure.repositories.conversation_repository import ConversationRepository
from ai_smart_city_concierge.domain.aggregates.conversation_aggregate import ConversationAggregate
from ai_smart_city_concierge.infrastructure.database.models import ConversationModel, MessageModel


@pytest.mark.asyncio
class TestConversationRepository:
    """Integration tests for ConversationRepository"""

    async def test_save_and_get_conversation(self, db_session: AsyncSession):
        """Test saving and retrieving a conversation"""
        repo = ConversationRepository(db_session)
        user_id = uuid4()

        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Test Conversation",
            language="en",
        )
        conversation.add_message(role="user", content="Hello")
        conversation.add_message(role="assistant", content="Hi there!")

        await repo.save(conversation)
        await db_session.commit()

        # Retrieve the conversation
        retrieved = await repo.get_by_id(conversation.id)
        assert retrieved is not None
        assert retrieved.id == conversation.id
        assert retrieved.user_id == user_id
        assert retrieved.title == "Test Conversation"
        assert retrieved.language == "en"
        assert retrieved.status == "active"
        assert len(retrieved.messages) == 2
        assert retrieved.messages[0].content == "Hello"
        assert retrieved.messages[1].content == "Hi there!"

    async def test_get_conversations_by_user(self, db_session: AsyncSession):
        """Test getting conversations by user"""
        repo = ConversationRepository(db_session)
        user_id = uuid4()
        other_user_id = uuid4()

        # Create conversations for user
        conv1 = ConversationAggregate.create(user_id=user_id, title="Conv 1")
        conv2 = ConversationAggregate.create(user_id=user_id, title="Conv 2")
        conv3 = ConversationAggregate.create(user_id=other_user_id, title="Conv 3")

        await repo.save(conv1)
        await repo.save(conv2)
        await repo.save(conv3)
        await db_session.commit()

        # Get conversations for user
        conversations = await repo.get_by_user_id(user_id)
        assert len(conversations) == 2
        assert all(c.user_id == user_id for c in conversations)

    async def test_update_conversation(self, db_session: AsyncSession):
        """Test updating a conversation"""
        repo = ConversationRepository(db_session)
        user_id = uuid4()

        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Original Title",
        )
        await repo.save(conversation)
        await db_session.commit()

        # Update conversation
        conversation.update_title("Updated Title")
        conversation.add_message(role="user", content="New message")
        await repo.save(conversation)
        await db_session.commit()

        # Verify update
        retrieved = await repo.get_by_id(conversation.id)
        assert retrieved.title == "Updated Title"
        assert len(retrieved.messages) == 1
        assert retrieved.messages[0].content == "New message"

    async def test_delete_conversation(self, db_session: AsyncSession):
        """Test deleting a conversation"""
        repo = ConversationRepository(db_session)
        user_id = uuid4()

        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="To Delete",
        )
        await repo.save(conversation)
        await db_session.commit()

        # Delete conversation
        await repo.delete(conversation.id)
        await db_session.commit()

        # Verify deletion
        retrieved = await repo.get_by_id(conversation.id)
        assert retrieved is None

    async def test_get_active_conversations(self, db_session: AsyncSession):
        """Test getting active conversations"""
        repo = ConversationRepository(db_session)
        user_id = uuid4()

        active_conv = ConversationAggregate.create(user_id=user_id, title="Active")
        ended_conv = ConversationAggregate.create(user_id=user_id, title="Ended")
        ended_conv.end_conversation()

        await repo.save(active_conv)
        await repo.save(ended_conv)
        await db_session.commit()

        active_conversations = await repo.get_active_by_user_id(user_id)
        assert len(active_conversations) == 1
        assert active_conversations[0].id == active_conv.id
        assert active_conversations[0].status == "active"

    async def test_conversation_persistence_with_events(self, db_session: AsyncSession):
        """Test that domain events are persisted with conversation"""
        repo = ConversationRepository(db_session)
        user_id = uuid4()

        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Event Test",
        )
        conversation.add_message(role="user", content="Hello")
        conversation.end_conversation(summary="Test ended")

        events = conversation.get_uncommitted_events()
        assert len(events) == 3  # Created, MessageSent, Ended

        await repo.save(conversation)
        await db_session.commit()

        # Events should be cleared after save
        assert len(conversation.get_uncommitted_events()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])