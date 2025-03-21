import os

class Config:
    # Toggle SSL for PostgreSQL
    USE_SSL = os.getenv("USE_SSL", "False").lower() in ("true", "1")

    # Flask-Limiter: Redis backend for rate limiting
    RATE_LIMIT_STORAGE_URL = os.getenv("RATE_LIMIT_STORAGE_URL", "redis://localhost:6379/0")

    # Enable or disable logging
    LOGGING_ENABLED = os.getenv("LOGGING_ENABLED", "True").lower() in ("true", "1")
