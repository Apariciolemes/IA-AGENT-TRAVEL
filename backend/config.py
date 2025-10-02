from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "travel_agent"
    POSTGRES_USER: str = "travel_user"
    POSTGRES_PASSWORD: str = "travel_password_123"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None

    # LLM
    LLM_PROVIDER: Literal["openai", "anthropic", "azure"] = "openai"
    LLM_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""

    # Pricing Engine
    R_PER_MILE: float = 0.03
    MAX_STOPS: int = 1
    PRICE_WEIGHT: float = 0.4
    DURATION_WEIGHT: float = 0.3
    STOPS_WEIGHT: float = 0.2
    ANCILLARY_WEIGHT: float = 0.1

    # Cache
    CACHE_TTL_MINUTES: int = 30
    LIVE_SEARCH_THRESHOLD_MINUTES: int = 30

    # Providers
    DUFFEL_API_KEY: str = ""
    AMADEUS_API_KEY: str = ""
    AMADEUS_API_SECRET: str = ""
    KIWI_API_KEY: str = ""

    # Scraping
    ROTATING_PROXY_URL: str = ""
    CAPTCHA_SOLVER_KEY: str = ""
    SCRAPING_ENABLED: bool = True
    SCRAPING_RATE_LIMIT_PER_MINUTE: int = 5

    # Email
    POSTMARK_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@travel-agent.com"

    # Application
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 3000
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "info"

    # JWT
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
