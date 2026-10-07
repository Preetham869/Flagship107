"""
Event Correlation Module (Milestone 5)

Correlates M4 anomaly observations into meaningful higher-level events.
"""

from .correlator import (
    EventCorrelator,
    EventConfig,
    EventType,
    CorrelatedEvent,
)

__all__ = [
    "EventCorrelator",
    "EventConfig",
    "EventType",
    "CorrelatedEvent",
]
