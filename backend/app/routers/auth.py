from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from pathlib import Path
import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from asyncpg import Connection, UniqueViolationError

from app.database import get_db
from app.config import settings

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / \
    "uploads" / "avatars"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()
security = HTTPBearer()


# --- Schemas ---

class RegisterRequest(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str
    hobbies: list[str] = []

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


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None

    @field_validator('email', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        return None if v == '' else v


# --- Helpers ---

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: str, username: str) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM)


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Connection = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[
                settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")

    revoked = await db.fetchval(
        "SELECT 1 FROM token_blacklist WHERE token = $1", token
    )
    if revoked:
        raise HTTPException(status_code=401, detail="Token has been revoked.")

    return payload


# --- Routes ---

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: Connection = Depends(get_db)):
    hashed = hash_password(body.password)
    try:
        await db.execute(
            "INSERT INTO users (username, email, password_hash, hobbies) "
            "VALUES ($1, $2, $3, $4)",
            body.username, body.email, hashed, body.hobbies
        )
    except UniqueViolationError:
        raise HTTPException(status_code=400,
                            detail="Username or email already taken.")
    return {"message": "Account created successfully."}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: Connection = Depends(get_db)):
    user = await db.fetchrow(
        "SELECT id, username, password_hash FROM users WHERE username = $1",
        body.username
    )
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401,
                            detail="Invalid username or password.")

    token = create_token(str(user["id"]), user["username"])
    return {"access_token": token}


@router.get("/me")
async def me(current_user=Depends(get_current_user),
             db: Connection = Depends(get_db)):
    user = await db.fetchrow(
        "SELECT id, username, email, name, surname, avatar_url, "
        "subscription, hobbies, created_at "
        "FROM users WHERE id = $1::uuid",
        current_user["sub"]
    )
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return {
        "id": str(user["id"]),
        "username": user["username"],
        "email": user["email"],
        "name": user["name"] or "",
        "surname": user["surname"] or "",
        "avatar_url": user["avatar_url"] or "",
        "subscription": user["subscription"] or "free",
        "hobbies": list(user["hobbies"] or []),
        "created_at": (
            user["created_at"].isoformat() if user["created_at"] else None
        ),
    }


@router.put("/profile")
async def update_profile(
    body: ProfileUpdateRequest,
    current_user=Depends(get_current_user),
    db: Connection = Depends(get_db),
):
    fields = []
    values = []
    idx = 1
    for col in ("name", "surname", "email"):
        val = getattr(body, col)
        if val is not None:
            fields.append(f"{col} = ${idx}")
            values.append(val)
            idx += 1
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update.")
    values.append(current_user["sub"])
    try:
        await db.execute(
            f"UPDATE users SET {', '.join(fields)} WHERE id = ${idx}::uuid",
            *values
        )
    except UniqueViolationError:
        raise HTTPException(status_code=400, detail="Email already taken.")
    return {"message": "Profile updated."}


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Connection = Depends(get_db),
):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, or WebP images are allowed.")
    data = await file.read()
    if len(data) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Image must be under 2 MB.")
    ext = file.content_type.split("/")[-1].replace("jpeg", "jpg")
    filename = f"{uuid.uuid4().hex}.{ext}"
    (UPLOAD_DIR / filename).write_bytes(data)
    avatar_url = f"/uploads/avatars/{filename}"
    await db.execute(
        "UPDATE users SET avatar_url = $1 WHERE id = $2::uuid",
        avatar_url, current_user["sub"]
    )
    return {"avatar_url": avatar_url}


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Connection = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[
                settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return {"message": "Token already expired."}
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")

    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    await db.execute(
        "INSERT INTO token_blacklist (token, expires_at) VALUES ($1, $2) "
        "ON CONFLICT (token) DO NOTHING",
        token, expires_at
    )
    return {"message": "Logged out successfully."}
