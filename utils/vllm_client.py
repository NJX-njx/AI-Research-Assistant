# -*- coding: utf-8 -*-
"""
VLM (Vision Language Model) client for multimodal image understanding.
Includes retry mechanism, rate limiting handling, and fallback strategies.
"""
import os
import time
import base64
import json
import re
from typing import Dict, List, Optional
from pathlib import Path
from openai import OpenAI

# VLM specific configuration
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "https://api-kdh1oah609r7q4z6.aistudio-app.com/v1")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", os.getenv("AISTUDIO_API_KEY"))
VLLM_MODEL = os.getenv("VLLM_MODEL", "default")

# Rate limiting settings
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 2.0  # seconds
DEFAULT_RATE_LIMIT_DELAY = 5.0  # seconds between calls to avoid 429


class VLMClient:
    """Client for Vision Language Model - handles image understanding tasks.
    
    Features:
    - Automatic retry with exponential backoff
    - Rate limit (429) handling
    - Fallback to text-only analysis when VLM unavailable
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        base_url: Optional[str] = None, 
        model: Optional[str] = None,
        max_retries: int = DEFAULT_RETRY_COUNT,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        self.api_key = api_key or VLLM_API_KEY
        self.base_url = base_url or VLLM_BASE_URL
        self.model = model or VLLM_MODEL
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._last_call_time = 0
        self._min_interval = DEFAULT_RATE_LIMIT_DELAY
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self._available = None  # Cache availability status
    
    def _rate_limit_wait(self):
        """Wait if needed to respect rate limits."""
        elapsed = time.time() - self._last_call_time
        if elapsed < self._min_interval:
            wait_time = self._min_interval - elapsed
            print(f"[VLM] Rate limit: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        self._last_call_time = time.time()
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image file to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _get_mime_type(self, image_path: str) -> str:
        """Get MIME type from file extension."""
        ext = Path(image_path).suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        return mime_map.get(ext, "image/png")
    
    def is_available(self, force_check: bool = False) -> bool:
        """Check if VLM service is available.
        
        Args:
            force_check: If True, always test the connection
            
        Returns:
            True if VLM is available
        """
        if self._available is not None and not force_check:
            return self._available
        
        try:
            # Simple test request
            self.client.models.list()
            self._available = True
        except Exception as e:
            print(f"[VLM] Service check failed: {e}")
            self._available = False
        
        return self._available
    
    def _call_with_retry(self, messages: List[Dict], temperature: float = 0.2, max_tokens: int = 2000) -> str:
        """Call VLM API with retry logic.
        
        Handles:
        - 429 (Rate Limit): Wait and retry with longer delay
        - 5xx (Server Error): Retry with exponential backoff
        - Connection errors: Retry a few times then give up
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self._rate_limit_wait()
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                
                if response.choices and len(response.choices) > 0:
                    return response.choices[0].message.content or ""
                return ""
                
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # Handle rate limit (429)
                if "429" in error_str:
                    wait_time = self.retry_delay * (2 ** attempt) + 5  # Extra wait for 429
                    print(f"[VLM] Rate limited (429), waiting {wait_time:.1f}s... (attempt {attempt + 1}/{self.max_retries})")
                    self._min_interval = min(self._min_interval * 1.5, 30)  # Increase future delays
                    time.sleep(wait_time)
                    continue
                
                # Handle server errors (5xx)
                elif "500" in error_str or "502" in error_str or "503" in error_str:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"[VLM] Server error, retrying in {wait_time:.1f}s... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue
                
                # Handle 403 (Forbidden) - likely service issue
                elif "403" in error_str:
                    print(f"[VLM] Access forbidden (403). Service may be unavailable.")
                    self._available = False
                    break
                
                # Other errors - don't retry
                else:
                    print(f"[VLM] Error: {e}")
                    break
        
        return f"[VLM Error after {self.max_retries} attempts: {last_error}]"
    
    def describe_image(self, image_path: str, prompt: Optional[str] = None, temperature: float = 0.2) -> str:
        """
        Describe an image using VLM with retry and rate limit handling.
        
        Args:
            image_path: Path to the image file
            prompt: Custom prompt for description (optional)
            temperature: Sampling temperature
            
        Returns:
            Text description of the image
        """
        if not os.path.exists(image_path):
            return f"[Error: Image not found at {image_path}]"
        
        base64_image = self._encode_image(image_path)
        mime_type = self._get_mime_type(image_path)
        
        default_prompt = (
            "请详细描述这张科研论文中的图片。"
            "包括：1) 图中的主要元素和对象；2) 数据趋势或关系；3) 图片想要表达的核心观点。"
            "用中文回答。"
        )
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt or default_prompt
                    }
                ]
            }
        ]
        
        return self._call_with_retry(messages, temperature)
    
    def analyze_figure(self, image_path: str, caption: Optional[str] = None, 
                       context_sentences: Optional[List[str]] = None,
                       use_fallback: bool = True) -> Dict:
        """
        Analyze a scientific figure with context.
        
        Args:
            image_path: Path to figure image
            caption: Figure caption text
            context_sentences: Sentences from paper that reference this figure
            use_fallback: If True, use text-only LLM when VLM fails
            
        Returns:
            Dict with entities, relations, and summary
        """
        prompt_parts = [
            "你是科研图像分析专家。请分析这张科研论文中的图片，并返回严格的JSON格式：",
            '{"entities": [{"type": "概念类型", "name": "名称"}], "relations": [{"source": "实体1", "target": "实体2", "type": "关系类型"}], "summary": "一句话总结"}',
            "",
            "实体类型可以是：Method, Dataset, Metric, Result, Component, Process",
            "关系类型可以是：trend, causal, correlates, part_of, outperform, compared_with",
        ]
        
        if caption:
            prompt_parts.append(f"\n图注：{caption}")
        
        if context_sentences:
            prompt_parts.append(f"\n论文中引用该图的句子：{' '.join(context_sentences[:3])}")
        
        prompt_parts.append("\n请返回JSON：")
        prompt = "\n".join(prompt_parts)
        
        result_text = self.describe_image(image_path, prompt, temperature=0.0)
        
        # Check if VLM call failed
        if result_text.startswith("[VLM Error") or result_text.startswith("[Error"):
            if use_fallback and (caption or context_sentences):
                print("[VLM] Falling back to text-only analysis...")
                return self._fallback_text_analysis(caption, context_sentences)
            return {
                "error": result_text,
                "entities": [],
                "relations": [],
                "summary": ""
            }
        
        # Try to parse JSON
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', result_text)
            if json_match:
                result_text = json_match.group(1).strip()
            
            start = result_text.find("{")
            end = result_text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result_text[start:end])
        except json.JSONDecodeError:
            pass
        
        return {
            "raw": result_text, 
            "entities": [], 
            "relations": [], 
            "summary": result_text[:200] if result_text else ""
        }
    
    def _fallback_text_analysis(self, caption: Optional[str], context_sentences: Optional[List[str]]) -> Dict:
        """Fallback: analyze figure using only caption and context (no image).
        
        Uses the regular LLM client when VLM is unavailable.
        """
        try:
            # Handle both package import and direct script execution
            try:
                from utils.llm_client import LLMClient
            except ImportError:
                from llm_client import LLMClient
            
            llm = LLMClient()
            
            prompt = (
                "你是科研文献分析专家。根据以下图注和引用信息，推断该图可能包含的实体和关系。\n"
                "返回JSON格式：\n"
                '{"entities": [{"type": "类型", "name": "名称"}], "relations": [{"source": "...", "target": "...", "type": "关系"}], "summary": "一句话总结"}\n\n'
            )
            
            if caption:
                prompt += f"图注：{caption}\n"
            if context_sentences:
                prompt += f"论文引用：{' '.join(context_sentences[:3])}\n"
            
            prompt += "\n请推断并返回JSON："
            
            result = llm.chat_json([{"role": "user", "content": prompt}])
            result["_fallback"] = True  # Mark as fallback result
            return result
            
        except Exception as e:
            return {
                "error": f"Fallback failed: {e}",
                "entities": [],
                "relations": [],
                "summary": "",
                "_fallback": True
            }


def analyze_figure_safe(
    image_path: Optional[str],
    caption: Optional[str] = None,
    context_sentences: Optional[List[str]] = None
) -> Dict:
    """
    Safe wrapper for figure analysis that handles all edge cases.
    
    - If image exists: try VLM, fallback to text if needed
    - If no image: use text-only analysis
    - Always returns a valid dict
    """
    vlm = VLMClient()
    
    if image_path and os.path.exists(image_path):
        return vlm.analyze_figure(image_path, caption, context_sentences, use_fallback=True)
    elif caption or context_sentences:
        # No image but have text context - use fallback directly
        print(f"[VLM] No image available, using text-only analysis")
        return vlm._fallback_text_analysis(caption, context_sentences)
    else:
        return {
            "error": "No image or context provided",
            "entities": [],
            "relations": [],
            "summary": ""
        }


# Test function
if __name__ == "__main__":
    print("Testing VLM Client...")
    vlm = VLMClient()
    print(f"VLM available: {vlm.is_available(force_check=True)}")
    
    # Test fallback
    result = analyze_figure_safe(
        image_path=None,
        caption="Figure 1: Over-refusal rate vs toxic prompts rejection rate",
        context_sentences=["Results show that GPT-4 achieves the best balance."]
    )
    print(f"Fallback result: {result}")
