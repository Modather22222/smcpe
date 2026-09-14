from fastapi import APIRouter, Depends, HTTPException, Header
from ..schemas import LoginIn
from ..security import verify_password, create_access_token, decode_token
import aiosqlite, os, pathlib

router = APIRouter(prefix="/api/auth", tags=["auth"])
DB_PATH = os.getenv("DB_PATH", str(pathlib.Path(__file__).parent.parent.parent / "db" / "smcpe.db"))

async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys=ON;")
    return db

@router.post("/login")
async def login(body: LoginIn):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys=ON;")
        cur = await db.execute("SELECT id, tenant_id, role, password_hash FROM users WHERE email=?", (body.email,))
        row = await cur.fetchone()
        if not row or not verify_password(body.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token(row["id"], row["tenant_id"], row["role"])
        return {"access_token": token, "token_type": "bearer", "role": row["role"], "tenant_id": row["tenant_id"]}

def _extract_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    return authorization[7:]

async def require_user(authorization: str = Header(None)):
    token = _extract_token(authorization)
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload
