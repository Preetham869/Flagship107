"""
M8: Contextual Behaviour Understanding

Synthesizes M3/M4/M5/M6 outputs into contextual behavioral scenes.
"""

from .schemas import (
    ContextualScene,
    TrackSummary,
    SourceReference,
    PatternEvidence,
    TrackEvidence,
    SceneEvidence,
)
from .evidence import EvidenceBuilder
from .patterns import PatternRecognizer, PatternConfig
from .synthesizer import ContextSynthesizer, ContextConfig

__all__ = [
    "ContextualScene",
    "TrackSummary",
    "SourceReference",
    "PatternEvidence",
    "TrackEvidence",
    "SceneEvidence",
    "EvidenceBuilder",
    "PatternRecognizer",
    "PatternConfig",
    "ContextSynthesizer",
    "ContextConfig",
]
