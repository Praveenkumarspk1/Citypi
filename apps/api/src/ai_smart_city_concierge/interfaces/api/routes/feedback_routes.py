"""
Feedback API Routes
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ....application.use_cases.feedback_use_cases import (
    CreateFeedbackRequest,
    FeedbackUseCases,
    ModerateFeedbackRequest,
    UpdateFeedbackRequest,
)
from ....domain.entities.feedback import Feedback, FeedbackStatus, FeedbackType
from ....domain.repositories.base import PaginationParams
from ....infrastructure.config.dependencies import get_feedback_use_cases

router = APIRouter(prefix="/feedback", tags=["Feedback"])


# Request/Response Models
class CreateFeedbackModel(BaseModel):
    user_id: UUID
    entity_type: str
    entity_id: UUID
    feedback_type: FeedbackType
    rating: float | None = Field(None, ge=0, le=5)
    title: str | None = None
    content: str | None = None
    pros: list[str] | None = None
    cons: list[str] | None = None
    metadata: dict | None = None


class UpdateFeedbackModel(BaseModel):
    rating: float | None = Field(None, ge=0, le=5)
    title: str | None = None
    content: str | None = None
    pros: list[str] | None = None
    cons: list[str] | None = None
    status: FeedbackStatus | None = None
    metadata: dict | None = None


class ModerateFeedbackModel(BaseModel):
    feedback_id: UUID
    moderator_id: UUID
    status: FeedbackStatus
    moderation_notes: str | None = None


class FeedbackResponse(BaseModel):
    id: UUID
    user_id: UUID
    entity_type: str
    entity_id: UUID
    feedback_type: FeedbackType
    rating: float | None
    title: str | None
    content: str | None
    pros: list[str]
    cons: list[str]
    status: FeedbackStatus
    moderated_by: UUID | None
    moderated_at: str | None
    moderation_notes: str | None
    metadata: dict
    created_at: str
    updated_at: str


class PaginatedFeedbackResponse(BaseModel):
    items: list[FeedbackResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class RatingSummaryResponse(BaseModel):
    entity_type: str
    entity_id: UUID
    average_rating: float
    total_reviews: int
    rating_distribution: dict
    recent_average: float | None


def feedback_to_response(feedback: Feedback) -> FeedbackResponse:
    """Convert Feedback entity to response model"""
    return FeedbackResponse(
        id=feedback.id,
        user_id=feedback.user_id,
        entity_type=feedback.entity_type,
        entity_id=feedback.entity_id,
        feedback_type=feedback.feedback_type,
        rating=feedback.rating,
        title=feedback.title,
        content=feedback.content,
        pros=feedback.pros,
        cons=feedback.cons,
        status=feedback.status,
        moderated_by=feedback.moderated_by,
        moderated_at=feedback.moderated_at.isoformat() if feedback.moderated_at else None,
        moderation_notes=feedback.moderation_notes,
        metadata=feedback.metadata,
        created_at=feedback.created_at.isoformat() if feedback.created_at else "",
        updated_at=feedback.updated_at.isoformat() if feedback.updated_at else "",
    )


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    request: CreateFeedbackModel,
    use_cases: FeedbackUseCases = Depends(get_feedback_use_cases),
):
    """Create feedback"""
    feedback_request = CreateFeedbackRequest(
        user_id=request.user_id,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        feedback_type=request.feedback_type,
        rating=request.rating,
        title=request.title,
        content=request.content,
        pros=request.pros,
        cons=request.cons,
        metadata=request.metadata,
    )

    feedback = await use_cases.create_feedback(feedback_request)
    return feedback_to_response(feedback)


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: UUID,
    use_cases: FeedbackUseCases = Depends(get_feedback_use_cases),
):
    """Get feedback by ID"""
    feedback = await use_cases.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback_to_response(feedback)


@router.get("/user/{user_id}", response_model=PaginatedFeedbackResponse)
async def get_user_feedback(
    user_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_cases: FeedbackUseCases = Depends(get_feedback_use_cases),
):
    """Get feedback by user"""
    result = await use_cases.get_user_feedback(
        user_id=user_id,
        pagination=PaginationParams(page=page, page_size=page_size),
    )

    return PaginatedFeedbackResponse(
        items=[feedback_to_response(f) for f in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=PaginatedFeedbackResponse)
async def get_entity_feedback(
    entity_type: str,
    entity_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_cases: FeedbackUseCases = Depends(get_feedback_use_cases),
):
    """Get feedback for an entity"""
    result = await use_cases.get_entity_feedback(
        entity_type=entity_type,
        entity_id=entity_id,
        pagination=PaginationParams(page=page, page_size=page_size),
    )

    return PaginatedFeedbackResponse(
        items=[feedback_to_response(f) for f in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


@router.put("/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: UUID,
    request: UpdateFeedbackModel,
    use_cases: FeedbackUseCases = Depends(get_feedback_use_cases),
):
    """Update feedback"""
    update_request = UpdateFeedbackRequest(
        rating=request.rating,
        title=request.title,
        content=request.content,
        pros=request.pros,
        cons=request.cons,
        status=request.status,
        metadata=request.metadata,
    )

    feedback = await use_cases.update_feedback(feedback_id, update_request)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback_to_response(feedback)


@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    feedback_id: UUID,
    use_cases: FeedbackUseCases = Depends(get_feedback_use_cases),
):
    """Delete feedback"""
    success = await use_cases.delete_feedback(feedback_id)
    if not success:
        raise HTTPException(status_code=404, detail="Feedback not found")


@router.post("/moderate", response_model=FeedbackResponse)
async def moderate_feedback(
    request: ModerateFeedbackModel,
    use_cases: FeedbackUseCases = Depends(get_feedback_use_cases),
):
    """Moderate feedback"""
    moderate_request = ModerateFeedbackRequest(
        feedback_id=request.feedback_id,
        moderator_id=request.moderator_id,
        status=request.status,
        moderation_notes=request.moderation_notes,
    )

    feedback = await use_cases.moderate_feedback(moderate_request)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback_to_response(feedback)


@router.get("/entity/{entity_type}/{entity_id}/rating-summary", response_model=RatingSummaryResponse)
async def get_entity_rating_summary(
    entity_type: str,
    entity_id: UUID,
    use_cases: FeedbackUseCases = Depends(get_feedback_use_cases),
):
    """Get rating summary for an entity"""
    summary = await use_cases.get_entity_rating_summary(entity_type, entity_id)
    return RatingSummaryResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        **summary
    )


@router.get("/stats", response_model=dict)
async def get_feedback_stats(
    use_cases: FeedbackUseCases = Depends(get_feedback_use_cases),
):
    """Get feedback statistics"""
    return await use_cases.get_feedback_stats()


@router.post("/{feedback_id}/flag", response_model=FeedbackResponse)
async def flag_feedback(
    feedback_id: UUID,
    reason: str = Query(..., min_length=1),
    use_cases: FeedbackUseCases = Depends(get_feedback_use_cases),
):
    """Flag feedback for review"""
    feedback = await use_cases.flag_feedback(feedback_id, reason)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback_to_response(feedback)


@router.get("/flagged", response_model=PaginatedFeedbackResponse)
async def get_flagged_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_cases: FeedbackUseCases = Depends(get_feedback_use_cases),
):
    """Get flagged feedback"""
    result = await use_cases.get_flagged_feedback(
        pagination=PaginationParams(page=page, page_size=page_size),
    )

    return PaginatedFeedbackResponse(
        items=[feedback_to_response(f) for f in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )
