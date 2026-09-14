"""Deprecated — use backend.api.deps.get_db instead."""
import warnings
warnings.warn("backend.db.conn.get_db is deprecated, use backend.api.deps.get_db", DeprecationWarning)

from backend.api.deps import get_db  # re-export
from backend.api.config import settings

DB_PATH = settings.DB_PATH
