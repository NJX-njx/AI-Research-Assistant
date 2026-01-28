# -*- coding: utf-8 -*-
"""
Unified LLM client wrapper using OpenAI Python SDK with custom base_url.
Supports:
- chat completion (non-stream and stream)
- JSON output for structured extraction
Reads API settings from environment when available.
"""
import os
from typing import Iterable, List, Dict, Optional
from openai import OpenAI

DEFAULT_BASE_URL = os.getenv("AISTUDIO_BASE_URL", "https://aistudio.baidu.com/llm/lmapi/v3")
DEFAULT_API_KEY = os.getenv("AISTUDIO_API_KEY")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "deepseek-v3")

class LLMClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or DEFAULT_API_KEY
        self.base_url = base_url or DEFAULT_BASE_URL
        self.model = model or DEFAULT_MODEL
        if not self.api_key:
            # Allow client to work if user hardcodes in model_api.py; here we warn but do not block
            print("[LLMClient] Warning: API key not found in env; fallback to client default.")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(self, messages: List[Dict], model: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 4096, web_search: bool = False) -> str:
        resp = self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            stream=False,
            extra_body={"web_search": {"enable": web_search}},
            max_completion_tokens=max_tokens,
            temperature=temperature,
        )
        # new OpenAI SDK returns object with choices[0].message
        if resp.choices and len(resp.choices) > 0:
            return (resp.choices[0].message.content or "").strip()
        return ""

    def chat_stream(self, messages: List[Dict], model: Optional[str] = None, temperature: float = 0.2, max_tokens: int = 4096, web_search: bool = False) -> Iterable[str]:
        stream = self.client.chat.completions.create(
            model=model or self.model,
            messages=messages,
            stream=True,
            extra_body={"web_search": {"enable": web_search}},
            max_completion_tokens=max_tokens,
            temperature=temperature,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            # reasoning_content if available; else content
            content = getattr(delta, "reasoning_content", None) or getattr(delta, "content", None)
            if content:
                yield content

    def chat_json(self, messages: List[Dict], model: Optional[str] = None, schema_hint: Optional[str] = None, temperature: float = 0.0, max_tokens: int = 4096) -> Dict:
        """Ask model to return JSON; use schema_hint to guide structure."""
        sys = "You are a precise extractor. Always return strict JSON with keys specified. No prose."
        if schema_hint:
            sys += f"\nSchema: {schema_hint}"
        msgs = [{"role": "system", "content": sys}] + messages
        text = self.chat(msgs, model=model, temperature=temperature, max_tokens=max_tokens)
        # best-effort JSON parse with markdown code block handling
        import json
        import re
        try:
            # Try direct parse first
            return json.loads(text)
        except Exception:
            # Try extracting from markdown code block
            try:
                # Match ```json ... ``` or ``` ... ```
                match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
                if match:
                    return json.loads(match.group(1).strip())
            except Exception:
                pass
            return {"raw": text}
