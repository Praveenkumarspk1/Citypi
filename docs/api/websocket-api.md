# WebSocket API Documentation

## Connection
```
WS /ws/conversations/{conversation_id}?token=<jwt>
```

### Authentication
Pass JWT token as query parameter: `?token=<jwt>`

## Message Types

### Client → Server

#### Chat Message
```json
{ "type": "message", "content": "Hello", "attachments": [] }
```

#### Voice Input
```json
{ "type": "voice", "audio_data": "base64...", "format": "webm" }
```

#### Image
```json
{ "type": "image", "image_data": "base64...", "mime_type": "image/jpeg" }
```

#### Location
```json
{ "type": "location", "lat": 37.7749, "lng": -122.4194 }
```

#### Typing Indicators
```json
{ "type": "typing_start" }
{ "type": "typing_stop" }
```

#### Ping/Pong
```json
{ "type": "ping" }
```

### Server → Client

#### Token (Streaming)
```json
{ "type": "token", "content": "Hello", "message_id": "msg_123" }
```

#### Tool Call
```json
{ "type": "tool_call", "tool": "search_pois", "args": {"query": "coffee"} }
```

#### Tool Result
```json
{ "type": "tool_result", "tool": "search_pois", "result": [...] }
```

#### Message Complete
```json
{ "type": "message_complete", "message_id": "msg_123", "content": "Full response" }
```

#### Typing Indicator
```json
{ "type": "typing", "user_id": "user_123" }
```

#### Presence
```json
{ "type": "presence", "user_id": "user_123", "status": "online" }
```

#### Error
```json
{ "type": "error", "code": "RATE_LIMIT", "message": "Rate limited" }
```

#### Pong
```json
{ "type": "pong" }
```

## Rooms
- Each conversation is a room
- Users join/leave rooms via WebSocket
- Messages are broadcast to all room members

## Presence
- Online/offline status tracked via Redis
- Presence updates broadcast to relevant rooms
- Multiple connections per user supported
