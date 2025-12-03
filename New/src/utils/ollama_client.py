"""
Shared Ollama client with retry logic and error handling
"""

import httpx
import os
import logging
from typing import Dict, Any, Optional
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))
RETRY_ATTEMPTS = int(os.getenv("OLLAMA_RETRY_ATTEMPTS", "3"))
RETRY_DELAY = int(os.getenv("OLLAMA_RETRY_DELAY", "2"))


class OllamaClient:
    """Shared Ollama client with retry logic"""
    
    def __init__(self, base_url: str = OLLAMA_HOST):
        self.base_url = base_url
        self.timeout = TIMEOUT
        self.retry_attempts = RETRY_ATTEMPTS
        self.retry_delay = RETRY_DELAY
    
    async def generate(self, model: str, prompt: str, system: Optional[str] = None,
                      options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate text with retry logic"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": options or {}
        }
        
        if system:
            payload["system"] = system
        
        for attempt in range(self.retry_attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException:
                logger.error(f"Ollama timeout (attempt {attempt + 1}/{self.retry_attempts})")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise
            except httpx.HTTPError as e:
                logger.error(f"Ollama HTTP error (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise
            except Exception as e:
                logger.error(f"Ollama error (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise
    
    async def embeddings(self, model: str, prompt: str) -> Dict[str, Any]:
        """Generate embeddings with retry logic"""
        url = f"{self.base_url}/api/embeddings"
        
        payload = {
            "model": model,
            "prompt": prompt
        }
        
        for attempt in range(self.retry_attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    return response.json()
            except Exception as e:
                logger.error(f"Ollama embeddings error (attempt {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models"""
        url = f"{self.base_url}/api/tags"
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    
    async def health_check(self) -> bool:
        """Check if Ollama is accessible"""
        try:
            await self.list_models()
            return True
        except:
            return False


# Singleton instance
ollama_client = OllamaClient()
