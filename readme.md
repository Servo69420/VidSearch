# VidSearch

Video search and analysis platform.
**Stack:** React + Vite (frontend) · FastAPI + PostgreSQL (backend)

---

## Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL

---

## Backend

```bash
# 1. Create the database
psql -U postgres -c "CREATE DATABASE vidsearch;"

# 2. Run the schema
psql -U postgres -d vidsearch -f backend/schema.sql

# 3. Set up environment
cp backend/.env.example backend/.env
# Edit backend/.env with your PostgreSQL password and a JWT secret

# 4. Install dependencies
cd backend
pip install -r requirements.txt

# 5. Start the server
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
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET` | Long random string for signing tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | How long login tokens last (default: 30) |
