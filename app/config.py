from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    public_base_url: str = "http://localhost:8000"
    generated_audio_dir: Path = Path("generated_audio")

    piper_executable: str = "piper"
    piper_model: Path = Field(default=Path("models/voice.onnx"))
    piper_config: Optional[Path] = None
    piper_speaker: Optional[str] = None
    piper_timeout_seconds: float = 60.0

    voximplant_account_id: str
    voximplant_api_key: str
    voximplant_rule_id: str
    voximplant_api_base_url: str = "https://api.voximplant.com/platform_api"
    voximplant_custom_data_max_bytes: int = 200
    request_timeout_seconds: float = 20.0

    github_token: Optional[str] = None
    github_repo: Optional[str] = None

    @field_validator("public_base_url", "voximplant_api_base_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
