## Architecture Diagram

┌───────────────────────────────┐
│         Frontend (Cloud Run)  │
│  React + Vite + Tailwind      │
│  UI Components                │
└───────────────┬───────────────┘
                │ HTTPS
                ▼
┌───────────────────────────────┐
│         Backend (Cloud Run)   │
│  Node/Python API              │
│  Auth, RAG, Agent calls       │
│  ElevenLabs TTS               │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│   Vertex AI Agent Engine      │
│   Multi‑Agent Logic           │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│   Vertex Vector DB (RAG)      │
│   Embeddings + Retrieval      │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│        Gemini LLM             │
│   Grounded Answer Generation  │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│        ElevenLabs TTS         │
│   Voice Synthesis             │
└───────────────────────────────┘
