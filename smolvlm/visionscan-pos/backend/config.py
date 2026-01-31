import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/visionscan_pos",
    )

    # API
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    API_TITLE: str = "VisionScan POS API"
    API_VERSION: str = "1.0.0"

    # CORS
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")

    # Fuzzy matching threshold (0-1)
    FUZZY_MATCH_THRESHOLD: float = 0.6

    # Ollama Configuration
    OLLAMA_ENDPOINT: str = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llava-phi3")
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "30"))

    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL."""
        return cls.DATABASE_URL


config = Config()
