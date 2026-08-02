import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application Settings validated at runtime using Pydantic v2.
    Reads from environment variables or .env file automatically.
    """
    GROQ_API_KEY: str = Field(
        ...,
        description="Free Groq API Key from https://console.groq.com"
    )
    GROQ_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model string (e.g. llama-3.3-70b-versatile or llama-3.1-8b-instant)"
    )

    DATABASE_URL: str = Field(
        default="postgresql://postgres:admin@123@localhost:5432/devops_agent",
        description="PostgreSQL connection string with pgvector support"
    )

    GITHUB_TOKEN: str = Field(
        default="",
        description="GitHub Personal Access Token for PR Diff inspection and commenting"
    )

    LANGFUSE_PUBLIC_KEY: str = Field(default="", description="Langfuse Public Key")
    LANGFUSE_SECRET_KEY: str = Field(default="", description="Langfuse Secret Key")
    LANGFUSE_HOST: str = Field(default="https://cloud.langfuse.com", description="Langfuse Host URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore", 
    )


settings = Settings()