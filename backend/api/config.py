"""Centralized settings — single source for env, validated, no defaults in prod."""
import pathlib
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(pathlib.Path(__file__).parent.parent / ".env"), env_file_encoding="utf-8", extra="ignore")

    JWT_SECRET: str = "dev-secret-change-me-32-chars-minimum"
    JWT_ALGO: str = "HS256"
    JWT_ACCESS_MIN: int = 15
    JWT_REFRESH_DAYS: int = 7
    JWT_ISSUER: str = "smcpe"
    DB_PATH: str = str(pathlib.Path(__file__).parent.parent / "db" / "smcpe.db")
    COBOL_LIB: str = str(pathlib.Path(__file__).parent.parent / "cobol" / "libpayroll.so")
    STATUTORY_VERSION: str = "v2026.09"
    CORS_ORIGIN: str = "https://pay.yourdomain.sd,http://localhost,http://127.0.0.1"
    ENV: str = "development"
    PORT: int = 8000

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGIN.split(",") if o.strip()]

    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    def validate_secret(self) -> None:
        if self.is_production() and (len(self.JWT_SECRET) < 32 or "change-me" in self.JWT_SECRET):
            raise ValueError("JWT_SECRET must be 32+ random chars in production")

settings = Settings()
# Validate on import in prod
try:
    settings.validate_secret()
except ValueError as e:
    import warnings
    warnings.warn(str(e))
