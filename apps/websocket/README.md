# WebSocket Service

Real-time WebSocket server for the AI Smart City Concierge.

## Features

- **Chat Messaging**: Real-time chat between users and AI assistant
- **Location Sharing**: Live location updates with proximity broadcasting
- **Transit Updates**: Real-time vehicle positions, arrival predictions, and alerts
- **Notifications**: Push notifications and in-app alerts

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │◄───►│  WebSocket       │◄───►│   Redis         │
│   (React)       │     │  Service         │     │   (Pub/Sub)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               ▲
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            ┌─────────────┐        ┌─────────────┐
            │   API       │        │   Worker    │
            │   Service   │        │   Service   │
            └─────────────┘        └─────────────┘
```

## Quick Start

### Prerequisites

- Python 3.12+
- Redis 7+
- Docker (optional)

### Local Development

1. Install dependencies:
```bash
cd apps/websocket
pip install -e ".[dev]"
```

2. Start Redis:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Run the service:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

### Docker

```bash
# From project root
docker-compose -f docker/docker-compose.yml up websocket
```

## API Endpoints

### WebSocket Connections

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8001/ws/chat/{user_id}` | Chat messaging |
| `ws://localhost:8001/ws/location/{user_id}` | Location sharing |
| `ws://localhost:8001/ws/transit/{user_id}` | Transit updates |
| `ws://localhost:8001/ws/notifications/{user_id}` | Notifications |
| `ws://localhost:8001/ws/{user_id}` | Unified endpoint |

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe |
| GET | `/health/status` | Detailed status |
| POST | `/api/v1/chat/send` | Send chat message |
| POST | `/api/v1/location/broadcast` | Broadcast location |
| POST | `/api/v1/transit/alert` | Send transit alert |
| POST | `/api/v1/notifications/send` | Send notification |

## WebSocket Message Types

### Chat

```json
// Send message
{
  "type": "chat_message",
  "recipient_id": "user_123",
  "content": "Hello!",
  "message_type": "text"
}

// Typing indicator
{
  "type": "chat_typing",
  "recipient_id": "user_123",
  "is_typing": true
}

// Read receipt
{
  "type": "chat_read",
  "sender_id": "user_123",
  "message_ids": ["msg_1", "msg_2"]
}

// Request history
{
  "type": "chat_history",
  "conversation_id": "conv_123",
  "limit": 50,
  "offset": 0
}
```

### Location

```json
// Location update
{
  "type": "location_update",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "accuracy": 10.0,
  "heading": 45.0,
  "speed": 5.0
}

// Subscribe to user's location
{
  "type": "location_subscribe",
  "target_user_id": "user_123",
  "radius": 1000.0
}

// Get nearby users
{
  "type": "location_get_nearby",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "radius": 1000.0,
  "limit": 50
}
```

### Transit

```json
// Subscribe to route
{
  "type": "transit_subscribe",
  "route_id": "route_123",
  "stop_id": "stop_456"
}

// Get vehicles
{
  "type": "transit_get_vehicles",
  "route_id": "route_123"
}

// Get predictions
{
  "type": "transit_get_predictions",
  "stop_id": "stop_456",
  "route_id": "route_123"
}
```

### Notifications

```json
// Acknowledge notification
{
  "type": "notification_ack",
  "notification_id": "notif_123"
}

// List notifications
{
  "type": "notification_list",
  "limit": 50,
  "offset": 0,
  "unread_only": false
}

// Mark as read
{
  "type": "notification_mark_read",
  "notification_ids": ["notif_123", "notif_456"]
}

// Delete
{
  "type": "notification_delete",
  "notification_ids": ["notif_123"]
}
```

## REST API Examples

### Send Chat Message
```bash
curl -X POST http://localhost:8001/api/v1/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_id": "user_123",
    "sender_id": "user_456",
    "content": "Hello from REST!",
    "message_type": "text"
  }'
```

### Broadcast Location
```bash
curl -X POST http://localhost:8001/api/v1/location/broadcast \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "accuracy": 10.0
  }'
```

### Send Transit Alert
```bash
curl -X POST http://localhost:8001/api/v1/transit/alert \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": ["user_123", "user_456"],
    "route_id": "route_789",
    "message": "Bus delayed by 15 minutes",
    "severity": "warning"
  }'
```

### Send Notification
```bash
curl -X POST http://localhost:8001/api/v1/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "title": "New Message",
    "body": "You have a new message from John",
    "type": "chat",
    "data": {"conversation_id": "conv_123"},
    "action_url": "/chat/conv_123"
  }'
```

## Configuration

Key environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `JWT_SECRET_KEY` | `dev-secret-key` | JWT signing key |
| `WS_HEARTBEAT_INTERVAL` | `30` | Heartbeat interval (seconds) |
| `LOCATION_BROADCAST_RADIUS` | `1000.0` | Location broadcast radius (meters) |
| `LOCATION_UPDATE_THROTTLE` | `5` | Min seconds between location updates |
| `CHAT_MAX_HISTORY` | `100` | Max messages to keep in history |
| `NOTIFICATION_TTL` | `86400` | Notification TTL (seconds) |

## Monitoring

- **Health Checks**: `/health/live`, `/health/ready`, `/health/status`
- **Metrics**: Prometheus metrics at `/metrics` (if enabled)
- **Tracing**: Jaeger integration via OpenTelemetry
- **Logging**: Structured JSON logging via structlog

## Testing

```bash
# Run tests
pytest apps/websocket/tests/

# Run with coverage
pytest --cov=websocket apps/websocket/tests/
```

## Development

### Adding a New Handler

1. Create handler in `src/handlers/`
2. Register message types in `__init__`
3. Add to `ConnectionManager` in `main.py`
4. Add WebSocket endpoint in `main.py`

### Message Flow

1. Client connects to WebSocket endpoint
2. `ConnectionManager.connect()` creates connection
3. Handler receives messages via `ConnectionManager.handle_message()`
4. Handler processes and routes messages
5. `ConnectionManager.send_to_user()` / `broadcast()` delivers messages

## License

MIT