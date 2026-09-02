# ADR 010: faster-whisper small (Local STT)

## Status
Accepted

## Context
The system needs speech-to-text for voice input. We need a local model that works without API calls and supports multiple languages.

## Decision
Use faster-whisper small model:
- CTranslate2 optimized
- CPU-friendly
- Best quality for small model size
- ~488MB model size

## Consequences
- **Pros**: Local, no API costs, multilingual, CPU-friendly
- **Cons**: ~488MB download, ~1GB RAM, slower than cloud APIs
