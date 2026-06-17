from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and/or .env file
    using Pydantic Settings v2.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENV: Literal["development", "production", "testing"] = "development"

    # OpenAI / OpenAI-Compatible LLM Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.groq.com/openai/v1"
    OPENAI_MODEL_NAME: str = "gpt-4o-mini"
    TEMPERATURE: float = 0.7
