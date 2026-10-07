"""
Evidence Builder

Constructs traceable evidence chains for contextual claims.
"""

from typing import List, Dict, Optional
import logging

from .schemas import (
    SourceReference,
    PatternEvidence,
    TrackEvidence,
    SceneEvidence,
)

logger = logging.getLogger(__name__)


class EvidenceBuilder:
    """
    Constructs evidence structures with complete provenance
    
    Every contextual claim must trace back to M3/M4/M5/M6 observations.
    """

    @staticmethod
    def create_source_reference(
        source_module: str,
        source_type: str,
        source_id: str,
        timestamp: float,
        track_ids: List[str],
        measurement: Optional[Dict] = None,
    ) -> SourceReference:
        """
        Create a source reference for traceability
        
        Args:
            source_module: "M3", "M4", "M5", or "M6"
            source_type: "behavior", "anomaly", "event", "relationship"
            source_id: Unique identifier from source
            timestamp: Timestamp of observation
            track_ids: Involved track IDs
            measurement: Optional measurements
            
        Returns:
            SourceReference with complete provenance
        """
        return SourceReference(
            source_module=source_module,
            source_type=source_type,
            source_id=source_id,
            timestamp=timestamp,
            track_ids=track_ids,
            measurement=measurement,
        )

    @staticmethod
    def create_pattern_evidence(
        pattern_name: str,
        confidence: float,
        supporting_observations: List[SourceReference],
        measurements: Dict,
        description: str,
    ) -> PatternEvidence:
        """
        Create evidence for a detected pattern
        
        Args:
            pattern_name: Name of the pattern
            confidence: Deterministic confidence score (0-1)
            supporting_observations: List of source references
            measurements: Pattern-specific measurements
            description: Evidence-based explanation
            
        Returns:
            PatternEvidence with supporting observations
        """
        return PatternEvidence(
            pattern_name=pattern_name,
            confidence=confidence,
            supporting_observations=supporting_observations,
            measurements=measurements,
            description=description,
        )

    @staticmethod
    def create_track_evidence(
        behaviors: List[Dict],
        anomalies: List[Dict],
        relationships: List[Dict],
        patterns: List[PatternEvidence],
    ) -> TrackEvidence:
        """
        Create evidence structure for track summary
        
        Args:
            behaviors: M3 behavior observations
            anomalies: M4 anomalies for this track
            relationships: M6 relationships involving this track
            patterns: Detected patterns with evidence
            
        Returns:
            TrackEvidence linking to all sources
        """
        return TrackEvidence(
            source_behaviors=[
                f"behavior_{b.get('frame_id', 'unknown')}_{b['track_id']}"
                for b in behaviors
            ],
            source_anomalies=[a.get("event_id", "") for a in anomalies],
            source_relationships=[r.get("relationship_id", "") for r in relationships],
            pattern_evidence=patterns,
        )

    @staticmethod
    def create_scene_evidence(
        segmentation_rationale: str,
        track_evidence: Dict[str, TrackEvidence],
        pattern_evidence: List[PatternEvidence],
        anomalies: List[Dict],
        events: List[Dict],
        relationships: List[Dict],
    ) -> SceneEvidence:
        """
        Create evidence structure for scene
        
        Args:
            segmentation_rationale: Why this is a scene
            track_evidence: Evidence for each track
            pattern_evidence: Scene-level patterns
            anomalies: M4 anomalies in scene
            events: M5 events in scene
            relationships: M6 relationships in scene
            
        Returns:
            SceneEvidence aggregating all evidence
        """
        # Aggregate anomaly evidence
        anomaly_summary = {
            "count": len(anomalies),
            "types": list(set(a.get("anomaly_type", "unknown") for a in anomalies)),
            "severities": {},
        }
        for a in anomalies:
            severity = a.get("severity", "unknown")
            anomaly_summary["severities"][severity] = (
                anomaly_summary["severities"].get(severity, 0) + 1
            )

        # Aggregate event evidence
        event_summary = {
            "count": len(events),
            "types": list(set(e.get("event_type", "unknown") for e in events)),
        }

        # Aggregate relationship evidence
        relationship_summary = {
            "count": len(relationships),
            "types": list(set(r.get("relationship_type", "unknown") for r in relationships)),
        }

        return SceneEvidence(
            segmentation_rationale=segmentation_rationale,
            track_evidence=track_evidence,
            pattern_evidence=pattern_evidence,
            anomaly_summary=anomaly_summary,
            event_summary=event_summary,
            relationship_summary=relationship_summary,
        )

    @staticmethod
    def filter_by_timerange(
        items: List[Dict], start: float, end: float
    ) -> List[Dict]:
        """
        Filter items within time range
        
        Args:
            items: List of dictionaries with 'timestamp' key
            start: Start timestamp
            end: End timestamp
            
        Returns:
            Filtered list
        """
        return [
            item
            for item in items
            if start <= item.get("timestamp", 0) <= end
        ]

    @staticmethod
    def filter_by_track_id(items: List[Dict], track_id: str) -> List[Dict]:
        """
        Filter items for specific track
        
        Args:
            items: List of dictionaries with 'track_id' or 'participating_track_ids'
            track_id: Track ID to filter for
            
        Returns:
            Filtered list
        """
        result = []
        for item in items:
            # Check direct track_id
            if item.get("track_id") == track_id:
                result.append(item)
            # Check participating_track_ids list
            elif track_id in item.get("participating_track_ids", []):
                result.append(item)
        
        return result
