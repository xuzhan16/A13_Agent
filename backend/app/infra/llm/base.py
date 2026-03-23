from abc import ABC, abstractmethod
from typing import Optional

import httpx


class LLMClient(ABC):
    @property
    @abstractmethod
    def enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = '') -> str:
        raise NotImplementedError


class MockLLMClient(LLMClient):
    @property
    def enabled(self) -> bool:
        return False

    def generate(self, prompt: str, system_prompt: str = '') -> str:
        del system_prompt
        return f'[mock-llm-disabled] {prompt[:120]}'


class OpenAICompatibleLLMClient(LLMClient):
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)

    def generate(self, prompt: str, system_prompt: str = '') -> str:
        if not self.enabled:
            raise RuntimeError('LLM client is not configured.')

        messages = []
        if system_prompt.strip():
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        response = httpx.post(
            f'{self.base_url}/chat/completions',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': self.model,
                'messages': messages,
                'temperature': 0.2,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get('choices') or []
        if not choices:
            return ''
        message = choices[0].get('message') or {}
        content = message.get('content', '')
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    parts.append(item.get('text', ''))
            return ''.join(parts)
        return str(content)


def build_llm_client(
    enable_llm: bool,
    base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: float,
) -> LLMClient:
    if enable_llm and base_url and api_key and model:
        return OpenAICompatibleLLMClient(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
        )
    return MockLLMClient()
