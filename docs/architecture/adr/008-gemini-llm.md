# ADR 008: Gemini 1.5 Flash (Google AI Studio)

## Status
Accepted

## Context
The system requires an LLM for chat completions, itinerary generation, and POI ranking. We need a free-tier option that doesn't require a credit card.

## Decision
Use Gemini 1.5 Flash via Google AI Studio:
- Free tier: 15 RPM, 1M tokens/day
- No credit card required
- Best cost-quality ratio for chat

## Consequences
- **Pros**: Free, no CC required, good quality, 1M token context
- **Cons**: Rate limited (15 RPM), requires API key management
