"""Auth service classes — demonstrates Abstraction, Inheritance,
Polymorphism, and Composition.

Abstraction:  BaseAuthService defines the interface via ABC.
Inheritance:  AuthService extends BaseAuthService.
Polymorphism: AuthService overrides abstract methods with concrete logic.
Composition:  AuthService *has-a* PasswordHasher and *has-a* TokenManager.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from asyncpg import Connection, UniqueViolationError
from fastapi import HTTPException

from app.config import settings


# --- Component classes (used via Composition) ---


class PasswordHasher:
    """Handles password hashing and verification using bcrypt."""

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())


class TokenManager:
    """Handles JWT creation, decoding, and blacklist checks."""

    def __init__(
        self,
        secret: str = settings.JWT_SECRET,
        algorithm: str = settings.JWT_ALGORITHM,
        expire_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._expire_minutes = expire_minutes

    def create(self, user_id: str, username: str) -> str:
        payload = {
            "sub": user_id,
            "username": username,
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=self._expire_minutes),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode(self, token: str) -> dict:
        """Decode and verify a JWT. Raises HTTPException on failure."""
        try:
            return jwt.decode(
                token, self._secret, algorithms=[self._algorithm]
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired.")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token.")

    async def is_blacklisted(self, token: str, db: Connection) -> bool:
        revoked = await db.fetchval(
            "SELECT 1 FROM token_blacklist WHERE token = $1", token
        )
        return revoked is not None

    async def blacklist(self, token: str, payload: dict, db: Connection) -> None:
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        await db.execute(
            "INSERT INTO token_blacklist (token, expires_at) VALUES ($1, $2) "
            "ON CONFLICT (token) DO NOTHING",
            token,
            expires_at,
        )


# --- Abstract base (Abstraction) ---


class BaseAuthService(ABC):
    """Abstract interface for authentication services."""

    @abstractmethod
    async def register(
        self,
        username: str,
        email: str | None,
        password: str,
        hobbies: list[str],
        db: Connection,
    ) -> dict:
        ...

    @abstractmethod
    async def authenticate(
        self, username: str, password: str, db: Connection
    ) -> str:
        ...

    @abstractmethod
    async def get_current_user(self, token: str, db: Connection) -> dict:
        ...


# --- Concrete implementation (Inheritance + Polymorphism) ---


class AuthService(BaseAuthService):
    """Concrete auth service.

    Composition: owns a PasswordHasher and a TokenManager.
    Inheritance: extends BaseAuthService.
    Polymorphism: overrides all abstract methods.
    """

    def __init__(self) -> None:
        self._hasher = PasswordHasher()
        self._tokens = TokenManager()

    @property
    def hasher(self) -> PasswordHasher:
        return self._hasher

    @property
    def tokens(self) -> TokenManager:
        return self._tokens

    async def register(
        self,
        username: str,
        email: str | None,
        password: str,
        hobbies: list[str],
        db: Connection,
    ) -> dict:
        hashed = self._hasher.hash(password)
        try:
            async with db.transaction():
                user_id = await db.fetchval(
                    "INSERT INTO users (username, email, password_hash) "
                    "VALUES ($1, $2, $3) RETURNING id",
                    username,
                    email,
                    hashed,
                )
                if hobbies:
                    await db.executemany(
                        "INSERT INTO user_hobbies (user_id, hobby) VALUES ($1, $2)",
                        [(user_id, h) for h in hobbies],
                    )
        except UniqueViolationError:
            raise HTTPException(
                status_code=400, detail="Username or email already taken."
            )
        return {"message": "Account created successfully."}

    async def authenticate(
        self, username: str, password: str, db: Connection
    ) -> str:
        user = await db.fetchrow(
            "SELECT id, username, password_hash FROM users WHERE username = $1",
            username,
        )
        if not user or not self._hasher.verify(password, user["password_hash"]):
            raise HTTPException(
                status_code=401, detail="Invalid username or password."
            )
        return self._tokens.create(str(user["id"]), user["username"])

    async def get_current_user(self, token: str, db: Connection) -> dict:
        payload = self._tokens.decode(token)
        if await self._tokens.is_blacklisted(token, db):
            raise HTTPException(
                status_code=401, detail="Token has been revoked."
            )
        return payload

    async def logout(self, token: str, db: Connection) -> dict:
        try:
            payload = self._tokens.decode(token)
        except HTTPException:
            return {"message": "Token already expired."}
        await self._tokens.blacklist(token, payload, db)
        return {"message": "Logged out successfully."}
