from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Academic Insights"

    # OpenAI config
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"  # or "gpt-4o" if you prefer

    # 🔐 AUTH / JWT CONFIG (NEW)
    JWT_SECRET_KEY: str = "change-this-secret"  # move to .env
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    class Config:
        env_file = "../.env"


settings = Settings()
