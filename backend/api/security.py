"""Security — bcrypt + JWT HS256 with UTC, jti, exp, iss."""
import datetime
import hashlib
import uuid
import bcrypt
from jose import jwt, JWTError
from .config import settings
import logging

logger = logging.getLogger("smcpe.security")

SECRET = settings.JWT_SECRET
ALGO = settings.JWT_ALGO

def hash_password(pw: str) -> str:
    if len(pw) > 72:
        logger.warning("Password truncated to 72 bytes for bcrypt")
    pw_bytes = pw.encode()[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode()

def verify_password(pw: str, h: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode()[:72], h.encode())
    except Exception as e:
        logger.debug("verify_password failed: %s", e)
        return False

def create_token(data: dict, expires_delta: datetime.timedelta) -> str:
    to_encode = data.copy()
    now = datetime.datetime.now(datetime.timezone.utc)
    expire = now + expires_delta
    to_encode.update({
        "exp": expire,
        "iat": now,
        "iss": settings.JWT_ISSUER,
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(to_encode, SECRET, algorithm=ALGO)

def create_access_token(sub: str, tenant_id: str, role: str) -> str:
    return create_token(
        {"sub": sub, "tenant_id": tenant_id, "role": role},
        datetime.timedelta(minutes=settings.JWT_ACCESS_MIN),
    )

def create_refresh_token(sub: str) -> str:
    return create_token({"sub": sub, "type": "refresh"}, datetime.timedelta(days=settings.JWT_REFRESH_DAYS))

def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO], issuer=settings.JWT_ISSUER, options={"require_exp": True})
        return payload
    except JWTError as e:
        logger.debug("JWT decode failed: %s", e)
        return None
    except Exception as e:
        logger.warning("Unexpected JWT error: %s", e)
        return None

def hash_chain(prev_hash: str, payload: str) -> str:
    return hashlib.sha256((prev_hash + payload).encode()).hexdigest()
