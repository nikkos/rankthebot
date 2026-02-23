from __future__ import annotations

from typing import Optional

import httpx


class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-5.2"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"

    def complete(self, prompt: str, temperature: Optional[float] = 0.3, model: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        m = model or self.model
        body: dict = {
            "model": m,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a product discovery assistant. Be concise and list concrete options.",
                },
                {"role": "user", "content": prompt},
            ],
        }
        if temperature is not None:
            body["temperature"] = temperature
        if max_tokens is not None:
            body["max_completion_tokens"] = max_tokens
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{self.base_url}/chat/completions", json=body, headers=headers)
            resp.raise_for_status()
            payload = resp.json()
        return payload["choices"][0]["message"]["content"]
