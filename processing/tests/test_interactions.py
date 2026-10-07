"""
Tests for multi-entity interaction detection (Milestone 6)

Covers:
- Spatial reasoning utilities
- Proximity detection
- Approach/departure detection
- Co-movement detection
- Following patterns
- Group formation/separation
- Pair normalization
- Temporal evidence requirements
"""

import pytest
import math
from processing.interactions.spatial import SpatialReasoning
from processing.interactions.detector import (
    InteractionDetector,
    InteractionConfig,
    RelationshipType,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def spatial():
    """Spatial reasoning instance"""
    return SpatialReasoning()


@pytest.fixture
def default_detector():
    """Interaction detector with default config"""
    return InteractionDetector()


@pytest.fixture
def custom_detector():
    """Interaction detector with custom config"""
    config = InteractionConfig(
        proximity_radius=100.0,
        interaction_radius=150.0,
        min_interaction_duration=1.0,
        min_observations=3,
        approach_rate_threshold=-3.0,
        departure_rate_threshold=3.0,
    )
    return InteractionDetector(config)


# ============================================================================
# Test: Spatial Reasoning - Distance
# ============================================================================


def test_euclidean_distance(spatial):
    """Test Euclidean distance calculation"""
    pos1 = [0, 0]
    pos2 = [3, 4]

    distance = spatial.euclidean_distance(pos1, pos2)

    assert distance == 5.0  # 3-4-5 triangle


def test_euclidean_distance_same_position(spatial):
    """Test distance when positions are identical"""
    pos = [100, 200]

    distance = spatial.euclidean_distance(pos, pos)

    assert distance == 0.0


def test_relative_displacement(spatial):
    """Test relative displacement calculation"""
    pos1 = [10, 20]
    pos2 = [15, 28]

    dx, dy = spatial.relative_displacement(pos1, pos2)

    assert dx == 5.0
    assert dy == 8.0


# ============================================================================
# Test: Spatial Reasoning - Direction
# ============================================================================


def test_direction_difference_simple(spatial):
    """Test direction difference for simple angles"""
    diff = spatial.direction_difference(0, 90)
    assert diff == 90.0


def test_direction_difference_wraparound(spatial):
    """Test direction difference with wraparound (350° to 10°)"""
    diff = spatial.direction_difference(350, 10)
    assert diff == 20.0  # Not 340°


def test_direction_difference_180(spatial):
    """Test direction difference of 180°"""
    diff = spatial.direction_difference(0, 180)
    assert diff == 180.0


# ============================================================================
# Test: Pair Normalization
# ============================================================================


def test_normalize_pair_id_order(spatial):
    """Test pair ID normalization maintains consistency"""
    pair1 = spatial.normalize_pair_id("7", "12")
    pair2 = spatial.normalize_pair_id("12", "7")

    assert pair1 == pair2
    assert pair1 == ("12", "7")  # Sorted order


def test_normalize_pair_id_already_sorted(spatial):
    """Test normalization when already in correct order"""
    pair = spatial.normalize_pair_id("3", "8")

    assert pair == ("3", "8")


# ============================================================================
# Test: Temporal Distance Change
# ============================================================================


def test_temporal_distance_change_approaching(spatial):
    """Test distance change for approaching entities"""
    distances = [200, 180, 160, 140, 120]

    change = spatial.temporal_distance_change(distances)

    assert change < 0  # Negative = approaching
    assert change == -20.0


def test_temporal_distance_change_departing(spatial):
    """Test distance change for departing entities"""
    distances = [100, 120, 140, 160, 180]

    change = spatial.temporal_distance_change(distances)

    assert change > 0  # Positive = departing
    assert change == 20.0


def test_temporal_distance_change_stable(spatial):
    """Test distance change for stable distance"""
    distances = [150, 148, 152, 150, 151]

    change = spatial.temporal_distance_change(distances)

    assert abs(change) < 1.0  # Nearly stable


# ============================================================================
# Test: Approaching/Departing Detection
# ============================================================================


def test_is_approaching(spatial):
    """Test approaching detection"""
    distances = [200, 180, 160, 140, 120, 100]

    assert spatial.is_approaching(distances, threshold=-5.0)


def test_is_not_approaching_stable(spatial):
    """Test not approaching when distance stable"""
    distances = [150, 148, 152, 150, 151, 149]

    assert not spatial.is_approaching(distances, threshold=-5.0)


def test_is_departing(spatial):
    """Test departing detection"""
    distances = [100, 120, 140, 160, 180, 200]

    assert spatial.is_departing(distances, threshold=5.0)


def test_is_not_departing_stable(spatial):
    """Test not departing when distance stable"""
    distances = [150, 148, 152, 150, 151, 149]

    assert not spatial.is_departing(distances, threshold=5.0)


def test_approaching_insufficient_data(spatial):
    """Test approaching requires minimum observations"""
    distances = [200, 180]  # Only 2 observations

    assert not spatial.is_approaching(distances)


# ============================================================================
# Test: Movement Similarity
# ============================================================================


def test_movement_similarity_true(spatial):
    """Test movement similarity when entities move similarly"""
    similar = spatial.movement_similarity(
        dir1=45.0,
        speed1=100.0,
        dir2=50.0,
        speed2=110.0,
        direction_threshold=30.0,
        speed_threshold=50.0,
    )

    assert similar is True


def test_movement_similarity_direction_different(spatial):
    """Test movement not similar when directions differ"""
    similar = spatial.movement_similarity(
        dir1=0.0,
        speed1=100.0,
        dir2=90.0,  # 90° different
        speed2=100.0,
        direction_threshold=30.0,
        speed_threshold=50.0,
    )

    assert similar is False


def test_movement_similarity_speed_different(spatial):
    """Test movement not similar when speeds differ"""
    similar = spatial.movement_similarity(
        dir1=45.0,
        speed1=50.0,
        dir2=45.0,
        speed2=150.0,  # 100 px/s different
        direction_threshold=30.0,
        speed_threshold=50.0,
    )

    assert similar is False


# ============================================================================
# Test: Trajectory Alignment
# ============================================================================


def test_trajectory_alignment_true(spatial):
    """Test trajectory alignment when A points toward B"""
    # A at (0,0), direction 45° (northeast)
    # B at (10,10) (also northeast of A)
    aligned = spatial.trajectory_alignment(
        pos_a=[0, 0], dir_a=45.0, pos_b=[10, 10], alignment_threshold=45.0
    )

    assert aligned is True


def test_trajectory_alignment_false(spatial):
    """Test trajectory not aligned when A points away from B"""
    # A at (0,0), direction 180° (west)
    # B at (10,0) (east of A)
    aligned = spatial.trajectory_alignment(
        pos_a=[0, 0], dir_a=180.0, pos_b=[10, 0], alignment_threshold=45.0
    )

    assert aligned is False


# ============================================================================
# Test: Connected Group
# ============================================================================


def test_connected_group_simple(spatial):
    """Test connected group with direct connections"""
    entities = {"A", "B", "C"}
    proximity_map = {"A": {"B"}, "B": {"A", "C"}, "C": {"B"}}

    group = spatial.connected_group(entities, proximity_map)

    assert group == {"A", "B", "C"}


def test_connected_group_indirect(spatial):
    """Test connected group with indirect connections (A-B-C)"""
    entities = {"A", "B", "C"}
    # A close to B, B close to C, but A and C not directly close
    proximity_map = {"A": {"B"}, "B": {"A", "C"}, "C": {"B"}}

    group = spatial.connected_group(entities, proximity_map)

    # All should be in same group due to connectivity
    assert group == {"A", "B", "C"}


def test_connected_group_empty(spatial):
    """Test connected group with empty input"""
    group = spatial.connected_group(set(), {})

    assert group == set()


# ============================================================================
# Test: Interaction Detector - Empty/Single Entity
# ============================================================================


def test_detect_empty_behaviors(default_detector):
    """Test detection with empty behavior list"""
    relationships = default_detector.detect([])

    assert relationships == []


def test_detect_single_entity(default_detector):
    """Test detection with single entity"""
    behaviors = [
        {
            "track_id": "1",
            "timestamp": 1.0,
            "position": [100, 100],
            "speed": 50.0,
            "direction": 45.0,
        }
    ]

    relationships = default_detector.detect(behaviors)

    # Single entity cannot have interactions
    assert relationships == []


# ============================================================================
# Test: Proximity Detection
# ============================================================================


def test_proximity_detection(custom_detector):
    """Test proximity relationship detection"""
    # Custom config: proximity_radius=100.0, min_observations=3
    behaviors_list = []

    # Create 5 observations of two entities staying close
    for i in range(5):
        behaviors_list.append(
            [
                {
                    "track_id": "1",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [100, 100],
                    "speed": 10.0,
                    "direction": 0.0,
                },
                {
                    "track_id": "2",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [150, 100],  # 50 pixels away
                    "speed": 10.0,
                    "direction": 0.0,
                },
            ]
        )

    # Process all observations
    all_relationships = []
    for behaviors in behaviors_list:
        rels = custom_detector.detect(behaviors)
        all_relationships.extend(rels)

    # Should detect proximity (50px < 100px radius)
    proximity_rels = [
        r for r in all_relationships if r.relationship_type == RelationshipType.PROXIMITY_EVENT
    ]
    assert len(proximity_rels) >= 1


def test_no_proximity_when_far(custom_detector):
    """Test no proximity when entities are far apart"""
    behaviors_list = []

    # Entities far apart (200px > 100px proximity radius)
    for i in range(5):
        behaviors_list.append(
            [
                {
                    "track_id": "1",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [100, 100],
                    "speed": 10.0,
                    "direction": 0.0,
                },
                {
                    "track_id": "2",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [300, 100],  # 200 pixels away
                    "speed": 10.0,
                    "direction": 0.0,
                },
            ]
        )

    all_relationships = []
    for behaviors in behaviors_list:
        rels = custom_detector.detect(behaviors)
        all_relationships.extend(rels)

    # Should not detect proximity (too far)
    proximity_rels = [
        r for r in all_relationships if r.relationship_type == RelationshipType.PROXIMITY_EVENT
    ]
    assert len(proximity_rels) == 0


# ============================================================================
# Test: Approach Detection
# ============================================================================


def test_approach_detection(custom_detector):
    """Test approach relationship detection"""
    behaviors_list = []

    # Two entities approaching each other
    distances = [200, 180, 160, 140, 120, 100]
    for i, dist in enumerate(distances):
        behaviors_list.append(
            [
                {
                    "track_id": "3",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [100, 100],
                    "speed": 20.0,
                    "direction": 0.0,
                },
                {
                    "track_id": "4",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [100 + dist, 100],
                    "speed": 20.0,
                    "direction": 180.0,
                },
            ]
        )

    all_relationships = []
    for behaviors in behaviors_list:
        rels = custom_detector.detect(behaviors)
        all_relationships.extend(rels)

    # Should detect approach
    approach_rels = [
        r for r in all_relationships if r.relationship_type == RelationshipType.APPROACH_EVENT
    ]
    assert len(approach_rels) >= 1


# ============================================================================
# Test: Departure Detection
# ============================================================================


def test_departure_detection(custom_detector):
    """Test departure relationship detection"""
    behaviors_list = []

    # Two entities moving apart
    distances = [80, 100, 120, 140, 160, 180]
    for i, dist in enumerate(distances):
        behaviors_list.append(
            [
                {
                    "track_id": "5",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [100, 100],
                    "speed": 20.0,
                    "direction": 0.0,
                },
                {
                    "track_id": "6",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [100 + dist, 100],
                    "speed": 20.0,
                    "direction": 0.0,
                },
            ]
        )

    all_relationships = []
    for behaviors in behaviors_list:
        rels = custom_detector.detect(behaviors)
        all_relationships.extend(rels)

    # Should detect departure
    departure_rels = [
        r for r in all_relationships if r.relationship_type == RelationshipType.DEPARTURE_EVENT
    ]
    assert len(departure_rels) >= 1


# ============================================================================
# Test: Co-Movement Detection
# ============================================================================


def test_co_movement_detection(custom_detector):
    """Test co-movement relationship detection"""
    behaviors_list = []

    # Two entities moving together with similar speed/direction
    for i in range(10):
        x_offset = i * 10  # Both moving right
        behaviors_list.append(
            [
                {
                    "track_id": "7",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [100 + x_offset, 100],
                    "speed": 20.0,
                    "direction": 0.0,  # Moving right
                },
                {
                    "track_id": "8",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [100 + x_offset, 180],  # Parallel, 80px apart
                    "speed": 22.0,  # Similar speed
                    "direction": 5.0,  # Similar direction
                },
            ]
        )

    all_relationships = []
    for behaviors in behaviors_list:
        rels = custom_detector.detect(behaviors)
        all_relationships.extend(rels)

    # Should detect co-movement
    co_move_rels = [
        r
        for r in all_relationships
        if r.relationship_type == RelationshipType.CO_MOVEMENT_EVENT
    ]
    assert len(co_move_rels) >= 1


# ============================================================================
# Test: Following Pattern Detection
# ============================================================================


def test_following_pattern_detection(custom_detector):
    """Test following pattern detection"""
    # Track 9 follows Track 10
    # Process observations to build history
    for i in range(10):
        x_offset = i * 10
        behaviors = [
            {
                "track_id": "10",  # Leader
                "timestamp": 1.0 + i * 0.5,
                "position": [100 + x_offset, 100],
                "speed": 20.0,
                "direction": 0.0,  # Moving right
            },
            {
                "track_id": "9",  # Follower
                "timestamp": 1.0 + i * 0.5,
                "position": [50 + x_offset, 100],  # Behind, 50px
                "speed": 20.0,
                "direction": 0.0,  # Same direction
            },
        ]
        custom_detector.detect(behaviors)

    # Check the pair history has enough observations
    pair_id = custom_detector.spatial.normalize_pair_id("9", "10")
    assert pair_id in custom_detector.pair_history
    assert len(custom_detector.pair_history[pair_id]) >= 5

    # Now detect with final observation batch
    final_behaviors = [
        {
            "track_id": "10",
            "timestamp": 6.0,
            "position": [200, 100],
            "speed": 20.0,
            "direction": 0.0,
        },
        {
            "track_id": "9",
            "timestamp": 6.0,
            "position": [150, 100],
            "speed": 20.0,
            "direction": 0.0,
        },
    ]

    relationships = custom_detector.detect(final_behaviors)

    # Should detect following pattern
    following_rels = [
        r
        for r in relationships
        if r.relationship_type == RelationshipType.FOLLOWING_PATTERN
    ]
    assert len(following_rels) >= 1


# ============================================================================
# Test: Group Formation
# ============================================================================


def test_group_formation_three_entities(default_detector):
    """Test group formation with 3 entities"""
    # Default config has group_proximity_radius=180.0, group_min_size=3
    behaviors = [
        {
            "track_id": "11",
            "timestamp": 5.0,
            "position": [100, 100],
            "speed": 5.0,
            "direction": 0.0,
        },
        {
            "track_id": "12",
            "timestamp": 5.0,
            "position": [180, 100],  # 80px from 11
            "speed": 5.0,
            "direction": 0.0,
        },
        {
            "track_id": "13",
            "timestamp": 5.0,
            "position": [180, 180],  # 80px from 12
            "speed": 5.0,
            "direction": 0.0,
        },
    ]

    relationships = default_detector.detect(behaviors)

    # Should detect group formation
    group_rels = [
        r for r in relationships if r.relationship_type == RelationshipType.GROUP_FORMATION
    ]
    assert len(group_rels) >= 1, f"Expected group formation, got {len(group_rels)} (relationships: {[r.relationship_type for r in relationships]})"

    if group_rels:
        assert len(group_rels[0].participating_track_ids) == 3


def test_group_formation_connected_group(default_detector):
    """Test group formation with connected but not all pairwise close"""
    # Default config: group_proximity_radius=180.0
    behaviors = [
        {
            "track_id": "14",
            "timestamp": 5.0,
            "position": [100, 100],
            "speed": 5.0,
            "direction": 0.0,
        },
        {
            "track_id": "15",
            "timestamp": 5.0,
            "position": [200, 100],  # 100px from 14 (close)
            "speed": 5.0,
            "direction": 0.0,
        },
        {
            "track_id": "16",
            "timestamp": 5.0,
            "position": [280, 100],  # 80px from 15, 180px from 14
            "speed": 5.0,
            "direction": 0.0,
        },
    ]

    relationships = default_detector.detect(behaviors)

    # Should still form one connected group (14-15-16)
    group_rels = [
        r for r in relationships if r.relationship_type == RelationshipType.GROUP_FORMATION
    ]
    assert len(group_rels) >= 1, f"Expected connected group, got {len(group_rels)}"


# ============================================================================
# Test: Multiple Independent Pairs
# ============================================================================


def test_multiple_independent_pairs(custom_detector):
    """Test detection with multiple independent pairs"""
    behaviors_list = []

    # Two separate pairs of entities
    for i in range(5):
        behaviors_list.append(
            [
                # Pair 1: tracks 20 and 21
                {
                    "track_id": "20",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [100, 100],
                    "speed": 10.0,
                    "direction": 0.0,
                },
                {
                    "track_id": "21",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [150, 100],  # Close to 20
                    "speed": 10.0,
                    "direction": 0.0,
                },
                # Pair 2: tracks 22 and 23 (far from pair 1)
                {
                    "track_id": "22",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [500, 500],
                    "speed": 10.0,
                    "direction": 0.0,
                },
                {
                    "track_id": "23",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [550, 500],  # Close to 22
                    "speed": 10.0,
                    "direction": 0.0,
                },
            ]
        )

    all_relationships = []
    for behaviors in behaviors_list:
        rels = custom_detector.detect(behaviors)
        all_relationships.extend(rels)

    # Should detect relationships for both pairs
    pairs_detected = set()
    for rel in all_relationships:
        pairs_detected.add(tuple(sorted(rel.participating_track_ids)))

    assert ("20", "21") in pairs_detected
    assert ("22", "23") in pairs_detected


# ============================================================================
# Test: Temporal Requirements
# ============================================================================


def test_no_relationship_from_single_frame(custom_detector):
    """Test that single close frame doesn't create relationship"""
    # Custom config: min_observations=3

    # Only 1 observation (not enough)
    behaviors = [
        {
            "track_id": "30",
            "timestamp": 1.0,
            "position": [100, 100],
            "speed": 10.0,
            "direction": 0.0,
        },
        {
            "track_id": "31",
            "timestamp": 1.0,
            "position": [120, 100],  # Very close
            "speed": 10.0,
            "direction": 0.0,
        },
    ]

    relationships = custom_detector.detect(behaviors)

    # Should not create relationship (need min_observations=3)
    assert len(relationships) == 0


def test_relationship_requires_min_observations(custom_detector):
    """Test relationship requires minimum observations"""
    behaviors_list = []

    # Only 2 observations (need 3)
    for i in range(2):
        behaviors_list.append(
            [
                {
                    "track_id": "32",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [100, 100],
                    "speed": 10.0,
                    "direction": 0.0,
                },
                {
                    "track_id": "33",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [130, 100],
                    "speed": 10.0,
                    "direction": 0.0,
                },
            ]
        )

    all_relationships = []
    for behaviors in behaviors_list:
        rels = custom_detector.detect(behaviors)
        all_relationships.extend(rels)

    # Should not create relationship yet (only 2 observations)
    assert len(all_relationships) == 0


# ============================================================================
# Test: Relationship Serialization
# ============================================================================


def test_relationship_serialization(custom_detector):
    """Test relationship to_dict() produces complete structure"""
    behaviors_list = []

    for i in range(5):
        behaviors_list.append(
            [
                {
                    "track_id": "40",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [100, 100],
                    "speed": 10.0,
                    "direction": 0.0,
                },
                {
                    "track_id": "41",
                    "timestamp": 1.0 + i * 0.5,
                    "position": [140, 100],
                    "speed": 10.0,
                    "direction": 0.0,
                },
            ]
        )

    all_relationships = []
    for behaviors in behaviors_list:
        rels = custom_detector.detect(behaviors)
        all_relationships.extend(rels)

    if all_relationships:
        rel_dict = all_relationships[0].to_dict()

        # Check required fields
        required_fields = [
            "relationship_id",
            "relationship_type",
            "start_timestamp",
            "end_timestamp",
            "duration_seconds",
            "participating_track_ids",
            "min_distance",
            "max_distance",
            "avg_distance",
            "confidence",
            "evidence",
            "explanation",
        ]

        for field in required_fields:
            assert field in rel_dict

        # Check types
        assert isinstance(rel_dict["relationship_id"], str)
        assert isinstance(rel_dict["relationship_type"], str)
        assert isinstance(rel_dict["participating_track_ids"], list)
        assert isinstance(rel_dict["confidence"], float)
        assert isinstance(rel_dict["evidence"], dict)


# ============================================================================
# Test: Configurable Thresholds
# ============================================================================


def test_configurable_proximity_radius():
    """Test proximity detection with different radius"""
    config1 = InteractionConfig(proximity_radius=50.0, min_observations=3, min_interaction_duration=1.0)
    detector1 = InteractionDetector(config1)

    config2 = InteractionConfig(proximity_radius=150.0, min_observations=3, min_interaction_duration=1.0)
    detector2 = InteractionDetector(config2)

    # Entities 100px apart - process multiple observations
    for i in range(5):
        behaviors = [
            {
                "track_id": "50",
                "timestamp": 1.0 + i * 0.5,
                "position": [100, 100],
                "speed": 10.0,
                "direction": 0.0,
            },
            {
                "track_id": "51",
                "timestamp": 1.0 + i * 0.5,
                "position": [200, 100],  # 100px away
                "speed": 10.0,
                "direction": 0.0,
            },
        ]
        detector1.detect(behaviors)
        detector2.detect(behaviors)

    # Final detection
    final_behaviors = [
        {
            "track_id": "50",
            "timestamp": 3.5,
            "position": [100, 100],
            "speed": 10.0,
            "direction": 0.0,
        },
        {
            "track_id": "51",
            "timestamp": 3.5,
            "position": [200, 100],
            "speed": 10.0,
            "direction": 0.0,
        },
    ]

    rels1 = detector1.detect(final_behaviors)
    rels2 = detector2.detect(final_behaviors)

    proximity1 = [
        r for r in rels1 if r.relationship_type == RelationshipType.PROXIMITY_EVENT
    ]
    proximity2 = [
        r for r in rels2 if r.relationship_type == RelationshipType.PROXIMITY_EVENT
    ]

    assert len(proximity1) == 0, "100px should be too far for 50px radius"
    assert len(proximity2) >= 1, "100px should be within 150px radius"


# ============================================================================
# Test: Statistics
# ============================================================================


def test_get_statistics(default_detector):
    """Test get_statistics method"""
    stats = default_detector.get_statistics()

    assert "tracked_pairs" in stats
    assert "proximity_radius" in stats
    assert "interaction_radius" in stats
    assert "min_observations" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
