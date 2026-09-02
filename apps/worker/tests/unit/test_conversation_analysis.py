"""
Unit tests for conversation analysis tasks
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from apps.worker.src.tasks.conversation_analysis import (
    analyze_conversation_sentiment,
    extract_conversation_topics,
    generate_conversation_summary,
    detect_conversation_intent,
    analyze_user_satisfaction,
)
from ai_smart_city_concierge.domain.aggregates.conversation_aggregate import ConversationAggregate


class TestConversationAnalysis:
    """Test cases for conversation analysis tasks"""

    @pytest.fixture
    def mock_conversation(self):
        """Create a mock conversation aggregate"""
        user_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Paris Travel Planning",
            language="en",
        )
        conversation.add_message(role="user", content="Hi, I want to plan a trip to Paris for 3 days")
        conversation.add_message(role="assistant", content="Great! Paris is a wonderful destination. What dates are you thinking?")
        conversation.add_message(role="user", content="June 15-17. I love museums and good food.")
        conversation.add_message(role="assistant", content="Perfect! For museums, I'd recommend the Louvre and Musée d'Orsay. For food, Le Marais has great restaurants.")
        conversation.add_message(role="user", content="That sounds amazing! Can you also suggest some landmarks?")
        conversation.add_message(role="assistant", content="Absolutely! The Eiffel Tower, Notre Dame, and Arc de Triomphe are must-sees.")
        conversation.add_message(role="user", content="Thanks! This is very helpful.")
        return conversation

    @pytest.fixture
    def mock_negative_conversation(self):
        """Create a mock conversation with negative sentiment"""
        user_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Complaint about service",
            language="en",
        )
        conversation.add_message(role="user", content="The app keeps crashing when I search for POIs")
        conversation.add_message(role="assistant", content="I apologize for the inconvenience. Let me help you.")
        conversation.add_message(role="user", content="This is frustrating. I've tried 3 times already.")
        conversation.add_message(role="assistant", content="I understand. Let me escalate this to our technical team.")
        conversation.add_message(role="user", content="This is unacceptable. I want a refund.")
        return conversation

    @pytest.mark.asyncio
    async def test_analyze_conversation_sentiment_positive(self, mock_conversation):
        """Test sentiment analysis for positive conversation"""
        with patch('apps.worker.src.tasks.conversation_analysis.get_gemini_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.analyze_sentiment.return_value = {
                "overall_sentiment": "positive",
                "sentiment_score": 0.85,
                "message_sentiments": [
                    {"role": "user", "sentiment": "neutral", "score": 0.1},
                    {"role": "assistant", "sentiment": "positive", "score": 0.7},
                    {"role": "user", "sentiment": "positive", "score": 0.8},
                    {"role": "assistant", "sentiment": "positive", "score": 0.9},
                    {"role": "user", "sentiment": "positive", "score": 0.75},
                    {"role": "assistant", "sentiment": "positive", "score": 0.85},
                    {"role": "user", "sentiment": "positive", "score": 0.9},
                ],
                "key_phrases": ["wonderful destination", "amazing", "very helpful", "love museums"],
            }
            mock_client.return_value = mock_client_instance

            result = await analyze_conversation_sentiment(mock_conversation)

            assert result is not None
            assert result["overall_sentiment"] == "positive"
            assert result["sentiment_score"] > 0.5
            assert len(result["message_sentiments"]) == 7
            mock_client_instance.analyze_sentiment.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_conversation_sentiment_negative(self, mock_negative_conversation):
        """Test sentiment analysis for negative conversation"""
        with patch('apps.worker.src.tasks.conversation_analysis.get_gemini_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.analyze_sentiment.return_value = {
                "overall_sentiment": "negative",
                "sentiment_score": -0.75,
                "message_sentiments": [
                    {"role": "user", "sentiment": "negative", "score": -0.8},
                    {"role": "assistant", "sentiment": "neutral", "score": 0.1},
                    {"role": "user", "sentiment": "negative", "score": -0.9},
                    {"role": "assistant", "sentiment": "neutral", "score": 0.0},
                    {"role": "user", "sentiment": "negative", "score": -0.95},
                ],
                "key_phrases": ["crashing", "frustrating", "unacceptable", "refund"],
            }
            mock_client.return_value = mock_client_instance

            result = await analyze_conversation_sentiment(mock_negative_conversation)

            assert result is not None
            assert result["overall_sentiment"] == "negative"
            assert result["sentiment_score"] < 0
            assert "crashing" in result["key_phrases"]

    @pytest.mark.asyncio
    async def test_extract_conversation_topics(self, mock_conversation):
        """Test topic extraction from conversation"""
        with patch('apps.worker.src.tasks.conversation_analysis.get_gemini_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.extract_topics.return_value = {
                "topics": [
                    {"topic": "travel_planning", "confidence": 0.95, "keywords": ["trip", "Paris", "plan", "days"]},
                    {"topic": "museums", "confidence": 0.85, "keywords": ["Louvre", "Musée d'Orsay", "museums"]},
                    {"topic": "food", "confidence": 0.80, "keywords": ["food", "restaurants", "Le Marais"]},
                    {"topic": "landmarks", "confidence": 0.90, "keywords": ["Eiffel Tower", "Notre Dame", "Arc de Triomphe"]},
                ],
                "main_topic": "travel_planning",
            }
            mock_client.return_value = mock_client_instance

            result = await extract_conversation_topics(mock_conversation)

            assert result is not None
            assert len(result["topics"]) == 4
            assert result["main_topic"] == "travel_planning"
            assert any(t["topic"] == "museums" for t in result["topics"])
            mock_client_instance.extract_topics.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_conversation_summary(self, mock_conversation):
        """Test conversation summary generation"""
        with patch('apps.worker.src.tasks.conversation_analysis.get_gemini_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.generate_summary.return_value = {
                "summary": "User planned a 3-day trip to Paris (June 15-17) with interests in museums (Louvre, Musée d'Orsay), food (Le Marais), and landmarks (Eiffel Tower, Notre Dame, Arc de Triomphe). Assistant provided recommendations for all categories.",
                "key_points": [
                    "3-day Paris trip planned for June 15-17",
                    "Interests: museums, food, landmarks",
                    "Louvre and Musée d'Orsay recommended for museums",
                    "Le Marais recommended for food",
                    "Eiffel Tower, Notre Dame, Arc de Triomphe for landmarks",
                ],
                "action_items": [],
                "user_satisfaction": "high",
            }
            mock_client.return_value = mock_client_instance

            result = await generate_conversation_summary(mock_conversation)

            assert result is not None
            assert "3-day trip to Paris" in result["summary"]
            assert len(result["key_points"]) == 5
            assert result["user_satisfaction"] == "high"
            mock_client_instance.generate_summary.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_conversation_intent(self, mock_conversation):
        """Test intent detection from conversation"""
        with patch('apps.worker.src.tasks.conversation_analysis.get_gemini_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.detect_intent.return_value = {
                "primary_intent": "travel_planning",
                "confidence": 0.95,
                "secondary_intents": [
                    {"intent": "poi_recommendation", "confidence": 0.85},
                    {"intent": "itinerary_creation", "confidence": 0.80},
                ],
                "entities": {
                    "destination": "Paris",
                    "dates": ["June 15-17"],
                    "interests": ["museums", "food", "landmarks"],
                    "duration": "3 days",
                },
            }
            mock_client.return_value = mock_client_instance

            result = await detect_conversation_intent(mock_conversation)

            assert result is not None
            assert result["primary_intent"] == "travel_planning"
            assert result["confidence"] > 0.9
            assert result["entities"]["destination"] == "Paris"
            assert "museums" in result["entities"]["interests"]
            mock_client_instance.detect_intent.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_user_satisfaction(self, mock_conversation):
        """Test user satisfaction analysis"""
        with patch('apps.worker.src.tasks.conversation_analysis.get_gemini_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.analyze_satisfaction.return_value = {
                "satisfaction_level": "high",
                "score": 0.9,
                "indicators": {
                    "positive_feedback": True,
                    "thank_you_messages": 1,
                    "follow_up_questions": 2,
                    "task_completion": True,
                    "repeated_issues": False,
                },
                "suggestions": [
                    "User seems satisfied with recommendations",
                    "Consider proactively suggesting booking options",
                ],
            }
            mock_client.return_value = mock_client_instance

            result = await analyze_user_satisfaction(mock_conversation)

            assert result is not None
            assert result["satisfaction_level"] == "high"
            assert result["score"] > 0.8
            assert result["indicators"]["positive_feedback"] is True
            assert result["indicators"]["thank_you_messages"] == 1
            mock_client_instance.analyze_satisfaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_analysis_handles_empty_conversation(self):
        """Test analysis handles empty conversation"""
        user_id = uuid4()
        conversation = ConversationAggregate.create(
            user_id=user_id,
            title="Empty Conversation",
            language="en",
        )

        with patch('apps.worker.src.tasks.conversation_analysis.get_gemini_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.analyze_sentiment.return_value = {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "message_sentiments": [],
                "key_phrases": [],
            }
            mock_client.return_value = mock_client_instance

            result = await analyze_conversation_sentiment(conversation)

            assert result is not None
            assert result["overall_sentiment"] == "neutral"
            assert result["sentiment_score"] == 0.0
            assert len(result["message_sentiments"]) == 0

    @pytest.mark.asyncio
    async def test_analysis_handles_api_error(self, mock_conversation):
        """Test analysis handles API errors"""
        with patch('apps.worker.src.tasks.conversation_analysis.get_gemini_client') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.analyze_sentiment.side_effect = Exception("Gemini API quota exceeded")
            mock_client.return_value = mock_client_instance

            with pytest.raises(Exception, match="Gemini API quota exceeded"):
                await analyze_conversation_sentiment(mock_conversation)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])