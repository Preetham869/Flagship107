"""
Pattern Recognizer

Detects observable behavioral patterns from M3/M4/M5/M6 data.

IMPORTANT: Detects only OBSERVABLE patterns, not intent or motivation.
Uses evidence-based language: "consistent with X" not "intends X".
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
import math

from .schemas import SourceReference, PatternEvidence
from .evidence import EvidenceBuilder

logger = logging.getLogger(__name__)


@dataclass
class PatternConfig:
    """Configuration for pattern recognition thresholds"""

    # Movement patterns
    stationary_displacement_threshold: float = 20.0  # Max displacement (px)
    stationary_duration_threshold: float = 10.0  # Min duration (s)
    stationary_speed_threshold: float = 10.0  # Max speed (px/s)

    circular_position_similarity: float = 0.7  # Path similarity threshold
    circular_min_loops: int = 2  # Minimum loops required

    rapid_movement_speed_percentile: float = 0.85  # Must be in top 15%
    rapid_movement_min_duration: float = 3.0  # Min sustained duration (s)

    erratic_direction_variance_threshold: float = 80.0  # Min direction variance (degrees)
    erratic_speed_variance_threshold: float = 0.5  # Min speed coefficient of variation

    # Spatial patterns
    proximity_radius: float = 150.0  # Distance for proximity (px)
    following_direction_threshold: float = 45.0  # Max angle difference (degrees)
    following_distance_min: float = 30.0  # Min following distance (px)
    following_distance_max: float = 200.0  # Max following distance (px)

    # Temporal patterns
    repeated_appearance_gap_threshold: float = 3.0  # Min gap between appearances (s)
    extended_presence_threshold: float = 10.0  # Min duration for "extended" (s)
    brief_presence_threshold: float = 2.0  # Max duration for "brief" (s)


class PatternRecognizer:
    """
    Recognizes observable behavioral patterns
    
    All patterns are evidence-based observations, not inferences about intent.
    """

    def __init__(self, config: Optional[PatternConfig] = None):
        """
        Initialize pattern recognizer
        
        Args:
            config: Pattern detection configuration
        """
        self.config = config or PatternConfig()
        logger.info("PatternRecognizer initialized")

    # ========================================================================
    # Movement Patterns (Observable Only)
    # ========================================================================

    def detect_stationary_extended(
        self, track_behaviors: List[Dict]
    ) -> Optional[PatternEvidence]:
        """
        Detect: Track remained in small area for extended time
        
        Observable evidence:
        - Average displacement < threshold
        - Duration > threshold
        - Speed consistently low
        
        Language: "stationary for extended period" (not "loitering")
        """
        if len(track_behaviors) < 2:
            return None

        # Calculate average displacement
        positions = [b["position"] for b in track_behaviors if "position" in b]
        if len(positions) < 2:
            return None

        # Calculate distance from first position
        first_pos = positions[0]
        displacements = [
            math.sqrt((p[0] - first_pos[0])**2 + (p[1] - first_pos[1])**2)
            for p in positions
        ]
        avg_displacement = sum(displacements) / len(displacements)

        # Calculate duration
        duration = track_behaviors[-1]["timestamp"] - track_behaviors[0]["timestamp"]

        # Calculate average speed
        speeds = [b.get("speed", 0) for b in track_behaviors]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0

        # Check criteria
        if (avg_displacement < self.config.stationary_displacement_threshold and
            duration > self.config.stationary_duration_threshold and
            avg_speed < self.config.stationary_speed_threshold):

            # Build evidence
            observations = [
                EvidenceBuilder.create_source_reference(
                    source_module="M3",
                    source_type="behavior",
                    source_id=f"behavior_{b.get('frame_id', 'unknown')}_{b['track_id']}",
                    timestamp=b["timestamp"],
                    track_ids=[str(b["track_id"])],
                    measurement={"speed": b.get("speed", 0), "position": b["position"]},
                )
                for b in track_behaviors[::max(1, len(track_behaviors) // 5)]  # Sample every ~20%
            ]

            return EvidenceBuilder.create_pattern_evidence(
                pattern_name="stationary_extended",
                confidence=min(1.0, duration / (self.config.stationary_duration_threshold * 2)),
                supporting_observations=observations,
                measurements={
                    "avg_displacement": round(avg_displacement, 2),
                    "duration": round(duration, 2),
                    "avg_speed": round(avg_speed, 2),
                },
                description=(
                    f"Track remained stationary (avg displacement: {avg_displacement:.1f}px, "
                    f"avg speed: {avg_speed:.1f}px/s) for {duration:.1f}s"
                ),
            )

        return None

    def detect_rapid_movement(
        self, track_behaviors: List[Dict], speed_threshold: float
    ) -> Optional[PatternEvidence]:
        """
        Detect: Track moved at sustained high speed
        
        Observable evidence:
        - Speed > threshold consistently
        - Sustained duration
        - Low speed variance (consistent)
        
        Language: "rapid sustained movement" (not "fleeing" or "rushing")
        """
        if len(track_behaviors) < 3:
            return None

        # Extract speeds
        speeds = [b.get("speed", 0) for b in track_behaviors]
        high_speed_observations = [
            (i, b) for i, b in enumerate(track_behaviors)
            if b.get("speed", 0) > speed_threshold
        ]

        if not high_speed_observations:
            return None

        # Calculate sustained duration
        first_idx = high_speed_observations[0][0]
        last_idx = high_speed_observations[-1][0]
        duration = (
            track_behaviors[last_idx]["timestamp"] -
            track_behaviors[first_idx]["timestamp"]
        )

        if duration < self.config.rapid_movement_min_duration:
            return None

        # Calculate speed statistics
        high_speeds = [b.get("speed", 0) for _, b in high_speed_observations]
        avg_speed = sum(high_speeds) / len(high_speeds)
        max_speed = max(high_speeds)

        # Build evidence (sample key observations)
        observations = [
            EvidenceBuilder.create_source_reference(
                source_module="M3",
                source_type="behavior",
                source_id=f"behavior_{b.get('frame_id', 'unknown')}_{b['track_id']}",
                timestamp=b["timestamp"],
                track_ids=[str(b["track_id"])],
                measurement={"speed": b.get("speed", 0)},
            )
            for _, b in high_speed_observations[::max(1, len(high_speed_observations) // 5)]
        ]

        return EvidenceBuilder.create_pattern_evidence(
            pattern_name="rapid_movement",
            confidence=min(1.0, avg_speed / (speed_threshold * 2)),
            supporting_observations=observations,
            measurements={
                "avg_speed": round(avg_speed, 2),
                "max_speed": round(max_speed, 2),
                "duration": round(duration, 2),
                "observation_count": len(high_speed_observations),
            },
            description=(
                f"Track exhibited rapid movement (avg: {avg_speed:.1f}px/s, "
                f"max: {max_speed:.1f}px/s) sustained for {duration:.1f}s"
            ),
        )

    def detect_linear_traversal(
        self, track_behaviors: List[Dict]
    ) -> Optional[PatternEvidence]:
        """
        Detect: Track moved in relatively straight line
        
        Observable evidence:
        - Direction variance low
        - Consistent movement
        
        Language: "linear traversal" (observable path)
        """
        if len(track_behaviors) < 5:
            return None

        # Extract directions (filter out None)
        directions = [
            b["direction"] for b in track_behaviors
            if b.get("direction") is not None
        ]

        if len(directions) < 5:
            return None

        # Calculate direction variance
        avg_direction = sum(directions) / len(directions)
        variance = sum((d - avg_direction) ** 2 for d in directions) / len(directions)
        std_dev = math.sqrt(variance)

        # Linear if low direction variance
        if std_dev < 30.0:  # Less than 30 degrees standard deviation
            # Sample observations
            observations = [
                EvidenceBuilder.create_source_reference(
                    source_module="M3",
                    source_type="behavior",
                    source_id=f"behavior_{b.get('frame_id', 'unknown')}_{b['track_id']}",
                    timestamp=b["timestamp"],
                    track_ids=[str(b["track_id"])],
                    measurement={"direction": b.get("direction")},
                )
                for b in track_behaviors[::max(1, len(track_behaviors) // 5)]
                if b.get("direction") is not None
            ]

            return EvidenceBuilder.create_pattern_evidence(
                pattern_name="linear_traversal",
                confidence=min(1.0, 1.0 - (std_dev / 90.0)),  # Inverse of variance
                supporting_observations=observations,
                measurements={
                    "avg_direction": round(avg_direction, 2),
                    "direction_std_dev": round(std_dev, 2),
                },
                description=(
                    f"Track moved in linear path (direction: {avg_direction:.1f}°±{std_dev:.1f}°)"
                ),
            )

        return None

    def detect_erratic_movement(
        self, track_behaviors: List[Dict]
    ) -> Optional[PatternEvidence]:
        """
        Detect: Track showed high variance in direction/speed
        
        Observable evidence:
        - High direction variance
        - High speed variance
        
        Language: "erratic movement" (observable pattern)
        """
        if len(track_behaviors) < 5:
            return None

        # Extract directions and speeds
        directions = [
            b["direction"] for b in track_behaviors
            if b.get("direction") is not None
        ]
        speeds = [b.get("speed", 0) for b in track_behaviors]

        if len(directions) < 5:
            return None

        # Calculate direction variance
        avg_direction = sum(directions) / len(directions)
        direction_variance = sum((d - avg_direction) ** 2 for d in directions) / len(directions)
        direction_std_dev = math.sqrt(direction_variance)

        # Calculate speed coefficient of variation
        avg_speed = sum(speeds) / len(speeds)
        if avg_speed < 1:
            return None  # Too slow to be erratic
        
        speed_variance = sum((s - avg_speed) ** 2 for s in speeds) / len(speeds)
        speed_std_dev = math.sqrt(speed_variance)
        speed_cv = speed_std_dev / avg_speed if avg_speed > 0 else 0

        # Check criteria
        if (direction_std_dev > self.config.erratic_direction_variance_threshold and
            speed_cv > self.config.erratic_speed_variance_threshold):

            observations = [
                EvidenceBuilder.create_source_reference(
                    source_module="M3",
                    source_type="behavior",
                    source_id=f"behavior_{b.get('frame_id', 'unknown')}_{b['track_id']}",
                    timestamp=b["timestamp"],
                    track_ids=[str(b["track_id"])],
                    measurement={
                        "direction": b.get("direction"),
                        "speed": b.get("speed", 0),
                    },
                )
                for b in track_behaviors[::max(1, len(track_behaviors) // 5)]
                if b.get("direction") is not None
            ]

            return EvidenceBuilder.create_pattern_evidence(
                pattern_name="erratic_movement",
                confidence=min(1.0, (direction_std_dev / 180.0) + speed_cv) / 2,
                supporting_observations=observations,
                measurements={
                    "direction_std_dev": round(direction_std_dev, 2),
                    "speed_cv": round(speed_cv, 3),
                    "avg_speed": round(avg_speed, 2),
                },
                description=(
                    f"Track exhibited erratic movement (direction variance: {direction_std_dev:.1f}°, "
                    f"speed CV: {speed_cv:.2f})"
                ),
            )

        return None

    # ========================================================================
    # Spatial Patterns (Observable Only)
    # ========================================================================

    def detect_maintaining_proximity(
        self, relationships: List[Dict]
    ) -> Optional[PatternEvidence]:
        """
        Detect: Entities maintained close distance
        
        Observable evidence:
        - Consistent proximity from M6
        - Duration above threshold
        
        Language: "maintaining proximity" (not "interacting with intent")
        """
        if not relationships:
            return None

        # Filter for proximity/co-movement relationships
        proximity_rels = [
            r for r in relationships
            if r.get("relationship_type") in ["proximity_event", "co_movement_event"]
        ]

        if not proximity_rels:
            return None

        # Get longest duration relationship
        longest_rel = max(proximity_rels, key=lambda r: r.get("duration_seconds", 0))
        duration = longest_rel.get("duration_seconds", 0)

        if duration < 2.0:  # Minimum duration
            return None

        observations = [
            EvidenceBuilder.create_source_reference(
                source_module="M6",
                source_type="relationship",
                source_id=r.get("relationship_id", ""),
                timestamp=r.get("start_timestamp", 0),
                track_ids=r.get("participating_track_ids", []),
                measurement={
                    "duration": r.get("duration_seconds", 0),
                    "type": r.get("relationship_type"),
                },
            )
            for r in proximity_rels
        ]

        return EvidenceBuilder.create_pattern_evidence(
            pattern_name="maintaining_proximity",
            confidence=min(1.0, duration / 10.0),
            supporting_observations=observations,
            measurements={
                "duration": round(duration, 2),
                "relationship_count": len(proximity_rels),
            },
            description=(
                f"Entities maintained proximity for {duration:.1f}s "
                f"({len(proximity_rels)} observations)"
            ),
        )

    def detect_approaching_entities(
        self, relationships: List[Dict]
    ) -> Optional[PatternEvidence]:
        """
        Detect: Distance between entities decreased
        
        Observable evidence:
        - M6 approach_event
        
        Language: "entities approaching" (not "pursuing" or "threatening")
        """
        approach_rels = [
            r for r in relationships
            if r.get("relationship_type") == "approach_event"
        ]

        if not approach_rels:
            return None

        observations = [
            EvidenceBuilder.create_source_reference(
                source_module="M6",
                source_type="relationship",
                source_id=r.get("relationship_id", ""),
                timestamp=r.get("start_timestamp", 0),
                track_ids=r.get("participating_track_ids", []),
                measurement={
                    "duration": r.get("duration_seconds", 0),
                },
            )
            for r in approach_rels
        ]

        return EvidenceBuilder.create_pattern_evidence(
            pattern_name="approaching_entities",
            confidence=0.9,  # High confidence for direct M6 detection
            supporting_observations=observations,
            measurements={
                "approach_count": len(approach_rels),
            },
            description=f"Entities approached each other ({len(approach_rels)} observations)",
        )

    def detect_parallel_movement(
        self, relationships: List[Dict]
    ) -> Optional[PatternEvidence]:
        """
        Detect: Entities moved in similar direction/speed
        
        Observable evidence:
        - M6 co_movement_event
        
        Language: "parallel movement" (observable)
        """
        comovement_rels = [
            r for r in relationships
            if r.get("relationship_type") == "co_movement_event"
        ]

        if not comovement_rels:
            return None

        # Get total duration
        total_duration = sum(r.get("duration_seconds", 0) for r in comovement_rels)

        observations = [
            EvidenceBuilder.create_source_reference(
                source_module="M6",
                source_type="relationship",
                source_id=r.get("relationship_id", ""),
                timestamp=r.get("start_timestamp", 0),
                track_ids=r.get("participating_track_ids", []),
                measurement={
                    "duration": r.get("duration_seconds", 0),
                },
            )
            for r in comovement_rels
        ]

        return EvidenceBuilder.create_pattern_evidence(
            pattern_name="parallel_movement",
            confidence=min(1.0, total_duration / 10.0),
            supporting_observations=observations,
            measurements={
                "total_duration": round(total_duration, 2),
                "observation_count": len(comovement_rels),
            },
            description=(
                f"Entities exhibited parallel movement for {total_duration:.1f}s "
                f"({len(comovement_rels)} observations)"
            ),
        )

    # ========================================================================
    # Temporal Patterns (Observable Only)
    # ========================================================================

    def detect_extended_presence(
        self, track_behaviors: List[Dict]
    ) -> Optional[PatternEvidence]:
        """
        Detect: Track present for extended duration
        
        Observable evidence:
        - Duration > threshold
        
        Language: "extended presence" (observable)
        """
        if len(track_behaviors) < 2:
            return None

        duration = track_behaviors[-1]["timestamp"] - track_behaviors[0]["timestamp"]

        if duration < self.config.extended_presence_threshold:
            return None

        # Sample observations
        observations = [
            EvidenceBuilder.create_source_reference(
                source_module="M3",
                source_type="behavior",
                source_id=f"behavior_{b.get('frame_id', 'unknown')}_{b['track_id']}",
                timestamp=b["timestamp"],
                track_ids=[str(b["track_id"])],
            )
            for b in [track_behaviors[0], track_behaviors[-1]]
        ]

        return EvidenceBuilder.create_pattern_evidence(
            pattern_name="extended_presence",
            confidence=min(1.0, duration / 30.0),
            supporting_observations=observations,
            measurements={
                "duration": round(duration, 2),
                "observation_count": len(track_behaviors),
            },
            description=f"Track present for {duration:.1f}s ({len(track_behaviors)} observations)",
        )

    # ========================================================================
    # Combined Pattern Detection
    # ========================================================================

    def detect_all_patterns(
        self,
        track_behaviors: List[Dict],
        relationships: List[Dict],
        speed_threshold: float = 150.0,
    ) -> List[PatternEvidence]:
        """
        Detect all applicable patterns for a track
        
        Args:
            track_behaviors: M3 behaviors for track
            relationships: M6 relationships involving track
            speed_threshold: Speed threshold for rapid movement
            
        Returns:
            List of detected patterns with evidence
        """
        patterns = []

        # Movement patterns
        if pattern := self.detect_stationary_extended(track_behaviors):
            patterns.append(pattern)
        
        if pattern := self.detect_rapid_movement(track_behaviors, speed_threshold):
            patterns.append(pattern)
        
        if pattern := self.detect_linear_traversal(track_behaviors):
            patterns.append(pattern)
        
        if pattern := self.detect_erratic_movement(track_behaviors):
            patterns.append(pattern)

        # Spatial patterns
        if pattern := self.detect_maintaining_proximity(relationships):
            patterns.append(pattern)
        
        if pattern := self.detect_approaching_entities(relationships):
            patterns.append(pattern)
        
        if pattern := self.detect_parallel_movement(relationships):
            patterns.append(pattern)

        # Temporal patterns
        if pattern := self.detect_extended_presence(track_behaviors):
            patterns.append(pattern)

        return patterns
