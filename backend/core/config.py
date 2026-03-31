from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Academic Insights"

    # OpenAI config
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"  # or "gpt-4o" if you prefer

    # 🔐 AUTH / JWT CONFIG
    JWT_SECRET_KEY: str = "change-this-secret"  # Default for development
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # 🗄️ DATABASE
    DATABASE_URL: str = "sqlite:///./academics_insights.db"

    # 🌐 CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
