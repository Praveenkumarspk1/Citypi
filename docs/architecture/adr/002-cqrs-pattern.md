# ADR 002: CQRS for Conversations and Itineraries

## Status
Accepted

## Context
Conversations and Itineraries have different read vs. write patterns. Writes require transactional consistency and domain validation, while reads are frequent and benefit from optimized query models.

## Decision
Implement Command Query Responsibility Segregation (CQRS):
- **Commands**: `StartConversation`, `SendMessage`, `CreateItinerary` — mutate state via aggregates
- **Queries**: `GetConversation`, `GetNearbyPOIs`, `GetTransitRoutes` — read optimized DTOs
- **Handlers**: Separate command and query handlers

## Consequences
- **Pros**: Optimized read models, clear write validation, scalable independently
- **Cons**: More code files, eventual consistency between read/write models
