"""
Feedback Routes
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ai_smart_city_concierge.application.dto.request import (
    CreateFeedbackRequest,
    RespondFeedbackRequest,
    UpdateFeedbackRequest,
)
from ai_smart_city_concierge.application.dto.response import FeedbackResponse, PaginatedResponse
from ai_smart_city_concierge.domain.entities.feedback import (
    FeedbackSentiment,
    FeedbackStatus,
    FeedbackType,
)
from ai_smart_city_concierge.infrastructure.auth import get_current_user
from ai_smart_city_concierge.infrastructure.di.container import get_feedback_use_cases
from ai_smart_city_concierge.application.use_cases.feedback_use_cases import FeedbackUseCases

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    request: CreateFeedbackRequest,
    service: FeedbackUseCases = Depends(get_feedback_use_cases),
    current_user: dict = Depends(get_current_user),
) -> FeedbackResponse:
    """Create new feedback"""
    from ...domain.entities.feedback import Feedback, FeedbackType, FeedbackTargetType, FeedbackSentiment, FeedbackStatus
    
    feedback = Feedback(
        user_id=UUID(current_user["id"]),
        type=FeedbackType(request.type),
        target_type=FeedbackTargetType(request.target_type),
        target_id=request.target_id,
        title=request.title,
        content=request.content,
        rating=request.rating,
        sentiment=FeedbackSentiment(request.sentiment) if request.sentiment else FeedbackSentiment.NEUTRAL,
        status=FeedbackStatus.PENDING,
        categories=request.categories,
        tags=request.tags,
        media_ids=request.media_ids,
        location=request.location,
        is_public=request.is_public,
        is_anonymous=request.is_anonymous,
        app_version=request.app_version,
        platform=request.platform,
        device_info=request.device_info,
    )
    created = await service.create_feedback(feedback)
    return FeedbackResponse.from_entity(created)


@router.get("/", response_model=PaginatedResponse[FeedbackResponse])
async def list_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: FeedbackType | None = None,
    status: FeedbackStatus | None = None,
    target_type: str | None = None,
    target_id: UUID | None = None,
    sentiment: FeedbackSentiment | None = None,
    service: FeedbackUseCases = Depends(get_feedback_use_cases),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[FeedbackResponse]:
    """List feedback with filters"""
    # If not admin, only show user's own feedback or public feedback
    user_id = UUID(current_user["id"]) if current_user.get("role") != "admin" else None

    feedback_list = await service.list_feedback(
        user_id=user_id,
        type=type,
        status=status,
        target_type=target_type,
        target_id=target_id,
        sentiment=sentiment,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[FeedbackResponse.from_entity(f) for f in feedback_list.items],
        total=feedback_list.total,
        page=feedback_list.page,
        page_size=feedback_list.page_size,
        total_pages=feedback_list.total_pages,
        has_next=feedback_list.has_next,
        has_prev=feedback_list.has_prev,
    )


@router.get("/pending-moderation", response_model=PaginatedResponse[FeedbackResponse])
async def get_pending_moderation(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: FeedbackUseCases = Depends(get_feedback_use_cases),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[FeedbackResponse]:
    """Get feedback pending moderation (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    feedback_list = await service.get_pending_moderation(page=page, page_size=page_size)
    return PaginatedResponse(
        items=[FeedbackResponse.from_entity(f) for f in feedback_list.items],
        total=feedback_list.total,
        page=feedback_list.page,
        page_size=feedback_list.page_size,
        total_pages=feedback_list.total_pages,
        has_next=feedback_list.has_next,
        has_prev=feedback_list.has_prev,
    )


@router.get("/by-target/{target_type}/{target_id}", response_model=PaginatedResponse[FeedbackResponse])
async def get_feedback_by_target(
    target_type: str,
    target_id: UUID,
    status: FeedbackStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: FeedbackUseCases = Depends(get_feedback_use_cases),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[FeedbackResponse]:
    """Get feedback for a target entity"""
    feedback_list = await service.get_by_target(
        target_type=target_type,
        target_id=target_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[FeedbackResponse.from_entity(f) for f in feedback_list.items],
        total=feedback_list.total,
        page=feedback_list.page,
        page_size=feedback_list.page_size,
        total_pages=feedback_list.total_pages,
        has_next=feedback_list.has_next,
        has_prev=feedback_list.has_prev,
    )


@router.get("/public/{target_type}/{target_id}", response_model=PaginatedResponse[FeedbackResponse])
async def get_public_feedback(
    target_type: str,
    target_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: FeedbackUseCases = Depends(get_feedback_use_cases),
) -> PaginatedResponse[FeedbackResponse]:
    """Get public feedback for a target entity"""
    feedback_list = await service.get_public_feedback(
        target_type=target_type,
        target_id=target_id,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[FeedbackResponse.from_entity(f) for f in feedback_list.items],
        total=feedback_list.total,
        page=feedback_list.page,
        page_size=feedback_list.page_size,
        total_pages=feedback_list.total_pages,
        has_next=feedback_list.has_next,
        has_prev=feedback_list.has_prev,
    )


@router.get("/average-rating/{target_type}/{target_id}")
async def get_average_rating(
    target_type: str,
    target_id: UUID,
    service: FeedbackUseCases = Depends(get_feedback_use_cases),
) -> dict:
    """Get average rating for target"""
    rating = await service.get_average_rating(target_type, target_id)
    return {"average_rating": rating}


@router.get("/rating-distribution/{target_type}/{target_id}")
async def get_rating_distribution(
    target_type: str,
    target_id: UUID,
    service: FeedbackUseCases = Depends(get_feedback_use_cases),
) -> dict:
    """Get rating distribution (1-5 stars)"""
    distribution = await service.get_rating_distribution(target_type, target_id)
    return distribution


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: UUID,
    service: FeedbackUseCases = Depends(get_feedback_use_cases),
    current_user: dict = Depends(get_current_user),
) -> FeedbackResponse:
    """Get feedback by ID"""
    feedback = await service.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    # Check access
    if str(feedback.user_id) != current_user["id"] and current_user.get("role") != "admin":
        if not feedback.is_public:
            raise HTTPException(status_code=403, detail="Not authorized to view this feedback")

    return FeedbackResponse.from_entity(feedback)


@router.patch("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: UUID,
    request: UpdateFeedbackRequest,
    service: FeedbackUseCases = Depends(get_feedback_use_cases),
    current_user: dict = Depends(get_current_user),
) -> FeedbackResponse:
    """Update feedback (admin only for status)"""
    feedback = await service.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    # Check ownership for non-admin updates
    if current_user.get("role") != "admin":
        if str(feedback.user_id) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to modify this feedback")
        # Users can only update their own feedback content, not status
        if request.status is not None:
            raise HTTPException(status_code=403, detail="Cannot change status")

    updated = await service.update_feedback(
        feedback_id=feedback_id,
        status=request.status,
        is_public=request.is_public,
        moderation_notes=request.moderation_notes,
    )
    return FeedbackResponse.from_entity(updated)


@router.post("/{feedback_id}/respond", response_model=FeedbackResponse)
async def respond_feedback(
    feedback_id: UUID,
    request: RespondFeedbackRequest,
    service: FeedbackUseCases = Depends(get_feedback_use_cases),
    current_user: dict = Depends(get_current_user),
) -> FeedbackResponse:
    """Respond to feedback (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    feedback = await service.respond_feedback(
        feedback_id=feedback_id,
        responder_id=UUID(current_user["id"]),
        response=request.response,
    )
    return FeedbackResponse.from_entity(feedback)


@router.post("/{feedback_id}/helpful")
async def mark_feedback_helpful(
    feedback_id: UUID,
    service: FeedbackUseCases = Depends(get_feedback_use_cases),
) -> dict:
    """Mark feedback as helpful"""
    await service.mark_helpful(feedback_id)
    return {"success": True}


@router.post("/{feedback_id}/unhelpful")
async def mark_feedback_unhelpful(
    feedback_id: UUID,
    service: FeedbackUseCases = Depends(get_feedback_use_cases),
) -> dict:
    """Mark feedback as unhelpful"""
    await service.mark_unhelpful(feedback_id)
    return {"success": True}


@router.get("/stats", response_model=dict)
async def get_feedback_stats(
    service: FeedbackUseCases = Depends(get_feedback_use_cases),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get feedback statistics (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return await service.get_stats()


@router.get("/trending-issues/{target_type}")
async def get_trending_issues(
    target_type: str,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=100),
    service: FeedbackUseCases = Depends(get_feedback_use_cases),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Get trending issues from feedback (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return await service.get_trending_issues(target_type, days, limit)
