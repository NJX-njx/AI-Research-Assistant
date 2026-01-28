# -*- coding: utf-8 -*-
"""
Simple runner showing how to call the LLM via our unified client.
Keeps compatibility with your previous API usage while moving logic into utils/llm_client.py.
"""
import os
from utils.llm_client import LLMClient

# Allow explicit override; otherwise env is used.
API_KEY = os.getenv("AISTUDIO_API_KEY")
BASE_URL = os.getenv("AISTUDIO_BASE_URL", "https://aistudio.baidu.com/llm/lmapi/v3")
MODEL = os.getenv("LLM_MODEL", "deepseek-v3")

client = LLMClient(api_key=API_KEY, base_url=BASE_URL, model=MODEL)

messages = [
    {"role": "system", "content": "你是科研论文助理，回答要简洁、准确。"},
    {"role": "user", "content": "你好，请问你是谁？"},
]

print("[stream] ", end="")
for chunk in client.chat_stream(messages, temperature=0.6, max_tokens=8000, web_search=True):
    print(chunk, end="", flush=True)

print("\n[done]")