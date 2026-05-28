# Casa Alo's Bistro — Aria AI Chatbot

[![Live Demo](https://img.shields.io/badge/Live_Demo-railway-8B5CF6?style=for-the-badge&logo=railway&logoColor=white)](https://alorestaurant-production.up.railway.app)
[![GitHub](https://img.shields.io/badge/GitHub-akabonge-181717?style=for-the-badge&logo=github)](https://github.com/akabonge/alorestaurant)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Claude](https://img.shields.io/badge/Claude_API-CC785C?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-orange?style=for-the-badge)](https://trychroma.com)
[![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.ai)
[![Portfolio](https://img.shields.io/badge/Portfolio-aialo.io-C9A84C?style=for-the-badge&logo=google-chrome&logoColor=white)](https://aialo.io)

**Demo 1 of the AI Alo Portfolio** · [aialo.io](https://aialo.io)

A RAG-powered restaurant chatbot built with FastAPI, ChromaDB, and sentence-transformers.
Supports Ollama (local, free) and Claude API (cloud, best quality) via a single `.env` flag.

**The pain point it solves:** Restaurant staff spend hours answering the same questions every day — menu questions, hours, allergens, reservations. Aria handles all of it 24/7.

---

## System Architecture

```mermaid
flowchart TD
    subgraph Browser["Browser (Client)"]
        SITE["Restaurant Website\nindex.html + app.js\nAria chat widget"]
    end

    subgraph Server["FastAPI Server — port 8080"]
        MAIN["main.py\nStatic file serving + CORS"]
        ROUTER["router.py\nPOST /api/chat"]
    end

    subgraph RAG["RAG Pipeline"]
        direction TB
        EMBED["embedder.py\nsentence-transformers\nall-MiniLM-L6-v2 (local)"]
        CHROMA[("ChromaDB\nchroma_store/\npersistent vector DB")]
        PIPE["pipeline.py\nSystem prompt + context\n→ Aria personality"]
    end

    subgraph LLM["LLM Layer (dual)"]
        CLAUDE["☁ Claude Haiku\n(Anthropic API)"]
        OLLAMA["⬡ Ollama llama3.2\n(local fallback)"]
    end

    subgraph Data["Knowledge Base"]
        FILES["data/\nmenu.json · faqs.json\nrestaurant_info.json"]
    end

    INGEST["scripts/ingest_data.py\n(run once)"]

    SITE -->|"POST /api/chat"| ROUTER
    MAIN --> ROUTER
    ROUTER --> PIPE
    PIPE --> EMBED
    EMBED -->|"query embedding"| CHROMA
    CHROMA -->|"top chunks"| PIPE
    PIPE -->|"API key set?"| CLAUDE
    PIPE -->|"no API key"| OLLAMA
    CLAUDE -->|"response"| ROUTER
    OLLAMA -->|"response"| ROUTER
    FILES --> INGEST
    INGEST --> EMBED
    EMBED -->|"batch embeddings"| CHROMA
```

---

## Part of the AI Alo Portfolio

| Demo | Business | Key Feature |
|---|---|---|
| **Demo 1** | **Casa Alo's Bistro** | **Restaurant RAG chatbot** |
| Demo 2 | Rappahannock Realty Group | Lead qualifier + CRM dashboard |
| Demo 3 | Luminara Med Spa | Treatment recommender + candidacy screening |

Built by [Aloysious Kabonge](https://aialo.io) — AI automation consulting for local businesses in Fredericksburg, VA.

---

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + Uvicorn |
| Vector DB | ChromaDB (local, persistent) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` |
| LLM (cloud) | Anthropic Claude (haiku) |
| LLM (local) | Ollama (`llama3.2`) |
| Frontend | Vanilla HTML/CSS/JS (embeddable widget) |

## Quick Start

### 1. Install dependencies
```bash
cd casa_alos_bistro
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY if you have one, or leave blank to use Ollama
```

### 3. Ingest data into ChromaDB
```bash
python scripts/ingest_data.py
```
This runs once (or whenever you update the data files). Downloads the embedding model on first run (~90MB).

### 4. Start the server
```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) — you'll see the restaurant website with the chat widget.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat` | Send a message, get a response |
| `GET`  | `/api/health` | Check status, provider, doc count |
| `DELETE` | `/api/session/{id}` | Clear a conversation session |

### Chat request
```json
POST /api/chat
{
  "message": "What are your most popular dishes?",
  "session_id": "user_abc"
}
```

### Chat response
```json
{
  "response": "Our guests always rave about the Cacio e Pepe...",
  "sources": ["menu/Paste (Pastas)", "faqs/Menu & Food"],
  "session_id": "user_abc",
  "provider": "claude"
}
```

## LLM Selection Logic

```
ANTHROPIC_API_KEY set?
  ✓ → Uses Claude (cloud, best quality)
  ✗ → Uses Ollama (local, free, requires Ollama running)
```

Embeddings always run locally via sentence-transformers — no API key needed regardless.

## Data Files

| File | Contents |
|------|----------|
| `data/menu.json` | Full menu — 7 categories, 40+ items, prices, dietary info |
| `data/faqs.json` | 30+ FAQ Q&A pairs across 6 categories |
| `data/restaurant_info.json` | Hours, address, contact, parking, policies |

To update content, edit the JSON files and re-run `python scripts/ingest_data.py`.

## Project Structure

```
casa_alos_bistro/
├── app/
│   ├── main.py          # FastAPI app + CORS + static file serving
│   ├── router.py        # Chat, health, session endpoints
│   ├── config.py        # Settings (pydantic-settings, .env)
│   ├── models.py        # Request/response schemas
│   └── rag/
│       ├── embedder.py  # ChromaDB collection setup
│       ├── retriever.py # Top-k semantic search
│       └── pipeline.py  # RAG: retrieve → generate (Ollama or Claude)
├── data/
│   ├── menu.json
│   ├── faqs.json
│   └── restaurant_info.json
├── frontend/
│   └── index.html       # Restaurant website + embedded chat widget
├── scripts/
│   └── ingest_data.py   # One-time data indexing script
├── requirements.txt
├── .env.example
└── .gitignore
```
