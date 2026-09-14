"""DB + auth dependencies — single correct pattern, no leaks."""
from typing import AsyncGenerator, Annotated
from fastapi import Depends, Header, HTTPException
import aiosqlite
from .config import settings
from .security import decode_token

async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    db = await aiosqlite.connect(settings.DB_PATH)
    try:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA foreign_keys=ON;")
        yield db
    finally:
        await db.close()

DBDep = Annotated[aiosqlite.Connection, Depends(get_db)]

def _extract_token(authorization: str | None = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    return authorization[7:]

async def require_user(authorization: str | None = Header(None)) -> dict:
    token = _extract_token(authorization)
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

UserDep = Annotated[dict, Depends(require_user)]

def require_role(*roles: str):
    async def checker(user: UserDep) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail=f"Requires role {roles}")
        return user
    return checker
