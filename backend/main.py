from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from file_input import router as file_router

from app.database import connect, disconnect
from app.routers import auth

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    yield
    await disconnect()


app = FastAPI(title="VidSearch API", version="0.1.0", lifespan=lifespan)
app.include_router(file_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/health")
async def health():
    return {"status": "ok"}

# & "C:\Users\Tima\miniconda3\envs\VidSearchpy12\Library\bin\pg_ctl.exe" -D "C:\Users\Tima\miniconda3\envs\VidSearchpy12\var\postgresql" start
# C:\Users\Tima\miniconda3\envs\VidSearchpy12\Library\bin\pg_ctl.exe -D $env:PGDATA start
# C:\Users\Tima\miniconda3\envs\VidSearchpy12\Library\bin\psql.exe -h 127.0.0.1 -U Tima -d postgres
