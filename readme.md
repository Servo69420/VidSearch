# VidSearch

Video search and analysis platform.
**Stack:** React + Vite (frontend) · FastAPI + PostgreSQL (backend)

---

## Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 14+
- FFmpeg (extract audio from vudeos uploaded by users)

---

## FFmpeg Setup (Windows)

1. Download **ffmpeg-release-essentials.zip** from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds)
2. Extract it (e.g. to `C:\Users\YourName\Desktop\ffmpegld`)
3. Add the `bin` folder to PATH:
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Users\YourName\Desktop\ffmpegld\bin", "User")
   ```
4. Restart your terminal and verify: `ffmpeg -version`

> **Conda users:** If `ffmpeg` is not recognized after activating your env, run this in the terminal before starting:
> ```powershell
> $env:Path += ";C:\Users\YourName\Desktop\ffmpegld\bin"
> ```

---

## Database Setup

### 1. Install PostgreSQL (if not installed)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Create the database

You can connect to PostgreSQL in one of two ways depending on your auth config:

```bash
# Option A: Using sudo (peer auth, default on Ubuntu)
sudo -u postgres psql

# Option B: Using password auth
psql -U postgres -h 127.0.0.1 -W
```

Once inside the `psql` shell, run:

```sql
CREATE DATABASE vidsearch;
\c vidsearch
\i /absolute/path/to/backend/schema.sql
\q
```

> Replace `/absolute/path/to/` with the actual path to your project.

### 3. Verify tables were created

```bash
sudo -u postgres psql -d vidsearch -c "\dt"
```

You should see the `users` table listed.

### Troubleshooting PostgreSQL

| Error | Fix |
|---|---|
| `Peer authentication failed for user "postgres"` | Use `sudo -u postgres psql` instead, or connect via TCP: `psql -U postgres -h 127.0.0.1 -W` |
| `role "postgres" does not exist` | Create it: `sudo -u postgres createuser --superuser postgres` |
| `database "vidsearch" does not exist` | Create it: `sudo -u postgres psql -c "CREATE DATABASE vidsearch;"` |
| `relation "users" does not exist` | Run the schema: `sudo -u postgres psql -d vidsearch -f backend/schema.sql` |
| `column "X" does not exist` | Your schema is outdated. See "Updating an existing database" below |

### Updating an existing database

If you already have the `users` table but are missing newer columns, run these in psql:

```sql
\c vidsearch
ALTER TABLE users ADD COLUMN IF NOT EXISTS name TEXT DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS surname TEXT DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription TEXT DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS hobbies TEXT[] DEFAULT '{}';
```

### pgvector + transcript chunks (3-pass summary feature)

The schema now requires the `pgvector` extension and adds a `transcript_chunks`
table plus a `status` column on `transcriptions`. If you're updating an
existing database, install pgvector first, then run the migration.

**Install pgvector:**

- **Ubuntu/Debian:** `sudo apt install postgresql-14-pgvector` (match your PG version)
- **Windows (conda):** `conda install -c conda-forge pgvector` inside your env
- **From source:** see https://github.com/pgvector/pgvector#installation

**Windows (conda-based Postgres — the setup used in this project):**

If you installed PostgreSQL into a conda env (e.g. `VidSearchpy12`) via
`conda install -c conda-forge postgresql`, the cleanest way to add pgvector
is to install it into the same env:

```powershell
# 1. Activate the env that owns your Postgres install
conda activate VidSearchpy12

# 2. Install pgvector into the env (must match the env's Postgres version)
conda install -c conda-forge pgvector

# 3. Make sure the server is running. If it's not, start it:
& "$env:CONDA_PREFIX\Library\bin\pg_ctl.exe" `
    -D "$env:CONDA_PREFIX\var\postgresql" `
    -l "$env:CONDA_PREFIX\var\postgresql\server.log" start

# 4. Enable the extension inside the vidsearch DB
& "$env:CONDA_PREFIX\Library\bin\psql.exe" -h 127.0.0.1 -p 5433 -U Tima -d vidsearch `
    -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 5. Apply the full schema (idempotent — safe to re-run)
& "$env:CONDA_PREFIX\Library\bin\psql.exe" -h 127.0.0.1 -p 5433 -U Tima -d vidsearch `
    -f .\backend\schema.sql
```

> Replace `-p 5433` and `-U Tima` with whatever port/user your local
> Postgres was initialized with. If you're not sure, check the
> `DATABASE_URL` in your `backend/.env`.

**Windows (native Postgres installer from EDB):**

If you installed Postgres via the official installer (not conda), pgvector
isn't bundled — you have to build it with MSVC:

```powershell
# 1. Open "x64 Native Tools Command Prompt for VS 2022" (not regular PowerShell)
# 2. Point nmake at your Postgres install
set "PGROOT=C:\Program Files\PostgreSQL\14"

# 3. Clone and build
git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git
cd pgvector
nmake /F Makefile.win
nmake /F Makefile.win install
```

Then, in `psql` connected to `vidsearch`:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

And apply the schema:

```powershell
& "C:\Program Files\PostgreSQL\14\bin\psql.exe" -U postgres -d vidsearch -f .\backend\schema.sql
```

**Updating an existing Windows DB (already has old `transcriptions` table):**

`CREATE TABLE IF NOT EXISTS` will *not* add the new `status` column to an
existing `transcriptions` table. Run this once after enabling the extension:

```sql
\c vidsearch
ALTER TABLE transcriptions
  ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'pending'
  CHECK (status IN ('pending', 'chunking', 'summarizing', 'ready', 'failed'));
```

**Verify the install:**

```powershell
& "$env:CONDA_PREFIX\Library\bin\psql.exe" -h 127.0.0.1 -p 5433 -U Tima -d vidsearch -c "\dx vector"
& "$env:CONDA_PREFIX\Library\bin\psql.exe" -h 127.0.0.1 -p 5433 -U Tima -d vidsearch -c "\d transcript_chunks"
```

You should see the `vector` extension listed and `transcript_chunks` with
`embedding vector(384)` and `summary_embedding vector(384)` columns.

**Migrate an existing DB:**

```sql
\c vidsearch
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE transcriptions
  ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'pending'
  CHECK (status IN ('pending', 'chunking', 'summarizing', 'ready', 'failed'));

CREATE TABLE IF NOT EXISTS transcript_chunks (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcription_id  UUID NOT NULL REFERENCES transcriptions(id) ON DELETE CASCADE,
    idx               INT NOT NULL,
    start_s           REAL NOT NULL,
    end_s             REAL NOT NULL,
    text              TEXT NOT NULL,
    summary           TEXT,
    role              TEXT,
    keywords          TEXT[] DEFAULT '{}',
    embedding         VECTOR(384),
    summary_embedding VECTOR(384),
    created_at        TIMESTAMPTZ DEFAULT now(),
    UNIQUE (transcription_id, idx)
);

CREATE INDEX IF NOT EXISTS transcript_chunks_transcription_idx
    ON transcript_chunks (transcription_id, idx);
CREATE INDEX IF NOT EXISTS transcript_chunks_embedding_idx
    ON transcript_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS transcript_chunks_summary_embedding_idx
    ON transcript_chunks USING ivfflat (summary_embedding vector_cosine_ops) WITH (lists = 100);
```

> If you later switch embedding models, change `VECTOR(384)` to match the new
> model's dimension (e.g. 1536 for OpenAI `text-embedding-3-small`) and
> re-create the table.

---

## Backend

```bash
# 1. Set up environment
cp backend/.env.example backend/.env
```

Edit `backend/.env` — you **must** change `JWT_SECRET` to a real random value:

```bash
# Generate a secure secret
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output into your `.env` file as `JWT_SECRET=<generated-value>`.

Also update `DATABASE_URL` with your actual PostgreSQL password.

```bash
# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Start the server
uvicorn main:app --reload
```

API runs at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

---

## Frontend

```bash
cd frontend
npm install
npm run dev

#(you may need to install)
npm install react-markdown remark-gfm        
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

---

## Testing the Auth Flow

1. Open `http://localhost:5173` and go to **Sign Up**
2. Create an account (username + password required, rest optional)
3. You should be redirected to the dashboard
4. Refresh the page — you should stay logged in
5. Log out, then log back in with your credentials

You can also test the API directly:

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test1234"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test1234"}'

# Get profile (replace <token> with the access_token from login)
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <token>"
```


IF could not start server AFTER & "C:\Users\Tima\miniconda3\envs\VidSearchpy12\Library\bin\pg_ctl.exe" -D "C:\Users\Tima\miniconda3\envs\VidSearchpy12\var\postgresql" start  
THEN:
& "C:\Users\Tima\miniconda3\envs\VidSearchpy12\Library\bin\psql.exe" -h 127.0.0.1 -p 5433 -U Tima -d vidsearch          