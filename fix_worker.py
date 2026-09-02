with open(r'C:\Users\prave\Desktop\P\ai-smart-city-concierge\apps\worker\src\main.py', 'r') as f:
    content = f.read()

# Find and remove the duplicate code
old_code = '''logger.info("Initialized event consumer and DLQ")
            user_repository=self.user_repository,
            max_concurrent=self.settings.worker_embedding_concurrency,
        )

        self.poi_enrichment_task = POIEnrichmentTask(
            overpass_client=self.overpass_client,
            nominatim_client=self.nominatim_client,
            poi_repository=self.poi_repository,
            max_concurrent=self.settings.worker_poi_enrichment_concurrency,
        )

        self.transit_sync_task = TransitSyncTask(
            gtfs_client=self.gtfs_client,
            transit_repository=self.transit_repository,
            max_concurrent=self.settings.worker_transit_sync_concurrency,
        )

        self.weather_sync_task = WeatherSyncTask(
            weather_client=self.weather_client,
            weather_repository=self.weather_repository,
            max_concurrent=self.settings.worker_weather_sync_concurrency,
        )

        self.itinerary_generation_task = ItineraryGenerationTask(
            gemini_client=self.gemini_client,
            itinerary_optimization_service=self.itinerary_optimization_service,
            poi_service=self.poi_service,
            transit_service=self.transit_service,
            weather_service=self.weather_service,
            itinerary_repository=self.itinerary_repository,
            poi_repository=self.poi_repository,
            max_concurrent=self.settings.worker_itinerary_concurrency,
        )

        self.media_processing_task = MediaProcessingTask(
            whisper_client=self.whisper_client,
            clip_client=self.clip_client,
            storage=self.storage,
            media_repository=self.media_repository,
            max_concurrent=self.settings.worker_media_concurrency,
        )

        self.conversation_analysis_task = ConversationAnalysisTask(
            gemini_client=self.gemini_client,
            embedding_client=self.embedding_client,
            vector_store=self.vector_store,
            conversation_repository=self.conversation_repository,
            user_repository=self.user_repository,
            max_concurrent=self.settings.worker_conversation_concurrency,
        )

        logger.info("Initialized background tasks")

        # Initialize task queue

    async def _setup_scheduled_jobs(self) -> None:'''

new_code = '''logger.info("Initialized event consumer and DLQ")

    async def _setup_scheduled_jobs(self) -> None:'''

content = content.replace(old_code, new_code)

with open(r'C:\Users\prave\Desktop\P\ai-smart-city-concierge\apps\worker\src\main.py', 'w') as f:
    f.write(content)

print('Done')