"""
Anomaly detection module

Main exports:
    AnomalyDetector: Explainable anomaly detection engine
    AnomalyConfig: Configuration for thresholds
    RestrictedZone: Restricted zone definition
    AnomalyType: Enumeration of anomaly types
    Severity: Severity levels
"""

from processing.anomaly.detector import (
    AnomalyDetector,
    AnomalyConfig,
    RestrictedZone,
    AnomalyType,
    Severity,
    AnomalyError,
)

__all__ = [
    "AnomalyDetector",
    "AnomalyConfig",
    "RestrictedZone",
    "AnomalyType",
    "Severity",
    "AnomalyError",
]
