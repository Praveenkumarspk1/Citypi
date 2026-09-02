"""
API Endpoints

Endpoint classes for each API resource.
"""
from typing import Optional, List, Dict, Any
from .base import BaseClient
from shared_types import (
    PaginatedResponse,
    POIResponse,
    POISearchParams,
    ConversationResponse,
    MessageResponse,
    ItineraryResponse,
    ItineraryGenerateRequest,
    TransitRoute,
    TransitStop,
    TransitPrediction,
    LocationWeather,
    UserResponse,
    MediaResponse,
    FeedbackResponse,
    AnalyticsEventCreate,
)


class BaseEndpoint:
    """Base endpoint class."""
    
    def __init__(self, client: BaseClient):
        self.client = client


class ChatEndpoint(BaseEndpoint):
    """Chat messaging endpoints."""
    
    def send_message(
        self,
        recipient_id: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a chat message."""
        response = self.client.post("/chat/send", json={
            "recipient_id": recipient_id,
            "content": content,
            "message_type": message_type,
            "metadata": metadata or {},
        })
        return response.json()

    def get_conversations(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[ConversationResponse]:
        """Get user's conversations."""
        response = self.client.get("/chat/conversations", params={
            "page": page,
            "page_size": page_size,
        })
        return PaginatedResponse[ConversationResponse](**response.json())

    def get_conversation(
        self,
        conversation_id: str,
    ) -> ConversationResponse:
        """Get a conversation with messages."""
        response = self.client.get(f"/chat/conversations/{conversation_id}")
        return ConversationResponse(**response.json())

    def create_conversation(
        self,
        title: Optional[str] = None,
    ) -> ConversationResponse:
        """Create a new conversation."""
        response = self.client.post("/chat/conversations", json={
            "title": title,
        })
        return ConversationResponse(**response.json())

    def send_message_in_conversation(
        self,
        conversation_id: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MessageResponse:
        """Send a message in a conversation."""
        response = self.client.post(f"/chat/conversations/{conversation_id}/messages", json={
            "content": content,
            "message_type": message_type,
            "metadata": metadata or {},
        })
        return MessageResponse(**response.json())

    def get_messages(
        self,
        conversation_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse[MessageResponse]:
        """Get messages in a conversation."""
        response = self.client.get(f"/chat/conversations/{conversation_id}/messages", params={
            "page": page,
            "page_size": page_size,
        })
        return PaginatedResponse[MessageResponse](**response.json())


class POIEndpoint(BaseEndpoint):
    """POI endpoints."""
    
    def search(
        self,
        params: Optional[POISearchParams] = None,
        **kwargs,
    ) -> PaginatedResponse[POIResponse]:
        """Search POIs."""
        search_params = params or POISearchParams()
        query_params = search_params.model_dump(exclude_none=True)
        query_params.update(kwargs)
        
        response = self.client.get("/pois/search", params=query_params)
        return PaginatedResponse[POIResponse](**response.json())

    def get(self, poi_id: str) -> POIResponse:
        """Get a POI by ID."""
        response = self.client.get(f"/pois/{poi_id}")
        return POIResponse(**response.json())

    def get_nearby(
        self,
        latitude: float,
        longitude: float,
        radius: int = 5000,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> List[POIResponse]:
        """Get nearby POIs."""
        response = self.client.get("/pois/nearby", params={
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
            "category": category,
            "limit": limit,
        })
        return [POIResponse(**item) for item in response.json()]

    def get_categories(self) -> List[Dict[str, Any]]:
        """Get POI categories."""
        response = self.client.get("/pois/categories")
        return response.json()

    def create(self, data: Dict[str, Any]) -> POIResponse:
        """Create a POI (admin)."""
        response = self.client.post("/pois", json=data)
        return POIResponse(**response.json())

    def update(self, poi_id: str, data: Dict[str, Any]) -> POIResponse:
        """Update a POI (admin)."""
        response = self.client.patch(f"/pois/{poi_id}", json=data)
        return POIResponse(**response.json())

    def delete(self, poi_id: str) -> Dict[str, Any]:
        """Delete a POI (admin)."""
        response = self.client.delete(f"/pois/{poi_id}")
        return response.json()


class ItineraryEndpoint(BaseEndpoint):
    """Itinerary endpoints."""
    
    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> PaginatedResponse[ItineraryResponse]:
        """List user's itineraries."""
        params = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        
        response = self.client.get("/itineraries", params=params)
        return PaginatedResponse[ItineraryResponse](**response.json())

    def get(self, itinerary_id: str) -> ItineraryResponse:
        """Get an itinerary by ID."""
        response = self.client.get(f"/itineraries/{itinerary_id}")
        return ItineraryResponse(**response.json())

    def create(self, data: Dict[str, Any]) -> ItineraryResponse:
        """Create a new itinerary."""
        response = self.client.post("/itineraries", json=data)
        return ItineraryResponse(**response.json())

    def update(self, itinerary_id: str, data: Dict[str, Any]) -> ItineraryResponse:
        """Update an itinerary."""
        response = self.client.patch(f"/itineraries/{itinerary_id}", json=data)
        return ItineraryResponse(**response.json())

    def delete(self, itinerary_id: str) -> Dict[str, Any]:
        """Delete an itinerary."""
        response = self.client.delete(f"/itineraries/{itinerary_id}")
        return response.json()

    def generate(self, request: ItineraryGenerateRequest) -> ItineraryResponse:
        """Generate an itinerary using AI."""
        response = self.client.post("/itineraries/generate", json=request.model_dump())
        return ItineraryResponse(**response.json())

    def share(
        self,
        itinerary_id: str,
        recipient_emails: List[str],
        message: Optional[str] = None,
        permission: str = "view",
    ) -> Dict[str, Any]:
        """Share an itinerary."""
        response = self.client.post(f"/itineraries/{itinerary_id}/share", json={
            "recipient_emails": recipient_emails,
            "message": message,
            "permission": permission,
        })
        return response.json()

    def export(
        self,
        itinerary_id: str,
        format: str = "pdf",
    ) -> Dict[str, Any]:
        """Export itinerary."""
        response = self.client.post(f"/itineraries/{itinerary_id}/export", json={
            "format": format,
        })
        return response.json()


class TransitEndpoint(BaseEndpoint):
    """Transit endpoints."""
    
    def get_agencies(self) -> List[TransitRoute]:
        """Get transit agencies."""
        response = self.client.get("/transit/agencies")
        return [TransitRoute(**item) for item in response.json()]

    def get_routes(
        self,
        agency_id: Optional[str] = None,
    ) -> List[TransitRoute]:
        """Get transit routes."""
        params = {}
        if agency_id:
            params["agency_id"] = agency_id
        
        response = self.client.get("/transit/routes", params=params)
        return [TransitRoute(**item) for item in response.json()]

    def get_route(self, route_id: str) -> TransitRoute:
        """Get a route by ID."""
        response = self.client.get(f"/transit/routes/{route_id}")
        return TransitRoute(**response.json())

    def get_stops(
        self,
        route_id: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius: int = 1000,
    ) -> List[TransitStop]:
        """Get transit stops."""
        params = {}
        if route_id:
            params["route_id"] = route_id
        if latitude and longitude:
            params["latitude"] = latitude
            params["longitude"] = longitude
            params["radius"] = radius
        
        response = self.client.get("/transit/stops", params=params)
        return [TransitStop(**item) for item in response.json()]

    def get_predictions(
        self,
        stop_id: str,
        route_id: Optional[str] = None,
    ) -> List[TransitPrediction]:
        """Get arrival predictions for a stop."""
        params = {}
        if route_id:
            params["route_id"] = route_id
        
        response = self.client.get(f"/transit/stops/{stop_id}/predictions", params=params)
        return [TransitPrediction(**item) for item in response.json()]

    def get_alerts(
        self,
        route_id: Optional[str] = None,
        stop_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get transit alerts."""
        params = {}
        if route_id:
            params["route_id"] = route_id
        if stop_id:
            params["stop_id"] = stop_id
        
        response = self.client.get("/transit/alerts", params=params)
        return response.json()

    def plan_trip(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        departure_time: Optional[str] = None,
        arrival_time: Optional[str] = None,
        modes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Plan a transit trip."""
        response = self.client.post("/transit/trip", json={
            "origin_lat": origin_lat,
            "origin_lng": origin_lng,
            "dest_lat": dest_lat,
            "dest_lng": dest_lng,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "modes": modes or [],
        })
        return response.json()


class WeatherEndpoint(BaseEndpoint):
    """Weather endpoints."""
    
    def get_current(
        self,
        latitude: float,
        longitude: float,
    ) -> Dict[str, Any]:
        """Get current weather."""
        response = self.client.get("/weather/current", params={
            "latitude": latitude,
            "longitude": longitude,
        })
        return response.json()

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
        hourly: bool = True,
    ) -> LocationWeather:
        """Get weather forecast."""
        response = self.client.get("/weather/forecast", params={
            "latitude": latitude,
            "longitude": longitude,
            "days": days,
            "hourly": hourly,
        })
        return LocationWeather(**response.json())

    def get_alerts(
        self,
        latitude: float,
        longitude: float,
    ) -> List[Dict[str, Any]]:
        """Get weather alerts."""
        response = self.client.get("/weather/alerts", params={
            "latitude": latitude,
            "longitude": longitude,
        })
        return response.json()

    def get_historical(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """Get historical weather."""
        response = self.client.get("/weather/historical", params={
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
        })
        return response.json()


class UserEndpoint(BaseEndpoint):
    """User endpoints."""
    
    def get_me(self) -> UserResponse:
        """Get current user."""
        response = self.client.get("/users/me")
        return UserResponse(**response.json())

    def get(self, user_id: str) -> UserResponse:
        """Get a user by ID."""
        response = self.client.get(f"/users/{user_id}")
        return UserResponse(**response.json())

    def update_profile(self, data: Dict[str, Any]) -> UserResponse:
        """Update user profile."""
        response = self.client.patch("/users/me/profile", json=data)
        return UserResponse(**response.json())

    def update_preferences(self, data: Dict[str, Any]) -> UserResponse:
        """Update user preferences."""
        response = self.client.patch("/users/me/preferences", json=data)
        return UserResponse(**response.json())

    def upload_avatar(self, file_path: str) -> UserResponse:
        """Upload user avatar."""
        with open(file_path, "rb") as f:
            files = {"file": (file_path, f, "image/jpeg")}
            response = self.client.request("POST", "/users/me/avatar", files=files)
        return UserResponse(**response.json())

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> PaginatedResponse[UserResponse]:
        """List users (admin)."""
        params = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        
        response = self.client.get("/users", params=params)
        return PaginatedResponse[UserResponse](**response.json())


class ConversationEndpoint(BaseEndpoint):
    """Conversation endpoints."""
    
    def list(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[ConversationResponse]:
        """List conversations."""
        response = self.client.get("/conversations", params={
            "page": page,
            "page_size": page_size,
        })
        return PaginatedResponse[ConversationResponse](**response.json())

    def get(self, conversation_id: str) -> ConversationResponse:
        """Get a conversation."""
        response = self.client.get(f"/conversations/{conversation_id}")
        return ConversationResponse(**response.json())

    def create(self, data: Dict[str, Any]) -> ConversationResponse:
        """Create a conversation."""
        response = self.client.post("/conversations", json=data)
        return ConversationResponse(**response.json())

    def update(self, conversation_id: str, data: Dict[str, Any]) -> ConversationResponse:
        """Update a conversation."""
        response = self.client.patch(f"/conversations/{conversation_id}", json=data)
        return ConversationResponse(**response.json())

    def delete(self, conversation_id: str) -> Dict[str, Any]:
        """Delete a conversation."""
        response = self.client.delete(f"/conversations/{conversation_id}")
        return response.json()


class MediaEndpoint(BaseEndpoint):
    """Media endpoints."""
    
    def upload(
        self,
        file_path: str,
        conversation_id: Optional[str] = None,
        itinerary_id: Optional[str] = None,
        poi_id: Optional[str] = None,
        is_public: bool = False,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> MediaResponse:
        """Upload media file."""
        with open(file_path, "rb") as f:
            filename = file_path.split("/")[-1]
            files = {"file": (filename, f)}
            data = {
                "is_public": str(is_public).lower(),
            }
            if conversation_id:
                data["conversation_id"] = conversation_id
            if itinerary_id:
                data["itinerary_id"] = itinerary_id
            if poi_id:
                data["poi_id"] = poi_id
            if tags:
                data["tags"] = ",".join(tags)
            if description:
                data["description"] = description
            
            response = self.client.request("POST", "/media", files=files, data=data)
        
        return MediaResponse(**response.json())

    def get(self, media_id: str) -> MediaResponse:
        """Get media by ID."""
        response = self.client.get(f"/media/{media_id}")
        return MediaResponse(**response.json())

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        media_type: Optional[str] = None,
    ) -> PaginatedResponse[MediaResponse]:
        """List user's media."""
        params = {"page": page, "page_size": page_size}
        if media_type:
            params["media_type"] = media_type
        
        response = self.client.get("/media", params=params)
        return PaginatedResponse[MediaResponse](**response.json())

    def delete(self, media_id: str) -> Dict[str, Any]:
        """Delete media."""
        response = self.client.delete(f"/media/{media_id}")
        return response.json()


class FeedbackEndpoint(BaseEndpoint):
    """Feedback endpoints."""
    
    def create(self, data: Dict[str, Any]) -> FeedbackResponse:
        """Submit feedback."""
        response = self.client.post("/feedback", json=data)
        return FeedbackResponse(**response.json())

    def get(self, feedback_id: str) -> FeedbackResponse:
        """Get feedback by ID."""
        response = self.client.get(f"/feedback/{feedback_id}")
        return FeedbackResponse(**response.json())

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        feedback_type: Optional[str] = None,
    ) -> PaginatedResponse[FeedbackResponse]:
        """List user's feedback."""
        params = {"page": page, "page_size": page_size}
        if feedback_type:
            params["type"] = feedback_type
        
        response = self.client.get("/feedback", params=params)
        return PaginatedResponse[FeedbackResponse](**response.json())


class AnalyticsEndpoint(BaseEndpoint):
    """Analytics endpoints."""
    
    def track_event(self, event: AnalyticsEventCreate) -> Dict[str, Any]:
        """Track an analytics event."""
        response = self.client.post("/analytics/events", json=event.model_dump())
        return response.json()

    def track_batch(self, events: List[AnalyticsEventCreate]) -> Dict[str, Any]:
        """Track multiple events."""
        response = self.client.post("/analytics/events/batch", json={
            "events": [e.model_dump() for e in events],
        })
        return response.json()

    def get_metrics(
        self,
        period_start: str,
        period_end: str,
    ) -> Dict[str, Any]:
        """Get user metrics."""
        response = self.client.get("/analytics/metrics", params={
            "period_start": period_start,
            "period_end": period_end,
        })
        return response.json()

    def get_system_metrics(
        self,
        period_start: str,
        period_end: str,
    ) -> Dict[str, Any]:
        """Get system metrics (admin)."""
        response = self.client.get("/analytics/system-metrics", params={
            "period_start": period_start,
            "period_end": period_end,
        })
        return response.json()