from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

APP_DIR = Path.home() / ".rankthebot"
CONFIG_PATH = APP_DIR / "config.json"
DB_PATH = APP_DIR / "rankthebot.db"


@dataclass
class Config:
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    @classmethod
    def load(cls) -> "Config":
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if openai_key or anthropic_key:
            return cls(openai_api_key=openai_key, anthropic_api_key=anthropic_key)
        if not CONFIG_PATH.exists():
            return cls()
        data = json.loads(CONFIG_PATH.read_text())
        return cls(
            openai_api_key=data.get("openai_api_key"),
            anthropic_api_key=data.get("anthropic_api_key"),
        )

    def save(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "openai_api_key": self.openai_api_key,
            "anthropic_api_key": self.anthropic_api_key,
        }
        CONFIG_PATH.write_text(json.dumps(payload, indent=2))
