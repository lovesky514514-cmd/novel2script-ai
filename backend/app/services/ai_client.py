from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings


class AIClient:
    def __init__(self):
        self.provider = settings.ai_provider
        self.chat_model = settings.ai_chat_model or settings.ai_model
        self.pro_model = settings.ai_pro_model or settings.ai_model
        self.model = self.chat_model
        self.api_key = settings.ai_api_key
        self.base_url = settings.ai_base_url.rstrip("/")
        self.timeout = settings.ai_timeout

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        if self.provider == "mock" or not self.api_key:
            return {
                "mode": "mock",
                "model": model or self.chat_model,
                "choices": [
                    {
                        "message": {
                            "content": "{}"
                        }
                    }
                ],
                "content": {
                    "summary": "AI mock mode enabled.",
                    "suggestions": [],
                },
            }

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model or self.chat_model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def chat_model_json(self, messages: List[Dict[str, str]], temperature: float = 0.25) -> Dict[str, Any]:
        return await self.chat_json(messages, model=self.chat_model, temperature=temperature)

    async def pro_model_json(self, messages: List[Dict[str, str]], temperature: float = 0.1) -> Dict[str, Any]:
        return await self.chat_json(messages, model=self.pro_model, temperature=temperature)


def response_content(response: Dict[str, Any]) -> str:
    try:
        return response["choices"][0]["message"]["content"] or ""
    except Exception:
        content = response.get("content", {})
        if isinstance(content, dict):
            return "{}"
        return str(content or "")
