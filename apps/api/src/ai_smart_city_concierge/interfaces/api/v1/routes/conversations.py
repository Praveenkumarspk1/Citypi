"""
Conversation Routes
"""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ai_smart_city_concierge.application.commands.conversation_commands import (
    ActivateConversationCommand,
    AddMessageCommand,
    ArchiveConversationCommand,
    ConversationCommandHandler,
    DeleteConversationCommand,
    StartConversationCommand,
    UpdateConversationCommand,
    UpdateConversationSummaryCommand,
)
from ai_smart_city_concierge.application.dto.request import (
    AddMessageRequest,
    StartConversationRequest,
    UpdateConversationRequest,
    UpdateConversationSummaryRequest,
)
from ai_smart_city_concierge.application.dto.response import (
    ConversationResponse,
    MessageResponse,
    PaginatedResponse,
)
from ai_smart_city_concierge.application.queries.conversation_queries import (
    ConversationQueryHandler,
    GetActiveConversationsByUserQuery,
    GetConversationMessagesQuery,
    GetConversationQuery,
    GetConversationsByUserQuery,
    GetConversationStatsQuery,
)
from ai_smart_city_concierge.domain.entities.conversation import (
    ConversationStatus,
)
from ai_smart_city_concierge.infrastructure.auth import get_current_user
from ai_smart_city_concierge.infrastructure.di.container import (
    get_conversation_command_handler,
    get_conversation_query_handler,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def start_conversation(
    request: StartConversationRequest,
    handler: ConversationCommandHandler = Depends(get_conversation_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ConversationResponse:
    """Start a new conversation"""
    command = StartConversationCommand(
        user_id=UUID(current_user["id"]),
        title=request.title,
        language=request.language,
        location=request.location,
        context=request.context,
        initial_message=request.initial_message,
        initial_message_type=request.initial_message_type,
    )
    conversation = await handler.handle_start_conversation(command)
    return ConversationResponse.from_entity(conversation)


@router.get("/", response_model=PaginatedResponse[ConversationResponse])
async def get_conversations(
    status: ConversationStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    handler: ConversationQueryHandler = Depends(get_conversation_query_handler),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[ConversationResponse]:
    """Get conversations for current user"""
    query = GetConversationsByUserQuery(
        user_id=UUID(current_user["id"]),
        status=status,
        page=page,
        page_size=page_size,
    )
    return await handler.handle_get_conversations_by_user(query)


@router.get("/active", response_model=list[ConversationResponse])
async def get_active_conversations(
    limit: int = Query(10, ge=1, le=50),
    handler: ConversationQueryHandler = Depends(get_conversation_query_handler),
    current_user: dict = Depends(get_current_user),
) -> list[ConversationResponse]:
    """Get active conversations for current user"""
    query = GetActiveConversationsByUserQuery(
        user_id=UUID(current_user["id"]),
        limit=limit,
    )
    return await handler.handle_get_active_conversations_by_user(query)


@router.get("/stats", response_model=dict)
async def get_conversation_stats(
    handler: ConversationQueryHandler = Depends(get_conversation_query_handler),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get conversation statistics for current user"""
    query = GetConversationStatsQuery(user_id=UUID(current_user["id"]))
    return await handler.handle_get_conversation_stats(query)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    include_messages: bool = False,
    message_limit: int = Query(50, ge=1, le=200),
    message_offset: int = Query(0, ge=0),
    handler: ConversationQueryHandler = Depends(get_conversation_query_handler),
    current_user: dict = Depends(get_current_user),
) -> ConversationResponse:
    """Get conversation by ID"""
    query = GetConversationQuery(
        conversation_id=conversation_id,
        include_messages=include_messages,
        message_limit=message_limit,
        message_offset=message_offset,
    )
    conversation = await handler.handle_get_conversation(query)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify ownership
    if str(conversation.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    return conversation


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    before: datetime | None = None,
    handler: ConversationQueryHandler = Depends(get_conversation_query_handler),
    current_user: dict = Depends(get_current_user),
) -> list[MessageResponse]:
    """Get messages for a conversation"""
    # First verify conversation ownership
    conv_query = GetConversationQuery(conversation_id=conversation_id)
    conversation = await handler.handle_get_conversation(conv_query)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if str(conversation.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    query = GetConversationMessagesQuery(
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
        before=before,
    )
    return await handler.handle_get_conversation_messages(query)


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: UUID,
    request: AddMessageRequest,
    handler: ConversationCommandHandler = Depends(get_conversation_command_handler),
    current_user: dict = Depends(get_current_user),
) -> MessageResponse:
    """Add a message to conversation"""
    # Verify conversation ownership
    from ....application.queries.conversation_queries import GetConversationQuery
    query_handler = get_conversation_query_handler()
    conv_query = GetConversationQuery(conversation_id=conversation_id)
    conversation = await query_handler.handle_get_conversation(conv_query)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if str(conversation.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    command = AddMessageCommand(
        conversation_id=conversation_id,
        role=request.role,
        content=request.content,
        type=request.type,
        tokens=request.tokens,
        model=request.model,
        processing_time_ms=request.processing_time_ms,
        attachments=request.attachments,
        tool_calls=request.tool_calls,
        tool_call_id=request.tool_call_id,
        context=request.context,
        location=request.location,
    )
    message = await handler.handle_add_message(command)
    return MessageResponse.from_entity(message)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    request: UpdateConversationRequest,
    handler: ConversationCommandHandler = Depends(get_conversation_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ConversationResponse:
    """Update conversation"""
    # Verify ownership
    from ....application.queries.conversation_queries import GetConversationQuery
    query_handler = get_conversation_query_handler()
    conv_query = GetConversationQuery(conversation_id=conversation_id)
    conversation = await query_handler.handle_get_conversation(conv_query)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if str(conversation.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    command = UpdateConversationCommand(
        conversation_id=conversation_id,
        title=request.title,
        language=request.language,
        location=request.location,
        context=request.context,
        status=request.status,
    )
    updated = await handler.handle_update_conversation(command)
    return ConversationResponse.from_entity(updated)


@router.patch("/{conversation_id}/summary", response_model=ConversationResponse)
async def update_conversation_summary(
    conversation_id: UUID,
    request: UpdateConversationSummaryRequest,
    handler: ConversationCommandHandler = Depends(get_conversation_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ConversationResponse:
    """Update conversation summary"""
    # Verify ownership
    from ....application.queries.conversation_queries import GetConversationQuery
    query_handler = get_conversation_query_handler()
    conv_query = GetConversationQuery(conversation_id=conversation_id)
    conversation = await query_handler.handle_get_conversation(conv_query)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if str(conversation.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    command = UpdateConversationSummaryCommand(
        conversation_id=conversation_id,
        summary=request.summary,
    )
    updated = await handler.handle_update_summary(command)
    return ConversationResponse.from_entity(updated)


@router.post("/{conversation_id}/archive", response_model=ConversationResponse)
async def archive_conversation(
    conversation_id: UUID,
    handler: ConversationCommandHandler = Depends(get_conversation_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ConversationResponse:
    """Archive conversation"""
    # Verify ownership
    from ai_smart_city_concierge.application.queries.conversation_queries import (
        GetConversationQuery,
    )
    query_handler = get_conversation_query_handler()
    conv_query = GetConversationQuery(conversation_id=conversation_id)
    conversation = await query_handler.handle_get_conversation(conv_query)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if str(conversation.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    command = ArchiveConversationCommand(conversation_id=conversation_id)
    archived = await handler.handle_archive(command)
    return ConversationResponse.from_entity(archived)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    handler: ConversationCommandHandler = Depends(get_conversation_command_handler),
    current_user: dict = Depends(get_current_user),
) -> None:
    """Delete conversation"""
    # Verify ownership
    from ai_smart_city_concierge.application.queries.conversation_queries import (
        GetConversationQuery,
    )
    query_handler = get_conversation_query_handler()
    conv_query = GetConversationQuery(conversation_id=conversation_id)
    conversation = await query_handler.handle_get_conversation(conv_query)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if str(conversation.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    command = DeleteConversationCommand(conversation_id=conversation_id)
    await handler.handle_delete(command)


@router.post("/{conversation_id}/activate", response_model=ConversationResponse)
async def activate_conversation(
    conversation_id: UUID,
    handler: ConversationCommandHandler = Depends(get_conversation_command_handler),
    current_user: dict = Depends(get_current_user),
) -> ConversationResponse:
    """Activate conversation"""
    # Verify ownership
    from ai_smart_city_concierge.application.queries.conversation_queries import (
        GetConversationQuery,
    )
    query_handler = get_conversation_query_handler()
    conv_query = GetConversationQuery(conversation_id=conversation_id)
    conversation = await query_handler.handle_get_conversation(conv_query)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if str(conversation.user_id) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    command = ActivateConversationCommand(conversation_id=conversation_id)
    activated = await handler.handle_activate(command)
    return ConversationResponse.from_entity(activated)
