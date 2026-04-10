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

## Coursework Context
This project is also a university OOP coursework submission. The following OOP requirements
must be clearly demonstrated in the code:
- All 4 OOP pillars: Encapsulation, Abstraction, Inheritance, Polymorphism
- At least 1 explicit design pattern (Factory Method preferred)
- Composition and/or Aggregation in custom classes
- File I/O: CSV export and/or TXT import (not just binary uploads)

Key files being added for coursework: `backend/app/models/` directory with proper class hierarchy.

## Conventions
- All backend routes are async
- Dependencies injected via FastAPI `Depends()` — `get_db` and `get_current_user`
- File uploads stored under `backend/uploads/`
- CORS allowed for `localhost:5173` and `localhost:5174`

## Frontend Changes
All edits to files under `frontend/` require explicit user approval before applying. Show the proposed change and wait for confirmation.

