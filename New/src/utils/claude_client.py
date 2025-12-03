"""
Claude API client wrapper
"""

from anthropic import Anthropic
import os
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Claude configuration
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")


class ClaudeClient:
    """Claude API client wrapper"""
    
    def __init__(self, api_key: Optional[str] = CLAUDE_API_KEY):
        if not api_key:
            logger.warning("CLAUDE_API_KEY not set - Claude functionality will be unavailable")
            self.client = None
        else:
            self.client = Anthropic(api_key=api_key)
    
    async def generate(self, prompt: str, system: Optional[str] = None,
                      model: str = "claude-4.5-sonnet-20250514",
                      max_tokens: int = 4096,
                      temperature: float = 0.1) -> Dict[str, Any]:
        """Generate text using Claude"""
        if not self.client:
            raise ValueError("Claude API key not configured")
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            if system:
                kwargs["system"] = system
            
            response = self.client.messages.create(**kwargs)
            
            return {
                "response": response.content[0].text,
                "tokens": response.usage.output_tokens,
                "input_tokens": response.usage.input_tokens,
                "model": response.model
            }
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Claude is available"""
        return self.client is not None


# Singleton instance
claude_client = ClaudeClient()
