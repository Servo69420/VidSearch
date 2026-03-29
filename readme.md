# VidSearch

Video search and analysis platform.
**Stack:** React + Vite (frontend) · FastAPI + PostgreSQL (backend)

---

## Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 14+

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
