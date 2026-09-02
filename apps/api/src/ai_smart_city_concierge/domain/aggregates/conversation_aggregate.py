"""
Conversation Aggregate
"""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from ..entities.conversation import (
    Conversation,
    ConversationStatus,
    Message,
    MessageRole,
    MessageType,
)
from ..events import (
    ConversationArchived,
    ConversationEnded,
    ConversationStarted,
    MessageReactionAdded,
    MessageSent,
)
from ..value_objects.coordinates import Coordinates


@dataclass
class ConversationAggregate:
    """
    Conversation aggregate root.
    Manages conversation lifecycle, messages, and participants.
    """
    conversation: Conversation
    _uncommitted_events: list = field(default_factory=list, init=False)

    @classmethod
    def create(
        cls,
        user_id: UUID,
        title: str | None = None,
        initial_message: str | None = None,
        location: Coordinates | None = None,
        language: str = "en",
    ) -> "ConversationAggregate":
        """Create a new conversation"""
        conversation = Conversation(
            id=uuid4(),
            user_id=user_id,
            title=title or "New Conversation",
            status=ConversationStatus.ACTIVE,
            language=language,
            location=location,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        aggregate = cls(conversation=conversation)

        if initial_message:
            aggregate.add_message(
                role=MessageRole.USER,
                content=initial_message,
                message_type=MessageType.TEXT,
            )

        aggregate._add_event(ConversationStarted(
            conversation_id=conversation.id,
            user_id=user_id,
            title=conversation.title,
            timestamp=datetime.utcnow(),
        ))
        return aggregate

    def add_message(
        self,
        role: MessageRole,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: dict | None = None,
        parent_message_id: UUID | None = None,
    ) -> Message:
        """Add a message to the conversation"""
        message = Message(
            id=uuid4(),
            conversation_id=self.conversation.id,
            role=role,
            content=content,
            message_type=message_type,
            metadata=metadata or {},
            parent_message_id=parent_message_id,
            created_at=datetime.utcnow(),
        )

        self.conversation.messages.append(message)
        self.conversation.updated_at = datetime.utcnow()

        self._add_event(MessageSent(
            conversation_id=self.conversation.id,
            message_id=message.id,
            role=role,
            content=content,
            message_type=message_type,
            timestamp=datetime.utcnow(),
        ))
        return message

    def add_user_message(self, content: str, metadata: dict | None = None) -> Message:
        """Add a user message"""
        return self.add_message(MessageRole.USER, content, MessageType.TEXT, metadata)

    def add_assistant_message(
        self,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: dict | None = None,
    ) -> Message:
        """Add an assistant message"""
        return self.add_message(MessageRole.ASSISTANT, content, message_type, metadata)

    def add_system_message(self, content: str, metadata: dict | None = None) -> Message:
        """Add a system message"""
        return self.add_message(MessageRole.SYSTEM, content, MessageType.SYSTEM, metadata)

    def end_conversation(self, reason: str = "") -> None:
        """End the conversation"""
        if self.conversation.status == ConversationStatus.ACTIVE:
            self.conversation.status = ConversationStatus.ENDED
            self.conversation.ended_at = datetime.utcnow()
            self.conversation.updated_at = datetime.utcnow()
            self._add_event(ConversationEnded(
                conversation_id=self.conversation.id,
                reason=reason,
                timestamp=datetime.utcnow(),
            ))

    def archive(self) -> None:
        """Archive the conversation"""
        if self.conversation.status != ConversationStatus.ARCHIVED:
            self.conversation.status = ConversationStatus.ARCHIVED
            self.conversation.updated_at = datetime.utcnow()
            self._add_event(ConversationArchived(
                conversation_id=self.conversation.id,
                timestamp=datetime.utcnow(),
            ))

    def add_reaction(self, message_id: UUID, user_id: UUID, reaction: str) -> None:
        """Add reaction to a message"""
        for message in self.conversation.messages:
            if message.id == message_id:
                if reaction not in message.reactions:
                    message.reactions[reaction] = []
                if user_id not in message.reactions[reaction]:
                    message.reactions[reaction].append(user_id)
                    self.conversation.updated_at = datetime.utcnow()
                    self._add_event(MessageReactionAdded(
                        conversation_id=self.conversation.id,
                        message_id=message_id,
                        user_id=user_id,
                        reaction=reaction,
                        timestamp=datetime.utcnow(),
                    ))
                break

    def update_title(self, title: str) -> None:
        """Update conversation title"""
        if self.conversation.title != title:
            self.conversation.title = title
            self.conversation.updated_at = datetime.utcnow()

    def set_language(self, language: str) -> None:
        """Set conversation language"""
        if self.conversation.language != language:
            self.conversation.language = language
            self.conversation.updated_at = datetime.utcnow()

    def set_location(self, location: Coordinates) -> None:
        """Set conversation location context"""
        self.conversation.location = location
        self.conversation.updated_at = datetime.utcnow()

    def get_messages(
        self,
        limit: int | None = None,
        before: datetime | None = None,
        after: datetime | None = None,
    ) -> list[Message]:
        """Get messages with optional filtering"""
        messages = self.conversation.messages

        if after:
            messages = [m for m in messages if m.created_at > after]
        if before:
            messages = [m for m in messages if m.created_at < before]

        messages.sort(key=lambda m: m.created_at)

        if limit:
            messages = messages[-limit:]

        return messages

    def get_context_window(
        self,
        max_tokens: int = 4000,
        system_prompt: str | None = None,
    ) -> list[Message]:
        """Get messages for LLM context window (most recent first)"""
        messages = self.conversation.messages.copy()
        messages.sort(key=lambda m: m.created_at, reverse=True)

        context_messages = []
        token_count = 0

        if system_prompt:
            # Rough token estimation: ~4 chars per token
            token_count += len(system_prompt) // 4

        for message in messages:
            msg_tokens = len(message.content) // 4 + 10  # overhead
            if token_count + msg_tokens > max_tokens:
                break
            context_messages.append(message)
            token_count += msg_tokens

        context_messages.reverse()  # chronological order
        return context_messages

    def _add_event(self, event) -> None:
        self._uncommitted_events.append(event)

    def get_uncommitted_events(self) -> list:
        events = self._uncommitted_events.copy()
        self._uncommitted_events.clear()
        return events

    def to_dict(self) -> dict:
        return {
            "conversation": self.conversation.to_dict(),
            "uncommitted_events_count": len(self._uncommitted_events),
        }
