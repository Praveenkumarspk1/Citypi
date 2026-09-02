# ADR 011: CLIP ViT-B/32 (Local Vision)

## Status
Accepted

## Context
The system needs image analysis for photo-based POI search and image understanding. We need a local vision model.

## Decision
Use CLIP ViT-B/32 for vision tasks:
- Zero-shot image classification
- Image embeddings (512-dim)
- OpenAI model, well-tested

## Consequences
- **Pros**: Local, zero-shot, no API costs, 512-dim embeddings
- **Cons**: ~150MB model, ~500MB RAM, lower resolution than larger models
