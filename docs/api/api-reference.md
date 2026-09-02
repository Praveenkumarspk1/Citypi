# API Documentation

## Base URL
- Development: `http://localhost:8000/api/v1`
- Staging: `https://staging-api.concierge.city/api/v1`
- Production: `https://api.concierge.city/api/v1`

## Authentication
All endpoints except login/register require a JWT token:
```
Authorization: Bearer <JWT_TOKEN>
```

## Core Endpoints

### Conversations
| Method | Path | Description |
|--------|------|-------------|
| POST | `/conversations` | Start new conversation |
| GET | `/conversations` | List conversations |
| GET | `/conversations/{id}` | Get conversation with messages |
| DELETE | `/conversations/{id}` | Delete conversation |
| POST | `/conversations/{id}/messages` | Send message |
| POST | `/conversations/{id}/messages/stream` | Stream message (SSE) |

### Itineraries
| Method | Path | Description |
|--------|------|-------------|
| POST | `/itineraries` | Create itinerary |
| GET | `/itineraries` | List itineraries |
| GET | `/itineraries/{id}` | Get itinerary |
| PUT | `/itineraries/{id}` | Update itinerary |
| DELETE | `/itineraries/{id}` | Delete itinerary |
| POST | `/itineraries/{id}/share` | Generate share link |

### POIs
| Method | Path | Description |
|--------|------|-------------|
| GET | `/pois` | Search POIs |
| GET | `/pois/nearby` | Nearby POIs |
| GET | `/pois/{id}` | Get POI details |
| POST | `/pois/search/semantic` | Semantic search |

### Transit
| Method | Path | Description |
|--------|------|-------------|
| POST | `/transit/routes` | Plan route |
| GET | `/transit/stops/nearby` | Nearby stops |
| GET | `/transit/stops/{id}/departures` | Real-time departures |

### Weather
| Method | Path | Description |
|--------|------|-------------|
| GET | `/weather/current` | Current weather |
| GET | `/weather/forecast` | Forecast |
| GET | `/weather/alerts` | Weather alerts |

### Media
| Method | Path | Description |
|--------|------|-------------|
| POST | `/media/transcribe` | Speech-to-text |
| POST | `/media/analyze-image` | Image analysis |
| POST | `/media/upload` | Upload media |

### Users
| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/me` | Current user profile |
| PUT | `/users/me` | Update profile |
| GET | `/users/me/preferences` | Get preferences |
| PUT | `/users/me/preferences` | Update preferences |

## WebSocket API
Connection: `WS /ws/conversations/{conversation_id}?token=<jwt>`

Message types: `message`, `voice`, `image`, `location`, `typing_start`, `typing_stop`, `ping`
