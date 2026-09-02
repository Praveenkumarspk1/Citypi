# ADR 001: Clean Architecture + Domain-Driven Design

## Status
Accepted

## Context
The AI Smart City Concierge is a complex domain with multiple bounded contexts (conversations, POIs, transit, weather, itineraries, users). We need an architecture that separates concerns, enables testability, and allows the domain logic to evolve independently of infrastructure.

## Decision
Adopt Clean Architecture with Domain-Driven Design (DDD) patterns:
- **Domain Layer**: Entities, Value Objects, Aggregates, Domain Events, Repository Interfaces, Domain Services
- **Application Layer**: Commands, Queries, Handlers, DTOs, Ports, Application Services
- **Infrastructure Layer**: Repository implementations, External API adapters, Messaging, Storage, Auth
- **Interface Layer**: REST API routes, WebSocket handlers, Middleware

## Consequences
- **Pros**: High testability, independent deployability, clear separation of concerns, domain logic isolated from frameworks
- **Cons**: More boilerplate code, steeper learning curve for new developers
