# pip install openai
import os
from openai import OpenAI

# Read API key from environment; do not hardcode secrets in source.
client = OpenAI(
    api_key=os.getenv("VLLM_API_KEY") or os.getenv("AISTUDIO_API_KEY"),
    base_url="https://api-kdh1oah609r7q4z6.aistudio-app.com/v1"
)

completion = client.chat.completions.create(
    model="default",
    temperature=0.6,
    messages=[
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ],
    stream=True
)

for chunk in completion:
    if hasattr(chunk.choices[0].delta, "reasoning_content") and chunk.choices[0].delta.reasoning_content:
        print(chunk.choices[0].delta.reasoning_content, end="", flush=True)
    else:
        print(chunk.choices[0].delta.content, end="", flush=True)