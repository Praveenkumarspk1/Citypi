# ADR 007: Redis 7 (Streams + Cache)

## Status
Accepted

## Context
The system needs caching, session storage, pub/sub, and message queuing. We need a single system that handles all these needs without adding infrastructure complexity.

## Decision
Use Redis 7 as a multi-purpose data store:
- **Cache**: L2 caching layer with TTL-based expiration
- **Session Store**: User sessions and refresh tokens
- **Pub/Sub**: Real-time event broadcasting
- **Streams**: Message queue for background tasks

## Consequences
- **Pros**: Sub-millisecond latency, built-in data structures, reduces infrastructure complexity
- **Cons**: Single point of failure (mitigated by Redis Cluster in production), data loss risk for streams
