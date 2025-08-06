import httpx
import json
from typing import AsyncGenerator, List, Dict, Optional
from ..config import settings
import tiktoken
import logging

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.encoder = tiktoken.encoding_for_model("gpt-4")
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))
    
    def trim_messages_to_token_limit(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 5000
    ) -> List[Dict[str, str]]:
        total_tokens = 0
        trimmed_messages = []
        
        for msg in reversed(messages):
            msg_tokens = self.count_tokens(msg["content"])
            if total_tokens + msg_tokens > max_tokens:
                break
            total_tokens += msg_tokens
            trimmed_messages.insert(0, msg)
        
        return trimmed_messages
    
    async def stream_chat_completion(
        self, 
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None
    ) -> AsyncGenerator[str, None]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.openai_api_key}"
        }
        
        trimmed_messages = self.trim_messages_to_token_limit(
            messages, 
            settings.max_context_tokens
        )
        
        payload = {
            "model": settings.model,
            "messages": trimmed_messages,
            "stream": True,
            "temperature": temperature or settings.chat_temperature,
            "top_p": top_p or settings.chat_top_p
        }
        
        try:
            async with self.client.stream(
                "POST",
                settings.litellm_url,
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse SSE chunk: {data}")
                            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during streaming: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during streaming: {e}")
            raise
    
    async def get_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None
    ) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.openai_api_key}"
        }
        
        payload = {
            "model": settings.model,
            "messages": messages,
            "temperature": temperature or settings.chat_temperature,
            "top_p": top_p or settings.chat_top_p
        }
        
        try:
            response = await self.client.post(
                settings.litellm_url.replace("/chat/completions", "") + "/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during completion: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during completion: {e}")
            raise