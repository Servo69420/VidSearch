import uuid
from pathlib import Path

from asyncpg import Connection, UniqueViolationError
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials

from app.database import get_db
from app.dependencies import auth_service, get_current_user, security
from app.models.user import User
from app.auth_schemas import (
    LoginRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    TokenResponse,
)

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "avatars"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: Connection = Depends(get_db)):
    return await auth_service.register(
        body.username, body.email, body.password, body.hobbies, db
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: Connection = Depends(get_db)):
    token = await auth_service.authenticate(body.username, body.password, db)
    return {"access_token": token}


@router.get("/me")
async def me(
    current_user=Depends(get_current_user),
    db: Connection = Depends(get_db),
):
    row = await db.fetchrow(
        "SELECT u.id, u.username, u.email, u.name, u.surname, u.avatar_url, "
        "u.subscription, u.created_at, "
        "COALESCE(array_agg(h.hobby) FILTER (WHERE h.hobby IS NOT NULL), '{}') AS hobbies "
        "FROM users u "
        "LEFT JOIN user_hobbies h ON h.user_id = u.id "
        "WHERE u.id = $1::uuid "
        "GROUP BY u.id",
        current_user["sub"],
    )
    if not row:
        raise HTTPException(status_code=401, detail="User not found.")
    user = User.from_db_row(row)
    return user.to_dict()


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
            *values,
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
            detail="Only JPEG, PNG, or WebP images are allowed.",
        )
    data = await file.read()
    if len(data) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be under 2 MB.")
    ext = file.content_type.split("/")[-1].replace("jpeg", "jpg")
    filename = f"{uuid.uuid4().hex}.{ext}"
    (UPLOAD_DIR / filename).write_bytes(data)
    avatar_url = f"/uploads/avatars/{filename}"
    await db.execute(
        "UPDATE users SET avatar_url = $1 WHERE id = $2::uuid",
        avatar_url, current_user["sub"],
    )
    return {"avatar_url": avatar_url}


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Connection = Depends(get_db),
):
    return await auth_service.logout(credentials.credentials, db)
