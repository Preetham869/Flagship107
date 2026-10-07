"""
Multi-Entity Interaction and Spatial Reasoning Module (Milestone 6)

Detects and analyzes relationships between multiple tracked entities.
"""

from .spatial import SpatialReasoning
from .detector import (
    InteractionDetector,
    InteractionConfig,
    RelationshipType,
    Relationship,
)

__all__ = [
    "SpatialReasoning",
    "InteractionDetector",
    "InteractionConfig",
    "RelationshipType",
    "Relationship",
]
