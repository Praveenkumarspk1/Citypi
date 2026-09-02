# ADR 009: BAAI/bge-m3 Embeddings

## Status
Accepted

## Context
The system needs text embeddings for semantic search, POI matching, and conversation similarity. We need high-quality multilingual embeddings that run locally.

## Decision
Use BAAI/bge-m3 for embeddings:
- 1024-dimensional vectors
- Multilingual support
- 8K context length
- SOTA quality on MTEB benchmark

## Consequences
- **Pros**: SOTA quality, multilingual, runs locally, no API costs
- **Cons**: ~2.7GB model size, requires ~3GB RAM
