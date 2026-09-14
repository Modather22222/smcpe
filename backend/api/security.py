import os, datetime, hashlib
from jose import jwt
import bcrypt

SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me-32-chars-minimum")
ALGO = "HS256"
ACCESS_MIN = 15
REFRESH_DAYS = 7

def hash_password(pw: str) -> str:
    # bcrypt 72-byte limit: truncate if needed (passlib behavior)
    pw_bytes = pw.encode()[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode()

def verify_password(pw: str, h: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode()[:72], h.encode())
    except Exception:
        return False

def create_token(data: dict, expires_delta: datetime.timedelta):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET, algorithm=ALGO)

def create_access_token(sub: str, tenant_id: str, role: str):
    return create_token({"sub": sub, "tenant_id": tenant_id, "role": role}, datetime.timedelta(minutes=ACCESS_MIN))

def create_refresh_token(sub: str):
    return create_token({"sub": sub, "type": "refresh"}, datetime.timedelta(days=REFRESH_DAYS))

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGO])
    except Exception:
        return None

def hash_chain(prev_hash: str, payload: str) -> str:
    return hashlib.sha256((prev_hash + payload).encode()).hexdigest()
