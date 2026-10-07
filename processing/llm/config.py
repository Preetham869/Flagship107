"""
M9 Configuration

Configuration for local LLM explanation generation.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """Configuration for M9 LLM explanations"""
    
    # Generic model provider settings
    provider: str = "ollama"  # "ollama", "openai", "anthropic", etc.
    base_url: str = "http://localhost:11434"  # Provider API endpoint
    model_name: str = "qwen3:8b"  # Model identifier
    api_key: Optional[str] = None  # For providers requiring authentication
    
    # Generation parameters (provider-agnostic)
    temperature: float = 0.3  # Low for consistency (0.0 = deterministic, 1.0 = creative)
    max_tokens: int = 1000  # Maximum tokens per explanation
    timeout_seconds: float = 120.0  # Request timeout (increased for CPU-based Ollama)
    
    # Retry behavior
    max_retries: int = 2
    retry_delay_seconds: float = 1.0
    
    # Quality control
    enable_hallucination_checks: bool = True
    min_evidence_coverage: float = 0.5  # Require 50% evidence citation
    
    # Fallback behavior
    use_fallback_on_error: bool = True
    fallback_to_m8_narrative: bool = True
    
    def __post_init__(self):
        """Validate configuration"""
        if self.temperature < 0.0 or self.temperature > 1.0:
            raise ValueError(f"temperature must be 0.0-1.0, got {self.temperature}")
        
        if self.max_tokens < 100:
            raise ValueError(f"max_tokens must be >= 100, got {self.max_tokens}")
        
        if self.timeout_seconds <= 0:
            raise ValueError(f"timeout_seconds must be > 0, got {self.timeout_seconds}")
        
        if self.min_evidence_coverage < 0.0 or self.min_evidence_coverage > 1.0:
            raise ValueError(f"min_evidence_coverage must be 0.0-1.0, got {self.min_evidence_coverage}")
