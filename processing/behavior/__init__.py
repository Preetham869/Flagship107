"""
Behavior analysis module

Main exports:
    BehaviorAnalyzer: Analyzes movement patterns and states
    BehaviorConfig: Configuration for thresholds
    TrackHistory: Temporal history for tracks
"""

from processing.behavior.analyzer import (
    BehaviorAnalyzer,
    BehaviorConfig,
    TrackHistory,
    BehaviorError,
)

__all__ = [
    "BehaviorAnalyzer",
    "BehaviorConfig",
    "TrackHistory",
    "BehaviorError",
]
