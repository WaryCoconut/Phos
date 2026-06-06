from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API IA compatible OpenAI — socle.ai par défaut
    api_base_url: str = "https://app.socle.ai/api/v1"
    api_key: str = "sk-change-me"
    model: str = "qwen3-235b-a22b-instruct-2507"

    # Serveur
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # Stockage des sessions
    sessions_dir: str = "./app/data/sessions"

    model_config = {"env_file": ".env", "env_prefix": "PAX_"}


settings = Settings()
