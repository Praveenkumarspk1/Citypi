"""
Feedback Repository Interface
"""
from abc import ABC, abstractmethod
from uuid import UUID

from ..entities.feedback import Feedback, FeedbackSentiment, FeedbackStatus, FeedbackType
from .base import BaseRepository, PaginatedResult, PaginationParams


class FeedbackRepository(BaseRepository[Feedback, UUID], ABC):
    """Feedback repository interface"""

    @abstractmethod
    async def get_by_user(
        self,
        user_id: UUID,
        feedback_type: FeedbackType | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get feedback by user"""
        pass

    @abstractmethod
    async def get_by_target(
        self,
        target_type: str,
        target_id: UUID,
        status: FeedbackStatus | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get feedback for a target entity"""
        pass

    @abstractmethod
    async def get_by_type(
        self,
        feedback_type: FeedbackType,
        status: FeedbackStatus | None = None,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get feedback by type"""
        pass

    @abstractmethod
    async def get_pending_moderation(
        self,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get feedback pending moderation"""
        pass

    @abstractmethod
    async def get_by_status(
        self,
        status: FeedbackStatus,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get feedback by status"""
        pass

    @abstractmethod
    async def get_by_sentiment(
        self,
        sentiment: FeedbackSentiment,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get feedback by sentiment"""
        pass

    @abstractmethod
    async def get_public_feedback(
        self,
        target_type: str,
        target_id: UUID,
        pagination: PaginationParams | None = None,
    ) -> PaginatedResult[Feedback]:
        """Get public feedback for target"""
        pass

    @abstractmethod
    async def get_average_rating(self, target_type: str, target_id: UUID) -> float | None:
        """Get average rating for target"""
        pass

    @abstractmethod
    async def get_rating_distribution(self, target_type: str, target_id: UUID) -> dict:
        """Get rating distribution (1-5 stars)"""
        pass

    @abstractmethod
    async def mark_helpful(self, feedback_id: UUID) -> None:
        """Mark feedback as helpful"""
        pass

    @abstractmethod
    async def mark_unhelpful(self, feedback_id: UUID) -> None:
        """Mark feedback as unhelpful"""
        pass

    @abstractmethod
    async def set_moderation(
        self,
        feedback_id: UUID,
        moderator_id: UUID,
        status: FeedbackStatus,
        notes: str | None = None,
    ) -> None:
        """Set moderation status"""
        pass

    @abstractmethod
    async def respond(
        self,
        feedback_id: UUID,
        responder_id: UUID,
        response: str,
    ) -> None:
        """Add response to feedback"""
        pass

    @abstractmethod
    async def get_stats(self) -> dict:
        """Get feedback statistics"""
        pass

    @abstractmethod
    async def get_trending_issues(
        self,
        target_type: str,
        days: int = 30,
        limit: int = 10,
    ) -> list[dict]:
        """Get trending issues from feedback"""
        pass
