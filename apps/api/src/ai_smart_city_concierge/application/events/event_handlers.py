"""
Main Event Handlers - Handles all domain events
"""
from typing import Any

from ...domain.events.domain_events import (
    # User events
    UserCreatedEvent,
    UserDeletedEvent,
    UserEmailVerifiedEvent,
    UserLoggedInEvent,
    UserPreferencesUpdatedEvent,
    UserUpdatedEvent,
    # Conversation events
    ConversationArchivedEvent,
    ConversationDeletedEvent,
    ConversationMessageAddedEvent,
    ConversationStartedEvent,
    ConversationSummaryGeneratedEvent,
    ConversationUpdatedEvent,
    # Itinerary events
    ItineraryActivatedEvent,
    ItineraryCompletedEvent,
    ItineraryCreatedEvent,
    ItineraryDayAddedEvent,
    ItineraryDeletedEvent,
    ItineraryGeneratedByAIEvent,
    ItineraryItemAddedEvent,
    ItineraryItemRemovedEvent,
    ItinerarySharedEvent,
    ItineraryUpdatedEvent,
    # POI events
    POICreatedEvent,
    POIDeletedEvent,
    POIFavoritedEvent,
    POIPhotoAddedEvent,
    POIRatingUpdatedEvent,
    POIUnfavoritedEvent,
    POIUpdatedEvent,
    POIVerifiedEvent,
    # Transit events
    TransitRouteCalculatedEvent,
    TransitRouteViewedEvent,
    TransitTripPlannedEvent,
    # Weather events
    WeatherAlertTriggeredEvent,
    # Media events
    MediaUploadedEvent,
    MediaProcessedEvent,
    # Feedback events
    FeedbackSubmittedEvent,
    # Analytics events
    AnalyticsEventRecordedEvent,
    # Recommendation events
    RecommendationGeneratedEvent,
    RecommendationFeedbackGivenEvent,
)
from ...domain.repositories import (
    AnalyticsRepository,
    ConversationRepository,
    FeedbackRepository,
    ItineraryRepository,
    MediaRepository,
    POIRepository,
    TransitRepository,
    UserRepository,
    WeatherRepository,
)
from ..ports.event_publisher import EventPublisher
from ..ports.external_services import (
    EmbeddingServicePort,
    NotificationServicePort,
    VectorDBServicePort,
)


class EventHandlers:
    """Central event handlers for all domain events"""

    def __init__(
        self,
        user_repository: UserRepository,
        conversation_repository: ConversationRepository,
        itinerary_repository: ItineraryRepository,
        poi_repository: POIRepository,
        transit_repository: TransitRepository,
        weather_repository: WeatherRepository,
        media_repository: MediaRepository,
        feedback_repository: FeedbackRepository,
        analytics_repository: AnalyticsRepository,
        embedding_service: EmbeddingServicePort,
        vector_db: VectorDBServicePort,
        notification_service: NotificationServicePort,
        event_publisher: EventPublisher,
    ):
        self.user_repository = user_repository
        self.conversation_repository = conversation_repository
        self.itinerary_repository = itinerary_repository
        self.poi_repository = poi_repository
        self.transit_repository = transit_repository
        self.weather_repository = weather_repository
        self.media_repository = media_repository
        self.feedback_repository = feedback_repository
        self.analytics_repository = analytics_repository
        self.embedding_service = embedding_service
        self.vector_db = vector_db
        self.notification_service = notification_service
        self.event_publisher = event_publisher

    # ========== User Event Handlers ==========

    async def handle_user_created(self, event: UserCreatedEvent) -> None:
        """Handle user created event"""
        # Create user preference embeddings for recommendations
        user = event.payload.user
        if user.interests:
            embedding_text = " ".join(user.interests)
            embedding = await self.embedding_service.generate_embedding(embedding_text)
            await self.vector_db.upsert(
                collection="user_preference_embeddings",
                id=str(user.id),
                vector=embedding,
                metadata={
                    "user_id": str(user.id),
                    "interests": user.interests,
                    "budget_level": user.budget_level,
                },
            )

        # Initialize analytics
        await self.analytics_repository.record_user_signup(user.id)

    async def handle_user_updated(self, event: UserUpdatedEvent) -> None:
        """Handle user updated event"""
        user = event.payload.user
        # Update preference embeddings if interests changed
        if "interests" in event.payload.changes or "budget_level" in event.payload.changes:
            embedding_text = " ".join(user.interests)
            embedding = await self.embedding_service.generate_embedding(embedding_text)
            await self.vector_db.upsert(
                collection="user_preference_embeddings",
                id=str(user.id),
                vector=embedding,
                metadata={
                    "user_id": str(user.id),
                    "interests": user.interests,
                    "budget_level": user.budget_level,
                },
            )

    async def handle_user_preferences_updated(self, event: UserPreferencesUpdatedEvent) -> None:
        """Handle user preferences updated event"""
        user = event.payload.user
        embedding_text = " ".join(user.interests)
        embedding = await self.embedding_service.generate_embedding(embedding_text)
        await self.vector_db.upsert(
            collection="user_preference_embeddings",
            id=str(user.id),
            vector=embedding,
            metadata={
                "user_id": str(user.id),
                "interests": user.interests,
                "budget_level": user.budget_level,
            },
        )

    async def handle_user_email_verified(self, event: UserEmailVerifiedEvent) -> None:
        """Handle user email verified event"""
        await self.analytics_repository.record_email_verification(event.payload.user_id)

    async def handle_user_logged_in(self, event: UserLoggedInEvent) -> None:
        """Handle user logged in event"""
        await self.analytics_repository.record_login(event.payload.user_id)

    async def handle_user_deleted(self, event: UserDeletedEvent) -> None:
        """Handle user deleted event"""
        user = event.payload.user
        # Remove embeddings
        await self.vector_db.delete(
            collection="user_preference_embeddings",
            id=str(user.id),
        )

    # ========== Conversation Event Handlers ==========

    async def handle_conversation_started(self, event: ConversationStartedEvent) -> None:
        """Handle conversation started event"""
        conversation = event.payload.conversation
        # Create conversation embedding for semantic search
        if conversation.title:
            embedding = await self.embedding_service.generate_embedding(conversation.title)
            await self.vector_db.upsert(
                collection="conversation_embeddings",
                id=str(conversation.id),
                vector=embedding,
                metadata={
                    "conversation_id": str(conversation.id),
                    "user_id": str(conversation.user_id),
                    "title": conversation.title,
                },
            )

        await self.analytics_repository.record_conversation_started(conversation.id, conversation.user_id)

    async def handle_conversation_message_added(self, event: ConversationMessageAddedEvent) -> None:
        """Handle message added to conversation"""
        conversation = event.payload.conversation
        message = event.payload.message

        # Update conversation embedding with new message
        if message.role.value == "user" and message.content:
            embedding = await self.embedding_service.generate_embedding(message.content)
            await self.vector_db.upsert(
                collection="conversation_embeddings",
                id=str(conversation.id),
                vector=embedding,
                metadata={
                    "conversation_id": str(conversation.id),
                    "user_id": str(conversation.user_id),
                    "last_message": message.content[:200],
                },
            )

        await self.analytics_repository.record_message(conversation.id, message.id, message.role.value)

    async def handle_conversation_updated(self, event: ConversationUpdatedEvent) -> None:
        """Handle conversation updated event"""
        pass  # Handled by message added

    async def handle_conversation_summary_generated(self, event: ConversationSummaryGeneratedEvent) -> None:
        """Handle conversation summary generated"""
        pass

    async def handle_conversation_archived(self, event: ConversationArchivedEvent) -> None:
        """Handle conversation archived"""
        await self.analytics_repository.record_conversation_archived(event.payload.conversation_id)

    async def handle_conversation_deleted(self, event: ConversationDeletedEvent) -> None:
        """Handle conversation deleted"""
        conversation = event.payload.conversation
        await self.vector_db.delete(
            collection="conversation_embeddings",
            id=str(conversation.id),
        )

    # ========== Itinerary Event Handlers ==========

    async def handle_itinerary_created(self, event: ItineraryCreatedEvent) -> None:
        """Handle itinerary created event"""
        itinerary = event.payload.itinerary
        # Create itinerary embedding
        embedding_text = f"{itinerary.title} {itinerary.description or ''} {' '.join(itinerary.interests)} {' '.join(itinerary.tags)}"
        embedding = await self.embedding_service.generate_embedding(embedding_text)
        await self.vector_db.upsert(
            collection="itinerary_embeddings",
            id=str(itinerary.id),
            vector=embedding,
            metadata={
                "itinerary_id": str(itinerary.id),
                "user_id": str(itinerary.user_id),
                "title": itinerary.title,
                "city": itinerary.city,
                "country": itinerary.country,
                "is_public": itinerary.is_public,
            },
        )

        await self.analytics_repository.record_itinerary_created(itinerary.id, itinerary.user_id)

    async def handle_itinerary_updated(self, event: ItineraryUpdatedEvent) -> None:
        """Handle itinerary updated event"""
        itinerary = event.payload.itinerary
        # Update embedding if content changed
        if any(k in event.payload.changes for k in ["title", "description", "interests", "tags"]):
            embedding_text = f"{itinerary.title} {itinerary.description or ''} {' '.join(itinerary.interests)} {' '.join(itinerary.tags)}"
            embedding = await self.embedding_service.generate_embedding(embedding_text)
            await self.vector_db.upsert(
                collection="itinerary_embeddings",
                id=str(itinerary.id),
                vector=embedding,
                metadata={
                    "itinerary_id": str(itinerary.id),
                    "user_id": str(itinerary.user_id),
                    "title": itinerary.title,
                    "city": itinerary.city,
                    "country": itinerary.country,
                    "is_public": itinerary.is_public,
                },
            )

    async def handle_itinerary_day_added(self, event: ItineraryDayAddedEvent) -> None:
        """Handle day added to itinerary"""
        await self.analytics_repository.record_itinerary_day_added(
            event.payload.itinerary_id,
            event.payload.day_id,
        )

    async def handle_itinerary_item_added(self, event: ItineraryItemAddedEvent) -> None:
        """Handle item added to itinerary"""
        await self.analytics_repository.record_itinerary_item_added(
            event.payload.itinerary_id,
            event.payload.day_id,
            event.payload.item_id,
            event.payload.item_type,
        )

        # If item has POI, increment POI visit count
        if event.payload.item_type == "poi":
            # This would need the POI ID from the item
            pass

    async def handle_itinerary_item_removed(self, event: ItineraryItemRemovedEvent) -> None:
        """Handle item removed from itinerary"""
        pass

    async def handle_itinerary_shared(self, event: ItinerarySharedEvent) -> None:
        """Handle itinerary shared"""
        await self.analytics_repository.record_itinerary_shared(
            event.payload.itinerary_id,
            event.payload.share_token,
        )

    async def handle_itinerary_activated(self, event: ItineraryActivatedEvent) -> None:
        """Handle itinerary activated"""
        await self.analytics_repository.record_itinerary_activated(event.payload.itinerary_id)

    async def handle_itinerary_completed(self, event: ItineraryCompletedEvent) -> None:
        """Handle itinerary completed"""
        await self.analytics_repository.record_itinerary_completed(event.payload.itinerary_id)

    async def handle_itinerary_deleted(self, event: ItineraryDeletedEvent) -> None:
        """Handle itinerary deleted"""
        itinerary = event.payload.itinerary
        await self.vector_db.delete(
            collection="itinerary_embeddings",
            id=str(itinerary.id),
        )

    async def handle_itinerary_generated_by_ai(self, event: ItineraryGeneratedByAIEvent) -> None:
        """Handle AI-generated itinerary"""
        await self.analytics_repository.record_ai_generation(
            event.payload.itinerary_id,
            event.payload.model,
            event.payload.tokens,
        )

    # ========== POI Event Handlers ==========

    async def handle_poi_created(self, event: POICreatedEvent) -> None:
        """Handle POI created event"""
        poi = event.payload.poi
        # Generate embedding for POI
        embedding_text = f"{poi.name} {poi.description or ''} {poi.category.value} {' '.join(poi.tags)}"
        embedding = await self.embedding_service.generate_embedding(embedding_text)
        await self.vector_db.upsert(
            collection="poi_embeddings",
            id=str(poi.id),
            vector=embedding,
            metadata={
                "poi_id": str(poi.id),
                "name": poi.name,
                "category": poi.category.value,
                "city": poi.city,
                "country": poi.country,
                "is_verified": poi.is_verified,
            },
        )

        await self.analytics_repository.record_poi_created(poi.id)

    async def handle_poi_updated(self, event: POIUpdatedEvent) -> None:
        """Handle POI updated event"""
        poi = event.payload.poi
        if any(k in event.payload.changes for k in ["name", "description", "category", "tags"]):
            embedding_text = f"{poi.name} {poi.description or ''} {poi.category.value} {' '.join(poi.tags)}"
            embedding = await self.embedding_service.generate_embedding(embedding_text)
            await self.vector_db.upsert(
                collection="poi_embeddings",
                id=str(poi.id),
                vector=embedding,
                metadata={
                    "poi_id": str(poi.id),
                    "name": poi.name,
                    "category": poi.category.value,
                    "city": poi.city,
                    "country": poi.country,
                    "is_verified": poi.is_verified,
                },
            )

    async def handle_poi_photo_added(self, event: POIPhotoAddedEvent) -> None:
        """Handle POI photo added"""
        await self.analytics_repository.record_poi_photo_added(event.payload.poi_id)

    async def handle_poi_rating_updated(self, event: POIRatingUpdatedEvent) -> None:
        """Handle POI rating updated"""
        await self.analytics_repository.record_poi_rating(
            event.payload.poi_id,
            event.payload.new_rating,
        )

    async def handle_poi_verified(self, event: POIVerifiedEvent) -> None:
        """Handle POI verified"""
        await self.analytics_repository.record_poi_verified(event.payload.poi_id)

    async def handle_poi_favorited(self, event: POIFavoritedEvent) -> None:
        """Handle POI favorited"""
        await self.analytics_repository.record_poi_favorite(event.payload.poi_id, event.payload.user_id)

    async def handle_poi_unfavorited(self, event: POIUnfavoritedEvent) -> None:
        """Handle POI unfavorited"""
        await self.analytics_repository.record_poi_unfavorite(event.payload.poi_id, event.payload.user_id)

    async def handle_poi_deleted(self, event: POIDeletedEvent) -> None:
        """Handle POI deleted"""
        poi = event.payload.poi
        await self.vector_db.delete(
            collection="poi_embeddings",
            id=str(poi.id),
        )

    # ========== Transit Event Handlers ==========

    async def handle_transit_route_calculated(self, event: TransitRouteCalculatedEvent) -> None:
        """Handle transit route calculated"""
        await self.analytics_repository.record_transit_route_calculated(
            event.payload.origin,
            event.payload.destination,
            len(event.payload.routes),
        )

    async def handle_transit_trip_planned(self, event: TransitTripPlannedEvent) -> None:
        """Handle transit trip planned"""
        await self.analytics_repository.record_transit_trip_planned(
            event.payload.origin,
            event.payload.destination,
        )

    async def handle_transit_route_viewed(self, event: TransitRouteViewedEvent) -> None:
        """Handle transit route viewed"""
        await self.analytics_repository.record_transit_route_viewed(
            event.payload.route_id,
            event.payload.user_id,
        )

    # ========== Weather Event Handlers ==========

    async def handle_weather_alert_triggered(self, event: WeatherAlertTriggeredEvent) -> None:
        """Handle weather alert triggered"""
        alert = event.payload.alert
        # Notify users in affected area
        # This would require a geospatial query to find users near the alert area
        await self.analytics_repository.record_weather_alert(alert.id)

    # ========== Media Event Handlers ==========

    async def handle_media_uploaded(self, event: MediaUploadedEvent) -> None:
        """Handle media uploaded"""
        media = event.payload.media
        await self.analytics_repository.record_media_uploaded(media.id, media.media_type.value)

    async def handle_media_processed(self, event: MediaProcessedEvent) -> None:
        """Handle media processed"""
        await self.analytics_repository.record_media_processed(event.payload.media_id, event.payload.processing_type)

    # ========== Feedback Event Handlers ==========

    async def handle_feedback_submitted(self, event: FeedbackSubmittedEvent) -> None:
        """Handle feedback submitted"""
        await self.analytics_repository.record_feedback(event.payload.feedback_id)

    # ========== Analytics Event Handlers ==========

    async def handle_analytics_event_recorded(self, event: AnalyticsEventRecordedEvent) -> None:
        """Handle analytics event recorded"""
        # Could trigger real-time dashboard updates
        pass

    # ========== Recommendation Event Handlers ==========

    async def handle_recommendation_generated(self, event: RecommendationGeneratedEvent) -> None:
        """Handle recommendation generated"""
        await self.analytics_repository.record_recommendation_generated(
            event.payload.recommendation_id,
            event.payload.user_id,
        )

    async def handle_recommendation_feedback_given(self, event: RecommendationFeedbackGivenEvent) -> None:
        """Handle recommendation feedback given"""
        await self.analytics_repository.record_recommendation_feedback(
            event.payload.recommendation_id,
            event.payload.user_id,
            event.payload.feedback_type,
        )

    # ========== Dispatcher ==========

    async def handle(self, event: Any) -> None:
        """Dispatch event to appropriate handler"""
        handler_map = {
            UserCreatedEvent: self.handle_user_created,
            UserUpdatedEvent: self.handle_user_updated,
            UserPreferencesUpdatedEvent: self.handle_user_preferences_updated,
            UserEmailVerifiedEvent: self.handle_user_email_verified,
            UserLoggedInEvent: self.handle_user_logged_in,
            UserDeletedEvent: self.handle_user_deleted,
            ConversationStartedEvent: self.handle_conversation_started,
            ConversationMessageAddedEvent: self.handle_conversation_message_added,
            ConversationUpdatedEvent: self.handle_conversation_updated,
            ConversationSummaryGeneratedEvent: self.handle_conversation_summary_generated,
            ConversationArchivedEvent: self.handle_conversation_archived,
            ConversationDeletedEvent: self.handle_conversation_deleted,
            ItineraryCreatedEvent: self.handle_itinerary_created,
            ItineraryUpdatedEvent: self.handle_itinerary_updated,
            ItineraryDayAddedEvent: self.handle_itinerary_day_added,
            ItineraryItemAddedEvent: self.handle_itinerary_item_added,
            ItineraryItemRemovedEvent: self.handle_itinerary_item_removed,
            ItinerarySharedEvent: self.handle_itinerary_shared,
            ItineraryActivatedEvent: self.handle_itinerary_activated,
            ItineraryCompletedEvent: self.handle_itinerary_completed,
            ItineraryDeletedEvent: self.handle_itinerary_deleted,
            ItineraryGeneratedByAIEvent: self.handle_itinerary_generated_by_ai,
            POICreatedEvent: self.handle_poi_created,
            POIUpdatedEvent: self.handle_poi_updated,
            POIPhotoAddedEvent: self.handle_poi_photo_added,
            POIRatingUpdatedEvent: self.handle_poi_rating_updated,
            POIVerifiedEvent: self.handle_poi_verified,
            POIFavoritedEvent: self.handle_poi_favorited,
            POIUnfavoritedEvent: self.handle_poi_unfavorited,
            POIDeletedEvent: self.handle_poi_deleted,
            TransitRouteCalculatedEvent: self.handle_transit_route_calculated,
            TransitTripPlannedEvent: self.handle_transit_trip_planned,
            TransitRouteViewedEvent: self.handle_transit_route_viewed,
            WeatherAlertTriggeredEvent: self.handle_weather_alert_triggered,
            MediaUploadedEvent: self.handle_media_uploaded,
            MediaProcessedEvent: self.handle_media_processed,
            FeedbackSubmittedEvent: self.handle_feedback_submitted,
            AnalyticsEventRecordedEvent: self.handle_analytics_event_recorded,
            RecommendationGeneratedEvent: self.handle_recommendation_generated,
            RecommendationFeedbackGivenEvent: self.handle_recommendation_feedback_given,
        }

        handler = handler_map.get(type(event))
        if handler:
            await handler(event)
        else:
            # Log unhandled event
            pass