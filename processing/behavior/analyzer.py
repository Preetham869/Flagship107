"""
Behaviour analysis module for tracked objects
Analyzes movement patterns, speed, direction, and states
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
import logging
import math

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BehaviorConfig:
    """Configuration for behavior analysis thresholds"""

    # Speed thresholds (pixels per second)
    stationary_threshold: float = 10.0  # Below this is stationary
    fast_moving_threshold: float = 100.0  # Above this is fast-moving

    # Duration thresholds (seconds)
    min_stationary_duration: float = 2.0  # Min duration to be considered stationary

    # History settings
    max_history_size: int = 30  # Maximum number of positions to keep in history
    min_history_for_speed: int = 2  # Minimum positions needed for speed calculation


class BehaviorError(Exception):
    """Custom exception for behavior analysis errors"""

    pass


@dataclass
class TrackHistory:
    """Temporal history for a single track"""

    track_id: int
    positions: deque = field(default_factory=lambda: deque(maxlen=30))
    timestamps: deque = field(default_factory=lambda: deque(maxlen=30))
    bbox_history: deque = field(default_factory=lambda: deque(maxlen=30))

    # Stationary tracking
    stationary_start_time: Optional[float] = None
    last_known_position: Optional[Tuple[float, float]] = None

    def add_observation(
        self, timestamp: float, bbox: List[float], center: Tuple[float, float]
    ):
        """
        Add a new observation to the history

        Args:
            timestamp: Observation timestamp in seconds
            bbox: Bounding box [x1, y1, x2, y2]
            center: Center position (x, y)
        """
        self.timestamps.append(timestamp)
        self.positions.append(center)
        self.bbox_history.append(bbox)
        self.last_known_position = center

    def get_duration(self) -> float:
        """
        Get total tracked duration

        Returns:
            Duration in seconds
        """
        if len(self.timestamps) < 2:
            return 0.0
        return self.timestamps[-1] - self.timestamps[0]

    def get_stationary_duration(self, current_time: float) -> float:
        """
        Get duration the track has been stationary

        Args:
            current_time: Current timestamp

        Returns:
            Stationary duration in seconds, or 0 if not stationary
        """
        if self.stationary_start_time is None:
            return 0.0
        return current_time - self.stationary_start_time


class BehaviorAnalyzer:
    """
    Analyzes behavior of tracked objects
    
    Maintains temporal history and computes movement features
    """

    def __init__(self, config: Optional[BehaviorConfig] = None):
        """
        Initialize behavior analyzer

        Args:
            config: Configuration for thresholds and parameters
        """
        self.config = config or BehaviorConfig()
        self.track_histories: Dict[int, TrackHistory] = {}

        logger.info("Behavior analyzer initialized")
        logger.info(
            f"Thresholds: stationary<{self.config.stationary_threshold}, "
            f"fast>{self.config.fast_moving_threshold} px/s"
        )

    def update(self, tracks: List[Dict], timestamp: float) -> List[Dict]:
        """
        Update behavior analysis with new tracking data

        Args:
            tracks: List of tracks from ObjectTracker
            timestamp: Current timestamp in seconds

        Returns:
            List of behavior analysis results
        """
        behaviors = []

        # Update histories and analyze each track
        for track in tracks:
            track_id = track["track_id"]
            bbox = track["bbox"]

            # Calculate center position
            center = self._calculate_center(bbox)

            # Get or create history
            if track_id not in self.track_histories:
                self.track_histories[track_id] = TrackHistory(track_id=track_id)

            history = self.track_histories[track_id]

            # Add observation
            history.add_observation(timestamp, bbox, center)

            # Analyze behavior
            behavior = self._analyze_track(history, timestamp)
            behavior["track_id"] = track_id
            behavior["class_name"] = track.get("class_name", "unknown")
            behavior["confidence"] = track.get("confidence", 0.0)

            behaviors.append(behavior)

        return behaviors

    def _analyze_track(self, history: TrackHistory, timestamp: float) -> Dict:
        """
        Analyze behavior for a single track

        Args:
            history: Track history
            timestamp: Current timestamp

        Returns:
            Dictionary with behavior features
        """
        # Calculate position
        position = history.last_known_position or (0, 0)

        # Calculate displacement
        displacement = self._calculate_displacement(history)

        # Calculate speed
        speed = self._calculate_speed(history)

        # Calculate direction
        direction = self._calculate_direction(history)

        # Determine state
        state = self._determine_state(speed, history, timestamp)

        # Calculate durations
        stationary_duration = history.get_stationary_duration(timestamp)
        total_duration = history.get_duration()

        return {
            "timestamp": timestamp,
            "position": list(position),
            "displacement": displacement,
            "speed": speed,
            "direction": direction,
            "state": state,
            "stationary_duration": stationary_duration,
            "total_duration": total_duration,
            "history_length": len(history.positions),
        }

    def _calculate_center(self, bbox: List[float]) -> Tuple[float, float]:
        """
        Calculate center point of bounding box

        Args:
            bbox: Bounding box [x1, y1, x2, y2]

        Returns:
            Center position (x, y)
        """
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        return (center_x, center_y)

    def _calculate_displacement(self, history: TrackHistory) -> float:
        """
        Calculate displacement between last two positions

        Args:
            history: Track history

        Returns:
            Displacement in pixels
        """
        if len(history.positions) < 2:
            return 0.0

        pos1 = history.positions[-2]
        pos2 = history.positions[-1]

        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]

        return math.sqrt(dx * dx + dy * dy)

    def _calculate_speed(self, history: TrackHistory) -> float:
        """
        Calculate estimated movement speed

        Args:
            history: Track history

        Returns:
            Speed in pixels per second
        """
        if len(history.positions) < self.config.min_history_for_speed:
            return 0.0

        # Use last few observations for speed
        positions = list(history.positions)
        timestamps = list(history.timestamps)

        # Calculate displacement over last few frames
        n = min(5, len(positions))  # Use last 5 positions
        if n < 2:
            return 0.0

        pos_start = positions[-n]
        pos_end = positions[-1]
        time_start = timestamps[-n]
        time_end = timestamps[-1]

        dx = pos_end[0] - pos_start[0]
        dy = pos_end[1] - pos_start[1]
        distance = math.sqrt(dx * dx + dy * dy)

        time_delta = time_end - time_start
        if time_delta <= 0:
            return 0.0

        speed = distance / time_delta
        return speed

    def _calculate_direction(self, history: TrackHistory) -> Optional[float]:
        """
        Calculate movement direction

        Args:
            history: Track history

        Returns:
            Direction in degrees (0-360), or None if cannot determine
        """
        if len(history.positions) < 2:
            return None

        pos1 = history.positions[-2]
        pos2 = history.positions[-1]

        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]

        if abs(dx) < 0.1 and abs(dy) < 0.1:
            return None  # No significant movement

        # Calculate angle in degrees (0 = right, 90 = down, 180 = left, 270 = up)
        angle = math.degrees(math.atan2(dy, dx))

        # Normalize to 0-360
        if angle < 0:
            angle += 360

        return angle

    def _determine_state(
        self, speed: float, history: TrackHistory, timestamp: float
    ) -> str:
        """
        Determine behavior state based on speed

        Args:
            speed: Current speed in pixels per second
            history: Track history
            timestamp: Current timestamp

        Returns:
            State string: 'stationary', 'moving', or 'fast-moving'
        """
        if speed < self.config.stationary_threshold:
            # Track is stationary
            if history.stationary_start_time is None:
                history.stationary_start_time = timestamp

            # Check if stationary long enough
            stationary_duration = history.get_stationary_duration(timestamp)
            if stationary_duration >= self.config.min_stationary_duration:
                return "stationary"
            else:
                return "moving"  # Not stationary long enough yet

        else:
            # Track is moving
            history.stationary_start_time = None

            if speed >= self.config.fast_moving_threshold:
                return "fast-moving"
            else:
                return "moving"

    def get_statistics(self) -> Dict:
        """
        Get analyzer statistics

        Returns:
            Dictionary with statistics
        """
        return {
            "total_tracks": len(self.track_histories),
            "active_tracks": len(self.track_histories),
        }

    def reset(self):
        """Reset analyzer state"""
        self.track_histories.clear()
        logger.info("Behavior analyzer state reset")

    def get_track_summary(self, track_id: int) -> Optional[Dict]:
        """
        Get summary for a specific track

        Args:
            track_id: Track ID

        Returns:
            Summary dictionary or None if track not found
        """
        if track_id not in self.track_histories:
            return None

        history = self.track_histories[track_id]

        if len(history.positions) == 0:
            return None

        # Calculate trajectory bounds
        positions = list(history.positions)
        x_coords = [p[0] for p in positions]
        y_coords = [p[1] for p in positions]

        return {
            "track_id": track_id,
            "total_duration": history.get_duration(),
            "observation_count": len(history.positions),
            "trajectory_bounds": {
                "min_x": min(x_coords),
                "max_x": max(x_coords),
                "min_y": min(y_coords),
                "max_y": max(y_coords),
            },
            "start_position": positions[0],
            "end_position": positions[-1],
        }
