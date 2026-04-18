from __future__ import annotations

import json
import os
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class AIClientConfig:
    provider: str
    gemini_api_key: str | None
    ollama_base_url: str
    ollama_model: str


class AIClient:
    def __init__(self, config: AIClientConfig):
        self._config = config

    @classmethod
    def from_env(cls) -> "AIClient":
        provider = (os.getenv("LLM_PROVIDER") or "gemini").strip().lower()
        return cls(
            AIClientConfig(
                provider=provider,
                gemini_api_key=os.getenv("GEMINI_API_KEY"),
                ollama_base_url=os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434",
                ollama_model=os.getenv("OLLAMA_MODEL") or "llama3.2:3b",
            )
        )

    async def call(self, system_prompt: str, user_prompt: str) -> str:
        if self._config.provider == "ollama":
            return await self._call_ollama(system_prompt, user_prompt)
        return await self._call_gemini(system_prompt, user_prompt)

    async def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        if not self._config.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")

        try:
            from google import genai  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("google-genai SDK is not installed") from e

        client = genai.Client(api_key=self._config.gemini_api_key)
        model = "gemini-2.0-flash"

        async def _generate(prompt: str) -> str:
            response = await client.aio.models.generate_content(
                model=model,
                contents=[
                    {"role": "system", "parts": [{"text": system_prompt}]},
                    {"role": "user", "parts": [{"text": prompt}]},
                ],
                config={
                    "temperature": 0.1,
                    "response_mime_type": "application/json",
                },
            )

            text = getattr(response, "text", None)
            if not text:
                raise RuntimeError("Gemini returned empty response")
            return text

        first = await _generate(user_prompt)
        try:
            json.loads(first)
            return first
        except json.JSONDecodeError:
            retry = await _generate(
                user_prompt
                + "\n\nRespond ONLY with valid JSON (no markdown, no commentary)."
            )
            try:
                json.loads(retry)
                return retry
            except json.JSONDecodeError as e:
                raise RuntimeError("Gemini returned invalid JSON after retry") from e

    async def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        url = self._config.ollama_base_url.rstrip("/") + "/api/chat"

        async def _post(prompt: str) -> str:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    url,
                    json={
                        "model": self._config.ollama_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        "format": "json",
                        "stream": False,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                message = data.get("message") or {}
                content = message.get("content")
                if not content:
                    raise RuntimeError("Ollama returned empty response")
                return content

        first = await _post(user_prompt)
        try:
            json.loads(first)
            return first
        except json.JSONDecodeError:
            retry = await _post(
                user_prompt
                + "\n\nRespond ONLY with valid JSON (no markdown, no commentary)."
            )
            try:
                json.loads(retry)
                return retry
            except json.JSONDecodeError as e:
                raise RuntimeError("Ollama returned invalid JSON after retry") from e

