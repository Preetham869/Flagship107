"""
Tests for event correlation module (Milestone 5)

Covers:
- Temporal grouping
- Deduplication
- Event type detection
- Multi-track separation
- Severity/confidence calculation
- Edge cases
"""

import pytest
from processing.events.correlator import (
    EventCorrelator,
    EventConfig,
    EventType,
    EventSeverity,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def default_correlator():
    """Event correlator with default config"""
    return EventCorrelator()


@pytest.fixture
def custom_correlator():
    """Event correlator with custom config"""
    config = EventConfig(
        temporal_window=10.0,
        min_loitering_duration=3.0,
        min_high_speed_count=2,
        min_movement_sequence=2,
        max_repeated_anomalies=3,
    )
    return EventCorrelator(config)


# ============================================================================
# Test: Empty and Single Anomaly
# ============================================================================


def test_empty_anomalies(default_correlator):
    """Test with empty anomaly list"""
    events = default_correlator.correlate([])
    assert events == []


def test_single_anomaly_no_correlation(default_correlator):
    """Test single anomaly that doesn't meet event criteria"""
    anomalies = [
        {
            "event_id": "anom_001",
            "track_id": "1",
            "frame_id": 10,
            "timestamp": 1.0,
            "anomaly_type": "unusual_speed",
            "severity": "low",
            "anomaly_score": 0.6,
            "evidence": {"observed_speed": 180.0},
            "observed_value": 180.0,
            "threshold": 150.0,
            "current_behavior_state": "moving",
            "explanation": "High speed",
        }
    ]

    events = default_correlator.correlate(anomalies)

    # Single speed anomaly doesn't meet min_high_speed_count (default 3)
    assert len(events) == 0


# ============================================================================
# Test: Temporal Grouping
# ============================================================================


def test_temporal_grouping_within_window(custom_correlator):
    """Test anomalies within temporal window are grouped"""
    # Custom config has temporal_window=10.0s
    anomalies = [
        {
            "event_id": f"anom_{i}",
            "track_id": "1",
            "frame_id": 10 + i,
            "timestamp": 1.0 + i * 2.0,  # 1s, 3s, 5s (within 10s window)
            "anomaly_type": "unusual_speed",
            "severity": "medium",
            "anomaly_score": 0.7,
            "evidence": {"observed_speed": 200.0},
            "observed_value": 200.0,
            "threshold": 150.0,
            "current_behavior_state": "fast_moving",
            "explanation": f"High speed at {1.0 + i * 2.0}s",
        }
        for i in range(3)
    ]

    events = custom_correlator.correlate(anomalies)

    # Should create one high-speed event (min_high_speed_count=2)
    assert len(events) == 1
    assert events[0].event_type == EventType.HIGH_SPEED_ACTIVITY
    assert len(events[0].source_anomaly_ids) == 3


def test_temporal_grouping_outside_window(custom_correlator):
    """Test anomalies outside temporal window are separated"""
    # Custom config has temporal_window=10.0s
    anomalies = []

    # Group 1: 1-5s
    for i in range(3):
        anomalies.append(
            {
                "event_id": f"anom_g1_{i}",
                "track_id": "1",
                "frame_id": 10 + i,
                "timestamp": 1.0 + i * 2.0,
                "anomaly_type": "unusual_speed",
                "severity": "medium",
                "anomaly_score": 0.7,
                "evidence": {"observed_speed": 200.0},
                "observed_value": 200.0,
                "threshold": 150.0,
                "current_behavior_state": "fast_moving",
                "explanation": "High speed",
            }
        )

    # Group 2: 20-24s (more than 10s gap)
    for i in range(3):
        anomalies.append(
            {
                "event_id": f"anom_g2_{i}",
                "track_id": "1",
                "frame_id": 100 + i,
                "timestamp": 20.0 + i * 2.0,
                "anomaly_type": "unusual_speed",
                "severity": "medium",
                "anomaly_score": 0.7,
                "evidence": {"observed_speed": 200.0},
                "observed_value": 200.0,
                "threshold": 150.0,
                "current_behavior_state": "fast_moving",
                "explanation": "High speed",
            }
        )

    events = custom_correlator.correlate(anomalies)

    # Should create two separate high-speed events
    assert len(events) == 2
    assert all(e.event_type == EventType.HIGH_SPEED_ACTIVITY for e in events)


# ============================================================================
# Test: Restricted Area Intrusion
# ============================================================================


def test_restricted_area_intrusion_single_entry(default_correlator):
    """Test single zone entry creates intrusion event"""
    anomalies = [
        {
            "event_id": "anom_001",
            "track_id": "2",
            "frame_id": 100,
            "timestamp": 5.0,
            "anomaly_type": "restricted_zone_entry",
            "severity": "high",
            "anomaly_score": 0.8,
            "evidence": {
                "zone_id": "zone_1",
                "zone_name": "Secure Area",
                "position": [700, 150],
            },
            "observed_value": "(700, 150)",
            "threshold": "Zone zone_1",
            "current_behavior_state": "moving",
            "explanation": "Entered zone",
        }
    ]

    events = default_correlator.correlate(anomalies)

    assert len(events) == 1
    assert events[0].event_type == EventType.RESTRICTED_AREA_INTRUSION
    assert events[0].participating_track_ids == ["2"]
    assert len(events[0].source_anomaly_ids) == 1
    assert events[0].severity == EventSeverity.HIGH


def test_restricted_area_intrusion_with_other_anomalies(default_correlator):
    """Test zone entry with other anomalies creates enhanced intrusion event"""
    anomalies = [
        # Zone entry
        {
            "event_id": "anom_001",
            "track_id": "2",
            "frame_id": 100,
            "timestamp": 5.0,
            "anomaly_type": "restricted_zone_entry",
            "severity": "high",
            "anomaly_score": 0.8,
            "evidence": {
                "zone_id": "zone_1",
                "zone_name": "Secure Area",
                "position": [700, 150],
            },
            "observed_value": "(700, 150)",
            "threshold": "Zone zone_1",
            "current_behavior_state": "moving",
            "explanation": "Entered zone",
        },
        # Unusual speed inside zone
        {
            "event_id": "anom_002",
            "track_id": "2",
            "frame_id": 110,
            "timestamp": 6.0,
            "anomaly_type": "unusual_speed",
            "severity": "medium",
            "anomaly_score": 0.7,
            "evidence": {"observed_speed": 200.0},
            "observed_value": 200.0,
            "threshold": 150.0,
            "current_behavior_state": "fast_moving",
            "explanation": "High speed",
        },
        # Direction change
        {
            "event_id": "anom_003",
            "track_id": "2",
            "frame_id": 120,
            "timestamp": 7.0,
            "anomaly_type": "sudden_direction_change",
            "severity": "medium",
            "anomaly_score": 0.65,
            "evidence": {"change_degrees": 120.0},
            "observed_value": 120.0,
            "threshold": 90.0,
            "current_behavior_state": "moving",
            "explanation": "Sharp turn",
        },
    ]

    events = default_correlator.correlate(anomalies)

    # Should have intrusion event with multiple anomalies
    intrusion_events = [
        e for e in events if e.event_type == EventType.RESTRICTED_AREA_INTRUSION
    ]
    assert len(intrusion_events) >= 1

    event = intrusion_events[0]
    assert len(event.source_anomaly_ids) >= 1
    assert "unusual_speed" in event.evidence.get("other_anomaly_types", []) or len(
        event.source_anomaly_types
    ) > 1


def test_restricted_area_deduplication(default_correlator):
    """Test repeated zone entries are consolidated"""
    # 20 repeated zone entry alerts (simulating M4 spam)
    anomalies = [
        {
            "event_id": f"anom_{i:03d}",
            "track_id": "2",
            "frame_id": 100 + i * 10,
            "timestamp": 5.0 + i * 0.5,
            "anomaly_type": "restricted_zone_entry",
            "severity": "high",
            "anomaly_score": 0.8,
            "evidence": {
                "zone_id": "zone_1",
                "zone_name": "Secure Area",
                "position": [700 + i, 150],
            },
            "observed_value": f"({700 + i}, 150)",
            "threshold": "Zone zone_1",
            "current_behavior_state": "moving",
            "explanation": "Still in zone",
        }
        for i in range(20)
    ]

    events = default_correlator.correlate(anomalies)

    # Should consolidate into 1 event, not 20
    intrusion_events = [
        e for e in events if e.event_type == EventType.RESTRICTED_AREA_INTRUSION
    ]
    assert len(intrusion_events) == 1
    assert len(intrusion_events[0].source_anomaly_ids) == 20


# ============================================================================
# Test: Loitering Events
# ============================================================================


def test_loitering_event_creation(custom_correlator):
    """Test loitering event from repeated observations"""
    # Custom config: min_loitering_duration=3.0s
    anomalies = [
        {
            "event_id": f"anom_{i:03d}",
            "track_id": "3",
            "frame_id": 200 + i * 10,
            "timestamp": 10.0 + i * 0.5,
            "anomaly_type": "loitering",
            "severity": "low",
            "anomaly_score": 0.4,
            "evidence": {
                "stationary_duration": 5.0 + i * 0.5,
                "position": [400, 300],
            },
            "observed_value": 5.0 + i * 0.5,
            "threshold": 5.0,
            "current_behavior_state": "stationary",
            "explanation": "Stationary",
        }
        for i in range(10)
    ]

    events = custom_correlator.correlate(anomalies)

    loitering_events = [
        e for e in events if e.event_type == EventType.LOITERING_EVENT
    ]
    assert len(loitering_events) == 1

    event = loitering_events[0]
    assert event.participating_track_ids == ["3"]
    assert len(event.source_anomaly_ids) == 10
    assert event.duration_seconds >= 3.0


def test_loitering_short_duration_no_event(custom_correlator):
    """Test short loitering doesn't create event"""
    # Duration less than min_loitering_duration
    anomalies = [
        {
            "event_id": "anom_001",
            "track_id": "3",
            "frame_id": 200,
            "timestamp": 10.0,
            "anomaly_type": "loitering",
            "severity": "low",
            "anomaly_score": 0.4,
            "evidence": {"stationary_duration": 5.0, "position": [400, 300]},
            "observed_value": 5.0,
            "threshold": 5.0,
            "current_behavior_state": "stationary",
            "explanation": "Stationary",
        },
        {
            "event_id": "anom_002",
            "track_id": "3",
            "frame_id": 210,
            "timestamp": 10.5,
            "anomaly_type": "loitering",
            "severity": "low",
            "anomaly_score": 0.4,
            "evidence": {"stationary_duration": 5.5, "position": [400, 300]},
            "observed_value": 5.5,
            "threshold": 5.0,
            "current_behavior_state": "stationary",
            "explanation": "Stationary",
        },
    ]

    events = custom_correlator.correlate(anomalies)

    # Duration is only 0.5s, less than min_loitering_duration=3.0s
    # And count=2 is less than max_repeated_anomalies=3
    loitering_events = [
        e for e in events if e.event_type == EventType.LOITERING_EVENT
    ]
    assert len(loitering_events) == 0


# ============================================================================
# Test: High-Speed Activity
# ============================================================================


def test_high_speed_activity(custom_correlator):
    """Test high-speed event from multiple speed anomalies"""
    # Custom config: min_high_speed_count=2
    anomalies = [
        {
            "event_id": f"anom_{i}",
            "track_id": "4",
            "frame_id": 50 + i * 10,
            "timestamp": 2.0 + i * 0.5,
            "anomaly_type": "unusual_speed",
            "severity": "high",
            "anomaly_score": 0.8,
            "evidence": {"observed_speed": 250.0},
            "observed_value": 250.0,
            "threshold": 150.0,
            "current_behavior_state": "fast_moving",
            "explanation": "Very high speed",
        }
        for i in range(5)
    ]

    events = custom_correlator.correlate(anomalies)

    speed_events = [e for e in events if e.event_type == EventType.HIGH_SPEED_ACTIVITY]
    assert len(speed_events) == 1

    event = speed_events[0]
    assert event.participating_track_ids == ["4"]
    assert len(event.source_anomaly_ids) == 5
    assert event.evidence["max_speed"] == 250.0


def test_high_speed_insufficient_count(custom_correlator):
    """Test insufficient speed anomalies don't create event"""
    # Only 1 anomaly, need min_high_speed_count=2
    anomalies = [
        {
            "event_id": "anom_001",
            "track_id": "4",
            "frame_id": 50,
            "timestamp": 2.0,
            "anomaly_type": "unusual_speed",
            "severity": "high",
            "anomaly_score": 0.8,
            "evidence": {"observed_speed": 250.0},
            "observed_value": 250.0,
            "threshold": 150.0,
            "current_behavior_state": "fast_moving",
            "explanation": "Very high speed",
        }
    ]

    events = custom_correlator.correlate(anomalies)

    speed_events = [e for e in events if e.event_type == EventType.HIGH_SPEED_ACTIVITY]
    assert len(speed_events) == 0


def test_high_speed_with_speed_change(custom_correlator):
    """Test speed anomalies combined with speed change"""
    anomalies = [
        {
            "event_id": "anom_001",
            "track_id": "4",
            "frame_id": 50,
            "timestamp": 2.0,
            "anomaly_type": "unusual_speed",
            "severity": "high",
            "anomaly_score": 0.8,
            "evidence": {"observed_speed": 200.0},
            "observed_value": 200.0,
            "threshold": 150.0,
            "current_behavior_state": "fast_moving",
            "explanation": "High speed",
        },
        {
            "event_id": "anom_002",
            "track_id": "4",
            "frame_id": 60,
            "timestamp": 2.5,
            "anomaly_type": "sudden_speed_change",
            "severity": "high",
            "anomaly_score": 0.85,
            "evidence": {"change_delta": 150.0},
            "observed_value": 150.0,
            "threshold": 100.0,
            "current_behavior_state": "fast_moving",
            "explanation": "Sudden acceleration",
        },
        {
            "event_id": "anom_003",
            "track_id": "4",
            "frame_id": 70,
            "timestamp": 3.0,
            "anomaly_type": "unusual_speed",
            "severity": "high",
            "anomaly_score": 0.8,
            "evidence": {"observed_speed": 220.0},
            "observed_value": 220.0,
            "threshold": 150.0,
            "current_behavior_state": "fast_moving",
            "explanation": "High speed",
        },
    ]

    events = custom_correlator.correlate(anomalies)

    # Should create high-speed event with both types
    speed_events = [e for e in events if e.event_type == EventType.HIGH_SPEED_ACTIVITY]
    assert len(speed_events) == 1
    assert len(speed_events[0].source_anomaly_ids) == 3


# ============================================================================
# Test: Abnormal Movement Sequence
# ============================================================================


def test_abnormal_movement_sequence(custom_correlator):
    """Test movement sequence event from multiple movement types"""
    # Custom config: min_movement_sequence=2
    anomalies = [
        {
            "event_id": "anom_001",
            "track_id": "5",
            "frame_id": 100,
            "timestamp": 5.0,
            "anomaly_type": "sudden_speed_change",
            "severity": "high",
            "anomaly_score": 0.85,
            "evidence": {"change_delta": 150.0},
            "observed_value": 150.0,
            "threshold": 100.0,
            "current_behavior_state": "fast_moving",
            "explanation": "Sudden acceleration",
        },
        {
            "event_id": "anom_002",
            "track_id": "5",
            "frame_id": 110,
            "timestamp": 5.5,
            "anomaly_type": "sudden_direction_change",
            "severity": "medium",
            "anomaly_score": 0.7,
            "evidence": {"change_degrees": 135.0},
            "observed_value": 135.0,
            "threshold": 90.0,
            "current_behavior_state": "moving",
            "explanation": "Sharp turn",
        },
    ]

    events = custom_correlator.correlate(anomalies)

    movement_events = [
        e for e in events if e.event_type == EventType.ABNORMAL_MOVEMENT_SEQUENCE
    ]
    assert len(movement_events) == 1

    event = movement_events[0]
    assert event.participating_track_ids == ["5"]
    assert len(event.source_anomaly_ids) == 2
    assert len(event.evidence["anomaly_types"]) == 2


def test_movement_sequence_single_type_no_event(custom_correlator):
    """Test same movement type doesn't create sequence event"""
    # Both are speed changes (same type)
    anomalies = [
        {
            "event_id": "anom_001",
            "track_id": "5",
            "frame_id": 100,
            "timestamp": 5.0,
            "anomaly_type": "sudden_speed_change",
            "severity": "high",
            "anomaly_score": 0.85,
            "evidence": {"change_delta": 150.0},
            "observed_value": 150.0,
            "threshold": 100.0,
            "current_behavior_state": "fast_moving",
            "explanation": "Sudden acceleration",
        },
        {
            "event_id": "anom_002",
            "track_id": "5",
            "frame_id": 110,
            "timestamp": 5.5,
            "anomaly_type": "sudden_speed_change",
            "severity": "high",
            "anomaly_score": 0.85,
            "evidence": {"change_delta": 120.0},
            "observed_value": 120.0,
            "threshold": 100.0,
            "current_behavior_state": "fast_moving",
            "explanation": "Another acceleration",
        },
    ]

    events = custom_correlator.correlate(anomalies)

    # Same type doesn't create movement sequence (needs 2+ different types)
    movement_events = [
        e for e in events if e.event_type == EventType.ABNORMAL_MOVEMENT_SEQUENCE
    ]
    assert len(movement_events) == 0


# ============================================================================
# Test: Multi-Track Separation
# ============================================================================


def test_multi_track_separate_events(default_correlator):
    """Test anomalies from different tracks create separate events"""
    anomalies = []

    # Track 1: Loitering
    for i in range(10):
        anomalies.append(
            {
                "event_id": f"anom_t1_{i}",
                "track_id": "1",
                "frame_id": 100 + i * 10,
                "timestamp": 5.0 + i * 0.5,
                "anomaly_type": "loitering",
                "severity": "low",
                "anomaly_score": 0.4,
                "evidence": {"stationary_duration": 5.0 + i * 0.5, "position": [100, 100]},
                "observed_value": 5.0 + i * 0.5,
                "threshold": 5.0,
                "current_behavior_state": "stationary",
                "explanation": "Stationary",
            }
        )

    # Track 2: Zone entry
    anomalies.append(
        {
            "event_id": "anom_t2_001",
            "track_id": "2",
            "frame_id": 200,
            "timestamp": 10.0,
            "anomaly_type": "restricted_zone_entry",
            "severity": "high",
            "anomaly_score": 0.8,
            "evidence": {"zone_id": "zone_1", "zone_name": "Area A", "position": [700, 150]},
            "observed_value": "(700, 150)",
            "threshold": "Zone zone_1",
            "current_behavior_state": "moving",
            "explanation": "Entered zone",
        }
    )

    events = default_correlator.correlate(anomalies)

    # Should have events for both tracks
    track_ids = {e.participating_track_ids[0] for e in events}
    assert "1" in track_ids
    assert "2" in track_ids

    # Each event should belong to only one track
    for event in events:
        assert len(event.participating_track_ids) == 1


# ============================================================================
# Test: Severity Calculation
# ============================================================================


def test_severity_all_high(default_correlator):
    """Test event severity when all anomalies are HIGH"""
    anomalies = [
        {
            "event_id": f"anom_{i}",
            "track_id": "6",
            "frame_id": 100 + i * 10,
            "timestamp": 5.0 + i * 1.0,
            "anomaly_type": "unusual_speed",
            "severity": "high",  # All high
            "anomaly_score": 0.85,
            "evidence": {"observed_speed": 300.0},
            "observed_value": 300.0,
            "threshold": 150.0,
            "current_behavior_state": "fast_moving",
            "explanation": "Very high speed",
        }
        for i in range(3)
    ]

    events = default_correlator.correlate(anomalies)

    if events:
        assert events[0].severity == EventSeverity.HIGH


def test_severity_majority_medium(default_correlator):
    """Test event severity when majority are MEDIUM"""
    anomalies = []

    # 1 low
    anomalies.append(
        {
            "event_id": "anom_001",
            "track_id": "6",
            "frame_id": 100,
            "timestamp": 5.0,
            "anomaly_type": "unusual_speed",
            "severity": "low",
            "anomaly_score": 0.6,
            "evidence": {"observed_speed": 180.0},
            "observed_value": 180.0,
            "threshold": 150.0,
            "current_behavior_state": "moving",
            "explanation": "Moderate speed",
        }
    )

    # 2 medium
    for i in range(2):
        anomalies.append(
            {
                "event_id": f"anom_{i+2:03d}",
                "track_id": "6",
                "frame_id": 110 + i * 10,
                "timestamp": 6.0 + i * 1.0,
                "anomaly_type": "unusual_speed",
                "severity": "medium",
                "anomaly_score": 0.7,
                "evidence": {"observed_speed": 200.0},
                "observed_value": 200.0,
                "threshold": 150.0,
                "current_behavior_state": "fast_moving",
                "explanation": "High speed",
            }
        )

    events = default_correlator.correlate(anomalies)

    if events:
        # Majority (2/3) are medium
        assert events[0].severity == EventSeverity.MEDIUM


def test_severity_all_low(default_correlator):
    """Test event severity when all anomalies are LOW"""
    anomalies = [
        {
            "event_id": f"anom_{i}",
            "track_id": "6",
            "frame_id": 200 + i * 10,
            "timestamp": 10.0 + i * 0.5,
            "anomaly_type": "loitering",
            "severity": "low",  # All low
            "anomaly_score": 0.4,
            "evidence": {"stationary_duration": 5.0 + i * 0.5, "position": [400, 300]},
            "observed_value": 5.0 + i * 0.5,
            "threshold": 5.0,
            "current_behavior_state": "stationary",
            "explanation": "Stationary",
        }
        for i in range(10)
    ]

    events = default_correlator.correlate(anomalies)

    if events:
        assert events[0].severity == EventSeverity.LOW


# ============================================================================
# Test: Confidence Calculation
# ============================================================================


def test_confidence_calculation(default_correlator):
    """Test confidence score calculation"""
    anomalies = [
        {
            "event_id": f"anom_{i}",
            "track_id": "7",
            "frame_id": 100 + i * 10,
            "timestamp": 5.0 + i * 1.0,
            "anomaly_type": "unusual_speed",
            "severity": "high",
            "anomaly_score": 0.8,
            "evidence": {"observed_speed": 250.0},
            "observed_value": 250.0,
            "threshold": 150.0,
            "current_behavior_state": "fast_moving",
            "explanation": "High speed",
        }
        for i in range(5)
    ]

    events = default_correlator.correlate(anomalies)

    if events:
        # Confidence should be between 0 and 1
        assert 0.0 <= events[0].confidence <= 1.0

        # With high anomaly scores and multiple observations, should be high confidence
        assert events[0].confidence > 0.7


# ============================================================================
# Test: Event Serialization
# ============================================================================


def test_event_to_dict(default_correlator):
    """Test event serialization to dictionary"""
    anomalies = [
        {
            "event_id": "anom_001",
            "track_id": "8",
            "frame_id": 100,
            "timestamp": 5.0,
            "anomaly_type": "restricted_zone_entry",
            "severity": "high",
            "anomaly_score": 0.8,
            "evidence": {"zone_id": "zone_1", "zone_name": "Area A", "position": [700, 150]},
            "observed_value": "(700, 150)",
            "threshold": "Zone zone_1",
            "current_behavior_state": "moving",
            "explanation": "Entered zone",
        }
    ]

    events = default_correlator.correlate(anomalies)

    if events:
        event_dict = events[0].to_dict()

        # Check all required fields are present
        required_fields = [
            "event_id",
            "event_type",
            "start_timestamp",
            "end_timestamp",
            "duration_seconds",
            "participating_track_ids",
            "source_anomaly_ids",
            "source_anomaly_types",
            "severity",
            "confidence",
            "evidence",
            "explanation",
        ]

        for field in required_fields:
            assert field in event_dict

        # Check types
        assert isinstance(event_dict["event_id"], str)
        assert isinstance(event_dict["event_type"], str)
        assert isinstance(event_dict["duration_seconds"], (int, float))
        assert isinstance(event_dict["participating_track_ids"], list)
        assert isinstance(event_dict["source_anomaly_ids"], list)
        assert isinstance(event_dict["confidence"], float)
        assert isinstance(event_dict["evidence"], dict)
        assert isinstance(event_dict["explanation"], str)


# ============================================================================
# Test: Complex Scenarios
# ============================================================================


def test_complex_single_track_scenario(default_correlator):
    """Test complex scenario with multiple event types for one track"""
    anomalies = []

    # Zone entries (5 repeated)
    for i in range(5):
        anomalies.append(
            {
                "event_id": f"anom_zone_{i}",
                "track_id": "9",
                "frame_id": 100 + i * 10,
                "timestamp": 5.0 + i * 1.0,
                "anomaly_type": "restricted_zone_entry",
                "severity": "high",
                "anomaly_score": 0.8,
                "evidence": {"zone_id": "zone_1", "zone_name": "Area", "position": [700, 150]},
                "observed_value": "(700, 150)",
                "threshold": "Zone zone_1",
                "current_behavior_state": "moving",
                "explanation": "In zone",
            }
        )

    # High speed (inside zone)
    for i in range(3):
        anomalies.append(
            {
                "event_id": f"anom_speed_{i}",
                "track_id": "9",
                "frame_id": 120 + i * 10,
                "timestamp": 6.0 + i * 0.5,
                "anomaly_type": "unusual_speed",
                "severity": "high",
                "anomaly_score": 0.85,
                "evidence": {"observed_speed": 220.0},
                "observed_value": 220.0,
                "threshold": 150.0,
                "current_behavior_state": "fast_moving",
                "explanation": "High speed",
            }
        )

    # Loitering (after leaving zone, 40s later)
    for i in range(10):
        anomalies.append(
            {
                "event_id": f"anom_loiter_{i}",
                "track_id": "9",
                "frame_id": 1200 + i * 10,
                "timestamp": 50.0 + i * 0.5,
                "anomaly_type": "loitering",
                "severity": "low",
                "anomaly_score": 0.4,
                "evidence": {"stationary_duration": 5.0 + i * 0.5, "position": [900, 300]},
                "observed_value": 5.0 + i * 0.5,
                "threshold": 5.0,
                "current_behavior_state": "stationary",
                "explanation": "Stationary",
            }
        )

    events = default_correlator.correlate(anomalies)

    # Should have multiple event types
    event_types = {e.event_type for e in events}
    assert len(event_types) >= 2  # At least intrusion and loitering

    # All events should be for track 9
    for event in events:
        assert event.participating_track_ids == ["9"]


def test_overlapping_events_same_track(default_correlator):
    """Test overlapping temporal windows create appropriate events"""
    anomalies = []

    # Group 1: Speed anomalies (0-10s)
    for i in range(5):
        anomalies.append(
            {
                "event_id": f"anom_speed_{i}",
                "track_id": "10",
                "frame_id": 10 + i * 20,
                "timestamp": 0.5 + i * 2.0,
                "anomaly_type": "unusual_speed",
                "severity": "high",
                "anomaly_score": 0.8,
                "evidence": {"observed_speed": 220.0},
                "observed_value": 220.0,
                "threshold": 150.0,
                "current_behavior_state": "fast_moving",
                "explanation": "High speed",
            }
        )

    # Group 2: Movement sequence (8-12s) - overlaps with speed
    anomalies.extend(
        [
            {
                "event_id": "anom_change_1",
                "track_id": "10",
                "frame_id": 240,
                "timestamp": 8.0,
                "anomaly_type": "sudden_speed_change",
                "severity": "high",
                "anomaly_score": 0.85,
                "evidence": {"change_delta": 150.0},
                "observed_value": 150.0,
                "threshold": 100.0,
                "current_behavior_state": "moving",
                "explanation": "Speed change",
            },
            {
                "event_id": "anom_change_2",
                "track_id": "10",
                "frame_id": 270,
                "timestamp": 9.0,
                "anomaly_type": "sudden_direction_change",
                "severity": "medium",
                "anomaly_score": 0.7,
                "evidence": {"change_degrees": 120.0},
                "observed_value": 120.0,
                "threshold": 90.0,
                "current_behavior_state": "moving",
                "explanation": "Direction change",
            },
        ]
    )

    events = default_correlator.correlate(anomalies)

    # Should create events (exact number depends on overlap handling)
    assert len(events) >= 1
    assert all(e.participating_track_ids == ["10"] for e in events)


# ============================================================================
# Test: Statistics
# ============================================================================


def test_get_statistics(default_correlator):
    """Test get_statistics method"""
    stats = default_correlator.get_statistics()

    assert "temporal_window" in stats
    assert "min_loitering_duration" in stats
    assert "min_high_speed_count" in stats
    assert "min_movement_sequence" in stats

    assert stats["temporal_window"] == 30.0  # Default value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
