from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from asyncpg import Connection

from app.database import get_db
from app.models.auth_service import AuthService

security = HTTPBearer()
auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Connection = Depends(get_db),
):
    return await auth_service.get_current_user(credentials.credentials, db)
