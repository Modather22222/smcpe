"""Auth — login + JWT, bcrypt, tenant-aware."""
import logging
from fastapi import APIRouter, HTTPException
from ..deps import DBDep
from ..schemas import LoginIn
from ..security import verify_password, create_access_token

logger = logging.getLogger("smcpe.auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login")
async def login(body: LoginIn, db: DBDep) -> dict:
    cur = await db.execute("SELECT id, tenant_id, role, password_hash FROM users WHERE email=?", (body.email,))
    row = await cur.fetchone()
    if not row or not verify_password(body.password, row["password_hash"]):
        logger.warning("Failed login for %s", body.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(row["id"], row["tenant_id"], row["role"])
    logger.info("Login %s tenant %s role %s", row["id"], row["tenant_id"], row["role"])
    return {"access_token": token, "token_type": "bearer", "role": row["role"], "tenant_id": row["tenant_id"]}
