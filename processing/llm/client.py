"""
M9 LLM Client

Generic interface for LLM providers (Ollama, OpenAI, etc.)
"""

import logging
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .config import LLMConfig

logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """Base exception for LLM client errors"""
    pass


class ProviderUnavailableError(LLMClientError):
    """LLM provider not reachable"""
    pass


class ModelNotFoundError(LLMClientError):
    """Requested model not available"""
    pass


class GenerationTimeoutError(LLMClientError):
    """Generation exceeded timeout"""
    pass


class LLMClient(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate completion from LLM
        
        Args:
            prompt: User prompt
            system: System prompt (optional)
        
        Returns:
            {
                "response": str,  # Generated text
                "model": str,  # Model identifier
                "finish_reason": str,  # "stop", "length", etc.
                "usage": {  # Token usage (optional)
                    "prompt_tokens": int,
                    "completion_tokens": int,
                    "total_tokens": int
                }
            }
        
        Raises:
            ProviderUnavailableError: Provider not reachable
            ModelNotFoundError: Model not available
            GenerationTimeoutError: Generation timeout
            LLMClientError: Other errors
        """
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """
        Check if provider is available
        
        Returns:
            True if provider is healthy, False otherwise
        """
        pass


class OllamaClient(LLMClient):
    """Ollama provider implementation"""
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate completion from Ollama"""
        
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                request_data = {
                    "model": self.config.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens,
                    }
                }
                
                if system:
                    request_data["system"] = system
                
                response = await client.post(
                    f"{self.config.base_url}/api/generate",
                    json=request_data
                )
                
                if response.status_code == 404:
                    raise ModelNotFoundError(
                        f"Model {self.config.model_name} not found. "
                        f"Run: ollama pull {self.config.model_name}"
                    )
                
                response.raise_for_status()
                data = response.json()
                
                # Normalize Ollama response to standard format
                return {
                    "response": data.get("response", ""),
                    "model": data.get("model", self.config.model_name),
                    "finish_reason": "stop" if data.get("done") else "length",
                    "usage": {
                        "prompt_tokens": 0,  # Ollama doesn't provide token counts
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                }
                
        except httpx.TimeoutException as e:
            raise GenerationTimeoutError(
                f"Generation exceeded {self.config.timeout_seconds}s timeout"
            ) from e
        except httpx.ConnectError as e:
            raise ProviderUnavailableError(
                f"Cannot connect to Ollama at {self.config.base_url}. "
                f"Is Ollama running?"
            ) from e
        except httpx.HTTPError as e:
            raise LLMClientError(f"HTTP error: {e}") from e
    
    async def check_health(self) -> bool:
        """Check if Ollama is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.config.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")
            return False


# Factory function for creating clients
def create_llm_client(config: LLMConfig) -> LLMClient:
    """
    Create LLM client based on provider
    
    Args:
        config: LLM configuration
    
    Returns:
        LLMClient instance
    
    Raises:
        ValueError: Unknown provider
    """
    if config.provider.lower() == "ollama":
        return OllamaClient(config)
    else:
        raise ValueError(
            f"Unknown provider: {config.provider}. "
            f"Supported: ollama"
        )
