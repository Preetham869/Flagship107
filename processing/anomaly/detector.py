"""
Explainable anomaly detection engine
Detects unusual behavior based on evidence-based rules
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid
import math

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of anomalies that can be detected"""

    UNUSUAL_SPEED = "unusual_speed"
    LOITERING = "loitering"
    SUDDEN_SPEED_CHANGE = "sudden_speed_change"
    SUDDEN_DIRECTION_CHANGE = "sudden_direction_change"
    RESTRICTED_ZONE_ENTRY = "restricted_zone_entry"


class Severity(Enum):
    """Severity levels for anomalies"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RestrictedZone:
    """Definition of a restricted zone (rectangular or polygonal)"""

    zone_id: str
    zone_type: str  # "rectangle" or "polygon"
    coordinates: List[float]  # Flat list: [x1, y1, x2, y2, ...] for vertices
    name: Optional[str] = None

    def contains_point(self, point: List[float]) -> bool:
        """
        Check if a point is inside the restricted zone

        Args:
            point: [x, y] coordinates

        Returns:
            True if point is inside zone
        """
        x, y = point[0], point[1]
        
        if self.zone_type == "rectangle":
            # Coordinates should be [x1, y1, x2, y2] for rectangle
            if len(self.coordinates) >= 4:
                x1, y1, x2, y2 = self.coordinates[:4]
                return min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(
                    y1, y2
                )
        elif self.zone_type == "polygon":
            # Ray casting algorithm for polygon
            return self._point_in_polygon(x, y)

        return False

    def _point_in_polygon(self, x: float, y: float) -> bool:
        """
        Ray casting algorithm to determine if point is in polygon

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if point is inside polygon
        """
        # Convert flat list to pairs
        vertices = [(self.coordinates[i], self.coordinates[i+1]) 
                    for i in range(0, len(self.coordinates), 2)]
        n = len(vertices)
        inside = False

        p1x, p1y = vertices[0]
        for i in range(1, n + 1):
            p2x, p2y = vertices[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside


@dataclass
class AnomalyConfig:
    """Configuration for anomaly detection thresholds"""

    # Unusual speed threshold (normalized pixels per second, 1080p reference baseline)
    unusual_speed_threshold: float = 150.0
    # Unusual speed threshold in body-heights per second (scale invariant)
    unusual_speed_threshold_bbox: float = 1.8
    
    # Temporal smoothing for speed anomalies (consecutive frames)
    speed_anomaly_min_frames: int = 3  # Require N consecutive frames above threshold

    # Loitering threshold (seconds)
    loitering_threshold: float = 10.0

    # Sudden speed change threshold (normalized pixels per second delta)
    speed_change_threshold: float = 100.0  # 100 px/s delta at 1080p reference
    speed_change_threshold_bbox: float = 1.2  # 1.2 body-heights per second delta

    # Sudden direction change threshold (degrees)
    direction_change_threshold: float = 90.0
    
    # Direction change evidence requirements (reduce jitter)
    direction_change_min_displacement: float = 20.0  # Min pixels moved to consider direction (at 1080p)
    direction_change_min_speed: float = 15.0  # Min speed (norm-px/s) for meaningful direction
    direction_change_min_frames: int = 2  # Consecutive frames showing direction change

    # Track lifecycle debouncing (prevent alerts on track creation / ID flicker)
    min_track_history: int = 4  # Minimum observations before speed anomalies
    max_observation_gap: float = 1.0  # Max gap in seconds before kinematic continuity is broken

    # Resolution normalization settings (reference: 1080p vertical resolution)
    reference_height: float = 1080.0
    frame_width: Optional[float] = None
    frame_height: Optional[float] = None

    # Restricted zones
    restricted_zones: List[RestrictedZone] = field(default_factory=list)

    # Anomaly score calculation weights
    score_weight_speed: float = 0.3
    score_weight_duration: float = 0.2
    score_weight_direction: float = 0.2
    score_weight_zone: float = 0.3


class AnomalyError(Exception):
    """Custom exception for anomaly detection errors"""

    pass


class AnomalyDetector:
    """
    Explainable anomaly detection engine
    
    Detects unusual behavior based on configurable evidence-based rules
    """

    def __init__(self, config: Optional[AnomalyConfig] = None):
        """
        Initialize anomaly detector

        Args:
            config: Configuration for thresholds and rules
        """
        self.config = config or AnomalyConfig()
        self.track_history: Dict[int, Dict] = {}  # Track previous states
        self.frame_width: Optional[float] = self.config.frame_width
        self.frame_height: Optional[float] = self.config.frame_height
        
        # Temporal evidence buffers for debouncing
        self.speed_anomaly_frames: Dict[int, int] = {}  # Track ID -> consecutive frames
        self.direction_change_buffer: Dict[int, List[Dict]] = {}  # Track ID -> recent changes

        logger.info("Anomaly detector initialized")
        logger.info(
            f"Thresholds: unusual_speed={self.config.unusual_speed_threshold}, "
            f"loitering={self.config.loitering_threshold}s, "
            f"speed_change={self.config.speed_change_threshold}%, "
            f"direction_change={self.config.direction_change_threshold}°"
        )

    def set_frame_dimensions(self, width: float, height: float):
        """
        Set frame dimensions for resolution-normalized anomaly detection

        Args:
            width: Frame width in pixels
            height: Frame height in pixels
        """
        self.frame_width = float(width)
        self.frame_height = float(height)
        logger.info(
            f"Anomaly detector frame dimensions set to {self.frame_width}x{self.frame_height}"
        )

    def detect(self, behaviors: List[Dict]) -> List[Dict]:
        """
        Detect anomalies from behavior analysis data

        Args:
            behaviors: List of behavior dictionaries from BehaviorAnalyzer

        Returns:
            List of detected anomalies with evidence and explanations
        """
        anomalies = []

        for behavior in behaviors:
            track_id = behavior["track_id"]

            # Rule 1: Unusual Speed
            speed_anomaly = self._check_unusual_speed(behavior)
            if speed_anomaly:
                anomalies.append(speed_anomaly)

            # Rule 2: Loitering (Prolonged Stationary)
            loitering_anomaly = self._check_loitering(behavior)
            if loitering_anomaly:
                anomalies.append(loitering_anomaly)

            # Rule 3: Sudden Speed Change
            speed_change_anomaly = self._check_sudden_speed_change(behavior, track_id)
            if speed_change_anomaly:
                anomalies.append(speed_change_anomaly)

            # Rule 4: Sudden Direction Change
            direction_anomaly = self._check_sudden_direction_change(
                behavior, track_id
            )
            if direction_anomaly:
                anomalies.append(direction_anomaly)

            # Rule 5: Restricted Zone Entry
            zone_anomaly = self._check_restricted_zone(behavior)
            if zone_anomaly:
                anomalies.append(zone_anomaly)

            # Update track history
            self._update_track_history(behavior, track_id)

        return anomalies

    def _check_unusual_speed(self, behavior: Dict) -> Optional[Dict]:
        """
        Rule 1: Detect unusual speed (with temporal smoothing and scale-awareness)

        Requires speed to exceed threshold for N consecutive frames
        to avoid false positives from tracking noise.

        Args:
            behavior: Behavior dictionary from analyzer

        Returns:
            Anomaly dictionary if detected, None otherwise
        """
        track_id = behavior["track_id"]
        speed = behavior.get("speed", 0.0)

        # Skip tracks with insufficient history (e.g. startup flicker or ID switch)
        history_len = behavior.get("history_length", 99)
        if history_len < self.config.min_track_history:
            return None

        # Temporal continuity check: if previous observation was across a gap, reset counter
        if track_id in self.track_history:
            prev_time = self.track_history[track_id].get("timestamp", 0.0)
            curr_time = behavior.get("timestamp", 0.0)
            max_gap = getattr(self.config, "max_observation_gap", 1.0)
            if prev_time > 0.0 and (curr_time - prev_time) > max_gap:
                if track_id in self.speed_anomaly_frames:
                    self.speed_anomaly_frames[track_id] = 0

        # Determine scale-normalized speed
        if "normalized_speed" in behavior:
            norm_speed = behavior["normalized_speed"]
        elif self.frame_height and self.frame_height > 0:
            norm_speed = speed * (self.config.reference_height / self.frame_height)
        else:
            norm_speed = speed

        speed_norm_bbox = behavior.get("speed_norm_bbox", 0.0)
        bbox_height = behavior.get("bbox_height", 0.0)

        # Scale verification: in low-resolution footage, discrete tracking jitter
        # is multiplied by 1080/H. When bounding box dimensions are available,
        # confirm the motion is significant in body scale or raw velocity.
        if bbox_height >= 10.0 and speed_norm_bbox > 0:
            if speed_norm_bbox < self.config.unusual_speed_threshold_bbox and speed < 50.0:
                if track_id in self.speed_anomaly_frames:
                    self.speed_anomaly_frames[track_id] = 0
                return None

        if norm_speed > self.config.unusual_speed_threshold:
            # Increment consecutive frame counter
            if track_id not in self.speed_anomaly_frames:
                self.speed_anomaly_frames[track_id] = 0
            self.speed_anomaly_frames[track_id] += 1

            # Only report after N consecutive frames
            if self.speed_anomaly_frames[track_id] >= self.config.speed_anomaly_min_frames:
                severity = self._calculate_severity(
                    norm_speed, self.config.unusual_speed_threshold, 2.0
                )
                anomaly_score = min(
                    1.0, norm_speed / (self.config.unusual_speed_threshold * 2)
                )

                # Reset counter after reporting
                self.speed_anomaly_frames[track_id] = 0

                observed_val = speed if norm_speed == speed else round(norm_speed, 1)

                return self._create_anomaly(
                    track_id=track_id,
                    frame_id=behavior.get("frame_id"),
                    timestamp=behavior["timestamp"],
                    anomaly_type=AnomalyType.UNUSUAL_SPEED,
                    severity=severity,
                    anomaly_score=anomaly_score,
                    evidence={
                        "observed_speed": speed,
                        "normalized_speed": round(norm_speed, 1),
                        "speed_norm_bbox": round(speed_norm_bbox, 2),
                        "position": behavior["position"],
                        "consecutive_frames": self.config.speed_anomaly_min_frames,
                        "description": (
                            f"High speed: {speed:.1f} px/s sustained over {self.config.speed_anomaly_min_frames} frames"
                            if norm_speed == speed
                            else f"High speed: {speed:.1f} px/s ({norm_speed:.1f} norm-px/s) sustained over {self.config.speed_anomaly_min_frames} frames"
                        )
                    },
                    observed_value=observed_val,
                    threshold=self.config.unusual_speed_threshold,
                    current_state=behavior.get("state", "unknown"),
                    explanation=(
                        f"Track moving at {speed:.1f} px/s for {self.config.speed_anomaly_min_frames} consecutive frames, exceeding unusual speed threshold of {self.config.unusual_speed_threshold:.1f} px/s"
                        if norm_speed == speed
                        else f"Track moving at {speed:.1f} px/s ({norm_speed:.1f} norm-px/s) for {self.config.speed_anomaly_min_frames} consecutive frames, exceeding unusual speed threshold of {self.config.unusual_speed_threshold:.1f} px/s"
                    ),
                )
        else:
            # Speed dropped below threshold, reset counter
            if track_id in self.speed_anomaly_frames:
                self.speed_anomaly_frames[track_id] = 0

        return None

    def _check_loitering(self, behavior: Dict) -> Optional[Dict]:
        """
        Rule 2: Detect loitering (prolonged stationary behavior)

        Args:
            behavior: Behavior dictionary from analyzer

        Returns:
            Anomaly dictionary if detected, None otherwise
        """
        stationary_duration = behavior.get("stationary_duration", 0.0)
        state = behavior.get("state", "")

        if (
            state == "stationary"
            and stationary_duration > self.config.loitering_threshold
        ):
            severity = self._calculate_severity(
                stationary_duration, self.config.loitering_threshold, 2.0
            )
            anomaly_score = min(
                1.0, stationary_duration / (self.config.loitering_threshold * 3)
            )

            return self._create_anomaly(
                track_id=behavior["track_id"],
                frame_id=behavior.get("frame_id"),
                timestamp=behavior["timestamp"],
                anomaly_type=AnomalyType.LOITERING,
                severity=severity,
                anomaly_score=anomaly_score,
                evidence={
                    "stationary_duration": stationary_duration,
                    "position": behavior["position"],
                    "description": f"Stationary for {stationary_duration:.1f}s"
                },
                observed_value=stationary_duration,
                threshold=self.config.loitering_threshold,
                current_state=state,
                explanation=f"Track stationary for {stationary_duration:.1f}s at position {behavior['position']}, exceeding loitering threshold of {self.config.loitering_threshold:.1f}s",
            )

        return None

    def _check_sudden_speed_change(
        self, behavior: Dict, track_id: str
    ) -> Optional[Dict]:
        """
        Rule 3: Detect sudden speed change

        Args:
            behavior: Behavior dictionary from analyzer
            track_id: Track ID

        Returns:
            Anomaly dictionary if detected, None otherwise
        """
        # Require track history to avoid track-entry or ID switch false positives
        history_len = behavior.get("history_length", 99)
        if history_len < self.config.min_track_history:
            return None

        current_speed = behavior.get("speed", 0.0)

        if track_id in self.track_history:
            prev_record = self.track_history[track_id]

            # Check temporal continuity: do not evaluate speed delta across observation gaps
            previous_time = prev_record.get("timestamp", 0.0)
            current_time = behavior.get("timestamp", 0.0)
            max_gap = getattr(self.config, "max_observation_gap", 1.0)
            if previous_time > 0.0 and (current_time - previous_time) > max_gap:
                return None

            previous_speed = prev_record.get("speed", 0.0)
            previous_state = prev_record.get("state", "unknown")

            # Avoid false positive when track first acquires initial speed from 0.0
            if previous_speed <= 0.0 and previous_state != "stationary":
                return None

            # Calculate scale-normalized speeds
            if "normalized_speed" in behavior and "normalized_speed" in prev_record:
                curr_norm = behavior["normalized_speed"]
                prev_norm = prev_record["normalized_speed"]
            elif self.frame_height and self.frame_height > 0:
                scale = self.config.reference_height / self.frame_height
                curr_norm = current_speed * scale
                prev_norm = previous_speed * scale
            else:
                curr_norm = current_speed
                prev_norm = previous_speed

            speed_delta = abs(current_speed - previous_speed)
            norm_delta = abs(curr_norm - prev_norm)

            # Scale verification: prevent low-resolution quantization noise
            bbox_height = behavior.get("bbox_height", 0.0)
            if bbox_height >= 10.0:
                delta_bbox = speed_delta / bbox_height
                if delta_bbox < self.config.speed_change_threshold_bbox and speed_delta < 40.0:
                    return None

            if norm_delta > self.config.speed_change_threshold:
                severity = self._calculate_severity(
                    norm_delta, self.config.speed_change_threshold, 1.5
                )
                anomaly_score = min(
                    1.0,
                    norm_delta / (self.config.speed_change_threshold * 2),
                )
                
                # Determine if acceleration or deceleration
                change_type = "acceleration" if current_speed > previous_speed else "deceleration"
                observed_val = speed_delta if norm_delta == speed_delta else round(norm_delta, 1)

                return self._create_anomaly(
                    track_id=track_id,
                    frame_id=behavior.get("frame_id"),
                    timestamp=behavior["timestamp"],
                    anomaly_type=AnomalyType.SUDDEN_SPEED_CHANGE,
                    severity=severity,
                    anomaly_score=anomaly_score,
                    evidence={
                        "previous_speed": previous_speed,
                        "current_speed": current_speed,
                        "change_delta": speed_delta,
                        "normalized_change_delta": round(norm_delta, 1),
                        "threshold": self.config.speed_change_threshold,
                        "description": f"Sudden {change_type}: speed changed by {speed_delta:.1f} px/s"
                    },
                    observed_value=observed_val,
                    threshold=self.config.speed_change_threshold,
                    current_state=behavior.get("state", "unknown"),
                    explanation=f"Track experienced sudden {change_type}: speed changed from {previous_speed:.1f} to {current_speed:.1f} px/s (delta {speed_delta:.1f} px/s), exceeding threshold of {self.config.speed_change_threshold:.1f} px/s",
                )

        return None

    def _check_sudden_direction_change(
        self, behavior: Dict, track_id: int
    ) -> Optional[Dict]:
        """
        Rule 4: Detect sudden direction change (with temporal smoothing)

        Requires:
        - Sufficient displacement between measurements
        - Sufficient speed (not stationary)
        - Evidence across multiple consecutive frames

        This prevents tracking jitter from generating false positives.

        Args:
            behavior: Behavior dictionary from analyzer
            track_id: Track ID

        Returns:
            Anomaly dictionary if detected, None otherwise
        """
        # Skip tracks with insufficient history (e.g. startup flicker or ID switch)
        history_len = behavior.get("history_length", 99)
        if history_len < self.config.min_track_history:
            return None

        current_direction = behavior.get("direction")

        if current_direction is not None and track_id in self.track_history:
            previous_record = self.track_history[track_id]
            previous_direction = previous_record.get("direction")
            previous_position = previous_record.get("position")
            current_position = behavior.get("position")
            current_speed = behavior.get("speed", 0)

            # Check temporal continuity: do not calculate direction changes across observation gaps
            previous_time = previous_record.get("timestamp", 0.0)
            current_time = behavior.get("timestamp", 0.0)
            max_gap = getattr(self.config, "max_observation_gap", 1.0)
            if previous_time > 0.0 and (current_time - previous_time) > max_gap:
                if track_id in self.direction_change_buffer:
                    self.direction_change_buffer[track_id] = []
                return None

            if previous_direction is not None and previous_position and current_position:
                # Purge stale events from direction_change_buffer that exceed max_gap
                if track_id in self.direction_change_buffer:
                    self.direction_change_buffer[track_id] = [
                        e for e in self.direction_change_buffer[track_id]
                        if (current_time - e.get("timestamp", 0.0)) <= max_gap
                    ]
                # Calculate displacement since last frame
                displacement = (
                    (current_position[0] - previous_position[0]) ** 2
                    + (current_position[1] - previous_position[1]) ** 2
                ) ** 0.5

                # Calculate angular difference
                direction_change = self._calculate_angle_difference(
                    previous_direction, current_direction
                )

                # Check if this exceeds threshold AND has sufficient evidence
                if direction_change > self.config.direction_change_threshold:
                    # Resolution-scaled displacement and speed requirements
                    if self.frame_height and self.frame_height > 0:
                        scale = self.frame_height / self.config.reference_height
                        min_disp = self.config.direction_change_min_displacement * scale
                        min_spd = self.config.direction_change_min_speed * scale
                    else:
                        min_disp = self.config.direction_change_min_displacement
                        min_spd = self.config.direction_change_min_speed

                    # Require minimum displacement to avoid jitter
                    if displacement < min_disp:
                        return None

                    # Require minimum speed to avoid stationary noise
                    if current_speed < min_spd:
                        return None

                    # Temporal buffering: accumulate consecutive direction changes
                    if track_id not in self.direction_change_buffer:
                        self.direction_change_buffer[track_id] = []

                    self.direction_change_buffer[track_id].append({
                        "frame_id": behavior.get("frame_id"),
                        "timestamp": behavior["timestamp"],
                        "direction_change": direction_change,
                        "displacement": displacement,
                        "speed": current_speed,
                        "previous_direction": previous_direction,
                        "current_direction": current_direction,
                    })

                    # Keep only recent frames (last N)
                    max_buffer = 5
                    if len(self.direction_change_buffer[track_id]) > max_buffer:
                        self.direction_change_buffer[track_id] = self.direction_change_buffer[track_id][-max_buffer:]

                    # Check if we have sufficient consecutive frames
                    if len(self.direction_change_buffer[track_id]) >= self.config.direction_change_min_frames:
                        # Report the anomaly with accumulated evidence
                        first_event = self.direction_change_buffer[track_id][0]
                        last_event = self.direction_change_buffer[track_id][-1]
                        
                        severity = self._calculate_severity(
                            direction_change, self.config.direction_change_threshold, 1.5
                        )
                        anomaly_score = min(
                            1.0,
                            direction_change / (self.config.direction_change_threshold * 2),
                        )

                        # Clear buffer after reporting
                        self.direction_change_buffer[track_id] = []

                        return self._create_anomaly(
                            track_id=track_id,
                            frame_id=behavior.get("frame_id"),
                            timestamp=behavior["timestamp"],
                            anomaly_type=AnomalyType.SUDDEN_DIRECTION_CHANGE,
                            severity=severity,
                            anomaly_score=anomaly_score,
                            evidence={
                                "previous_direction": previous_direction,
                                "current_direction": current_direction,
                                "change_degrees": direction_change,
                                "displacement": displacement,
                                "speed": current_speed,
                                "consecutive_frames": len(self.direction_change_buffer[track_id]),
                                "description": f"Turned {direction_change:.1f} degrees (displacement={displacement:.1f}px, speed={current_speed:.1f}px/s)"
                            },
                            observed_value=direction_change,
                            threshold=self.config.direction_change_threshold,
                            current_state=behavior.get("state", "unknown"),
                            explanation=f"Track turned {direction_change:.1f}° (from {previous_direction:.1f}° to {current_direction:.1f}°) with displacement {displacement:.1f}px at {current_speed:.1f}px/s, exceeding threshold of {self.config.direction_change_threshold:.1f}°",
                        )
                else:
                    # No significant direction change, clear buffer
                    if track_id in self.direction_change_buffer:
                        self.direction_change_buffer[track_id] = []

        return None

    def _check_restricted_zone(self, behavior: Dict) -> Optional[Dict]:
        """
        Rule 5: Detect restricted zone entry

        Args:
            behavior: Behavior dictionary from analyzer

        Returns:
            Anomaly dictionary if detected, None otherwise
        """
        position = behavior.get("position")

        if position and len(self.config.restricted_zones) > 0:
            x, y = position

            for zone in self.config.restricted_zones:
                if zone.contains_point(position):
                    anomaly_score = 0.8  # High score for zone violation

                    return self._create_anomaly(
                        track_id=behavior["track_id"],
                        frame_id=behavior["frame_id"],
                        timestamp=behavior["timestamp"],
                        anomaly_type=AnomalyType.RESTRICTED_ZONE_ENTRY,
                        severity=Severity.HIGH,
                        anomaly_score=anomaly_score,
                        evidence={
                            "position": position,
                            "zone_id": zone.zone_id,
                            "zone_name": zone.name or zone.zone_id,
                            "zone_type": zone.zone_type,
                            "description": f"Entered {zone.name or zone.zone_id}"
                        },
                        observed_value=f"({x:.1f}, {y:.1f})",
                        threshold=f"Zone {zone.zone_id}",
                        current_state=behavior.get("state", "unknown"),
                        explanation=f"Track entered restricted zone '{zone.name or zone.zone_id}' at position ({x:.1f}, {y:.1f})",
                    )

        return None

    def _create_anomaly(
        self,
        track_id: str,
        frame_id: int,
        timestamp: float,
        anomaly_type: AnomalyType,
        severity: Severity,
        anomaly_score: float,
        evidence: Dict,
        observed_value,
        threshold,
        current_state: str,
        explanation: str,
    ) -> Dict:
        """
        Create a structured anomaly dictionary

        Args:
            track_id: Track ID
            frame_id: Frame ID where anomaly occurred
            timestamp: Timestamp of anomaly
            anomaly_type: Type of anomaly
            severity: Severity level
            anomaly_score: Score between 0 and 1
            evidence: Dictionary of supporting evidence
            observed_value: The observed value that triggered anomaly
            threshold: The configured threshold
            current_state: Current behavior state
            explanation: Human-readable explanation

        Returns:
            Anomaly dictionary
        """
        return {
            "event_id": str(uuid.uuid4()),
            "track_id": track_id,
            "frame_id": frame_id,
            "timestamp": timestamp,
            "anomaly_type": anomaly_type.value,
            "severity": severity.value,
            "anomaly_score": round(anomaly_score, 3),
            "evidence": evidence,
            "observed_value": observed_value,
            "threshold": threshold,
            "current_behavior_state": current_state,
            "explanation": explanation,
        }

    def _calculate_severity(
        self, value: float, threshold: float, multiplier: float = 2.0
    ) -> Severity:
        """
        Calculate severity based on how much value exceeds threshold

        Args:
            value: Observed value
            threshold: Configured threshold
            multiplier: Multiplier for high severity

        Returns:
            Severity level
        """
        ratio = value / threshold

        if ratio >= multiplier:
            return Severity.HIGH
        elif ratio >= (1.0 + multiplier) / 2:
            return Severity.MEDIUM
        else:
            return Severity.LOW

    def _calculate_angle_difference(
        self, angle1: float, angle2: float
    ) -> float:
        """
        Calculate the minimum difference between two angles (0-360)

        Args:
            angle1: First angle in degrees
            angle2: Second angle in degrees

        Returns:
            Minimum angular difference in degrees
        """
        diff = abs(angle2 - angle1)
        if diff > 180:
            diff = 360 - diff
        return diff

    def _update_track_history(self, behavior: Dict, track_id: int):
        """
        Update track history for temporal comparison

        Args:
            behavior: Current behavior data
            track_id: Track ID
        """
        speed = behavior.get("speed", 0.0)
        norm_speed = behavior.get(
            "normalized_speed",
            speed * (self.config.reference_height / self.frame_height)
            if (self.frame_height and self.frame_height > 0)
            else speed,
        )
        self.track_history[track_id] = {
            "speed": speed,
            "normalized_speed": norm_speed,
            "speed_norm_bbox": behavior.get("speed_norm_bbox", 0.0),
            "direction": behavior.get("direction"),
            "position": behavior.get("position"),
            "timestamp": behavior.get("timestamp", 0.0),
            "state": behavior.get("state", "unknown"),
        }

    def get_statistics(self) -> Dict:
        """
        Get detector statistics

        Returns:
            Dictionary with statistics
        """
        return {
            "tracked_entities": len(self.track_history),
            "restricted_zones": len(self.config.restricted_zones),
        }

    def reset(self):
        """Reset detector state"""
        self.track_history.clear()
        logger.info("Anomaly detector state reset")
