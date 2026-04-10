# VidSearch — Project Guide for Claude Code

## Project Overview
VidSearch is a full-stack video transcription and AI-powered search/chat platform.
Users can upload videos or paste YouTube URLs to get transcriptions, then chat with an AI about the video content.

## Stack
- **Backend**: Python + FastAPI (async), asyncpg, PostgreSQL + pgvector
- **Frontend**: React + Vite (SPA)
- **Auth**: JWT (PyJWT) + bcrypt
- **Transcription**: OpenAI Whisper (uploads), YouTube Transcript API (YT links)
- **AI Chat**: OpenRouter API
- **Audio extraction**: FFmpeg
- **Containerisation**: Docker Compose (db + pgadmin)

## Repo Structure
```
VidSearch/
├── backend/
│   ├── main.py               # FastAPI app, middleware, lifespan, router registration
│   ├── requirements.txt
│   ├── schema.sql            # PostgreSQL schema (auto-applied by Docker)
│   ├── uploads/              # Runtime file storage (videos, avatars)
│   └── app/
│       ├── config.py         # Pydantic Settings (env vars)
│       ├── database.py       # asyncpg connection pool, get_db dependency
│       ├── transcription.py  # Core transcription business logic
│       ├── video_to_audio.py # FFmpeg wrapper
│       ├── file_input.py     # Generic file upload router
│       └── routers/
│           ├── auth.py       # Register, login, profile, avatar
│           ├── chat.py       # AI chat with video context
│           └── transcription.py  # Transcription HTTP endpoints
├── frontend/
│   └── src/                  # React components, pages, contexts
└── docker-compose.yml        # PostgreSQL (pgvector/pg16) + pgAdmin
```

## Running the Project

### Database (Docker)
```bash
docker compose up -d
```
PostgreSQL available at `localhost:5432`, pgAdmin at `http://localhost:5050`.

### Backend
```bash
cd backend
uvicorn main:app --reload
```
API at `http://localhost:8000`. Uses conda env `VidSearchpy12`.

Start PostgreSQL manually (without Docker):
```
C:\Users\Tima\miniconda3\envs\VidSearchpy12\Library\bin\pg_ctl.exe -D $env:PGDATA start
```

### Frontend
```bash
cd frontend
npm run dev
```
App at `http://localhost:5173`.

## Environment Variables
Backend reads from a `.env` file (not committed). Expected keys include:
- `DATABASE_URL` — asyncpg connection string
- `JWT_SECRET`
- `OPENROUTER_API_KEY`

## Database
- Engine: PostgreSQL 16 + pgvector extension
- Schema auto-applied from `backend/schema.sql` on first Docker run
- Key tables: `users`, `yt_videos`, `user_videos`, `transcriptions`, `chat_history`
- `transcriptions` stores segments as JSONB

## Coursework Requirements (OOP Coursework 2026)

This project is a university OOP coursework submission.

### Functional Requirements (all mandatory)

| # | Requirement | Status | Notes |
|---|-------------|--------|-------|
| 1 | **GitHub usage** | Done | Repo already on GitHub |
| 2 | **PEP 8 code style** | Partial | Verify with linter before submission |
| 3 | **4 OOP pillars** | TODO | Must demonstrate **Encapsulation**, **Abstraction**, **Inheritance**, **Polymorphism** in code. Each must be explained in the report with code snippets |
| 4 | **Composition and/or Aggregation** | TODO | Custom classes must show has-a relationships. Explain in report |
| 5 | **At least 1 design pattern** | TODO | Pick from: Singleton, Factory Method, Abstract Factory, Builder, Prototype, Adapter, Composite, Decorator. Must explain why it fits the project |
| 6 | **File I/O (read & write)** | TODO | Import/export data via TXT, CSV, or similar. Not just binary uploads — must be structured text files (e.g., CSV export of transcriptions, TXT import of config) |
| 7 | **Unit tests** | TODO | Use Python `unittest` framework. Cover core functionality |
| 8 | **Report (Markdown)** | TODO | See report structure below |

### Report Structure (Markdown file, English or Lithuanian)

1. **Introduction** — What is the app? How to run it? How to use it?
2. **Body/Analysis** — How the code meets each functional requirement. Use code snippets
3. **Results** — 3-5 bullet points on outcomes and challenges
4. **Conclusions** — Key findings, what was achieved, future prospects
5. *(Optional)* Resources and references

### Evaluation Breakdown

- **Code requirements (items 1-7)**: 70% (2.1 points)
- **Report + presentation**: 30% (0.9 points)
- **Total**: 3 points

### Implementation Plan for OOP Requirements

Key files: `backend/app/models/` directory with proper class hierarchy.

- **Encapsulation**: Private attributes with property accessors in model classes
- **Abstraction**: Abstract base classes (ABC) defining interfaces for services
- **Inheritance**: Class hierarchy (e.g., BaseVideo -> YouTubeVideo / UploadedVideo)
- **Polymorphism**: Method overriding in subclasses (e.g., different transcription strategies)
- **Design pattern**: Factory Method for creating video/transcription objects based on source type
- **Composition/Aggregation**: e.g., Transcription *has* Segments, User *has* Videos
- **File I/O**: CSV export of transcription data, TXT import for batch processing
- **Tests**: `unittest` test cases for model classes, factory, and file I/O

## Conventions
- All backend routes are async
- Dependencies injected via FastAPI `Depends()` — `get_db` and `get_current_user`
- File uploads stored under `backend/uploads/`
- CORS allowed for `localhost:5173` and `localhost:5174`

## Frontend Changes
All edits to files under `frontend/` require explicit user approval before applying. Show the proposed change and wait for confirmation.
<<<<<<< HEAD

testing merge
=======
aasaasasaassasasas
>>>>>>> 310e92d41f79052383672334d2b7f58fe9ea8813
