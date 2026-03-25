import os
from functools import lru_cache


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
    )
    ALLOWED_ORIGIN: str = os.getenv("ALLOWED_ORIGIN", "http://localhost:5173")
    ADMIN_DEFAULT_USERNAME: str = os.getenv("ADMIN_DEFAULT_USERNAME", "admin")
    ADMIN_DEFAULT_PASSWORD: str = os.getenv("ADMIN_DEFAULT_PASSWORD", "")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    def validate(self):
        errors = []
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is not set")
        if not self.JWT_SECRET:
            errors.append("JWT_SECRET is not set")
        if self.ENVIRONMENT == "production" and self.ALLOWED_ORIGIN == "*":
            errors.append("ALLOWED_ORIGIN cannot be wildcard in production")
        if self.ENVIRONMENT == "production" and len(self.JWT_SECRET) < 32:
            errors.append("JWT_SECRET must be at least 32 characters in production")
        if errors:
            raise RuntimeError(
                "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            )


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.validate()
    return s
