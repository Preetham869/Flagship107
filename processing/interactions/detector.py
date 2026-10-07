"""
Multi-entity interaction detector.

Detects relationships between tracked entities based on spatial and temporal evidence.
"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import uuid
import logging

from .spatial import SpatialReasoning

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of spatial/temporal relationships between entities"""

    PROXIMITY_EVENT = "proximity_event"
    APPROACH_EVENT = "approach_event"
    DEPARTURE_EVENT = "departure_event"
    CO_MOVEMENT_EVENT = "co_movement_event"
    FOLLOWING_PATTERN = "following_pattern"
    GROUP_FORMATION = "group_formation"
    GROUP_SEPARATION = "group_separation"


@dataclass
class InteractionConfig:
    """Configuration for interaction detection"""

    # Spatial thresholds (pixels)
    proximity_radius: float = 150.0  # Within this distance = proximity
    interaction_radius: float = 200.0  # Wider radius for co-movement/following

    # Temporal thresholds
    min_interaction_duration: float = 2.0  # Minimum seconds for relationship
    min_observations: int = 5  # Minimum observations to confirm relationship

    # Approach/departure thresholds
    approach_rate_threshold: float = -5.0  # Pixels per observation (negative)
    departure_rate_threshold: float = 5.0  # Pixels per observation (positive)

    # Co-movement thresholds
    direction_similarity_threshold: float = 30.0  # Max degrees difference
    speed_similarity_threshold: float = 50.0  # Max pixels/sec difference

    # Following pattern thresholds
    following_direction_threshold: float = 45.0  # Max degrees misalignment
    following_distance_min: float = 30.0  # Min distance for following
    following_distance_max: float = 200.0  # Max distance for following

    # Group thresholds
    group_proximity_radius: float = 180.0  # Distance for group membership
    group_min_size: int = 3  # Minimum entities for group
    group_separation_distance: float = 300.0  # Distance beyond which separated


@dataclass
class Relationship:
    """
    A detected relationship between entities
    
    Represents an interaction lifecycle, not frame-by-frame observations
    """

    # Identity
    relationship_id: str
    relationship_type: RelationshipType

    # Temporal extent
    start_timestamp: float
    end_timestamp: float
    duration_seconds: float

    # Participants
    participating_track_ids: List[str]

    # Spatial evidence
    min_distance: float
    max_distance: float
    avg_distance: float

    # Assessment
    confidence: float  # 0-1, deterministic score
    evidence: Dict
    explanation: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "relationship_id": self.relationship_id,
            "relationship_type": self.relationship_type.value,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "duration_seconds": round(self.duration_seconds, 2),
            "participating_track_ids": self.participating_track_ids,
            "min_distance": round(self.min_distance, 2),
            "max_distance": round(self.max_distance, 2),
            "avg_distance": round(self.avg_distance, 2),
            "confidence": round(self.confidence, 3),
            "evidence": self.evidence,
            "explanation": self.explanation,
        }


class InteractionDetector:
    """
    Detects multi-entity interactions and spatial relationships
    
    Consumes M2 tracking and M3 behavior data to identify relationships
    between multiple entities over time.
    """

    def __init__(self, config: Optional[InteractionConfig] = None):
        """
        Initialize interaction detector
        
        Args:
            config: Configuration (uses defaults if None)
        """
        self.config = config or InteractionConfig()
        self.spatial = SpatialReasoning()

        # Track pairwise observation history
        # Key: (track_id_a, track_id_b) normalized
        # Value: List of observations
        self.pair_history: Dict[Tuple[str, str], List[Dict]] = defaultdict(list)

        # Track group membership over time
        # Key: timestamp
        # Value: Dict[track_id, group_id]
        self.group_history: Dict[float, Dict[str, str]] = {}

        logger.info("InteractionDetector initialized")

    def detect(self, behaviors: List[Dict]) -> List[Relationship]:
        """
        Detect relationships from behavior data
        
        Args:
            behaviors: List of M3 behavior dictionaries
            
        Returns:
            List of detected relationships
        """
        if len(behaviors) < 2:
            return []

        timestamp = behaviors[0].get("timestamp", 0.0)

        # Update pairwise observations
        self._update_pair_observations(behaviors, timestamp)

        # Detect relationships
        relationships = []

        # Detect pairwise relationships
        pairwise = self._detect_pairwise_relationships()
        relationships.extend(pairwise)

        # Detect group relationships
        groups = self._detect_group_relationships(behaviors, timestamp)
        relationships.extend(groups)

        if len(relationships) > 0:
            logger.info(f"Detected {len(relationships)} relationships at t={timestamp:.2f}s")
        return relationships

    def _update_pair_observations(self, behaviors: List[Dict], timestamp: float):
        """
        Update pairwise observation history
        
        Args:
            behaviors: List of behavior dictionaries
            timestamp: Current timestamp
        """
        # Create position map
        positions = {}
        for behavior in behaviors:
            track_id = behavior.get("track_id")
            position = behavior.get("position")
            if track_id and position:
                positions[track_id] = behavior

        # Update all pairs
        track_ids = list(positions.keys())
        for i in range(len(track_ids)):
            for j in range(i + 1, len(track_ids)):
                id_a = track_ids[i]
                id_b = track_ids[j]

                # Normalize pair ID
                pair_id = self.spatial.normalize_pair_id(id_a, id_b)

                # Calculate distance
                pos_a = positions[id_a]["position"]
                pos_b = positions[id_b]["position"]
                distance = self.spatial.euclidean_distance(pos_a, pos_b)

                # Store observation
                observation = {
                    "timestamp": timestamp,
                    "distance": distance,
                    "pos_a": pos_a,
                    "pos_b": pos_b,
                    "speed_a": positions[id_a].get("speed", 0.0),
                    "speed_b": positions[id_b].get("speed", 0.0),
                    "direction_a": positions[id_a].get("direction"),
                    "direction_b": positions[id_b].get("direction"),
                }

                self.pair_history[pair_id].append(observation)

                # Trim old observations (keep last 100 per pair)
                if len(self.pair_history[pair_id]) > 100:
                    self.pair_history[pair_id] = self.pair_history[pair_id][-100:]

    def _detect_pairwise_relationships(self) -> List[Relationship]:
        """
        Detect relationships between pairs of entities
        
        Returns:
            List of pairwise relationships
        """
        relationships = []

        for pair_id, observations in self.pair_history.items():
            if len(observations) < self.config.min_observations:
                continue

            # Get recent observations
            recent = observations[-self.config.min_observations :]

            # Check if still in proximity
            current_distance = recent[-1]["distance"]
            if current_distance > self.config.interaction_radius:
                continue  # Too far apart

            # Calculate temporal extent
            start_time = recent[0]["timestamp"]
            end_time = recent[-1]["timestamp"]
            duration = end_time - start_time

            if duration < self.config.min_interaction_duration:
                continue  # Too short

            # Detect specific relationship types
            track_id_a, track_id_b = pair_id

            # Check proximity
            if current_distance <= self.config.proximity_radius:
                prox = self._create_proximity_relationship(
                    track_id_a, track_id_b, recent
                )
                if prox:
                    relationships.append(prox)

            # Check approach
            distances = [obs["distance"] for obs in recent]
            if self.spatial.is_approaching(
                distances, self.config.approach_rate_threshold
            ):
                approach = self._create_approach_relationship(
                    track_id_a, track_id_b, recent
                )
                if approach:
                    relationships.append(approach)

            # Check departure
            if self.spatial.is_departing(distances, self.config.departure_rate_threshold):
                departure = self._create_departure_relationship(
                    track_id_a, track_id_b, recent
                )
                if departure:
                    relationships.append(departure)

            # Check co-movement
            if self._is_co_movement(recent):
                co_move = self._create_co_movement_relationship(
                    track_id_a, track_id_b, recent
                )
                if co_move:
                    relationships.append(co_move)

            # Check following pattern
            if self._is_following_pattern(recent, track_id_a, track_id_b):
                following = self._create_following_relationship(
                    track_id_a, track_id_b, recent
                )
                if following:
                    relationships.append(following)

        return relationships

    def _detect_group_relationships(
        self, behaviors: List[Dict], timestamp: float
    ) -> List[Relationship]:
        """
        Detect group formation and separation
        
        Args:
            behaviors: Current behavior data
            timestamp: Current timestamp
            
        Returns:
            List of group relationships
        """
        relationships = []

        # Build proximity graph
        positions = {}
        for behavior in behaviors:
            track_id = behavior.get("track_id")
            position = behavior.get("position")
            if track_id and position:
                positions[track_id] = position

        # Find connected groups
        proximity_map = defaultdict(set)
        track_ids = list(positions.keys())

        for i in range(len(track_ids)):
            for j in range(i + 1, len(track_ids)):
                id_a = track_ids[i]
                id_b = track_ids[j]

                distance = self.spatial.euclidean_distance(
                    positions[id_a], positions[id_b]
                )

                if distance <= self.config.group_proximity_radius:
                    proximity_map[id_a].add(id_b)
                    proximity_map[id_b].add(id_a)

        # Find connected components (groups)
        visited = set()
        groups = []

        for track_id in track_ids:
            if track_id in visited:
                continue

            # Find all entities connected to this one
            # Use BFS to find connected component
            component = {track_id}
            to_visit = {track_id}
            
            while to_visit:
                current = to_visit.pop()
                neighbors = proximity_map.get(current, set())
                for neighbor in neighbors:
                    if neighbor not in component:
                        component.add(neighbor)
                        to_visit.add(neighbor)

            if len(component) >= self.config.group_min_size:
                groups.append(component)
                visited.update(component)

        # Check for group formation (new groups)
        for group in groups:
            group_list = sorted(list(group))

            # Create group formation event
            if len(group_list) >= self.config.group_min_size:
                group_rel = self._create_group_formation(group_list, timestamp)
                if group_rel:
                    relationships.append(group_rel)

        # Check for group separation
        # (Would need persistent group tracking for proper separation detection)
        # This is a simplified version

        return relationships

    def _create_proximity_relationship(
        self, track_id_a: str, track_id_b: str, observations: List[Dict]
    ) -> Optional[Relationship]:
        """Create proximity relationship"""
        distances = [obs["distance"] for obs in observations]

        return Relationship(
            relationship_id=str(uuid.uuid4()),
            relationship_type=RelationshipType.PROXIMITY_EVENT,
            start_timestamp=observations[0]["timestamp"],
            end_timestamp=observations[-1]["timestamp"],
            duration_seconds=observations[-1]["timestamp"]
            - observations[0]["timestamp"],
            participating_track_ids=[track_id_a, track_id_b],
            min_distance=min(distances),
            max_distance=max(distances),
            avg_distance=sum(distances) / len(distances),
            confidence=self._calculate_confidence(observations, "proximity"),
            evidence={
                "observation_count": len(observations),
                "current_distance": distances[-1],
                "proximity_radius": self.config.proximity_radius,
            },
            explanation=f"Tracks #{track_id_a} and #{track_id_b} remained within {self.config.proximity_radius:.0f} pixels for {observations[-1]['timestamp'] - observations[0]['timestamp']:.1f} seconds. Avg distance: {sum(distances)/len(distances):.1f}px.",
        )

    def _create_approach_relationship(
        self, track_id_a: str, track_id_b: str, observations: List[Dict]
    ) -> Optional[Relationship]:
        """Create approach relationship"""
        distances = [obs["distance"] for obs in observations]
        change_rate = self.spatial.temporal_distance_change(distances)

        return Relationship(
            relationship_id=str(uuid.uuid4()),
            relationship_type=RelationshipType.APPROACH_EVENT,
            start_timestamp=observations[0]["timestamp"],
            end_timestamp=observations[-1]["timestamp"],
            duration_seconds=observations[-1]["timestamp"]
            - observations[0]["timestamp"],
            participating_track_ids=[track_id_a, track_id_b],
            min_distance=min(distances),
            max_distance=max(distances),
            avg_distance=sum(distances) / len(distances),
            confidence=self._calculate_confidence(observations, "approach"),
            evidence={
                "initial_distance": distances[0],
                "final_distance": distances[-1],
                "change_rate": change_rate,
                "distance_reduction": distances[0] - distances[-1],
            },
            explanation=f"Tracks #{track_id_a} and #{track_id_b} approached each other from {distances[0]:.1f}px to {distances[-1]:.1f}px over {observations[-1]['timestamp'] - observations[0]['timestamp']:.1f} seconds (rate: {change_rate:.1f}px/obs).",
        )

    def _create_departure_relationship(
        self, track_id_a: str, track_id_b: str, observations: List[Dict]
    ) -> Optional[Relationship]:
        """Create departure relationship"""
        distances = [obs["distance"] for obs in observations]
        change_rate = self.spatial.temporal_distance_change(distances)

        return Relationship(
            relationship_id=str(uuid.uuid4()),
            relationship_type=RelationshipType.DEPARTURE_EVENT,
            start_timestamp=observations[0]["timestamp"],
            end_timestamp=observations[-1]["timestamp"],
            duration_seconds=observations[-1]["timestamp"]
            - observations[0]["timestamp"],
            participating_track_ids=[track_id_a, track_id_b],
            min_distance=min(distances),
            max_distance=max(distances),
            avg_distance=sum(distances) / len(distances),
            confidence=self._calculate_confidence(observations, "departure"),
            evidence={
                "initial_distance": distances[0],
                "final_distance": distances[-1],
                "change_rate": change_rate,
                "distance_increase": distances[-1] - distances[0],
            },
            explanation=f"Tracks #{track_id_a} and #{track_id_b} moved apart from {distances[0]:.1f}px to {distances[-1]:.1f}px over {observations[-1]['timestamp'] - observations[0]['timestamp']:.1f} seconds (rate: {change_rate:.1f}px/obs).",
        )

    def _is_co_movement(self, observations: List[Dict]) -> bool:
        """Check if observations indicate co-movement"""
        if len(observations) < 3:
            return False

        # Check distance stability
        distances = [obs["distance"] for obs in observations]
        distance_variance = max(distances) - min(distances)

        if distance_variance > 100.0:  # Distance varies too much
            return False

        # Check movement similarity
        similar_count = 0
        for obs in observations[-5:]:  # Check recent observations
            dir_a = obs.get("direction_a")
            dir_b = obs.get("direction_b")
            speed_a = obs.get("speed_a", 0.0)
            speed_b = obs.get("speed_b", 0.0)

            if dir_a is not None and dir_b is not None:
                if self.spatial.movement_similarity(
                    dir_a,
                    speed_a,
                    dir_b,
                    speed_b,
                    self.config.direction_similarity_threshold,
                    self.config.speed_similarity_threshold,
                ):
                    similar_count += 1

        return similar_count >= 3  # Majority of recent observations

    def _create_co_movement_relationship(
        self, track_id_a: str, track_id_b: str, observations: List[Dict]
    ) -> Optional[Relationship]:
        """Create co-movement relationship"""
        distances = [obs["distance"] for obs in observations]

        return Relationship(
            relationship_id=str(uuid.uuid4()),
            relationship_type=RelationshipType.CO_MOVEMENT_EVENT,
            start_timestamp=observations[0]["timestamp"],
            end_timestamp=observations[-1]["timestamp"],
            duration_seconds=observations[-1]["timestamp"]
            - observations[0]["timestamp"],
            participating_track_ids=[track_id_a, track_id_b],
            min_distance=min(distances),
            max_distance=max(distances),
            avg_distance=sum(distances) / len(distances),
            confidence=self._calculate_confidence(observations, "co_movement"),
            evidence={
                "observation_count": len(observations),
                "distance_stability": max(distances) - min(distances),
                "avg_distance": sum(distances) / len(distances),
            },
            explanation=f"Tracks #{track_id_a} and #{track_id_b} moved together maintaining similar directions and speeds for {observations[-1]['timestamp'] - observations[0]['timestamp']:.1f} seconds. Avg distance: {sum(distances)/len(distances):.1f}px.",
        )

    def _is_following_pattern(
        self, observations: List[Dict], track_id_a: str, track_id_b: str
    ) -> bool:
        """Check if A is following B (or vice versa)"""
        min_obs = max(self.config.min_observations, 3)  # Need at least 3 for pattern
        if len(observations) < min_obs:
            return False

        # Check distance is in following range
        distances = [obs["distance"] for obs in observations]
        avg_distance = sum(distances) / len(distances)
        
        if not (
            self.config.following_distance_min
            <= avg_distance
            <= self.config.following_distance_max
        ):
            return False

        # Check trajectory alignment for multiple observations
        # Need to check BOTH directions: A following B OR B following A
        alignment_count_a_to_b = 0
        alignment_count_b_to_a = 0
        
        # Use all available observations for alignment check
        for obs in observations:
            pos_a = obs["pos_a"]
            pos_b = obs["pos_b"]
            dir_a = obs.get("direction_a")
            dir_b = obs.get("direction_b")

            # Check if A's direction aligns toward B (A following B)
            if dir_a is not None:
                if self.spatial.trajectory_alignment(
                    pos_a, dir_a, pos_b, self.config.following_direction_threshold
                ):
                    alignment_count_a_to_b += 1

            # Check if B's direction aligns toward A (B following A)
            if dir_b is not None:
                if self.spatial.trajectory_alignment(
                    pos_b, dir_b, pos_a, self.config.following_direction_threshold
                ):
                    alignment_count_b_to_a += 1

        # Require at least 2 aligned observations (or majority if we have few observations)
        min_alignments = min(2, max(1, len(observations) // 2))
        return (alignment_count_a_to_b >= min_alignments) or (alignment_count_b_to_a >= min_alignments)

    def _create_following_relationship(
        self, track_id_a: str, track_id_b: str, observations: List[Dict]
    ) -> Optional[Relationship]:
        """Create following pattern relationship"""
        distances = [obs["distance"] for obs in observations]

        return Relationship(
            relationship_id=str(uuid.uuid4()),
            relationship_type=RelationshipType.FOLLOWING_PATTERN,
            start_timestamp=observations[0]["timestamp"],
            end_timestamp=observations[-1]["timestamp"],
            duration_seconds=observations[-1]["timestamp"]
            - observations[0]["timestamp"],
            participating_track_ids=[track_id_a, track_id_b],
            min_distance=min(distances),
            max_distance=max(distances),
            avg_distance=sum(distances) / len(distances),
            confidence=self._calculate_confidence(observations, "following"),
            evidence={
                "observation_count": len(observations),
                "avg_distance": sum(distances) / len(distances),
                "pattern_type": "trajectory_following",
            },
            explanation=f"Track #{track_id_a} exhibited a following pattern relative to Track #{track_id_b} for {observations[-1]['timestamp'] - observations[0]['timestamp']:.1f} seconds. Note: This is a spatial/temporal pattern, not proof of intent. Avg distance: {sum(distances)/len(distances):.1f}px.",
        )

    def _create_group_formation(
        self, track_ids: List[str], timestamp: float
    ) -> Optional[Relationship]:
        """Create group formation relationship"""
        return Relationship(
            relationship_id=str(uuid.uuid4()),
            relationship_type=RelationshipType.GROUP_FORMATION,
            start_timestamp=timestamp,
            end_timestamp=timestamp,
            duration_seconds=0.0,  # Instantaneous detection
            participating_track_ids=track_ids,
            min_distance=0.0,
            max_distance=self.config.group_proximity_radius,
            avg_distance=self.config.group_proximity_radius / 2,  # Approximation
            confidence=0.7,  # Conservative for group formation
            evidence={
                "group_size": len(track_ids),
                "proximity_radius": self.config.group_proximity_radius,
                "connection_type": "spatial_proximity",
            },
            explanation=f"Group of {len(track_ids)} entities formed (Tracks: {', '.join(f'#{tid}' for tid in track_ids)}). Entities are spatially connected within {self.config.group_proximity_radius:.0f}px radius.",
        )

    def _calculate_confidence(
        self, observations: List[Dict], relationship_type: str
    ) -> float:
        """
        Calculate deterministic confidence score
        
        Based on:
        - Number of observations (more = higher confidence)
        - Consistency of pattern
        - Duration
        
        Args:
            observations: List of observations
            relationship_type: Type of relationship
            
        Returns:
            Confidence score (0-1)
        """
        # Base confidence from observation count
        obs_count = len(observations)
        base_confidence = min(1.0, obs_count / 20.0)  # Max at 20 observations

        # Duration bonus
        duration = observations[-1]["timestamp"] - observations[0]["timestamp"]
        duration_bonus = min(0.2, duration / 10.0)  # Max 0.2 bonus for 10+ seconds

        confidence = min(1.0, base_confidence + duration_bonus)
        return round(confidence, 3)

    def get_statistics(self) -> Dict:
        """Get detector statistics"""
        return {
            "tracked_pairs": len(self.pair_history),
            "proximity_radius": self.config.proximity_radius,
            "interaction_radius": self.config.interaction_radius,
            "min_observations": self.config.min_observations,
        }
