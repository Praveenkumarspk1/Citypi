"""
Conversation Analysis Background Tasks

Handles analysis of conversations for insights, sentiment, topic extraction,
and recommendation generation.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from ai_smart_city_concierge.domain.repositories.conversation_repository import (
    ConversationRepository,
)
from ai_smart_city_concierge.domain.repositories.user_repository import UserRepository
from ai_smart_city_concierge.infrastructure.external_apis.bge_m3_client import BGEM3Client
from ai_smart_city_concierge.infrastructure.external_apis.gemini_client import GeminiClient
from ai_smart_city_concierge.infrastructure.vector_stores.base_vector_store import BaseVectorStore

logger = logging.getLogger(__name__)


@dataclass
class ConversationAnalysisTask:
    """Task for conversation analysis."""
    conversation_id: str
    analysis_type: str  # 'sentiment', 'topics', 'recommendations', 'summary', 'intent', 'full'
    priority: int = 0
    force_refresh: bool = False


class ConversationAnalysisTask:
    """
    Background task for analyzing conversations.
    """

    def __init__(
        self,
        gemini_client: GeminiClient,
        embedding_client: BGEM3Client,
        vector_store: BaseVectorStore,
        conversation_repository: ConversationRepository,
        user_repository: UserRepository,
        max_concurrent: int = 4,
    ):
        self.gemini_client = gemini_client
        self.embedding_client = embedding_client
        self.vector_store = vector_store
        self.conversation_repository = conversation_repository
        self.user_repository = user_repository
        self.max_concurrent = max_concurrent
        self._queue: asyncio.Queue[ConversationAnalysisTask] = asyncio.Queue()
        self._running = False
        self._worker_tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Start the conversation analysis workers."""
        if self._running:
            return

        self._running = True
        logger.info("Starting conversation analysis workers")

        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._worker(f"conversation-analysis-worker-{i}"))
            self._worker_tasks.append(task)

    async def stop(self) -> None:
        """Stop the conversation analysis workers."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping conversation analysis workers")

        await self._queue.join()

        for task in self._worker_tasks:
            task.cancel()

        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

    async def enqueue(self, task: ConversationAnalysisTask) -> None:
        """Add a conversation analysis task to the queue."""
        await self._queue.put(task)

    async def enqueue_batch(self, tasks: list[ConversationAnalysisTask]) -> None:
        """Add multiple conversation analysis tasks to the queue."""
        for task in tasks:
            await self._queue.put(task)

    async def _worker(self, worker_name: str) -> None:
        """Worker coroutine that processes conversation analysis tasks."""
        logger.info(f"{worker_name} started")

        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)

                try:
                    await self._process_task(task)
                except Exception as e:
                    logger.error(f"{worker_name} error processing task {task.conversation_id}: {e}")
                finally:
                    self._queue.task_done()

            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{worker_name} unexpected error: {e}")
                await asyncio.sleep(1)

        logger.info(f"{worker_name} stopped")

    async def _process_task(self, task: ConversationAnalysisTask) -> None:
        """Process a single conversation analysis task."""
        logger.debug(f"Analyzing conversation {task.conversation_id} ({task.analysis_type})")

        conversation = await self.conversation_repository.get_by_id(task.conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found: {task.conversation_id}")
            return

        # Get messages for analysis
        messages = await self.conversation_repository.get_messages(task.conversation_id)
        if not messages:
            logger.debug(f"No messages to analyze for conversation {task.conversation_id}")
            return

        # Prepare conversation text
        conversation_text = self._prepare_conversation_text(messages)

        if task.analysis_type == "sentiment":
            await self._analyze_sentiment(conversation, conversation_text, messages)
        elif task.analysis_type == "topics":
            await self._extract_topics(conversation, conversation_text)
        elif task.analysis_type == "recommendations":
            await self._generate_recommendations(conversation, conversation_text, messages)
        elif task.analysis_type == "summary":
            await self._generate_summary(conversation, conversation_text)
        elif task.analysis_type == "intent":
            await self._analyze_intent(conversation, conversation_text, messages)
        elif task.analysis_type == "full":
            await asyncio.gather(
                self._analyze_sentiment(conversation, conversation_text, messages),
                self._extract_topics(conversation, conversation_text),
                self._generate_recommendations(conversation, conversation_text, messages),
                self._generate_summary(conversation, conversation_text),
                self._analyze_intent(conversation, conversation_text, messages),
                return_exceptions=True,
            )
        else:
            logger.warning(f"Unknown analysis type: {task.analysis_type}")

    def _prepare_conversation_text(self, messages: list[Any]) -> str:
        """Prepare conversation text for analysis."""
        parts = []
        for msg in messages:
            role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
            parts.append(f"{role}: {msg.content}")
        return "\n".join(parts)

    async def _analyze_sentiment(
        self,
        conversation,
        conversation_text: str,
        messages: list[Any],
    ) -> None:
        """Analyze sentiment of the conversation."""
        try:
            prompt = f"""
Analyze the sentiment of this conversation between a user and an AI travel assistant.

Conversation:
{conversation_text}

Provide a JSON response with:
{{
  "overall_sentiment": "positive|negative|neutral",
  "sentiment_score": 0.0 to 1.0,
  "user_satisfaction": "satisfied|neutral|frustrated",
  "key_emotions": ["emotion1", "emotion2"],
  "sentiment_trend": "improving|stable|declining",
  "frustration_points": ["point1", "point2"]
}}
"""

            response = await self.gemini_client.generate_text(prompt)
            sentiment_data = self._parse_json_response(response)

            if sentiment_data:
                await self.conversation_repository.update_analysis(
                    conversation.id,
                    {"sentiment": sentiment_data}
                )
                logger.debug(f"Analyzed sentiment for conversation {conversation.id}")

        except Exception as e:
            logger.error(f"Failed to analyze sentiment for {conversation.id}: {e}")

    async def _extract_topics(
        self,
        conversation,
        conversation_text: str,
    ) -> None:
        """Extract topics from the conversation."""
        try:
            prompt = f"""
Extract the main topics and themes from this travel planning conversation.

Conversation:
{conversation_text}

Provide a JSON response with:
{{
  "primary_topics": ["topic1", "topic2", "topic3"],
  "secondary_topics": ["topic4", "topic5"],
  "locations_mentioned": ["location1", "location2"],
  "categories_discussed": ["restaurants", "museums", "transport"],
  "user_intents": ["find_poi", "plan_route", "get_weather"],
  "entities": {{
    "pois": ["poi1", "poi2"],
    "cities": ["city1"],
    "dates": ["date1"],
    "budget_mentions": ["budget1"]
  }}
}}
"""

            response = await self.gemini_client.generate_text(prompt)
            topics_data = self._parse_json_response(response)

            if topics_data:
                await self.conversation_repository.update_analysis(
                    conversation.id,
                    {"topics": topics_data}
                )
                logger.debug(f"Extracted topics for conversation {conversation.id}")

        except Exception as e:
            logger.error(f"Failed to extract topics for {conversation.id}: {e}")

    async def _generate_recommendations(
        self,
        conversation,
        conversation_text: str,
        messages: list[Any],
    ) -> None:
        """Generate recommendations based on conversation."""
        try:
            # Get user preferences
            user = await self.user_repository.get_by_id(conversation.user_id)

            prompt = f"""
Based on this travel planning conversation, generate personalized recommendations.

User Preferences:
- Interests: {user.interests if user else 'Unknown'}
- Budget: {user.budget_level if user else 'Unknown'}
- Accessibility: {user.accessibility_needs if user else 'None'}
- Dietary: {user.dietary_restrictions if user else 'None'}

Conversation:
{conversation_text}

Provide a JSON response with:
{{
  "poi_recommendations": [
    {{"name": "POI name", "category": "category", "reason": "why recommended", "priority": 1-5}}
  ],
  "itinerary_suggestions": [
    {{"title": "Itinerary idea", "description": "details", "duration_days": 1-7}}
  ],
  "activity_suggestions": ["activity1", "activity2"],
  "dining_suggestions": ["restaurant1", "restaurant2"],
  "practical_tips": ["tip1", "tip2"]
}}
"""

            response = await self.gemini_client.generate_text(prompt)
            recommendations_data = self._parse_json_response(response)

            if recommendations_data:
                await self.conversation_repository.update_analysis(
                    conversation.id,
                    {"recommendations": recommendations_data}
                )

                # Store recommendations in vector DB for future retrieval
                await self._store_recommendations_embeddings(
                    conversation.id,
                    recommendations_data
                )

                logger.debug(f"Generated recommendations for conversation {conversation.id}")

        except Exception as e:
            logger.error(f"Failed to generate recommendations for {conversation.id}: {e}")

    async def _store_recommendations_embeddings(
        self,
        conversation_id: str,
        recommendations: dict[str, Any],
    ) -> None:
        """Store recommendation embeddings for semantic search."""
        try:
            # Create text representation of recommendations
            text_parts = []

            for rec in recommendations.get("poi_recommendations", []):
                text_parts.append(f"{rec.get('name', '')}: {rec.get('reason', '')}")

            for rec in recommendations.get("itinerary_suggestions", []):
                text_parts.append(f"{rec.get('title', '')}: {rec.get('description', '')}")

            text_parts.extend(recommendations.get("activity_suggestions", []))
            text_parts.extend(recommendations.get("dining_suggestions", []))
            text_parts.extend(recommendations.get("practical_tips", []))

            if not text_parts:
                return

            text_content = " ".join(text_parts)
            embedding = await self.embedding_client.embed_text(text_content)

            if embedding:
                await self.vector_store.upsert(
                    collection_name="conversation_recommendations",
                    vectors=[{
                        "id": f"recommendations:{conversation_id}",
                        "vector": embedding,
                        "metadata": {
                            "conversation_id": conversation_id,
                            "type": "recommendations",
                            "content": text_content[:500],
                            "created_at": datetime.utcnow().isoformat(),
                        }
                    }]
                )

        except Exception as e:
            logger.error(f"Failed to store recommendation embeddings: {e}")

    async def _generate_summary(
        self,
        conversation,
        conversation_text: str,
    ) -> None:
        """Generate a summary of the conversation."""
        try:
            prompt = f"""
Generate a concise summary of this travel planning conversation.

Conversation:
{conversation_text}

Provide a JSON response with:
{{
  "summary": "2-3 sentence summary",
  "key_decisions": ["decision1", "decision2"],
  "action_items": ["action1", "action2"],
  "unresolved_questions": ["question1", "question2"],
  "conversation_outcome": "completed|in_progress|abandoned"
}}
"""

            response = await self.gemini_client.generate_text(prompt)
            summary_data = self._parse_json_response(response)

            if summary_data:
                await self.conversation_repository.update_analysis(
                    conversation.id,
                    {"summary": summary_data}
                )
                logger.debug(f"Generated summary for conversation {conversation.id}")

        except Exception as e:
            logger.error(f"Failed to generate summary for {conversation.id}: {e}")

    async def _analyze_intent(
        self,
        conversation,
        conversation_text: str,
        messages: list[Any],
    ) -> None:
        """Analyze user intent throughout the conversation."""
        try:
            # Analyze last few user messages for current intent
            user_messages = [m for m in messages if m.role.value == "user"][-5:]
            recent_text = "\n".join([f"User: {m.content}" for m in user_messages])

            prompt = f"""
Analyze the user's current intent in this travel planning conversation.

Recent user messages:
{recent_text}

Full conversation context:
{conversation_text[-2000:]}

Provide a JSON response with:
{{
  "primary_intent": "find_poi|plan_itinerary|get_transit|get_weather|book|general_chat",
  "intent_confidence": 0.0 to 1.0,
  "secondary_intents": ["intent1", "intent2"],
  "required_tools": ["search_pois", "plan_route", "get_weather"],
  "missing_information": ["info1", "info2"],
  "suggested_next_actions": ["action1", "action2"]
}}
"""

            response = await self.gemini_client.generate_text(prompt)
            intent_data = self._parse_json_response(response)

            if intent_data:
                await self.conversation_repository.update_analysis(
                    conversation.id,
                    {"intent": intent_data}
                )
                logger.debug(f"Analyzed intent for conversation {conversation.id}")

        except Exception as e:
            logger.error(f"Failed to analyze intent for {conversation.id}: {e}")

    def _parse_json_response(self, response: str) -> dict[str, Any] | None:
        """Parse JSON from LLM response."""
        import json

        try:
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
        return None

    # High-level methods

    async def analyze_conversation(
        self,
        conversation_id: str,
        analysis_types: list[str] = None,
    ) -> None:
        """Enqueue analysis tasks for a specific conversation."""
        if analysis_types is None:
            analysis_types = ["sentiment", "topics", "recommendations", "summary", "intent"]

        tasks = [
            ConversationAnalysisTask(
                conversation_id=conversation_id,
                analysis_type=atype,
                priority=1,
            )
            for atype in analysis_types
        ]

        await self.enqueue_batch(tasks)

    async def analyze_recent_conversations(
        self,
        hours: int = 24,
        analysis_types: list[str] = None,
    ) -> int:
        """Analyze recent conversations. Returns count queued."""
        since = datetime.utcnow() - timedelta(hours=hours)
        conversations = await self.conversation_repository.get_recent(since=since)

        count = 0
        for conv in conversations:
            await self.analyze_conversation(conv.id, analysis_types)
            count += 1

        logger.info(f"Queued analysis for {count} recent conversations")
        return count

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def is_running(self) -> bool:
        """Check if workers are running."""
        return self._running
