"""
Event correlation engine for grouping anomalies into meaningful events.

Consumes M4 anomaly observations and produces higher-level correlated events.
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import uuid
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """High-level event types derived from anomaly patterns"""

    RESTRICTED_AREA_INTRUSION = "restricted_area_intrusion"
    LOITERING_EVENT = "loitering_event"
    HIGH_SPEED_ACTIVITY = "high_speed_activity"
    ABNORMAL_MOVEMENT_SEQUENCE = "abnormal_movement_sequence"


class EventSeverity(Enum):
    """Event severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class EventConfig:
    """Configuration for event correlation"""

    # Temporal correlation window (seconds)
    temporal_window: float = 30.0  # Group anomalies within 30 seconds

    # Minimum duration for loitering event (seconds)
    min_loitering_duration: float = 5.0

    # Minimum anomalies for high-speed activity
    min_high_speed_count: int = 3

    # Minimum anomalies for movement sequence
    min_movement_sequence: int = 2

    # Deduplication: max anomalies of same type before consolidating
    max_repeated_anomalies: int = 5


@dataclass
class CorrelatedEvent:
    """
    A high-level event derived from correlated anomalies
    
    Answers: WHO, WHEN, WHAT, HOW LONG, WHY, WHAT EVIDENCE
    """

    # Identity
    event_id: str
    event_type: EventType

    # Temporal extent
    start_timestamp: float
    end_timestamp: float
    duration_seconds: float

    # Participants
    participating_track_ids: List[str]

    # Source data
    source_anomaly_ids: List[str]
    source_anomaly_types: List[str]

    # Assessment
    severity: EventSeverity
    confidence: float  # 0-1, deterministic score

    # Evidence
    evidence: Dict
    explanation: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "duration_seconds": round(self.duration_seconds, 2),
            "participating_track_ids": self.participating_track_ids,
            "source_anomaly_ids": self.source_anomaly_ids,
            "source_anomaly_types": self.source_anomaly_types,
            "severity": self.severity.value,
            "confidence": round(self.confidence, 3),
            "evidence": self.evidence,
            "explanation": self.explanation,
        }


class EventCorrelator:
    """
    Event correlation engine
    
    Groups related M4 anomalies into meaningful higher-level events.
    Handles temporal correlation, deduplication, and event lifecycle.
    """

    def __init__(self, config: Optional[EventConfig] = None):
        """
        Initialize event correlator
        
        Args:
            config: Event configuration (uses defaults if None)
        """
        self.config = config or EventConfig()
        logger.info(
            f"EventCorrelator initialized with temporal_window={self.config.temporal_window}s"
        )

    def correlate(self, anomalies: List[Dict]) -> List[CorrelatedEvent]:
        """
        Correlate anomalies into higher-level events
        
        Args:
            anomalies: List of M4 anomaly dictionaries
            
        Returns:
            List of correlated events
        """
        if not anomalies:
            return []

        logger.info(f"Correlating {len(anomalies)} anomalies into events")

        # Group anomalies by track
        track_anomalies = self._group_by_track(anomalies)

        # Generate events for each track
        events = []
        for track_id, track_anomaly_list in track_anomalies.items():
            track_events = self._correlate_track_anomalies(track_id, track_anomaly_list)
            events.extend(track_events)

        logger.info(f"Generated {len(events)} correlated events")
        return events

    def _group_by_track(self, anomalies: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group anomalies by track ID
        
        Args:
            anomalies: List of anomaly dictionaries
            
        Returns:
            Dictionary mapping track_id to list of anomalies
        """
        grouped = defaultdict(list)
        for anomaly in anomalies:
            track_id = anomaly.get("track_id")
            if track_id:
                grouped[track_id].append(anomaly)

        return dict(grouped)

    def _correlate_track_anomalies(
        self, track_id: str, anomalies: List[Dict]
    ) -> List[CorrelatedEvent]:
        """
        Correlate anomalies for a single track
        
        Args:
            track_id: Track identifier
            anomalies: List of anomalies for this track
            
        Returns:
            List of correlated events
        """
        # Sort by timestamp
        sorted_anomalies = sorted(anomalies, key=lambda a: a.get("timestamp", 0))

        events = []

        # Check for restricted area intrusion
        intrusion_events = self._detect_intrusion_events(track_id, sorted_anomalies)
        events.extend(intrusion_events)

        # Check for loitering events
        loitering_events = self._detect_loitering_events(track_id, sorted_anomalies)
        events.extend(loitering_events)

        # Check for high-speed activity
        speed_events = self._detect_high_speed_events(track_id, sorted_anomalies)
        events.extend(speed_events)

        # Check for abnormal movement sequences
        movement_events = self._detect_movement_sequences(track_id, sorted_anomalies)
        events.extend(movement_events)

        return events

    def _detect_intrusion_events(
        self, track_id: str, anomalies: List[Dict]
    ) -> List[CorrelatedEvent]:
        """
        Detect restricted area intrusion events
        
        Triggered when track enters restricted zone, possibly with other anomalies
        
        Args:
            track_id: Track identifier
            anomalies: Sorted list of anomalies
            
        Returns:
            List of intrusion events
        """
        events = []

        # Find restricted zone entries
        zone_entries = [
            a for a in anomalies if a.get("anomaly_type") == "restricted_zone_entry"
        ]

        if not zone_entries:
            return events

        # Group zone entries by temporal window
        grouped_entries = self._group_by_temporal_window(zone_entries)

        for entry_group in grouped_entries:
            # Find other anomalies in same temporal window
            start_time = entry_group[0]["timestamp"]
            end_time = entry_group[-1]["timestamp"]

            related_anomalies = [
                a
                for a in anomalies
                if start_time <= a["timestamp"] <= end_time + self.config.temporal_window
            ]

            # Create intrusion event
            event = self._create_intrusion_event(track_id, related_anomalies)
            if event:
                events.append(event)

        return events

    def _detect_loitering_events(
        self, track_id: str, anomalies: List[Dict]
    ) -> List[CorrelatedEvent]:
        """
        Detect loitering events
        
        Consolidates repeated loitering anomalies into single event
        
        Args:
            track_id: Track identifier
            anomalies: Sorted list of anomalies
            
        Returns:
            List of loitering events
        """
        events = []

        # Find loitering anomalies
        loitering_anomalies = [
            a for a in anomalies if a.get("anomaly_type") == "loitering"
        ]

        if not loitering_anomalies:
            return events

        # Group by temporal window
        grouped_loitering = self._group_by_temporal_window(loitering_anomalies)

        for loiter_group in grouped_loitering:
            # Check duration
            start_time = loiter_group[0]["timestamp"]
            end_time = loiter_group[-1]["timestamp"]
            duration = end_time - start_time

            if duration >= self.config.min_loitering_duration or len(
                loiter_group
            ) >= self.config.max_repeated_anomalies:
                # Create loitering event
                event = self._create_loitering_event(track_id, loiter_group)
                if event:
                    events.append(event)

        return events

    def _detect_high_speed_events(
        self, track_id: str, anomalies: List[Dict]
    ) -> List[CorrelatedEvent]:
        """
        Detect high-speed activity events
        
        Triggered by sustained or repeated unusual speed
        
        Args:
            track_id: Track identifier
            anomalies: Sorted list of anomalies
            
        Returns:
            List of high-speed events
        """
        events = []

        # Find speed-related anomalies
        speed_anomalies = [
            a
            for a in anomalies
            if a.get("anomaly_type")
            in ["unusual_speed", "sudden_speed_change"]
        ]

        if len(speed_anomalies) < self.config.min_high_speed_count:
            return events

        # Group by temporal window
        grouped_speed = self._group_by_temporal_window(speed_anomalies)

        for speed_group in grouped_speed:
            if len(speed_group) >= self.config.min_high_speed_count:
                # Create high-speed event
                event = self._create_high_speed_event(track_id, speed_group)
                if event:
                    events.append(event)

        return events

    def _detect_movement_sequences(
        self, track_id: str, anomalies: List[Dict]
    ) -> List[CorrelatedEvent]:
        """
        Detect abnormal movement sequences
        
        Triggered when multiple movement anomalies occur in temporal sequence
        
        Args:
            track_id: Track identifier
            anomalies: Sorted list of anomalies
            
        Returns:
            List of movement sequence events
        """
        events = []

        # Find movement anomalies (excluding loitering and zone entry)
        movement_types = {
            "sudden_speed_change",
            "sudden_direction_change",
            "unusual_speed",
        }
        movement_anomalies = [
            a for a in anomalies if a.get("anomaly_type") in movement_types
        ]

        if len(movement_anomalies) < self.config.min_movement_sequence:
            return events

        # Look for sequences with multiple different types
        grouped_movements = self._group_by_temporal_window(movement_anomalies)

        for movement_group in grouped_movements:
            # Check if multiple anomaly types are present
            anomaly_types = {a.get("anomaly_type") for a in movement_group}

            if (
                len(anomaly_types) >= 2
                and len(movement_group) >= self.config.min_movement_sequence
            ):
                # Create movement sequence event
                event = self._create_movement_sequence_event(track_id, movement_group)
                if event:
                    events.append(event)

        return events

    def _group_by_temporal_window(
        self, anomalies: List[Dict]
    ) -> List[List[Dict]]:
        """
        Group anomalies into temporal windows
        
        Args:
            anomalies: Sorted list of anomalies
            
        Returns:
            List of anomaly groups
        """
        if not anomalies:
            return []

        groups = []
        current_group = [anomalies[0]]

        for i in range(1, len(anomalies)):
            prev_time = current_group[-1]["timestamp"]
            curr_time = anomalies[i]["timestamp"]

            if curr_time - prev_time <= self.config.temporal_window:
                # Within window, add to current group
                current_group.append(anomalies[i])
            else:
                # Outside window, start new group
                groups.append(current_group)
                current_group = [anomalies[i]]

        # Add last group
        groups.append(current_group)

        return groups

    def _create_intrusion_event(
        self, track_id: str, anomalies: List[Dict]
    ) -> Optional[CorrelatedEvent]:
        """
        Create a restricted area intrusion event
        
        Args:
            track_id: Track identifier
            anomalies: Related anomalies
            
        Returns:
            Correlated event or None
        """
        if not anomalies:
            return None

        start_time = min(a["timestamp"] for a in anomalies)
        end_time = max(a["timestamp"] for a in anomalies)
        duration = end_time - start_time

        # Extract zone information
        zone_entries = [
            a for a in anomalies if a.get("anomaly_type") == "restricted_zone_entry"
        ]
        zone_info = zone_entries[0]["evidence"] if zone_entries else {}
        zone_name = zone_info.get("zone_name", "unknown zone")

        # Calculate severity (zone entry is always high, but check for other anomalies)
        severity = self._calculate_event_severity(anomalies)

        # Calculate confidence
        confidence = self._calculate_event_confidence(anomalies, len(zone_entries))

        # Build evidence
        evidence = {
            "zone_name": zone_name,
            "zone_id": zone_info.get("zone_id", "unknown"),
            "anomaly_count": len(anomalies),
            "zone_entry_count": len(zone_entries),
            "other_anomaly_types": list(
                {
                    a["anomaly_type"]
                    for a in anomalies
                    if a["anomaly_type"] != "restricted_zone_entry"
                }
            ),
        }

        # Build explanation
        other_behaviors = []
        if any(a.get("anomaly_type") == "unusual_speed" for a in anomalies):
            other_behaviors.append("unusual speed")
        if any(a.get("anomaly_type") == "sudden_direction_change" for a in anomalies):
            other_behaviors.append("sudden direction change")

        behavior_desc = (
            f" with {', '.join(other_behaviors)}" if other_behaviors else ""
        )

        explanation = (
            f"Track #{track_id} entered restricted zone '{zone_name}' "
            f"and remained inside for {duration:.1f} seconds{behavior_desc}. "
            f"Consolidated {len(zone_entries)} zone entry observation(s) "
            f"and {len(anomalies) - len(zone_entries)} related anomaly/anomalies."
        )

        return CorrelatedEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.RESTRICTED_AREA_INTRUSION,
            start_timestamp=start_time,
            end_timestamp=end_time,
            duration_seconds=duration,
            participating_track_ids=[track_id],
            source_anomaly_ids=[a["event_id"] for a in anomalies],
            source_anomaly_types=[a["anomaly_type"] for a in anomalies],
            severity=severity,
            confidence=confidence,
            evidence=evidence,
            explanation=explanation,
        )

    def _create_loitering_event(
        self, track_id: str, anomalies: List[Dict]
    ) -> Optional[CorrelatedEvent]:
        """
        Create a loitering event
        
        Args:
            track_id: Track identifier
            anomalies: Loitering anomalies
            
        Returns:
            Correlated event or None
        """
        if not anomalies:
            return None

        start_time = min(a["timestamp"] for a in anomalies)
        end_time = max(a["timestamp"] for a in anomalies)
        duration = end_time - start_time

        # Calculate severity
        severity = self._calculate_event_severity(anomalies)

        # Calculate confidence (higher for longer duration and more observations)
        confidence = self._calculate_event_confidence(anomalies, len(anomalies))

        # Extract position if available
        positions = [
            a.get("evidence", {}).get("position") for a in anomalies if "evidence" in a
        ]
        position = positions[0] if positions else None

        # Build evidence
        evidence = {
            "loitering_duration": duration,
            "observation_count": len(anomalies),
            "position": position,
            "deduplication_note": f"Consolidated {len(anomalies)} repeated loitering observations",
        }

        # Build explanation
        explanation = (
            f"Track #{track_id} remained stationary for {duration:.1f} seconds "
            f"at position {position}. This event consolidates {len(anomalies)} "
            f"repeated loitering observations to reduce alert spam."
        )

        return CorrelatedEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LOITERING_EVENT,
            start_timestamp=start_time,
            end_timestamp=end_time,
            duration_seconds=duration,
            participating_track_ids=[track_id],
            source_anomaly_ids=[a["event_id"] for a in anomalies],
            source_anomaly_types=[a["anomaly_type"] for a in anomalies],
            severity=severity,
            confidence=confidence,
            evidence=evidence,
            explanation=explanation,
        )

    def _create_high_speed_event(
        self, track_id: str, anomalies: List[Dict]
    ) -> Optional[CorrelatedEvent]:
        """
        Create a high-speed activity event
        
        Args:
            track_id: Track identifier
            anomalies: Speed-related anomalies
            
        Returns:
            Correlated event or None
        """
        if not anomalies:
            return None

        start_time = min(a["timestamp"] for a in anomalies)
        end_time = max(a["timestamp"] for a in anomalies)
        duration = end_time - start_time

        # Calculate severity
        severity = self._calculate_event_severity(anomalies)

        # Calculate confidence
        confidence = self._calculate_event_confidence(anomalies, len(anomalies))

        # Extract speed information
        speed_values = [
            a.get("observed_value", 0)
            for a in anomalies
            if a.get("anomaly_type") == "unusual_speed"
        ]
        max_speed = max(speed_values) if speed_values else 0.0

        # Build evidence
        evidence = {
            "duration": duration,
            "observation_count": len(anomalies),
            "max_speed": max_speed,
            "anomaly_types": list({a["anomaly_type"] for a in anomalies}),
        }

        # Build explanation
        explanation = (
            f"Track #{track_id} exhibited sustained high-speed activity for {duration:.1f} seconds "
            f"with maximum speed of {max_speed:.1f} px/s. "
            f"Consolidated {len(anomalies)} speed-related observation(s)."
        )

        return CorrelatedEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.HIGH_SPEED_ACTIVITY,
            start_timestamp=start_time,
            end_timestamp=end_time,
            duration_seconds=duration,
            participating_track_ids=[track_id],
            source_anomaly_ids=[a["event_id"] for a in anomalies],
            source_anomaly_types=[a["anomaly_type"] for a in anomalies],
            severity=severity,
            confidence=confidence,
            evidence=evidence,
            explanation=explanation,
        )

    def _create_movement_sequence_event(
        self, track_id: str, anomalies: List[Dict]
    ) -> Optional[CorrelatedEvent]:
        """
        Create an abnormal movement sequence event
        
        Args:
            track_id: Track identifier
            anomalies: Movement anomalies
            
        Returns:
            Correlated event or None
        """
        if not anomalies:
            return None

        start_time = min(a["timestamp"] for a in anomalies)
        end_time = max(a["timestamp"] for a in anomalies)
        duration = end_time - start_time

        # Calculate severity
        severity = self._calculate_event_severity(anomalies)

        # Calculate confidence
        anomaly_types = {a["anomaly_type"] for a in anomalies}
        confidence = self._calculate_event_confidence(anomalies, len(anomaly_types))

        # Build evidence
        evidence = {
            "duration": duration,
            "observation_count": len(anomalies),
            "anomaly_types": list(anomaly_types),
            "sequence": [
                {
                    "timestamp": a["timestamp"],
                    "type": a["anomaly_type"],
                    "severity": a["severity"],
                }
                for a in anomalies
            ],
        }

        # Build explanation
        anomaly_desc = ", ".join(sorted(anomaly_types))
        explanation = (
            f"Track #{track_id} exhibited an abnormal movement sequence over {duration:.1f} seconds "
            f"involving: {anomaly_desc}. "
            f"Consolidated {len(anomalies)} movement observation(s) into coherent sequence."
        )

        return CorrelatedEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.ABNORMAL_MOVEMENT_SEQUENCE,
            start_timestamp=start_time,
            end_timestamp=end_time,
            duration_seconds=duration,
            participating_track_ids=[track_id],
            source_anomaly_ids=[a["event_id"] for a in anomalies],
            source_anomaly_types=[a["anomaly_type"] for a in anomalies],
            severity=severity,
            confidence=confidence,
            evidence=evidence,
            explanation=explanation,
        )

    def _calculate_event_severity(self, anomalies: List[Dict]) -> EventSeverity:
        """
        Calculate event severity from constituent anomalies
        
        Deterministic logic:
        - If any anomaly is HIGH severity → Event is HIGH
        - If majority are MEDIUM → Event is MEDIUM
        - Otherwise → Event is LOW
        
        Args:
            anomalies: List of anomalies
            
        Returns:
            Event severity
        """
        severities = [a.get("severity", "low") for a in anomalies]

        # Count severity levels
        high_count = severities.count("high")
        medium_count = severities.count("medium")
        total = len(severities)

        if high_count > 0:
            return EventSeverity.HIGH
        elif medium_count > total / 2:
            return EventSeverity.MEDIUM
        else:
            return EventSeverity.LOW

    def _calculate_event_confidence(
        self, anomalies: List[Dict], factor: int
    ) -> float:
        """
        Calculate event confidence score
        
        Deterministic score based on:
        - Number of supporting anomalies
        - Average anomaly scores
        - Factor (e.g., number of unique types or observations)
        
        Formula: min(1.0, avg_anomaly_score * (1 + log(factor)/10))
        
        Args:
            anomalies: List of anomalies
            factor: Additional weight factor
            
        Returns:
            Confidence score (0-1)
        """
        if not anomalies:
            return 0.0

        # Calculate average anomaly score
        scores = [a.get("anomaly_score", 0.5) for a in anomalies]
        avg_score = sum(scores) / len(scores)

        # Apply factor bonus (logarithmic scaling to avoid over-confidence)
        import math

        bonus = math.log(max(1, factor)) / 10
        confidence = avg_score * (1 + bonus)

        return min(1.0, round(confidence, 3))

    def get_statistics(self) -> Dict:
        """
        Get correlator statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            "temporal_window": self.config.temporal_window,
            "min_loitering_duration": self.config.min_loitering_duration,
            "min_high_speed_count": self.config.min_high_speed_count,
            "min_movement_sequence": self.config.min_movement_sequence,
        }
