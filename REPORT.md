# VidSearch — OOP Coursework Report

> **Course:** Object-Oriented Programming (2026)
> **Author:** Tima and Adam

---

## Table of Contents
1. [Introduction](#1-introduction)
2. [Body / Analysis](#2-body--analysis)
   - 2.1 [Functional Requirements](#21-functional-requirements)
   - 2.2 [Architecture Overview](#22-architecture-overview)
   - 2.3 [Encapsulation](#23-encapsulation)
   - 2.4 [Abstraction](#24-abstraction)
   - 2.5 [Inheritance](#25-inheritance)
   - 2.6 [Polymorphism](#26-polymorphism)
   - 2.7 [Composition and Aggregation](#27-composition-and-aggregation)
   - 2.8 [Design Pattern — Factory Method](#28-design-pattern--factory-method)
   - 2.9 [File I/O](#29-file-io)
   - 2.10 [Unit Tests](#210-unit-tests)
   - 2.11 [Code Style — PEP 8](#211-code-style--pep-8)
3. [Results](#3-results)
4. [Conclusions](#4-conclusions)
5. [Resources](#5-resources)

---

## 1. Introduction

### Goal of the Coursework

The goal of this coursework is to design and implement a non-trivial software application in Python that demonstrates all four pillars of Object-Oriented Programming, at least one design pattern, file input/output, and test coverage using the `unittest` framework.

### What is VidSearch?

**VidSearch** is a full-stack video transcription and AI-powered search platform. Users can upload video files or paste YouTube URLs to obtain time-stamped transcriptions. Once transcribed, users can have an interactive AI chat conversation about the video content, ask questions, get summaries, and control video playback through natural language commands.

**Core features:**

- Upload MP4 videos or paste any YouTube URL
- Automatic transcription via OpenAI Whisper (uploads) or YouTube Transcript API (YouTube links)
- AI chat with full video context using Retrieval-Augmented Generation (RAG)
- Video player integration — AI can seek, play, pause, and mute the video in response to chat commands
- Admin dashboard with statistics and CSV data export
- JWT-based user authentication with bcrypt password hashing

**Technology stack:**

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI (async) |
| Database | PostgreSQL 16 + pgvector extension |
| Frontend | React 18 + Vite |
| Auth | PyJWT + bcrypt |
| Transcription | OpenAI Whisper, YouTube Transcript API |
| AI Chat | OpenRouter API (Gemma, Gemini models) |
| Audio extraction | FFmpeg |

---

### How to Run the Program

#### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16 with the `pgvector` extension
- FFmpeg on `PATH`
- A `.env` file in `backend/` (see variables below)

#### Required Environment Variables

Create `backend/.env` with the following keys:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/vidsearch
JWT_SECRET=your-random-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
OPENROUTER_API_KEY=your-openrouter-key
OPENAI_API_KEY=your-openai-key
```

#### Step 1 — Database

```bash
# Apply the schema (PostgreSQL must be running)
psql -U postgres -d vidsearch -f backend/schema.sql
```

#### Step 2 — Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# API available at http://localhost:8000
```

#### Step 3 — Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

#### Step 4 — Run tests

```bash
cd backend
python -m unittest discover -s tests -v
```

---

### How to Use the Program

1. Open `http://localhost:5173` and create an account
2. On the dashboard, paste a YouTube URL or upload a video file
3. Wait for the transcription to complete (status indicator in the UI)
4. Open the video — the AI chat panel appears alongside the player
5. Ask questions such as:
   - *"What is this video about?"*
   - *"Summarise the main points"*
   - *"Jump to where they explain recursion"*
   - *"What is happening right now?"*
6. The AI responds with text and, where appropriate, controls the video player automatically

---

## 2. Body / Analysis

### 2.1 Functional Requirements

The table below lists every mandatory coursework requirement and its implementation status.

| # | Requirement | Status | Key Files |
|---|---|---|---|
| 1 | GitHub version control | Done | Repository hosted on GitHub |
| 2 | PEP 8 code style | Done | `setup.cfg` — `flake8` reports 0 violations |
| 3 | All 4 OOP pillars | Done | `app/models/`, `app/transcription.py`, `app/routers/admin.py` |
| 4 | Composition / Aggregation | Done | `AuthService` owns `PasswordHasher` + `TokenManager` |
| 5 | At least 1 design pattern | Done | Factory Method — `User.from_db_row()` |
| 6 | File I/O (read and write) | Done | CSV export (3 classes), TXT URL import |
| 7 | Unit tests (`unittest`) | Done | 11 test modules, 100+ individual test cases |
| 8 | This report (Markdown) | Done | `REPORT.md` |

---

### 2.2 Architecture Overview

```
VidSearch/
├── backend/
│   ├── main.py                     # FastAPI application entry point
│   ├── setup.cfg                   # flake8 configuration (max-line-length = 120)
│   ├── schema.sql                  # PostgreSQL schema
│   ├── app/
│   │   ├── config.py               # Pydantic Settings — reads .env
│   │   ├── database.py             # asyncpg connection pool
│   │   ├── transcription.py        # BaseTranscriber, YouTubeTranscriber, VideoFileTranscriber
│   │   ├── model_config.py         # Frozen dataclass for AI model settings
│   │   ├── rag.py                  # RAG pipeline (embedding + retrieval)
│   │   ├── models/
│   │   │   ├── user.py             # User domain model (Encapsulation + Factory Method)
│   │   │   ├── auth_service.py     # Auth class hierarchy (Abstraction + Inheritance + Composition)
│   │   │   └── background_tasks.py # BackgroundTask ABC + TokenCleanupTask
│   │   └── routers/
│   │       ├── admin.py            # BaseCSVExporter hierarchy + TXTURLImporter
│   │       ├── auth.py             # Auth HTTP endpoints
│   │       ├── chat.py             # AI chat endpoint
│   │       └── transcription.py    # Transcription HTTP endpoints
│   └── tests/
│       ├── test_models.py          # User model tests
│       ├── test_auth.py            # PasswordHasher + TokenManager tests
│       ├── test_admin_io.py        # CSV exporter + TXT importer tests
│       ├── test_chat.py            # Chat loop logic tests
│       └── ...                     # 7 further test modules
└── frontend/
    └── src/                        # React components and pages
```

All backend routes are `async`. Dependencies are injected via FastAPI `Depends()`.

---

### 2.3 Encapsulation

**Encapsulation** bundles data and the methods that operate on it into a single unit, and restricts direct access to internal state through access control.

In VidSearch, the `User` domain model (`app/models/user.py`) stores every attribute as a private field (Python convention: `_` prefix) and exposes them through read-only properties. External code can read user data but cannot mutate it after construction.

```python
class User:
    def __init__(self, user_id: str, username: str, hobbies: list[str] | None = None) -> None:
        self._id = user_id
        self._username = username
        self._hobbies = list(hobbies or [])   # defensive copy

    @property
    def id(self) -> str:
        return self._id

    @property
    def username(self) -> str:
        return self._username

    @property
    def hobbies(self) -> list[str]:
        return list(self._hobbies)    # return copy — caller cannot mutate internal list
```

Attempting to assign a value to any property raises `AttributeError` because no setter is defined:

```python
user = User(user_id="1", username="alice")
user.username = "hacked"   # → AttributeError: can't set attribute
```

This is verified in `tests/test_models.py`:

```python
class TestUserEncapsulation(unittest.TestCase):
    def test_cannot_set_property(self):
        with self.assertRaises(AttributeError):
            self.user.username = "hacked"

    def test_hobbies_returns_copy(self):
        user = User(user_id="1", username="u", hobbies=["a", "b"])
        hobbies = user.hobbies
        hobbies.append("c")
        self.assertEqual(user.hobbies, ["a", "b"])   # internal list unchanged
```

---

### 2.4 Abstraction

**Abstraction** hides implementation details behind a well-defined interface, allowing callers to work with concepts rather than specific implementations.

VidSearch uses Python's `abc.ABC` and `@abstractmethod` in three separate class hierarchies:

#### BaseTranscriber (`app/transcription.py`)

```python
from abc import ABC, abstractmethod

class BaseTranscriber(ABC):
    @abstractmethod
    async def transcribe(self, source: str, db) -> dict:
        pass
```

Callers only interact with `transcribe(source, db)` — they do not need to know whether the source is a YouTube URL or a video file.

#### BaseAuthService (`app/models/auth_service.py`)

```python
class BaseAuthService(ABC):
    @abstractmethod
    async def register(self, username: str, email: str | None,
                       password: str, hobbies: list[str], db) -> dict: ...

    @abstractmethod
    async def authenticate(self, username: str, password: str, db) -> str: ...

    @abstractmethod
    async def get_current_user(self, token: str, db) -> dict: ...
```

#### BaseCSVExporter (`app/routers/admin.py`)

```python
class BaseCSVExporter(ABC):
    @property
    @abstractmethod
    def fieldnames(self) -> list[str]: ...

    @abstractmethod
    def row(self, record) -> list: ...

    def export(self, records) -> str:
        """Template method: concrete subclasses provide fieldnames and row()."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(self.fieldnames)
        for record in records:
            writer.writerow(self.row(record))
        return buf.getvalue()
```

The `export()` method is a **Template Method** variant — the algorithm (write header, iterate rows) is fixed in the base class, while subclasses supply the varying parts (`fieldnames` and `row()`).

#### BackgroundTask (`app/models/background_tasks.py`)

```python
class BackgroundTask(ABC):
    def __init__(self, interval_seconds: int) -> None:
        self._interval = interval_seconds

    @abstractmethod
    async def execute(self) -> None: ...

    async def run_forever(self) -> None:
        while True:
            await asyncio.sleep(self._interval)
            try:
                await self.execute()
            except Exception:
                logger.exception("%s failed", self.__class__.__name__)
```

---

### 2.5 Inheritance

**Inheritance** allows a class to reuse and extend the behaviour of a parent class.

#### Transcriber hierarchy

```
BaseTranscriber (ABC)
├── YouTubeTranscriber     — fetches transcripts via YouTube Transcript API
└── VideoFileTranscriber   — extracts audio with FFmpeg → OpenAI Whisper
```

#### Auth service hierarchy

```
BaseAuthService (ABC)
└── AuthService            — concrete implementation with bcrypt + JWT
```

#### CSV exporter hierarchy

```
BaseCSVExporter (ABC)
├── StatsExporter          — per-user statistics (9 columns)
├── TranscriptionsExporter — transcription metadata (10 columns)
└── VideosExporter         — video catalogue (7 columns)
```

#### Background task hierarchy

```
BackgroundTask (ABC)
└── TokenCleanupTask       — deletes expired JWT blacklist entries hourly
```

Each subclass calls `super().__init__()` where needed (e.g., `TokenCleanupTask`) and overrides only the abstract methods, inheriting the shared logic from the parent.

```python
class TokenCleanupTask(BackgroundTask):
    def __init__(self, interval_seconds: int = 3600) -> None:
        super().__init__(interval_seconds)       # inherits run_forever()

    async def execute(self) -> None:
        pool = get_pool()
        async with pool.acquire() as conn:
            deleted = await conn.execute(
                "DELETE FROM token_blacklist WHERE expires_at < now()"
            )
            logger.info("Token blacklist cleanup: %s", deleted)
```

---

### 2.6 Polymorphism

**Polymorphism** means that different classes can be used through the same interface, with each class providing its own implementation.

#### Same interface, different behaviour — Transcribers

`TranscriberFactory` (see §2.8) returns either a `YouTubeTranscriber` or a `VideoFileTranscriber`. Both are called identically through the `BaseTranscriber` interface:

```python
transcriber: BaseTranscriber = TranscriberFactory.get_transcriber(source)
result = await transcriber.transcribe(source, db)
```

The method dispatched depends on the concrete type at runtime — calling `transcribe()` on a `YouTubeTranscriber` downloads a transcript; on a `VideoFileTranscriber` it runs Whisper. The calling code is identical in both cases.

#### Same interface, different CSV output — Exporters

The three CSV-export endpoints in `app/routers/admin.py` all follow the same shape — only the concrete exporter type changes:

```python
# /admin/stats/export.csv
exporter = StatsExporter()
content = exporter.export(rows)
return StreamingResponse(iter([content]), media_type="text/csv", headers={...})

# /admin/transcriptions/export.csv
exporter = TranscriptionsExporter()
content = exporter.export(rows)
return StreamingResponse(iter([content]), media_type="text/csv", headers={...})

# /admin/videos/export.csv
exporter = VideosExporter()
content = exporter.export(rows)
return StreamingResponse(iter([content]), media_type="text/csv", headers={...})
```

The same `exporter.export(rows)` call dispatches to three different `row()` and `fieldnames` implementations at runtime, producing CSVs with different columns and derived values — without the surrounding endpoint code needing to know the concrete type.

---

### 2.7 Composition and Aggregation

**Composition** (has-a relationship) is when one class owns an instance of another class as part of its internal state. The contained objects do not exist independently of the owner.

`AuthService` is composed of two helper objects:

```python
class AuthService(BaseAuthService):
    def __init__(self) -> None:
        self._hasher = PasswordHasher()    # AuthService owns PasswordHasher
        self._tokens = TokenManager()      # AuthService owns TokenManager

    async def authenticate(self, username: str, password: str, db) -> str:
        user = await db.fetchrow(...)
        if not user or not self._hasher.verify(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid username or password.")
        return self._tokens.create(str(user["id"]), user["username"])
```

`PasswordHasher` wraps `bcrypt` for hashing and verification. `TokenManager` wraps `PyJWT` for token creation, decoding, and blacklist management. Neither class makes sense without an owning service, so this is composition rather than aggregation.

**Aggregation** also appears at the data level: a `Transcription` record *has* many `TranscriptChunks` stored in the `transcript_chunks` table. The chunks reference the transcription by foreign key and are deleted when the transcription is deleted (`ON DELETE CASCADE`), which models the stronger has-a relationship.

---

### 2.8 Design Pattern — Factory Method

**Factory Method** defines an interface for creating objects, letting a factory decide which concrete class to instantiate. This decouples object creation from usage.

`TranscriberFactory` in `app/transcription.py` examines the `source` string and returns the appropriate concrete transcriber. It caches one instance of each subclass at class level, so the factory never re-creates objects:

```python
class TranscriberFactory:
    _yt = YouTubeTranscriber()
    _video = VideoFileTranscriber()

    @classmethod
    def get_transcriber(cls, source: str) -> BaseTranscriber:
        if extract_video_id(source):
            return cls._yt
        return cls._video
```

The dispatch uses `extract_video_id()` rather than a string-prefix check, which means the factory also handles bare YouTube IDs (e.g. `"dQw4w9WgXcQ"`) — a case verified in `tests/test_transcription.py`. The router calls only `TranscriberFactory.get_transcriber(source)` and then `transcriber.transcribe(source, db)`. Adding a third transcription strategy in the future (e.g., an audio-only file) requires only a new subclass and one extra branch in `get_transcriber()` — no changes to any router code.

The `User.from_db_row()` classmethod is a second Factory Method: it constructs a fully-typed `User` object from a raw `asyncpg` database record, centralising the mapping logic in one place:

```python
@classmethod
def from_db_row(cls, row) -> "User":
    return cls(
        user_id=str(row["id"]),
        username=row["username"],
        email=row.get("email"),
        name=row.get("name") or "",
        subscription=row.get("subscription") or "free",
        hobbies=list(row.get("hobbies") or []),
        created_at=row.get("created_at"),
    )
```

---

### 2.9 File I/O

The project implements both **file writing** (CSV export) and **file reading** (TXT batch import) through dedicated classes in `app/routers/admin.py`.

#### Writing — CSV export

Three concrete exporters produce CSV files that administrators can download from the admin dashboard. Each exporter inherits the writing logic from `BaseCSVExporter.export()` and only defines the column names and row-mapping logic.

**Example — StatsExporter** computes derived columns (estimated transcription minutes and cost) on the fly:

```python
class StatsExporter(BaseCSVExporter):
    @property
    def fieldnames(self) -> list[str]:
        return [
            "username", "email", "joined_at", "subscription",
            "transcriptions", "uploaded_videos", "chat_messages",
            "est_transcription_minutes", "est_transcription_cost_usd",
        ]

    def row(self, r) -> list:
        est_min = round((r["total_chars"] / 5) / 130, 2)   # chars → words → minutes
        est_cost = round(est_min * 0.006, 4)
        return [
            r["username"], r["email"] or "",
            r["created_at"].isoformat() if r["created_at"] else "",
            r["subscription"] or "free",
            r["transcriptions"], r["uploaded_videos"], r["chat_messages"],
            est_min, est_cost,
        ]
```

The exported CSV is streamed directly to the client without writing to disk (`io.StringIO` buffer), which is appropriate for a web API context.

#### Reading — TXT batch URL import

Administrators can upload a plain-text file containing one YouTube URL per line. Lines beginning with `#` are treated as comments and skipped. The `TXTURLImporter` class parses the uploaded content:

```python
class TXTURLImporter:
    def parse(self, content: str) -> list[str]:
        urls = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                urls.append(stripped)
        return urls
```

**Example input file (`batch.txt`):**

```text
# Science lectures
https://youtu.be/dQw4w9WgXcQ
https://youtu.be/ZbZSe6N_BXs

# History
https://www.youtube.com/watch?v=abc123
```

**Example API response:**

```json
{
  "imported": 3,
  "urls": [
    "https://youtu.be/dQw4w9WgXcQ",
    "https://youtu.be/ZbZSe6N_BXs",
    "https://www.youtube.com/watch?v=abc123"
  ]
}
```

---

### 2.10 Unit Tests

All tests are written using Python's built-in `unittest` framework and are located in `backend/tests/`.

#### Test modules

| Module | What is tested | Highlights |
|---|---|---|
| `test_models.py` | `User` — properties, encapsulation, `from_db_row()`, `to_dict()` | Verifies that property mutation raises `AttributeError`; confirms hobbies list is defensively copied |
| `test_auth.py` | `PasswordHasher`, `TokenManager` | Roundtrip encode/decode, expired token raises HTTP 401, wrong-secret rejection |
| `test_admin_io.py` | `StatsExporter`, `TranscriptionsExporter`, `VideosExporter`, `TXTURLImporter` | CSV header row, derived columns (estimated minutes/cost), comment line skipping in TXT parser |
| `test_chat.py` | `_run_chat_loop`, `_build_followup_turns`, `_strip_tool_call_literals` | Two-round chat logic, error fallbacks, AI hallucination stripping |
| `test_transcription.py` | `YouTubeTranscriber`, `VideoFileTranscriber`, `TranscriberFactory` | URL parsing with `@unittest.mock.patch`; heavy Whisper model is mocked at import time |
| `test_model_config.py` | `ModelConfig` — env var overrides | Frozen dataclass rejects mutation |
| `test_embedder.py` | `OpenRouterEmbedder` | API mocked; batch splitting logic |
| `test_summarizer.py` | `OpenRouterSummarizer` | Prompt construction, API mocked |
| `test_rag.py` | `RAGPipeline` | Chunk splitting, similarity thresholds |
| `test_youtube_utils.py` | `extract_video_id`, URL normalisation | Standard, short, embed, and edge-case YouTube URL formats |
| `test_groq_key.py` | API key validation helper | Empty, malformed, and valid key strings |

#### Running all tests

```bash
cd backend
python -m unittest discover -s tests -v
```

#### Example test — encapsulation

```python
class TestUserEncapsulation(unittest.TestCase):
    def test_cannot_set_property(self):
        user = User(user_id="1", username="enc_test")
        with self.assertRaises(AttributeError):
            user.username = "hacked"

    def test_hobbies_returns_copy(self):
        user = User(user_id="1", username="u", hobbies=["a", "b"])
        hobbies = user.hobbies
        hobbies.append("c")
        self.assertEqual(user.hobbies, ["a", "b"])
```

#### Example test — Factory Method

```python
class TestTranscriberFactory(unittest.TestCase):
    def test_youtube_url_returns_youtube_transcriber(self):
        t = TranscriberFactory.get_transcriber("https://www.youtube.com/watch?v=abc")
        self.assertIsInstance(t, YouTubeTranscriber)

    def test_file_path_returns_video_file_transcriber(self):
        t = TranscriberFactory.get_transcriber("/tmp/lecture.mp4")
        self.assertIsInstance(t, VideoFileTranscriber)
```

---

### 2.11 Code Style — PEP 8

PEP 8 compliance is enforced using `flake8`. A project-level configuration file (`backend/setup.cfg`) sets the maximum line length to 120 characters, which is a widely accepted team convention explicitly permitted by PEP 8:

```ini
[flake8]
max-line-length = 120
```

Running the linter from the `backend/` directory produces zero violations:

```bash
flake8
# (no output — exit code 0)
```

Additional style conventions followed throughout the codebase:

- All public functions and classes have a one-line docstring describing purpose
- Imports are grouped: standard library → third-party → local (separated by blank lines)
- All backend route handlers are `async def` for non-blocking I/O
- Type hints are used consistently on all function signatures

---

## 3. Results

- **All seven functional code requirements were implemented.** The application is fully working: users can register, upload or link videos, receive transcriptions, and chat with an AI about the video content using RAG-based context retrieval.

- **OOP is applied meaningfully, not artificially.** Each OOP mechanism solves a real design problem: encapsulation protects user state from mutation; the Factory Method eliminates `if/else` branching in the router; the CSV exporter hierarchy allows three different export formats to share the same writing algorithm.

- **The test suite is self-contained.** Heavy external dependencies (OpenAI Whisper, the OpenRouter API) are mocked at the module level, so all 100+ tests run without network access or GPU hardware.

- **The main challenge was asynchronous architecture.** FastAPI's `async`/`await` model is not directly compatible with Python's synchronous `unittest`. Tests that exercise async logic use `unittest.IsolatedAsyncioTestCase` and `asyncio.run()`, while blocking I/O (Whisper inference, FFmpeg) is offloaded using `asyncio.to_thread()` to avoid blocking the event loop.

- **Integrating vector search required extending the standard PostgreSQL setup.** The `pgvector` extension must be installed alongside the database, and embedding dimensions (1024 by default) must be consistent between insertion and retrieval. This added operational complexity beyond a typical web application.

- **Working in one repository as a team was both challenging and interesting.** We used GitHub issues to organize tasks and worked mainly with two branches: `main` and `production`. During development, we also created an extra branch for changing how uploaded video transcription is handled. The original implementation used local Whisper, but we wanted to move it to OpenAI Whisper. Before that, we tried to implement Grok Whisper, but it did not work correctly. At the same time, new changes were being added to the `production` branch from another team member, so my unfinished Grok implementation could not be safely merged. To avoid breaking the working version, I created a separate branch for that experiment. This made the workflow cleaner because the experimental code stayed isolated until it was fixed and ready to merge back into `production`.

- **The project also required managing several external tools and APIs.** Besides the core Python application, we worked with multiple APIs and external services, including AI transcription and chat-related integrations. To keep the development environment more stable, we used Conda to manage the Python environment and installed libraries in a consistent way across the project. We also experimented with visual documentation: using the Markdown Preview Mermaid Support extension in Visual Studio Code, we created flow diagrams and table-style visualizations to better understand how data moves through the application. This helped us document the system more clearly and made the architecture easier to discuss inside the team.

---

## 4. Conclusions

VidSearch demonstrates that all four OOP pillars can be applied naturally in a real-world Python web application. Encapsulation keeps domain models safe from external mutation; abstraction defines clean contracts that isolate the chat router from transcription implementation details; inheritance shares common behaviour across multiple exporter and task classes; and polymorphism allows a single code path to handle YouTube videos and uploaded files identically.

The Factory Method pattern proved particularly valuable: as transcription sources may expand in the future, only `TranscriberFactory.get_transcriber()` needs to change — no router code is touched. This made the application easier to extend and helped keep the router cleaner.

The project also showed that building an AI-based application is not only about writing Python code. A large part of the work involved integrating different services, managing dependencies, handling asynchronous logic, and making sure that experimental changes did not break the working version of the application. Working in a team repository also made Git workflow more important, because unfinished features had to be separated from stable code.

**What was achieved:**

- A production-quality full-stack application with a working UI, authentication, file uploads, AI integration, and an admin panel
- A clean, testable class hierarchy that maps directly to the coursework OOP requirements
- Zero `flake8` violations with the agreed 120-character line limit
- A more realistic understanding of teamwork, branching, dependency management, API integration, and technical documentation

**Future prospects:**

- Introduce a `Subscription` strategy pattern to gate features by user tier.

- Develop a deeper video understanding system that analyzes not only the transcription, but also the visual timeline of the video. For example, the system could recognize when a speaker starts writing on a whiteboard, stops writing, moves to another part of the board, or changes to a new slide. This would make the AI more aware of what is happening at specific moments in the video, not only what is being said. In presentation videos, the system could detect when a new slide appears and connect each part of the transcription to the correct visual context. This would make the chat experience more accurate because the AI would understand both the spoken explanation and the visual material shown at that time.

- Add support for AI interaction directly with video frames. In the future, the system could allow the AI to visually annotate the current frame, for example by crossing out incorrect information, drawing a graph, highlighting an important formula, or marking a specific part of a slide or whiteboard. This would make the application more interactive and useful for learning, because the AI would not only explain the video content in text, but also work with the visual content itself.

- Extend language support beyond English. Currently, the project works mainly with English transcription and chat interaction. A useful improvement would be to support more languages, especially languages used by local students. However, this may be difficult for smaller languages such as Lithuanian or Latvian, where transcription quality and AI understanding may be less reliable than for English.

- Improve the legal and technical approach to video frame extraction. At the moment, video processing depends on downloading or handling videos through FFmpeg. In the future, it would be better to design a more legally safe and platform-friendly way to capture or reference video frames, especially for videos from external platforms such as YouTube. This would make the application more reliable and easier to use in real-world conditions.

- Finish and polish the project so it can become either a product that could be presented or sold in the future, or at least a strong GitHub portfolio project that can be shown on a CV.

---

## 5. Resources

| Resource | Purpose |
|---|---|
| [FastAPI documentation](https://fastapi.tiangolo.com/) | Async web framework |
| [asyncpg documentation](https://magicstack.github.io/asyncpg/) | PostgreSQL async driver |
| [pgvector GitHub](https://github.com/pgvector/pgvector) | Vector similarity extension for PostgreSQL |
| [OpenAI Whisper](https://platform.openai.com/docs/guides/speech-to-text) | Speech-to-text transcription |
| [YouTube Transcript API](https://pypi.org/project/youtube-transcript-api/) | YouTube caption retrieval |
| [OpenRouter](https://openrouter.ai/docs) | Unified API for multiple LLM providers |
| [PyJWT](https://pyjwt.readthedocs.io/) | JSON Web Token implementation |
| [bcrypt](https://pypi.org/project/bcrypt/) | Password hashing |
| [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/) | Code style standard |
| [Python `abc` module](https://docs.python.org/3/library/abc.html) | Abstract base classes |
| [Python `unittest` module](https://docs.python.org/3/library/unittest.html) | Unit testing framework |
| [Refactoring Guru — Factory Method](https://refactoring.guru/design-patterns/factory-method) | Design pattern reference |

