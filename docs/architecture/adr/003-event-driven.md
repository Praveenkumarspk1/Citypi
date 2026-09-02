# ADR 003: Event-Driven Architecture with Redis Streams

## Status
Accepted

## Context
The system needs to handle asynchronous events (message received, POI discovered, itinerary created) reliably without blocking the main request flow.

## Decision
Use Redis Streams as the event bus for local development:
- Domain events are published to Redis Streams
- Workers consume events asynchronously
- Outbox pattern ensures reliable event delivery
- Dead letter queue handles failed events

## Consequences
- **Pros**: Decoupled services, reliable delivery, built-in retry, no extra infrastructure
- **Cons**: Redis Streams less feature-rich than Kafka, requires Redis
