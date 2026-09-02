"""
Unit tests for Worker Tasks
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from worker.src.tasks.embedding_generation import EmbeddingGenerationTask
from worker.src.tasks.poi_enrichment import POIEnrichmentTask
from worker.src.tasks.transit_sync import TransitSyncTask
from worker.src.tasks.weather_sync import WeatherSyncTask
from worker.src.tasks.itinerary_generation import ItineraryGenerationTask
from worker.src.tasks.media_processing import MediaProcessingTask
from worker.src.tasks.conversation_analysis import ConversationAnalysisTask
from worker.src.tasks.queue import TaskQueue, TaskPriority


class TestTaskQueue:
    """Test Task Queue"""
    
    @pytest.fixture
    def task_queue(self):
        return TaskQueue()
    
    @pytest.mark.asyncio
    async def test_enqueue_task(self, task_queue):
        """Test enqueueing a task"""
        task_id = await task_queue.enqueue(
            task_name="test_task",
            payload={"key": "value"},
            priority=TaskPriority.NORMAL,
        )
        
        assert task_id is not None
        assert isinstance(task_id, str)
    
    @pytest.mark.asyncio
    async def test_dequeue_task(self, task_queue):
        """Test dequeueing a task"""
        task_id = await task_queue.enqueue(
            task_name="test_task",
            payload={"key": "value"},
        )
        
        task = await task_queue.dequeue()
        
        assert task is not None
        assert task.id == task_id
        assert task.name == "test_task"
        assert task.payload == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self, task_queue):
        """Test that higher priority tasks are dequeued first"""
        await task_queue.enqueue("low_priority", {}, priority=TaskPriority.LOW)
        await task_queue.enqueue("high_priority", {}, priority=TaskPriority.HIGH)
        await task_queue.enqueue("normal_priority", {}, priority=TaskPriority.NORMAL)
        
        task1 = await task_queue.dequeue()
        task2 = await task_queue.dequeue()
        task3 = await task_queue.dequeue()
        
        assert task1.name == "high_priority"
        assert task2.name == "normal_priority"
        assert task3.name == "low_priority"
    
    @pytest.mark.asyncio
    async def test_task_retry(self, task_queue):
        """Test task retry mechanism"""
        task_id = await task_queue.enqueue("failing_task", {})
        task = await task_queue.dequeue()
        
        # Mark as failed
        await task_queue.mark_failed(task.id, "Test error")
        
        # Should be requeued with incremented retry count
        retried_task = await task_queue.dequeue()
        assert retried_task.retry_count == 1
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, task_queue):
        """Test that tasks are moved to dead letter after max retries"""
        task_id = await task_queue.enqueue("failing_task", {}, max_retries=2)
        
        # Fail the task 3 times (exceeding max_retries)
        for i in range(3):
            task = await task_queue.dequeue()
            await task_queue.mark_failed(task.id, f"Error {i}")
        
        # Next dequeue should not return the failed task
        task = await task_queue.dequeue()
        assert task is None or task.name != "failing_task"
    
    @pytest.mark.asyncio
    async def test_mark_completed(self, task_queue):
        """Test marking task as completed"""
        task_id = await task_queue.enqueue("test_task", {})
        task = await task_queue.dequeue()
        
        await task_queue.mark_completed(task.id, {"result": "success"})
        
        # Task should not be returned again
        next_task = await task_queue.dequeue()
        assert next_task is None


class TestEmbeddingGenerationTask:
    """Test Embedding Generation Task"""
    
    @pytest.fixture
    def task(self):
        return EmbeddingGenerationTask()
    
    @pytest.mark.asyncio
    async def test_generate_text_embedding(self, task):
        """Test generating text embedding"""
        with patch.object(task, '_call_embedding_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = [0.1] * 768  # Mock embedding vector
            
            result = await task.execute({
                "text": "Test text for embedding",
                "model": "bge-m3",
            })
            
            assert "embedding" in result
            assert len(result["embedding"]) == 768
            mock_api.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_batch_embeddings(self, task):
        """Test generating batch embeddings"""
        with patch.object(task, '_call_embedding_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = [[0.1] * 768, [0.2] * 768]
            
            result = await task.execute({
                "texts": ["Text 1", "Text 2"],
                "model": "bge-m3",
            })
            
            assert "embeddings" in result
            assert len(result["embeddings"]) == 2
            assert len(result["embeddings"][0]) == 768
    
    @pytest.mark.asyncio
    async def test_invalid_input(self, task):
        """Test handling of invalid input"""
        with pytest.raises(ValueError):
            await task.execute({})  # Missing required fields


class TestPOIEnrichmentTask:
    """Test POI Enrichment Task"""
    
    @pytest.fixture
    def task(self):
        return POIEnrichmentTask()
    
    @pytest.mark.asyncio
    async def test_enrich_poi_from_external_apis(self, task):
        """Test enriching POI from external APIs"""
        with patch.object(task, '_fetch_from_overpass', new_callable=AsyncMock) as mock_overpass, \
             patch.object(task, '_fetch_from_nominatim', new_callable=AsyncMock) as mock_nominatim, \
             patch.object(task, '_fetch_photos', new_callable=AsyncMock) as mock_photos:
            
            mock_overpass.return_value = {"tags": {"cuisine": "italian", "wheelchair": "yes"}}
            mock_nominatim.return_value = {"address": {"city": "New York", "country": "USA"}}
            mock_photos.return_value = ["photo1.jpg", "photo2.jpg"]
            
            result = await task.execute({
                "poi_id": str(uuid4()),
                "name": "Test Restaurant",
                "coordinates": {"latitude": 40.7128, "longitude": -74.0060},
            })
            
            assert "enriched_data" in result
            assert result["enriched_data"]["cuisine"] == "italian"
            assert "photos" in result
            assert len(result["photos"]) == 2
    
    @pytest.mark.asyncio
    async def test_enrich_poi_with_missing_data(self, task):
        """Test enriching POI when some APIs fail"""
        with patch.object(task, '_fetch_from_overpass', new_callable=AsyncMock) as mock_overpass, \
             patch.object(task, '_fetch_from_nominatim', new_callable=AsyncMock) as mock_nominatim:
            
            mock_overpass.return_value = None  # API failed
            mock_nominatim.return_value = {"address": {"city": "New York"}}
            
            result = await task.execute({
                "poi_id": str(uuid4()),
                "name": "Test POI",
                "coordinates": {"latitude": 40.7128, "longitude": -74.0060},
            })
            
            # Should still return partial enrichment
            assert "enriched_data" in result
            assert result["enriched_data"]["city"] == "New York"


class TestTransitSyncTask:
    """Test Transit Sync Task"""
    
    @pytest.fixture
    def task(self):
        return TransitSyncTask()
    
    @pytest.mark.asyncio
    async def test_sync_gtfs_feed(self, task):
        """Test syncing GTFS feed"""
        with patch.object(task, '_download_gtfs', new_callable=AsyncMock) as mock_download, \
             patch.object(task, '_parse_gtfs', new_callable=AsyncMock) as mock_parse, \
             patch.object(task, '_store_transit_data', new_callable=AsyncMock) as mock_store:
            
            mock_download.return_value = b"gtfs_data"
            mock_parse.return_value = {
                "routes": [{"id": "1", "name": "Line 1"}],
                "stops": [{"id": "1", "name": "Stop 1"}],
                "trips": [{"id": "1", "route_id": "1"}],
            }
            
            result = await task.execute({
                "feed_url": "https://example.com/gtfs.zip",
                "city": "New York",
            })
            
            assert result["routes_synced"] == 1
            assert result["stops_synced"] == 1
            assert result["trips_synced"] == 1
            mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_invalid_gtfs(self, task):
        """Test handling invalid GTFS feed"""
        with patch.object(task, '_download_gtfs', new_callable=AsyncMock) as mock_download:
            mock_download.side_effect = Exception("Download failed")
            
            with pytest.raises(Exception):
                await task.execute({
                    "feed_url": "https://invalid.com/gtfs.zip",
                    "city": "New York",
                })


class TestWeatherSyncTask:
    """Test Weather Sync Task"""
    
    @pytest.fixture
    def task(self):
        return WeatherSyncTask()
    
    @pytest.mark.asyncio
    async def test_sync_weather_for_locations(self, task):
        """Test syncing weather for multiple locations"""
        with patch.object(task, '_fetch_weather', new_callable=AsyncMock) as mock_fetch, \
             patch.object(task, '_store_weather', new_callable=AsyncMock) as mock_store:
            
            mock_fetch.return_value = {
                "temperature": 22,
                "condition": "Sunny",
                "humidity": 60,
            }
            
            result = await task.execute({
                "locations": [
                    {"latitude": 40.7128, "longitude": -74.0060, "name": "New York"},
                    {"latitude": 34.0522, "longitude": -118.2437, "name": "Los Angeles"},
                ],
            })
            
            assert result["locations_synced"] == 2
            assert mock_fetch.call_count == 2
            assert mock_store.call_count == 2
    
    @pytest.mark.asyncio
    async def test_sync_weather_partial_failure(self, task):
        """Test syncing weather when some locations fail"""
        with patch.object(task, '_fetch_weather', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                {"temperature": 22, "condition": "Sunny"},
                Exception("API error"),
            ]
            
            result = await task.execute({
                "locations": [
                    {"latitude": 40.7128, "longitude": -74.0060},
                    {"latitude": 34.0522, "longitude": -118.2437},
                ],
            })
            
            assert result["locations_synced"] == 1
            assert result["locations_failed"] == 1


class TestItineraryGenerationTask:
    """Test Itinerary Generation Task"""
    
    @pytest.fixture
    def task(self):
        return ItineraryGenerationTask()
    
    @pytest.mark.asyncio
    async def test_generate_itinerary(self, task):
        """Test generating an itinerary"""
        with patch.object(task, '_find_pois', new_callable=AsyncMock) as mock_find_pois, \
             patch.object(task, '_optimize_route', new_callable=AsyncMock) as mock_optimize, \
             patch.object(task, '_call_llm', new_callable=AsyncMock) as mock_llm:
            
            mock_find_pois.return_value = [
                {"id": "1", "name": "Central Park", "category": "park", "coordinates": {"lat": 40.7829, "lon": -73.9654}},
                {"id": "2", "name": "Met Museum", "category": "museum", "coordinates": {"lat": 40.7794, "lon": -73.9632}},
            ]
            mock_optimize.return_value = [
                {"poi_id": "1", "order": 1, "duration": 120},
                {"poi_id": "2", "order": 2, "duration": 180},
            ]
            mock_llm.return_value = "Here's your personalized itinerary..."
            
            result = await task.execute({
                "user_id": str(uuid4()),
                "destination": "New York",
                "start_date": "2024-06-01",
                "end_date": "2024-06-05",
                "preferences": {"interests": ["parks", "museums"], "pace": "moderate"},
            })
            
            assert "itinerary" in result
            assert len(result["itinerary"]["items"]) == 2
            assert "description" in result["itinerary"]
    
    @pytest.mark.asyncio
    async def test_generate_itinerary_no_pois_found(self, task):
        """Test generating itinerary when no POIs found"""
        with patch.object(task, '_find_pois', new_callable=AsyncMock) as mock_find_pois:
            mock_find_pois.return_value = []
            
            result = await task.execute({
                "user_id": str(uuid4()),
                "destination": "Unknown City",
                "start_date": "2024-06-01",
                "end_date": "2024-06-05",
            })
            
            assert result["itinerary"]["items"] == []
            assert "No POIs found" in result["itinerary"]["description"]


class TestMediaProcessingTask:
    """Test Media Processing Task"""
    
    @pytest.fixture
    def task(self):
        return MediaProcessingTask()
    
    @pytest.mark.asyncio
    async def test_process_image(self, task):
        """Test processing an image"""
        with patch.object(task, '_download_image', new_callable=AsyncMock) as mock_download, \
             patch.object(task, '_resize_image', new_callable=AsyncMock) as mock_resize, \
             patch.object(task, '_upload_to_storage', new_callable=AsyncMock) as mock_upload:
            
            mock_download.return_value = b"image_data"
            mock_resize.return_value = b"resized_image_data"
            mock_upload.return_value = "https://storage.example.com/image.jpg"
            
            result = await task.execute({
                "media_url": "https://example.com/photo.jpg",
                "operations": ["resize", "compress"],
                "sizes": [{"width": 800, "height": 600}, {"width": 400, "height": 300}],
            })
            
            assert "processed_urls" in result
            assert len(result["processed_urls"]) == 2
            assert mock_upload.call_count == 2
    
    @pytest.mark.asyncio
    async def test_process_video(self, task):
        """Test processing a video"""
        with patch.object(task, '_extract_thumbnail', new_callable=AsyncMock) as mock_thumbnail, \
             patch.object(task, '_transcode_video', new_callable=AsyncMock) as mock_transcode, \
             patch.object(task, '_upload_to_storage', new_callable=AsyncMock) as mock_upload:
            
            mock_thumbnail.return_value = b"thumbnail_data"
            mock_transcode.return_value = b"transcoded_video"
            mock_upload.side_effect = [
                "https://storage.example.com/thumb.jpg",
                "https://storage.example.com/video.mp4",
            ]
            
            result = await task.execute({
                "media_url": "https://example.com/video.mp4",
                "operations": ["thumbnail", "transcode"],
            })
            
            assert "thumbnail_url" in result
            assert "video_url" in result


class TestConversationAnalysisTask:
    """Test Conversation Analysis Task"""
    
    @pytest.fixture
    def task(self):
        return ConversationAnalysisTask()
    
    @pytest.mark.asyncio
    async def test_analyze_conversation(self, task):
        """Test analyzing a conversation"""
        with patch.object(task, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "sentiment": "positive",
                "topics": ["travel", "restaurants", "museums"],
                "intent": "plan_trip",
                "entities": [
                    {"type": "location", "value": "New York"},
                    {"type": "date", "value": "2024-06-01"},
                ],
                "summary": "User wants to plan a trip to New York",
            }
            
            result = await task.execute({
                "conversation_id": str(uuid4()),
                "messages": [
                    {"role": "user", "content": "I want to visit New York in June"},
                    {"role": "assistant", "content": "Great! What are your interests?"},
                    {"role": "user", "content": "I like museums and good food"},
                ],
            })
            
            assert result["sentiment"] == "positive"
            assert "travel" in result["topics"]
            assert result["intent"] == "plan_trip"
            assert len(result["entities"]) == 2
    
    @pytest.mark.asyncio
    async def test_analyze_empty_conversation(self, task):
        """Test analyzing empty conversation"""
        result = await task.execute({
            "conversation_id": str(uuid4()),
            "messages": [],
        })
        
        assert result["sentiment"] == "neutral"
        assert result["topics"] == []
        assert result["intent"] == "unknown"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])