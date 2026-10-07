"""
Spatial reasoning utilities for multi-entity interactions.

Provides coordinate-independent spatial calculations.
"""

import math
from typing import List, Tuple, Set


class SpatialReasoning:
    """
    Reusable spatial calculations for entity relationships
    
    IMPORTANT: All calculations operate in pixel coordinates.
    Do NOT claim these represent real-world meters or distances.
    """

    @staticmethod
    def euclidean_distance(pos1: List[float], pos2: List[float]) -> float:
        """
        Calculate Euclidean distance between two positions
        
        Args:
            pos1: [x, y] position
            pos2: [x, y] position
            
        Returns:
            Distance in pixels
        """
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        return math.sqrt(dx * dx + dy * dy)

    @staticmethod
    def relative_displacement(pos1: List[float], pos2: List[float]) -> Tuple[float, float]:
        """
        Calculate relative displacement vector from pos1 to pos2
        
        Args:
            pos1: [x, y] starting position
            pos2: [x, y] ending position
            
        Returns:
            (dx, dy) displacement vector
        """
        return (pos2[0] - pos1[0], pos2[1] - pos1[1])

    @staticmethod
    def direction_difference(dir1: float, dir2: float) -> float:
        """
        Calculate minimum angular difference between two directions
        
        Handles wraparound (e.g., 350° and 10° are 20° apart, not 340°)
        
        Args:
            dir1: Direction in degrees (0-360)
            dir2: Direction in degrees (0-360)
            
        Returns:
            Absolute angular difference in degrees (0-180)
        """
        diff = abs(dir2 - dir1)
        if diff > 180:
            diff = 360 - diff
        return diff

    @staticmethod
    def normalize_pair_id(track_id_a: str, track_id_b: str) -> Tuple[str, str]:
        """
        Normalize pair ID so (A, B) and (B, A) are treated as same pair
        
        Args:
            track_id_a: First track ID
            track_id_b: Second track ID
            
        Returns:
            Normalized (min_id, max_id) tuple
        """
        # Sort alphabetically/numerically to ensure consistency
        if str(track_id_a) <= str(track_id_b):
            return (track_id_a, track_id_b)
        else:
            return (track_id_b, track_id_a)

    @staticmethod
    def temporal_distance_change(distances: List[float]) -> float:
        """
        Calculate rate of distance change over time
        
        Args:
            distances: List of distances ordered by time
            
        Returns:
            Average change per observation (negative = approaching, positive = departing)
        """
        if len(distances) < 2:
            return 0.0

        changes = []
        for i in range(1, len(distances)):
            changes.append(distances[i] - distances[i - 1])

        return sum(changes) / len(changes)

    @staticmethod
    def is_approaching(distances: List[float], threshold: float = -5.0) -> bool:
        """
        Determine if entities are approaching based on distance history
        
        Args:
            distances: List of distances ordered by time
            threshold: Negative value indicating approach rate (pixels per observation)
            
        Returns:
            True if consistently approaching
        """
        if len(distances) < 3:
            return False

        change_rate = SpatialReasoning.temporal_distance_change(distances)
        return change_rate < threshold

    @staticmethod
    def is_departing(distances: List[float], threshold: float = 5.0) -> bool:
        """
        Determine if entities are departing based on distance history
        
        Args:
            distances: List of distances ordered by time
            threshold: Positive value indicating departure rate (pixels per observation)
            
        Returns:
            True if consistently departing
        """
        if len(distances) < 3:
            return False

        change_rate = SpatialReasoning.temporal_distance_change(distances)
        return change_rate > threshold

    @staticmethod
    def connected_group(entities: Set[str], proximity_map: dict) -> Set[str]:
        """
        Find all entities in a connected group using proximity relationships
        
        Uses graph connectivity: A-B-C forms one group even if A and C aren't directly close
        
        Args:
            entities: Set of entity IDs to check
            proximity_map: Dict mapping entity_id to set of nearby entity_ids
            
        Returns:
            Set of all connected entities
        """
        if not entities:
            return set()

        # Start with first entity
        group = set()
        to_visit = {next(iter(entities))}

        # Breadth-first search for connected entities
        while to_visit:
            current = to_visit.pop()
            if current in group:
                continue

            group.add(current)

            # Add neighbors that are in our entities set
            neighbors = proximity_map.get(current, set())
            for neighbor in neighbors:
                if neighbor in entities and neighbor not in group:
                    to_visit.add(neighbor)

        return group

    @staticmethod
    def movement_similarity(
        dir1: float,
        speed1: float,
        dir2: float,
        speed2: float,
        direction_threshold: float = 30.0,
        speed_threshold: float = 50.0,
    ) -> bool:
        """
        Check if two entities have similar movement patterns
        
        Args:
            dir1: Direction of entity 1 (degrees)
            speed1: Speed of entity 1 (pixels/sec)
            dir2: Direction of entity 2 (degrees)
            speed2: Speed of entity 2 (pixels/sec)
            direction_threshold: Max direction difference for similarity (degrees)
            speed_threshold: Max speed difference for similarity (pixels/sec)
            
        Returns:
            True if movements are similar
        """
        dir_diff = SpatialReasoning.direction_difference(dir1, dir2)
        speed_diff = abs(speed2 - speed1)

        return dir_diff <= direction_threshold and speed_diff <= speed_threshold

    @staticmethod
    def trajectory_alignment(
        pos_a: List[float],
        dir_a: float,
        pos_b: List[float],
        alignment_threshold: float = 45.0,
    ) -> bool:
        """
        Check if entity A's direction aligns with the direction toward entity B
        
        Useful for detecting following patterns.
        
        Args:
            pos_a: Position of entity A [x, y]
            dir_a: Direction of entity A (degrees)
            pos_b: Position of entity B [x, y]
            alignment_threshold: Max angular difference for alignment (degrees)
            
        Returns:
            True if A's direction points toward B
        """
        # Calculate direction from A to B
        dx = pos_b[0] - pos_a[0]
        dy = pos_b[1] - pos_a[1]

        if dx == 0 and dy == 0:
            return False  # Same position

        # Convert to degrees (0° = right, 90° = down in typical screen coordinates)
        dir_to_b = math.degrees(math.atan2(dy, dx))
        if dir_to_b < 0:
            dir_to_b += 360

        # Check alignment
        dir_diff = SpatialReasoning.direction_difference(dir_a, dir_to_b)
        return dir_diff <= alignment_threshold
