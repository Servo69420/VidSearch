from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from asyncpg import Connection

from app.database import get_db
from app.config import settings

router = APIRouter()
security = HTTPBearer()


# --- Schemas ---

class RegisterRequest(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str

    @field_validator('email', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        return None if v == '' else v

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Helpers ---

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, username: str) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")


# --- Routes ---

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: Connection = Depends(get_db)):
    existing = await db.fetchrow(
        "SELECT id FROM users WHERE username = $1" + (" OR email = $2" if body.email else ""),
        *([body.username, body.email] if body.email else [body.username])
    )
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already taken.")

    hashed = hash_password(body.password)
    await db.execute(
        "INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3)",
        body.username, body.email, hashed
    )
    return {"message": "Account created successfully."}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: Connection = Depends(get_db)):
    user = await db.fetchrow(
        "SELECT id, username, password_hash FROM users WHERE username = $1",
        body.username
    )
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = create_token(str(user["id"]), user["username"])
    return {"access_token": token}


@router.get("/me")
async def me(current_user=Depends(get_current_user), db: Connection = Depends(get_db)):
    user = await db.fetchrow(
        "SELECT id, username, email FROM users WHERE id = $1::uuid",
        current_user["sub"]
    )
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return {"id": str(user["id"]), "username": user["username"], "email": user["email"]}
