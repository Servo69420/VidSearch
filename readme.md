# VidSearch

Video search and analysis platform — upload a video or paste a YouTube URL to get a transcript, then chat with an AI about the content.

**Stack:** React + Vite (frontend) · FastAPI + PostgreSQL 16 + pgvector (backend)

---

## Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 16 (with pgvector extension)
- FFmpeg (extracts audio from uploaded videos)

---

## FFmpeg Setup (Windows)

1. Download **ffmpeg-release-essentials.zip** from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds)
2. Extract it (e.g. to `C:\ffmpeg`)
3. Add the `bin` folder to PATH:
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\ffmpeg\bin", "User")
   ```
4. Restart your terminal and verify: `ffmpeg -version`

> **Conda users:** If `ffmpeg` is not recognized after activating your env, prepend it manually before starting the server:
> ```powershell
> $env:Path += ";C:\ffmpeg\bin"
> ```

---

## Database Setup

### Option A — Docker (recommended)

The easiest way to get PostgreSQL 16 + pgvector running locally:

```bash
docker compose up -d
```

- PostgreSQL available at `localhost:5432`
- pgAdmin UI at `http://localhost:5050`

The schema is applied automatically **on first run only** (i.e. when the named volume is created). Skip to [Backend](#backend).

> **Picking up schema changes:** `docker compose up` against an existing volume will not re-run `schema.sql`. To apply a new schema, wipe the volume and recreate:
>
> ```bash
> docker compose down -v          # ⚠️ deletes all local DB data
> docker compose up -d --build    # schema.sql runs again on first boot
>


```powershell
# 1. Activate the env
conda activate VidSearchpy12

### Migrating an existing DB to the current schema

Run this once after enabling pgvector:

```sql
\c vidsearch
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE transcriptions
  ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'pending'
  CHECK (status IN ('pending', 'chunking', 'summarizing', 'ready', 'failed', 'cancel'));

CREATE TABLE IF NOT EXISTS transcript_chunks (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcription_id  UUID NOT NULL REFERENCES transcriptions(id) ON DELETE CASCADE,
    idx               INT NOT NULL,
    level             SMALLINT NOT NULL DEFAULT 1,
    parent_chunk_id   UUID REFERENCES transcript_chunks(id) ON DELETE CASCADE,
    start_s           REAL NOT NULL,
    end_s             REAL NOT NULL,
    text              TEXT NOT NULL,
    segment_start_idx INT,
    segment_end_idx   INT,
    summary           TEXT,
    role              TEXT,
    keywords          TEXT[] DEFAULT '{}',
    embedding         VECTOR(1024),
    summary_embedding VECTOR(1024),
    created_at        TIMESTAMPTZ DEFAULT now(),
    UNIQUE (transcription_id, level, idx)
);

CREATE INDEX IF NOT EXISTS transcript_chunks_transcription_idx
    ON transcript_chunks (transcription_id, idx);
CREATE INDEX IF NOT EXISTS transcript_chunks_embedding_idx
    ON transcript_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS transcript_chunks_summary_embedding_idx
    ON transcript_chunks USING ivfflat (summary_embedding vector_cosine_ops) WITH (lists = 100);
```

> If you switch embedding models, change `VECTOR(1024)` to match the new model's output dimension (e.g. 1536 for OpenAI `text-embedding-3-small`) and recreate the table.

---

## Backend

```bash
# 1. Copy and fill in the environment file
cp backend/.env.example backend/.env
```

Edit `backend/.env` — you **must** set a real `JWT_SECRET`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output as `JWT_SECRET=<generated-value>`. Also update `DATABASE_URL`, `OPENROUTER_API_KEY`, and `OPENAI_API_KEY`.

```bash
# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Start the server
uvicorn main:app --reload
```

API at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:5173`

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (e.g. `postgresql://postgres:yourpassword@localhost:5432/vidsearch`) |
| `JWT_SECRET` | Long random string for signing tokens — **do not use the default** |
| `JWT_ALGORITHM` | Signing algorithm (default: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | How long login tokens last (default: `30`) |
| `OPENROUTER_API_KEY` | API key for AI chat + embeddings + summarization (OpenRouter) |
| `OPENAI_API_KEY` | API key for Whisper transcription of uploaded videos |

---

## Testing the Auth Flow

1. Open `http://localhost:5173` and go to **Sign Up**
2. Create an account (username + password required, rest optional)
3. You should be redirected to the dashboard
4. Refresh the page — you should stay logged in
5. Log out, then log back in with your credentials

You can also test the API directly:

## Architecture & Diagrams

### System Architecture

```mermaid
flowchart TD
    User([Browser / User])

    subgraph Frontend["Frontend (React + Vite :5173)"]
        UI[Pages & Components]
        AuthCtx[Auth Context / JWT]
    end

    subgraph Backend["Backend (FastAPI :8000)"]
        Auth[auth router]
        Trans[transcription router]
        ChatR[chat router]
        FileR[file_input router]
        TCore[transcription.py]
        V2A[video_to_audio.py\nFFmpeg]
    end

    subgraph External["External Services"]
        Whisper[OpenAI Whisper]
        YTAPI[YouTube Transcript API]
        OpenRouter[OpenRouter AI]
    end

    subgraph DB["Database (PostgreSQL 16 + pgvector)"]
        PG[(vidsearch)]
    end

    User <--> Frontend
    Frontend <-->|REST / JWT| Auth
    Frontend <-->|REST / JWT| Trans
    Frontend <-->|REST / JWT| ChatR
    Auth --> PG
    Trans --> TCore
    ChatR --> OpenRouter
    ChatR --> PG
    TCore --> Whisper
    TCore --> YTAPI
    TCore --> V2A
    TCore --> PG
    FileR --> PG
```

---

### Database ER Diagram

```mermaid
erDiagram
    users {
        UUID id PK
        TEXT username UK
        TEXT email UK
        TEXT password_hash
        TEXT name
        TEXT surname
        TEXT avatar_url
        TEXT subscription
        BOOLEAN is_admin
        TIMESTAMPTZ created_at
    }
    user_hobbies {
        UUID user_id FK
        TEXT hobby
    }
    yt_videos {
        UUID id PK
        TEXT source_type
        TEXT source_url UK
        TEXT title
        TIMESTAMPTZ created_at
    }
    user_videos {
        UUID id PK
        UUID user_id FK
        TEXT file_name
        TEXT file_path
        TEXT file_hash
        TIMESTAMPTZ created_at
    }
    transcriptions {
        UUID id PK
        UUID video_id FK
        UUID user_video_id FK
        TEXT full_text
        JSONB segments
        TEXT language
        TEXT model_version
        TEXT status
        TIMESTAMPTZ created_at
    }
    transcript_chunks {
        UUID id PK
        UUID transcription_id FK
        UUID parent_chunk_id FK
        INT idx
        SMALLINT level
        REAL start_s
        REAL end_s
        TEXT text
        TEXT summary
        TEXT role
        VECTOR_1024 embedding
        VECTOR_1024 summary_embedding
        TIMESTAMPTZ created_at
    }
    token_blacklist {
        UUID jti PK
        TEXT token UK
        TIMESTAMPTZ expires_at
    }
    chat_history {
        UUID id PK
        UUID user_id FK
        UUID video_id FK
        UUID user_video_id FK
        TEXT role
        TEXT content
        TIMESTAMPTZ created_at
    }

    users ||--o{ user_hobbies : "has"
    users ||--o{ user_videos : "uploads"
    users ||--o{ chat_history : "sends"
    yt_videos ||--o{ transcriptions : "has"
    user_videos ||--o{ transcriptions : "has"
    transcriptions ||--o{ transcript_chunks : "chunked into"
    transcript_chunks ||--o{ transcript_chunks : "parent of"
    yt_videos ||--o{ chat_history : "referenced in"
    user_videos ||--o{ chat_history : "referenced in"
```

---

### OOP Class Diagram

```mermaid
classDiagram
    class BaseTranscriber {
        <<abstract>>
        +transcribe(source, db) dict
    }
    class YouTubeTranscriber {
        +transcribe(source, db) dict
    }
    class VideoFileTranscriber {
        +transcribe(source, db, user_video_id) dict
    }
    class TranscriberFactory {
        -_yt YouTubeTranscriber
        -_video VideoFileTranscriber
        +get_transcriber(source) BaseTranscriber
    }

    class BaseAuthService {
        <<abstract>>
        +register(...) dict
        +authenticate(username, password, db) str
        +get_current_user(token, db) dict
    }
    class AuthService {
        -_hasher PasswordHasher
        -_tokens TokenManager
        +register(...) dict
        +authenticate(...) str
        +logout(token, db) dict
    }
    class PasswordHasher {
        +hash(password) str
        +verify(password, hashed) bool
    }
    class TokenManager {
        +create(user_id, username) str
        +decode(token) dict
        +blacklist(token, payload, db)
    }

    class BaseCSVExporter {
        <<abstract>>
        +fieldnames list
        +row(record) list
        +export(records) str
    }
    class StatsExporter
    class TranscriptionsExporter
    class VideosExporter
    class TXTURLImporter {
        +parse(content) list~str~
    }

    class BackgroundTask {
        <<abstract>>
        -_interval int
        +execute()
        +run_forever()
    }
    class TokenCleanupTask {
        +execute()
    }

    class User {
        -_id str
        -_username str
        -_hobbies list
        +id str
        +username str
        +hobbies list
        +from_db_row(row) User$
        +to_dict() dict
    }

    BaseTranscriber <|-- YouTubeTranscriber
    BaseTranscriber <|-- VideoFileTranscriber
    TranscriberFactory ..> BaseTranscriber : creates

    BaseAuthService <|-- AuthService
    AuthService *-- PasswordHasher : composition
    AuthService *-- TokenManager : composition

    BaseCSVExporter <|-- StatsExporter
    BaseCSVExporter <|-- TranscriptionsExporter
    BaseCSVExporter <|-- VideosExporter

    BackgroundTask <|-- TokenCleanupTask
```

---

### Upload & Chat Sequence

```mermaid
sequenceDiagram
    actor U as User
    participant FE as Frontend
    participant BE as FastAPI
    participant DB as PostgreSQL
    participant EXT as Whisper / YT API
    participant OR as OpenRouter

    U->>FE: Upload video or paste YouTube URL
    FE->>BE: POST /transcription/upload or /transcription/youtube
    BE->>DB: Insert yt_videos / user_videos row
    BE->>EXT: Transcribe audio / fetch transcript
    EXT-->>BE: Segments + full text
    BE->>DB: Insert transcriptions row (status=pending)
    Note over BE,DB: RAG pipeline: chunking → summarizing → ready
    BE->>DB: Insert transcript_chunks with embeddings
    BE-->>FE: transcription_id + status
    FE-->>U: Show transcript

    U->>FE: Send chat message
    FE->>BE: POST /chat with video_id + message
    BE->>DB: Vector search transcript_chunks
    DB-->>BE: Relevant chunks (context)
    BE->>OR: Prompt = context + message
    OR-->>BE: AI response
    BE->>DB: Save to chat_history
    BE-->>FE: reply text
    FE-->>U: Display AI response
```
