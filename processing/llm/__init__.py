"""
M9: Local LLM Explanation Layer

Generates natural language explanations for M8 contextual scenes using local LLM.
"""

from .config import LLMConfig
from .schemas import SceneExplanation, TrackExplanation
from .explanations import ExplanationGenerator

__all__ = [
    "LLMConfig",
    "SceneExplanation",
    "TrackExplanation",
    "ExplanationGenerator",
]
