from __future__ import annotations

from typing import Optional

import httpx


class AnthropicClient:
    def __init__(self, api_key: str, model: str = "claude-opus-4-6"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"

    def complete(self, prompt: str, temperature: float = 0.3, model: Optional[str] = None) -> str:
        m = model or self.model
        body = {
            "model": m,
            "max_tokens": 1024,
            "system": "You are a product discovery assistant. Be concise and list concrete options.",
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f"{self.base_url}/messages", json=body, headers=headers)
            resp.raise_for_status()
            payload = resp.json()
        return payload["content"][0]["text"]
