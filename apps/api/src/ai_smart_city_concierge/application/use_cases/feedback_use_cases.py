"""
Feedback Application Use Cases
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from ...domain.entities.feedback import Feedback, FeedbackStatus, FeedbackType
from ...domain.repositories.base import FilterParams, PaginatedResult, PaginationParams
from ...domain.repositories.feedback_repository import FeedbackRepository


@dataclass
class CreateFeedbackRequest:
    """Request to create feedback"""
    user_id: UUID
    entity_type: str
    entity_id: UUID
    feedback_type: FeedbackType
    rating: float | None = None
    title: str | None = None
    content: str | None = None
    pros: list[str] | None = None
    cons: list[str] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class UpdateFeedbackRequest:
    """Request to update feedback"""
    rating: float | None = None
    title: str | None = None
    content: str | None = None
    pros: list[str] | None = None
    cons: list[str] | None = None
    status: FeedbackStatus | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class ModerateFeedbackRequest:
    """Request to moderate feedback"""
    feedback_id: UUID
    moderator_id: UUID
    status: FeedbackStatus
    moderation_notes: str | None = None


class FeedbackUseCases:
    """Feedback Application Use Cases"""

    def __init__(
        self,
        feedback_repository: FeedbackRepository,
        feedback_service: FeedbackService,
    ):
        self.feedback_repository = feedback_repository

    async def create_feedback(self, request: CreateFeedbackRequest) -> Feedback:
        """Create feedback"""
        feedback = Feedback(
            user_id=request.user_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            feedback_type=request.feedback_type,
            rating=request.rating,
            title=request.title,
            content=request.content,
            pros=request.pros or [],
            cons=request.cons or [],
            metadata=request.metadata or {},
        )

        return await self.feedback_repository.add(feedback)

    async def get_feedback(self, feedback_id: UUID) -> Feedback | None:
        """Get feedback by ID"""
        return await self.feedback_repository.get_by_id(feedback_id)

    async def get_user_feedback(
        self,
        user_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get feedback by user"""
        return await self.feedback_repository.get_by_user(user_id, pagination)

    async def get_entity_feedback(
        self,
        entity_type: str,
        entity_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get feedback for an entity"""
        return await self.feedback_repository.get_by_entity(entity_type, entity_id, pagination)

    async def update_feedback(self, feedback_id: UUID, request: UpdateFeedbackRequest) -> Feedback | None:
        """Update feedback"""
        feedback = await self.feedback_repository.get_by_id(feedback_id)
        if not feedback:
            return None

        if request.rating is not None:
            feedback.rating = request.rating
        if request.title is not None:
            feedback.title = request.title
        if request.content is not None:
            feedback.content = request.content
        if request.pros is not None:
            feedback.pros = request.pros
        if request.cons is not None:
            feedback.cons = request.cons
        if request.status is not None:
            feedback.status = request.status
        if request.metadata is not None:
            feedback.metadata = request.metadata

        return await self.feedback_repository.update(feedback)

    async def delete_feedback(self, feedback_id: UUID) -> bool:
        """Delete feedback"""
        return await self.feedback_repository.delete(feedback_id)

    async def moderate_feedback(self, request: ModerateFeedbackRequest) -> Feedback | None:
        """Moderate feedback"""
        feedback = await self.feedback_repository.get_by_id(request.feedback_id)
        if not feedback:
            return None

        feedback.status = request.status
        feedback.moderated_by = request.moderator_id
        feedback.moderated_at = datetime.utcnow()
        feedback.moderation_notes = request.moderation_notes

        return await self.feedback_repository.update(feedback)

    async def get_entity_rating_summary(self, entity_type: str, entity_id: UUID) -> dict[str, Any]:
        """Get rating summary for an entity"""
        return await self.feedback_service.get_rating_summary(entity_type, entity_id)

    async def get_feedback_stats(self) -> dict[str, Any]:
        """Get feedback statistics"""
        return await self.feedback_repository.get_stats()

    async def flag_feedback(self, feedback_id: UUID, reason: str) -> Feedback | None:
        """Flag feedback for review"""
        feedback = await self.feedback_repository.get_by_id(feedback_id)
        if not feedback:
            return None

        feedback.status = FeedbackStatus.FLAGGED
        feedback.metadata["flag_reason"] = reason
        feedback.metadata["flagged_at"] = datetime.utcnow().isoformat()

        return await self.feedback_repository.update(feedback)

    async def get_flagged_feedback(
        self,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get flagged feedback"""
        return await self.feedback_repository.list(
            pagination=pagination,
            filters=FilterParams(filters={"status": FeedbackStatus.FLAGGED}),
        )
