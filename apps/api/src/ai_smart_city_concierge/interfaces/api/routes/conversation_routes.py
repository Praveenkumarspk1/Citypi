"""
Conversation API Routes
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ....application.use_cases.conversation_use_cases import (
    ConversationUseCases,
    CreateConversationRequest,
    SendMessageRequest,
    UpdateConversationRequest,
)
from ....domain.entities.conversation import Conversation, Message, MessageRole
from ....domain.repositories.base import PaginationParams
from ....infrastructure.config.dependencies import get_conversation_use_cases

router = APIRouter(prefix="/conversations", tags=["Conversations"])


# Request/Response Models
class CreateConversationModel(BaseModel):
    user_id: UUID
    title: str | None = None
    context: dict | None = None
    metadata: dict | None = None


class SendMessageModel(BaseModel):
    conversation_id: UUID
    role: MessageRole
    content: str
    metadata: dict | None = None
    tokens: int | None = None
    model: str | None = None


class UpdateConversationModel(BaseModel):
    title: str | None = None
    context: dict | None = None
    metadata: dict | None = None
    is_archived: bool | None = None
    is_pinned: bool | None = None


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    metadata: dict
    tokens: int | None
    model: str | None
    is_read: bool
    created_at: str


class ConversationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str | None
    context: dict
    metadata: dict
    is_archived: bool
    is_pinned: bool
    message_count: int
    created_at: str
    updated_at: str
    messages: list[MessageResponse] | None = None


class PaginatedConversationResponse(BaseModel):
    items: list[ConversationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


def message_to_response(message: Message) -> MessageResponse:
    """Convert Message entity to response model"""
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        metadata=message.metadata,
        tokens=message.tokens,
        model=message.model,
        is_read=message.is_read,
        created_at=message.created_at.isoformat() if message.created_at else "",
    )


def conversation_to_response(conversation: Conversation) -> ConversationResponse:
    """Convert Conversation entity to response model"""
    return ConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        context=conversation.context,
        metadata=conversation.metadata,
        is_archived=conversation.is_archived,
        is_pinned=conversation.is_pinned,
        message_count=conversation.message_count,
        created_at=conversation.created_at.isoformat() if conversation.created_at else "",
        updated_at=conversation.updated_at.isoformat() if conversation.updated_at else "",
        messages=[message_to_response(m) for m in conversation.messages] if conversation.messages else None,
    )


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationModel,
    use_cases: ConversationUseCases = Depends(get_conversation_use_cases),
):
    """Create a new conversation"""
    conv_request = CreateConversationRequest(
        user_id=request.user_id,
        title=request.title,
        context=request.context,
        metadata=request.metadata,
    )

    conversation = await use_cases.create_conversation(conv_request)
    return conversation_to_response(conversation)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    include_messages: bool = Query(False),
    message_limit: int = Query(50, ge=1, le=200),
    use_cases: ConversationUseCases = Depends(get_conversation_use_cases),
):
    """Get conversation by ID"""
    if include_messages:
        conversation = await use_cases.get_conversation_with_messages(
            conversation_id=conversation_id,
            message_limit=message_limit,
        )
    else:
        conversation = await use_cases.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation_to_response(conversation)


@router.get("/user/{user_id}", response_model=PaginatedConversationResponse)
async def get_user_conversations(
    user_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_cases: ConversationUseCases = Depends(get_conversation_use_cases),
):
    """Get conversations for a user"""
    result = await use_cases.get_user_conversations(
        user_id=user_id,
        pagination=PaginationParams(page=page, page_size=page_size),
    )

    return PaginatedConversationResponse(
        items=[conversation_to_response(c) for c in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    request: UpdateConversationModel,
    use_cases: ConversationUseCases = Depends(get_conversation_use_cases),
):
    """Update a conversation"""
    update_request = UpdateConversationRequest(
        title=request.title,
        context=request.context,
        metadata=request.metadata,
        is_archived=request.is_archived,
        is_pinned=request.is_pinned,
    )

    conversation = await use_cases.update_conversation(conversation_id, update_request)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation_to_response(conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    use_cases: ConversationUseCases = Depends(get_conversation_use_cases),
):
    """Delete a conversation"""
    success = await use_cases.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    request: SendMessageModel,
    use_cases: ConversationUseCases = Depends(get_conversation_use_cases),
):
    """Send a message in a conversation"""
    msg_request = SendMessageRequest(
        conversation_id=request.conversation_id,
        role=request.role,
        content=request.content,
        metadata=request.metadata,
        tokens=request.tokens,
        model=request.model,
    )

    message = await use_cases.send_message(msg_request)
    return message_to_response(message)


@router.post("/{conversation_id}/ai-response", response_model=MessageResponse)
async def generate_ai_response(
    conversation_id: UUID,
    user_message: str = Query(..., min_length=1),
    system_prompt: str | None = Query(None),
    use_cases: ConversationUseCases = Depends(get_conversation_use_cases),
):
    """Generate AI response for a conversation"""
    try:
        message = await use_cases.generate_ai_response(
            conversation_id=conversation_id,
            user_message=user_message,
            system_prompt=system_prompt,
        )
        return message_to_response(message)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{conversation_id}/summary")
async def get_conversation_summary(
    conversation_id: UUID,
    use_cases: ConversationUseCases = Depends(get_conversation_use_cases),
):
    """Get conversation summary"""
    summary = await use_cases.get_conversation_summary(conversation_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"summary": summary}


@router.post("/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_messages_read(
    conversation_id: UUID,
    use_cases: ConversationUseCases = Depends(get_conversation_use_cases),
):
    """Mark all messages in conversation as read"""
    await use_cases.mark_messages_read(conversation_id)


@router.get("/user/{user_id}/unread-count")
async def get_unread_count(
    user_id: UUID,
    use_cases: ConversationUseCases = Depends(get_conversation_use_cases),
):
    """Get unread message count for user"""
    count = await use_cases.get_unread_count(user_id)
    return {"unread_count": count}


@router.post("/user/{user_id}/search", response_model=PaginatedConversationResponse)
async def search_conversations(
    user_id: UUID,
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_cases: ConversationUseCases = Depends(get_conversation_use_cases),
):
    """Search conversations by content"""
    result = await use_cases.search_conversations(
        user_id=user_id,
        query=query,
        pagination=PaginationParams(page=page, page_size=page_size),
    )

    return PaginatedConversationResponse(
        items=[conversation_to_response(c) for c in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )
