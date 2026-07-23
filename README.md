# RAG Chatbot Starter (FastAPI + ChromaDB)

A minimal, working **Retrieval-Augmented Generation (RAG)** chatbot backend. Upload a PDF, ask questions about it, and get answers grounded in the document — with page-level source citations.

Built with **FastAPI** and **ChromaDB**, with a pluggable LLM layer supporting **OpenAI, Claude, Gemini, and local Ollama**. Runs with **no API key** in retrieval-only mode, and starts with one Docker command.

This is the free starter edition. For the full production version — with a built-in chat UI, streaming, re-ranking, OCR, and more — see [Pro version](#pro-version) below.

---

## Features

- **RAG pipeline** — PDF upload -> text extraction -> chunking -> embedding -> retrieval -> answer generation
- **Source citations** — every answer includes the source filename, page number, and matched text
- **Pluggable LLM providers** — switch between OpenAI, Claude, Gemini, or Ollama with one env var
- **Runs with zero API keys** — default retrieval mode returns matched passages without calling any paid LLM
- **Multilingual embeddings** — works with English, Thai, and many other languages
- **Dockerized** — one `docker compose up` and you're running

---

## Quick start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Interactive docs (Swagger): http://localhost:8000/docs

By default it runs in `retrieval` mode — no API key needed. To use a real LLM, set `LLM_PROVIDER` and the matching key in `.env`.

## Quick start (local)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

> The first run downloads the embedding model (a few hundred MB), once.

---

## API endpoints

| Method   | Path                              | Description                       |
| -------- | --------------------------------- | --------------------------------- |
| `POST`   | `/api/v1/documents/upload`        | Upload & index a PDF              |
| `GET`    | `/api/v1/documents`               | List indexed documents            |
| `DELETE` | `/api/v1/documents/{document_id}` | Delete a document and its vectors |
| `POST`   | `/api/v1/chat`                    | Ask a question over indexed docs  |

### Ask a question

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?", "top_k": 3}'
```

---

## Configuration

Everything is set in `.env` (copy from `.env.example`). Key options:

| Variable          | Default             | Description                                          |
| ----------------- | ------------------- | ---------------------------------------------------- |
| `LLM_PROVIDER`    | `retrieval`         | `retrieval`, `openai`, `ollama`, `gemini`, `claude`  |
| `EMBEDDING_MODEL` | multilingual MiniLM | SentenceTransformers model for embeddings            |
| `*_API_KEY`       | —                   | Key for your chosen provider                         |

Set the model IDs (`OPENAI_MODEL`, `CLAUDE_MODEL`, `GEMINI_MODEL`, `OLLAMA_MODEL`) to ones your account has access to.

---

## Pro version

This starter covers the core RAG flow. The **Pro version** is the production-ready template, with everything wired up and documented:

| Feature                              | Starter (free) | Pro |
| ------------------------------------ | :------------: | :-: |
| Core RAG pipeline + citations        |       yes      | yes |
| OpenAI / Claude / Gemini / Ollama    |       yes      | yes |
| Docker setup                         |       yes      | yes |
| Built-in chat UI (no build step)     |       —        | yes |
| Streaming responses (SSE)            |       —        | yes |
| Cross-encoder re-ranking             |       —        | yes |
| Multi-turn chat memory               |       —        | yes |
| OCR for scanned PDFs                 |       —        | yes |
| DOCX / TXT / Markdown ingestion      |       —        | yes |
| Non-blocking concurrent requests     |       —        | yes |
| Full docs + troubleshooting guide    |       —        | yes |

**Get the Pro version:** https://deaw.gumroad.com/l/deawai

---

## Tech stack

FastAPI - ChromaDB - SentenceTransformers - pypdf - Docker

## License

MIT — see [LICENSE](LICENSE). Free to use in personal and commercial projects.
