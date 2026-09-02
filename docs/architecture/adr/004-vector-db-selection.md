# ADR 004: ChromaDB (Dev) / Qdrant (Prod)

## Status
Accepted

## Context
The system requires vector search for POI semantic search, conversation embeddings, and recommendation features. We need a vector database that works locally (free) and scales in production.

## Decision
- **Development**: ChromaDB — pure Python, lightweight, no extra containers
- **Production**: Qdrant — high-performance, scalable, supports quantization and replication

## Consequences
- **Pros**: Free local dev, production-grade performance, HNSW indexing
- **Cons**: Two systems to maintain, migration path from ChromaDB to Qdrant
