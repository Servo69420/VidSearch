# VidSearch — DB & System Flow

Visual reference of how data moves through VidSearch: HTTP routers, the
PostgreSQL schema, the implemented OOP class hierarchy, the transcription
status machine, and the three end-to-end sequences (YouTube ingestion, file
upload, chat).

All diagrams are kept in sync with the current `backend/` source tree. When
adding a router, table, or class, update the matching diagram below.

---

## 1. System Architecture

```mermaid
flowchart TD
    User([Browser / User])

    subgraph Frontend["Frontend (React + Vite :5173)"]
        UI[Pages & Components]
        AuthCtx[Auth Context / JWT]
    end

    subgraph Backend["Backend (FastAPI :8000)"]
        direction TB
        subgraph Routers["Routers (app/routers)"]
            AuthR[auth]
            TransR[transcription]
            ChatR[chat]
            ChatHistR[chat_history]
            FilesR[files]
            FrameR[frame_capture]
            AdminR[admin]
        end
        subgraph Core["Core modules (app/)"]
            TCore[transcription.py<br/>BaseTranscriber + Factory]
            RAG[rag.py<br/>RAGPipeline]
            Embed[embedder.py<br/>OpenRouterEmbedder]
            Summ[summarizer.py<br/>OpenRouterSummarizer]
            V2A[video_to_audio.py<br/>FFmpeg]
            YT[youtube.py]
            Ctx[routers/context.py]
            Deps[dependencies.py<br/>get_current_user]
        end
        subgraph Models["app/models"]
            UserM[User]
            AuthSvc[AuthService]
            BgTask[TokenCleanupTask<br/>lifespan-managed]
        end
    end

    subgraph External["External Services"]
        Whisper[OpenAI Whisper]
        YTAPI[YouTube Transcript API]
        OpenRouter[OpenRouter AI<br/>chat + embeddings + summaries]
    end

    subgraph DB["Database (PostgreSQL 16 + pgvector)"]
        PG[(vidsearch)]
    end

    User <--> Frontend
    Frontend <-->|REST + JWT| AuthR
    Frontend <-->|REST + JWT| TransR
    Frontend <-->|REST + JWT| ChatR
    Frontend <-->|REST + JWT| ChatHistR
    Frontend <-->|REST + JWT| FilesR
    Frontend <-->|REST + JWT| FrameR
    Frontend <-->|REST + JWT, admin only| AdminR

    AuthR --> AuthSvc --> PG
    TransR --> TCore
    TransR --> Ctx
    ChatR --> Ctx
    ChatR --> OpenRouter
    ChatR --> PG
    ChatHistR --> PG
    AdminR --> PG
    FilesR --> PG
    FrameR --> PG

    TCore --> Whisper
    TCore --> YTAPI
    TCore --> V2A
    TCore --> RAG
    RAG --> Embed --> OpenRouter
    RAG --> Summ --> OpenRouter
    RAG --> PG
    Ctx --> RAG
    TCore --> PG

    BgTask -. periodic cleanup .-> PG
    Deps --> PG
```

Notes:
- `app/file_input.py` exists (defines `BaseFileUploader` / `VideoFileUploader`) but is **not** registered as a router — the actual upload router is `app/routers/files.py`.
- `OpenRouter` is consumed by three places: chat completions (`chat.py`), embeddings (`embedder.py`), and summaries (`summarizer.py`).
- `TokenCleanupTask` is started by the FastAPI `lifespan` handler in `main.py` and runs forever, deleting expired rows from `token_blacklist`.

---

## 2. Database ER Diagram

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
        TEXT source_type "upload | youtube"
        TEXT source_url UK
        TEXT title
        TIMESTAMPTZ created_at
    }
    user_videos {
        UUID id PK
        UUID user_id FK
        TEXT file_name
        TEXT file_path
        TEXT file_hash "for dedupe"
        TIMESTAMPTZ created_at
    }
    transcriptions {
        UUID id PK
        UUID video_id FK "XOR with user_video_id"
        UUID user_video_id FK
        TEXT full_text
        JSONB segments
        TEXT language
        TEXT model_version
        TEXT status "pending|chunking|summarizing|ready|failed|cancel"
        TIMESTAMPTZ created_at
    }
    transcript_chunks {
        UUID id PK
        UUID transcription_id FK
        UUID parent_chunk_id FK "self-ref, hierarchical"
        INT idx
        SMALLINT level "1=window, 2=section"
        REAL start_s
        REAL end_s
        TEXT text
        INT segment_start_idx
        INT segment_end_idx
        TEXT summary
        TEXT role
        TEXT_ARRAY keywords
        VECTOR_1024 embedding "ivfflat cosine"
        VECTOR_1024 summary_embedding "ivfflat cosine"
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
        UUID video_id FK "XOR with user_video_id"
        UUID user_video_id FK
        TEXT role "user | assistant"
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

Vector indexes (defined in `schema.sql`):
- `transcript_chunks_embedding_idx` — `ivfflat (embedding vector_cosine_ops)`
- `transcript_chunks_summary_embedding_idx` — `ivfflat (summary_embedding vector_cosine_ops)`

XOR check on both `transcriptions` and `chat_history`: exactly one of `video_id` and `user_video_id` is non-null per row.

---

## 3. `transcriptions.status` State Machine

```mermaid
stateDiagram-v2
    [*] --> pending : YouTube ingest insert
    [*] --> ready   : Whisper insert (file upload)

    pending     --> chunking    : RAGPipeline.process()
    ready       --> chunking    : RAGPipeline.process() (post-Whisper)
    chunking    --> summarizing : embeddings written
    summarizing --> ready       : section summaries written
    chunking    --> failed      : RAG error
    summarizing --> failed      : RAG error
    ready       --> [*]
    failed      --> [*]

    note right of chunking
        rag.py:201 — _set_status("chunking")
    end note
    note right of summarizing
        rag.py:211 — _set_status("summarizing")
    end note
```

`cancel` is allowed by the CHECK constraint but is not currently driven by any
code path; it is reserved for future user-initiated cancellation.

---

## 4. OOP Class Diagram (as implemented)

```mermaid
classDiagram
    %% --- Transcription strategy (Factory + Strategy patterns) ---
    class BaseTranscriber {
        <<abstract>>
        +transcribe(source, db) dict*
    }
    class YouTubeTranscriber {
        -__get_video_id(url) str
        +transcribe(source, db, embed_model, summary_model) dict
    }
    class VideoFileTranscriber {
        -_call_whisper(audio_path)
        +transcribe(source, db, user_video_id) dict
    }
    class TranscriberFactory {
        <<factory>>
        +get_transcriber(source) BaseTranscriber
    }

    BaseTranscriber <|-- YouTubeTranscriber
    BaseTranscriber <|-- VideoFileTranscriber
    TranscriberFactory ..> BaseTranscriber : creates

    %% --- RAG pipeline (Composition + Strategy) ---
    class RAGPipeline {
        -db
        -embedder : Embedder
        -summarizer : Summarizer
        -section_summarizer : Summarizer
        -chunker : ChunkingStrategy
        +process(transcription_id)
        +search(transcription_id, query, top_k) list~RetrievedChunk~
    }
    class ChunkingStrategy {
        <<abstract>>
        +chunk(segments) list~Chunk~*
    }
    class FixedWindowChunker
    class Embedder {
        <<abstract>>
        +embed(texts) list*
    }
    class Summarizer {
        <<abstract>>
        +summarize(text) str*
    }
    class OpenRouterEmbedder
    class OpenRouterSummarizer
    class PlaceholderEmbedder
    class PlaceholderSummarizer

    ChunkingStrategy <|-- FixedWindowChunker
    Embedder        <|-- OpenRouterEmbedder
    Embedder        <|-- PlaceholderEmbedder
    Summarizer      <|-- OpenRouterSummarizer
    Summarizer      <|-- PlaceholderSummarizer
    RAGPipeline o-- ChunkingStrategy : composition
    RAGPipeline o-- Embedder         : composition
    RAGPipeline o-- Summarizer       : composition

    %% --- Audio extraction (Strategy) ---
    class BaseAudioExtractor {
        <<abstract>>
        +extract(video_path) str*
    }
    class FFmpegAudioExtractor
    BaseAudioExtractor <|-- FFmpegAudioExtractor

    %% --- File upload (Strategy) ---
    class BaseFileUploader {
        <<abstract>>
        +save(upload_file) Path*
    }
    class VideoFileUploader
    BaseFileUploader <|-- VideoFileUploader

    %% --- Auth (Composition) ---
    class PasswordHasher {
        +hash(raw) str
        +verify(raw, hashed) bool
    }
    class TokenManager {
        +issue(user_id) str
        +decode(token) dict
        +blacklist(token, db)
    }
    class BaseAuthService {
        <<abstract>>
        +register(...)*
        +login(...)*
    }
    class AuthService {
        -hasher : PasswordHasher
        -tokens : TokenManager
        +register(...)
        +login(...)
        +logout(...)
    }
    BaseAuthService <|-- AuthService
    AuthService o-- PasswordHasher : composition
    AuthService o-- TokenManager   : composition

    %% --- Background tasks (Template Method) ---
    class BackgroundTask {
        <<abstract>>
        +run_forever()
        +tick()*
    }
    class TokenCleanupTask {
        +tick()
    }
    BackgroundTask <|-- TokenCleanupTask

    %% --- Database (Strategy) ---
    class BaseDatabase {
        <<abstract>>
        +connect()*
        +get_connection()*
    }
    class PostgresDatabase
    BaseDatabase <|-- PostgresDatabase

    %% --- Domain model (Encapsulation + Factory Method) ---
    class User {
        -_id, _username, _email, _name, _surname
        -_avatar_url, _subscription, _is_admin
        -_hobbies, _created_at
        +id, username, email, ... (read-only @property)
        +from_db_row(row) User$
        +to_dict() dict
        +__repr__() str
    }

    %% --- CSV / TXT IO (Strategy + Template Method) ---
    class BaseCSVExporter {
        <<abstract>>
        +export(db) str
        +rows(db)*
        +headers()*
    }
    class StatsExporter
    class TranscriptionsExporter
    class VideosExporter
    class TXTURLImporter {
        +import_urls(text) list~str~
    }
    BaseCSVExporter <|-- StatsExporter
    BaseCSVExporter <|-- TranscriptionsExporter
    BaseCSVExporter <|-- VideosExporter
```

OOP pillars / patterns demonstrated (matches the coursework rubric in
`CLAUDE.md`):

| Pillar / Pattern  | Where in code |
|-------------------|---------------|
| Encapsulation     | `User` — every attribute is `_private` with a read-only `@property` (`models/user.py`) |
| Abstraction       | All `<<abstract>>` ABCs above (`BaseTranscriber`, `Embedder`, `Summarizer`, `ChunkingStrategy`, `BaseAudioExtractor`, `BaseFileUploader`, `BaseAuthService`, `BackgroundTask`, `BaseDatabase`, `BaseCSVExporter`) |
| Inheritance       | Each concrete class extending one of the ABCs above |
| Polymorphism      | `TranscriberFactory.get_transcriber(...).transcribe(...)`; `RAGPipeline` calling `Embedder.embed()` regardless of concrete type; admin route iterating `BaseCSVExporter` subclasses |
| Factory Method    | `User.from_db_row()` (`models/user.py`); `TranscriberFactory.get_transcriber()` (`transcription.py`) |
| Strategy          | `ChunkingStrategy`/`FixedWindowChunker` inside `RAGPipeline`; `BaseTranscriber` subclasses chosen by `TranscriberFactory` |
| Template Method   | `BackgroundTask.run_forever()` calling abstract `tick()`; `BaseCSVExporter.export()` calling abstract `rows()` / `headers()` |
| Composition       | `RAGPipeline` *has-a* `Embedder` + `Summarizer` + `ChunkingStrategy`; `AuthService` *has-a* `PasswordHasher` + `TokenManager` |
| Aggregation       | `User` *has-a* `hobbies` list (loaded from `user_hobbies`) |
| File I/O          | `TXTURLImporter` (TXT in) + `BaseCSVExporter` family (CSV out) in `routers/admin.py` |

---

## 5. Sequence A — YouTube URL Submission

```mermaid
sequenceDiagram
    actor U as User
    participant FE as Frontend
    participant TR as transcription router<br/>POST /transcription/url
    participant TC as TranscriberFactory<br/>YouTubeTranscriber
    participant YT as YouTube Transcript API
    participant RAG as RAGPipeline
    participant OR as OpenRouter<br/>(embed + summary)
    participant DB as PostgreSQL

    U->>FE: Paste YouTube URL
    FE->>TR: POST /transcription/url { url }
    TR->>TC: transcribe_video_yt(url, db, ...)

    TC->>DB: SELECT existing 'ready' transcription<br/>JOIN yt_videos
    alt transcription cached
        DB-->>TC: row
        TC->>DB: SELECT count(transcript_chunks)
        opt chunks missing
            TC->>RAG: process(transcription_id)
            RAG->>DB: UPDATE status='chunking'
            RAG->>OR: embed chunks
            RAG->>DB: UPDATE status='summarizing'
            RAG->>OR: summarize sections
            RAG->>DB: INSERT transcript_chunks (level 1 + 2)<br/>with embedding, summary_embedding
            RAG->>DB: UPDATE status='ready'
        end
        TC-->>TR: cached transcription
    else new
        TC->>YT: fetch transcript
        YT-->>TC: segments + full text
        TC->>DB: resolve_or_create yt_videos row
        TC->>DB: INSERT transcriptions (status='pending')
        TC->>RAG: process(transcription_id)
        RAG->>DB: UPDATE status='chunking'
        RAG->>OR: embed
        RAG->>DB: UPDATE status='summarizing'
        RAG->>OR: summarize sections
        RAG->>DB: INSERT transcript_chunks
        RAG->>DB: UPDATE status='ready'
        TC-->>TR: transcription row
    end
    TR-->>FE: transcription { id, status }
    FE-->>U: Show transcript / poll /transcription/status/{id}
```

---

## 6. Sequence B — File Upload

```mermaid
sequenceDiagram
    actor U as User
    participant FE as Frontend
    participant TR as transcription router<br/>POST /transcription/upload
    participant TC as TranscriberFactory<br/>VideoFileTranscriber
    participant V2A as FFmpeg (video_to_audio)
    participant W as OpenAI Whisper
    participant RAG as RAGPipeline
    participant OR as OpenRouter
    participant DB as PostgreSQL
    participant FS as uploads/videos/

    U->>FE: Choose video file
    FE->>TR: POST multipart file
    TR->>FS: write file to disk
    TR->>DB: INSERT user_videos (file_name, file_path)
    DB-->>TR: user_video row

    opt file_hash known
        TR->>DB: SELECT cached transcription<br/>JOIN user_videos ON file_hash
        alt cached hit
            DB-->>TR: cached row
            TR->>DB: INSERT transcriptions copy (status='ready')
            TR-->>FE: transcription row (no Whisper)
        end
    end

    TR->>TC: VideoFileTranscriber.transcribe(path, db, user_video_id)
    TC->>V2A: extract audio (mp3)
    V2A-->>TC: audio path
    TC->>W: whisper-1 transcribe (verbose_json, segments)
    W-->>TC: text + segments + language
    TC->>FS: delete temporary audio
    TC->>DB: INSERT transcriptions (status='ready')

    TC->>RAG: process(transcription_id)
    RAG->>DB: UPDATE status='chunking'
    RAG->>OR: embed chunks
    RAG->>DB: UPDATE status='summarizing'
    RAG->>OR: summarize sections
    RAG->>DB: INSERT transcript_chunks<br/>(embedding, summary_embedding)
    RAG->>DB: UPDATE status='ready'

    TC-->>TR: transcription row
    TR-->>FE: { id, status }
    FE-->>U: Show transcript
```

---

## 7. Sequence C — Chat (`POST /chat/ask`)

```mermaid
sequenceDiagram
    actor U as User
    participant FE as Frontend
    participant CR as chat router<br/>POST /chat/ask
    participant CTX as routers/context.py
    participant RAG as RAGPipeline.search()
    participant OR as OpenRouter<br/>(chat / vision)
    participant DB as PostgreSQL

    U->>FE: Type message<br/>(optional: attach frame, attach .txt)
    FE->>CR: { video_id, message[], frame_base64?, current_time_s?, txt_context? }

    CR->>DB: resolve video_id<br/>(user_videos / yt_videos / YouTube ref)
    CR->>CTX: get_transcript(video_id, db)
    CTX->>DB: SELECT latest transcription
    DB-->>CTX: row (must be status='ready')
    CTX-->>CR: transcript

    par RAG retrieval
        CR->>CTX: search_video_context(query)
        CTX->>RAG: search(transcription_id, query, top_k)
        RAG->>DB: pgvector ANN over transcript_chunks.embedding<br/>+ summary_embedding
        DB-->>RAG: top-k chunks
        RAG-->>CTX: hits
        CTX-->>CR: grounding chunks
    and Now-playing context
        opt current_time_s present
            CR->>CTX: fetch_chunks_at_time(video_id, t)
            CTX->>DB: SELECT level=1 chunks where start_s ≤ t ≤ end_s
            DB-->>CTX: covering chunks
            CTX-->>CR: "happening NOW" snippet
        end
    end

    CR->>OR: round 1 — system + grounding + history + user msg<br/>(tools = VIDEO_PLAYER_TOOLS, vision model if frame)
    OR-->>CR: content + tool_calls?

    opt tool_calls present
        CR->>OR: round 2 — same convo + assistant tool_calls,<br/>tool_choice='none'
        OR-->>CR: natural-language answer
    end

    CR->>DB: INSERT chat_history (role='user', content=user_msg)
    CR->>DB: INSERT chat_history (role='assistant', content=final)
    CR-->>FE: { choices:[{ message:{ content, tool_calls } }] }
    FE-->>U: Render answer + execute player tool_calls<br/>(seek, play, pause, mute)
```

Tool calls are the structured side-channel the chat uses to drive the React
video player (`seek_video`, `play_video`, `pause_video`, etc.) — defined in
`app/routers/video_player_tools.py`.

---

## 8. Cross-references

| Diagram | Source of truth |
|---|---|
| System Architecture | `backend/main.py` (router includes + lifespan) |
| ER + indexes        | `backend/schema.sql` |
| Status state machine| `backend/app/rag.py:201,211,260,270` |
| OOP class diagram   | `grep -rn "^class " backend/app` |
| Sequence A          | `backend/app/transcription.py` (`YouTubeTranscriber`) + `backend/app/rag.py` |
| Sequence B          | `backend/app/transcription.py` (`VideoFileTranscriber`) + `backend/app/routers/transcription.py` |
| Sequence C          | `backend/app/routers/chat.py` + `backend/app/routers/context.py` |

To re-verify after refactors: every router box should match an
`app.include_router(...)` line in `main.py`; every column in the ER diagram
should appear in `schema.sql`; every class in the class diagram should be
findable with `grep -rn "^class <Name>" backend/app`.
