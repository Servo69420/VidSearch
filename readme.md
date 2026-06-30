# VidSearch

Barebones video transcription and RAG chat app. Paste a YouTube URL or upload a video, wait for transcription/indexing, then ask contextual questions about the video. The system also lets the LLM control the video player through function calls. This was the foundation that <img src="logo.png" alt="LentaI" width="30" style="vertical-align: middle;" /> was later built upon.

**Stack:** React + Vite frontend, FastAPI backend, PostgreSQL 16 + pgvector, OpenRouter.

## Prerequisites

- Node.js 18+
- Python 3.11+
- Docker, or PostgreSQL 16 with pgvector installed

## Backend

Create `backend/.env` with:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/vidsearch
OPENROUTER_API_KEY=your-openrouter-key
OPENAI_API_KEY=your-openai-key
```
OPENAI_API_KEY is optional


Then run:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

API: `http://localhost:8000`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

The frontend opens directly into the workspace. There are no accounts, login pages, dashboards, subscriptions, or admin UI.

## Core Endpoints

- `POST /transcription/url` starts YouTube transcription and RAG indexing.
- `GET /transcription/status/{video_id}` checks readiness.
- `GET /transcription/segments/{video_id}` returns timeline segments.
- `POST /files/upload_video` uploads a local video and starts transcription.
- `POST /chat/ask` asks the AI about a ready video.
- `GET /chat-history/{video_id}` returns video-scoped chat history.
- `POST /capture-frame` captures a YouTube frame for visual questions.

## Database Tables

- `yt_videos`: shared YouTube/video references.
- `user_videos`: uploaded video files. The legacy table name remains, but it is not account-scoped.
- `transcriptions`: transcript text and segment JSON.
- `transcript_chunks`: embedded RAG chunks.
- `chat_history`: video-scoped conversation history.

## Verification

```bash
cd backend
python -m unittest discover -s tests -v

cd ../frontend
npm run build
```
