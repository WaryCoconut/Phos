from dataclasses import dataclass
from typing import Annotated, Optional
from fastapi import Header
from app.config import settings


@dataclass
class AiConfig:
    api_key: str
    base_url: str
    model: str
    provider: str = "socle"  # "socle" | "ollama"
    language: str = "English"


async def get_ai_config(
    x_api_key: Annotated[Optional[str], Header()] = None,
    x_api_base_url: Annotated[Optional[str], Header()] = None,
    x_api_model: Annotated[Optional[str], Header()] = None,
    x_api_provider: Annotated[Optional[str], Header()] = None,
    x_api_language: Annotated[Optional[str], Header()] = None,
) -> AiConfig:
    return AiConfig(
        api_key=x_api_key or settings.api_key,
        base_url=x_api_base_url or settings.api_base_url,
        model=x_api_model or settings.model,
        provider=x_api_provider or "socle",
        language=x_api_language or "English",
    )
