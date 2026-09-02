"""
Unit tests for ConversationAggregate
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from ai_smart_city_concierge.domain.aggregates.conversation_aggregate import ConversationAggregate
from ai_smart_city_concierge.domain.value_objects.rating import Rating
from ai_smart_city_concierge.domain.events.conversation_events import (
    ConversationStarted,
    MessageSent,
    ConversationEnded,
)


class TestConversationAggregate:
    """Test cases for ConversationAggregate"""

    def test_create_conversation(self):
        """Test creating a new conversation"""
        user_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Test Conversation",
            language="en",
        )

        assert conversation.user_id == user_id
        assert conversation.title == "Test Conversation"
        assert conversation.language == "en"
        assert conversation.status == "active"
        assert len(conversation.messages) == 0
        assert conversation.created_at is not None
        assert conversation.updated_at is not None

    def test_add_message(self):
        """Test adding a message to conversation"""
        user_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Test Conversation",
        )

        message_id = conversation.add_message(
            role="user",
            content="Hello, world!",
            metadata={"source": "web"},
        )

        assert len(conversation.messages) == 1
        msg = conversation.messages[0]
        assert msg.id == message_id
        assert msg.role == "user"
        assert msg.content == "Hello, world!"
        assert msg.metadata == {"source": "web"}

    def test_add_multiple_messages(self):
        """Test adding multiple messages"""
        user_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Test Conversation",
        )

        conversation.add_message(role="user", content="Message 1")
        conversation.add_message(role="assistant", content="Response 1")
        conversation.add_message(role="user", content="Message 2")

        assert len(conversation.messages) == 3
        assert conversation.messages[0].role == "user"
        assert conversation.messages[1].role == "assistant"
        assert conversation.messages[2].role == "user"

    def test_end_conversation(self):
        """Test ending a conversation"""
        user_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Test Conversation",
        )

        conversation.add_message(role="user", content="Hello")
        conversation.end_conversation(summary="Test conversation ended")

        assert conversation.status == "ended"
        assert conversation.ended_at is not None
        assert conversation.summary == "Test conversation ended"

    def test_cannot_add_message_to_ended_conversation(self):
        """Test that messages cannot be added to ended conversation"""
        user_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Test Conversation",
        )

        conversation.end_conversation()

        with pytest.raises(ValueError, match="Cannot add message to ended conversation"):
            conversation.add_message(role="user", content="Hello")

    def test_get_message_count(self):
        """Test getting message count"""
        user_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Test Conversation",
        )

        assert conversation.get_message_count() == 0

        conversation.add_message(role="user", content="Message 1")
        assert conversation.get_message_count() == 1

        conversation.add_message(role="assistant", content="Response 1")
        assert conversation.get_message_count() == 2

    def test_get_last_message(self):
        """Test getting last message"""
        user_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Test Conversation",
        )

        assert conversation.get_last_message() is None

        conversation.add_message(role="user", content="Message 1")
        last_msg = conversation.get_last_message()
        assert last_msg is not None
        assert last_msg.content == "Message 1"

        conversation.add_message(role="assistant", content="Response 1")
        last_msg = conversation.get_last_message()
        assert last_msg.content == "Response 1"

    def test_update_title(self):
        """Test updating conversation title"""
        user_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Old Title",
        )

        conversation.update_title("New Title")

        assert conversation.title == "New Title"
        assert conversation.updated_at is not None

    def test_add_participant(self):
        """Test adding a participant"""
        user_id = uuid4()
        participant_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Test Conversation",
        )

        conversation.add_participant(participant_id)

        assert participant_id in conversation.participants

    def test_remove_participant(self):
        """Test removing a participant"""
        user_id = uuid4()
        participant_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Test Conversation",
        )

        conversation.add_participant(participant_id)
        assert participant_id in conversation.participants

        conversation.remove_participant(participant_id)
        assert participant_id not in conversation.participants

    def test_conversation_events_emitted(self):
        """Test that domain events are emitted"""
        user_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Test Conversation",
        )

        # Check ConversationStarted event
        events = conversation.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ConversationStarted)
        assert events[0].user_id == user_id
        assert events[0].title == "Test Conversation"

        # Clear events and add message
        conversation.clear_events()
        conversation.add_message(role="user", content="Hello")

        events = conversation.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], MessageSent)
        assert events[0].role == "user"
        assert events[0].content == "Hello"

        # Clear events and end conversation
        conversation.clear_events()
        conversation.end_conversation(summary="Ended")

        events = conversation.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], ConversationEnded)
        assert events[0].summary == "Ended"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])