"""
Tests for anomaly detection module (Milestone 4).

Tests cover:
- Unusual speed detection
- Loitering detection
- Sudden speed change detection
- Sudden direction change detection
- Restricted zone entry detection
- Multiple tracks and anomalies
- No false positives
- Edge cases
"""

import pytest
import math
from typing import List, Dict
from processing.anomaly.detector import (
    AnomalyDetector,
    AnomalyConfig,
    RestrictedZone,
    AnomalyType,
    Severity
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def default_config():
    """Default anomaly configuration."""
    return AnomalyConfig()


@pytest.fixture
def detector(default_config):
    """Anomaly detector with default config."""
    return AnomalyDetector(default_config)


@pytest.fixture
def custom_config():
    """Custom anomaly configuration for testing thresholds."""
    return AnomalyConfig(
        unusual_speed_threshold=100.0,
        loitering_threshold=5.0,
        speed_change_threshold=50.0,
        direction_change_threshold=45.0
    )


@pytest.fixture
def custom_detector(custom_config):
    """Anomaly detector with custom config."""
    return AnomalyDetector(custom_config)


# ============================================================================
# Test: Unusual Speed Detection
# ============================================================================

def test_unusual_speed_high_speed(detector):
    """Test detection of unusually high speed (requires 3 consecutive frames)."""
    # Need 3 consecutive frames with high speed to trigger anomaly
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_001",
            "position": [100, 100],
            "speed": 200.0,  # Above default threshold of 150 (1.33x = LOW)
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_001",
            "position": [150, 150],
            "speed": 210.0,  # Still above threshold
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        },
        {
            "frame_id": 12,
            "timestamp": 0.40,
            "track_id": "track_001",
            "position": [200, 200],
            "speed": 205.0,  # Still above threshold
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    assert len(anomalies) == 1
    anomaly = anomalies[0]
    
    assert anomaly["anomaly_type"] == AnomalyType.UNUSUAL_SPEED.value
    assert anomaly["track_id"] == "track_001"
    assert anomaly["frame_id"] == 12  # Reported on 3rd frame
    assert anomaly["timestamp"] == 0.40
    assert anomaly["observed_value"] == 205.0
    assert anomaly["threshold"] == 150.0
    assert anomaly["severity"] == Severity.LOW.value  # 1.37x threshold = LOW
    assert "speed" in anomaly["evidence"]["description"].lower()
    assert "moving at 205.0 px/s" in anomaly["explanation"]


def test_unusual_speed_normal_speed(detector):
    """Test no detection when speed is normal."""
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_001",
            "position": [100, 100],
            "speed": 100.0,  # Below threshold
            "direction": 45.0,
            "displacement": 30.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    # Should not detect unusual speed
    speed_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.UNUSUAL_SPEED.value]
    assert len(speed_anomalies) == 0


def test_unusual_speed_custom_threshold(custom_detector):
    """Test unusual speed detection with custom threshold (requires 3 consecutive frames)."""
    # Need 3 consecutive frames with high speed to trigger anomaly
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_001",
            "position": [100, 100],
            "speed": 120.0,  # Above custom threshold of 100
            "direction": 45.0,
            "displacement": 40.0,
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_001",
            "position": [140, 140],
            "speed": 125.0,  # Still above threshold
            "direction": 45.0,
            "displacement": 40.0,
            "state": "moving"
        },
        {
            "frame_id": 12,
            "timestamp": 0.40,
            "track_id": "track_001",
            "position": [180, 180],
            "speed": 122.0,  # Still above threshold
            "direction": 45.0,
            "displacement": 40.0,
            "state": "moving"
        }
    ]
    
    anomalies = custom_detector.detect(behaviors)
    
    assert len(anomalies) == 1
    assert anomalies[0]["anomaly_type"] == AnomalyType.UNUSUAL_SPEED.value
    assert anomalies[0]["threshold"] == 100.0


# ============================================================================
# Test: Loitering Detection
# ============================================================================

def test_loitering_detection(detector):
    """Test detection of loitering (stationary too long)."""
    behaviors = [
        {
            "frame_id": 300,  # Frame 300
            "timestamp": 10.0,
            "track_id": "track_002",
            "position": [200, 200],
            "speed": 0.0,
            "direction": 0.0,
            "displacement": 0.0,
            "state": "stationary",
            "stationary_duration": 11.0  # Stationary for 11 seconds
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    assert len(anomalies) == 1
    anomaly = anomalies[0]
    
    assert anomaly["anomaly_type"] == AnomalyType.LOITERING.value
    assert anomaly["track_id"] == "track_002"
    assert anomaly["observed_value"] == 11.0  # Duration
    assert anomaly["threshold"] == 10.0
    assert "stationary" in anomaly["evidence"]["description"].lower()


def test_loitering_short_duration(detector):
    """Test no loitering detection for short stationary duration."""
    behaviors = [
        {
            "frame_id": 150,  # Frame 150 (5 seconds)
            "timestamp": 5.0,
            "track_id": "track_002",
            "position": [200, 200],
            "speed": 0.0,
            "direction": 0.0,
            "displacement": 0.0,
            "state": "stationary"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    loitering_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.LOITERING.value]
    assert len(loitering_anomalies) == 0


def test_loitering_custom_threshold(custom_detector):
    """Test loitering detection with custom threshold."""
    behaviors = [
        {
            "frame_id": 150,  # Frame 150 (5 seconds)
            "timestamp": 5.0,
            "track_id": "track_002",
            "position": [200, 200],
            "speed": 0.0,
            "direction": 0.0,
            "displacement": 0.0,
            "state": "stationary",
            "stationary_duration": 6.0  # Stationary for 6 seconds
        }
    ]
    
    # Custom threshold is 5.0 seconds
    anomalies = custom_detector.detect(behaviors)
    
    loitering_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.LOITERING.value]
    assert len(loitering_anomalies) == 1
    assert loitering_anomalies[0]["threshold"] == 5.0


# ============================================================================
# Test: Sudden Speed Change Detection
# ============================================================================

def test_sudden_speed_change_acceleration(detector):
    """Test detection of sudden acceleration."""
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_003",
            "position": [100, 100],
            "speed": 50.0,
            "direction": 45.0,
            "displacement": 15.0,
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_003",
            "position": [120, 120],
            "speed": 200.0,  # Sudden increase
            "direction": 45.0,
            "displacement": 20.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    # Should detect sudden speed change on frame 11
    speed_change_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.SUDDEN_SPEED_CHANGE.value]
    assert len(speed_change_anomalies) == 1
    
    anomaly = speed_change_anomalies[0]
    assert anomaly["frame_id"] == 11
    assert anomaly["observed_value"] == 150.0  # Delta
    assert anomaly["threshold"] == 100.0
    assert "acceleration" in anomaly["explanation"].lower()


def test_sudden_speed_change_deceleration(detector):
    """Test detection of sudden deceleration."""
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_003",
            "position": [100, 100],
            "speed": 200.0,
            "direction": 45.0,
            "displacement": 40.0,
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_003",
            "position": [110, 110],
            "speed": 50.0,  # Sudden decrease
            "direction": 45.0,
            "displacement": 10.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    speed_change_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.SUDDEN_SPEED_CHANGE.value]
    assert len(speed_change_anomalies) == 1
    
    anomaly = speed_change_anomalies[0]
    assert anomaly["observed_value"] == 150.0  # Absolute delta
    assert "deceleration" in anomaly["explanation"].lower()


def test_sudden_speed_change_gradual(detector):
    """Test no detection for gradual speed change."""
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_003",
            "position": [100, 100],
            "speed": 80.0,
            "direction": 45.0,
            "displacement": 24.0,
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_003",
            "position": [120, 120],
            "speed": 110.0,  # Small increase
            "direction": 45.0,
            "displacement": 28.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    speed_change_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.SUDDEN_SPEED_CHANGE.value]
    assert len(speed_change_anomalies) == 0


# ============================================================================
# Test: Sudden Direction Change Detection
# ============================================================================

def test_sudden_direction_change(detector):
    """Test detection of sudden direction change (requires min displacement, speed, consecutive frames)."""
    # Need 2 consecutive frames with direction change >90°, sufficient displacement and speed
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_004",
            "position": [100, 100],
            "speed": 100.0,  # Sufficient speed (>15px/s)
            "direction": 0.0,  # Moving right
            "displacement": 30.0,  # Sufficient displacement (>20px)
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_004",
            "position": [130, 100],  # Moved 30px right
            "speed": 100.0,
            "direction": 95.0,  # Turned 95° (> 90° threshold) - buffer count = 1
            "displacement": 30.0,
            "state": "moving"
        },
        {
            "frame_id": 12,
            "timestamp": 0.40,
            "track_id": "track_004",
            "position": [130, 132],  # Moved ~32px from frame 11
            "speed": 100.0,
            "direction": 190.0,  # Turned another 95° (> 90° threshold) - buffer count = 2, TRIGGER
            "displacement": 32.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    direction_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.SUDDEN_DIRECTION_CHANGE.value]
    assert len(direction_anomalies) == 1
    
    anomaly = direction_anomalies[0]
    assert anomaly["frame_id"] == 12  # Reported on frame 12 after 2 consecutive changes
    assert anomaly["observed_value"] == 95.0  # Last direction change (190-95)
    assert anomaly["threshold"] == 90.0
    assert "turned" in anomaly["explanation"].lower()


def test_sudden_direction_change_wraparound(detector):
    """Test direction change detection with angle wraparound (350° to 10°)."""
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_004",
            "position": [100, 100],
            "speed": 100.0,
            "direction": 350.0,
            "displacement": 30.0,
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_004",
            "position": [130, 100],
            "speed": 100.0,
            "direction": 10.0,  # Should be 20° change, not 340°
            "displacement": 30.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    # 20° change should not trigger (threshold is 90°)
    direction_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.SUDDEN_DIRECTION_CHANGE.value]
    assert len(direction_anomalies) == 0


def test_sudden_direction_change_180_degree(detector):
    """Test detection of 180° direction reversal (requires min displacement, speed, consecutive frames)."""
    # Need 2 consecutive frames with >90° direction changes
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_004",
            "position": [100, 100],
            "speed": 100.0,  # Sufficient speed
            "direction": 0.0,  # Moving right
            "displacement": 30.0,  # Sufficient displacement
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_004",
            "position": [130, 100],  # Moved 30px right
            "speed": 100.0,
            "direction": 100.0,  # Turned 100° - buffer count = 1
            "displacement": 30.0,
            "state": "moving"
        },
        {
            "frame_id": 12,
            "timestamp": 0.40,
            "track_id": "track_004",
            "position": [125, 130],  # Moved in new direction
            "speed": 100.0,
            "direction": 210.0,  # Turned another 110° - buffer count = 2, TRIGGER
            "displacement": 30.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    direction_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.SUDDEN_DIRECTION_CHANGE.value]
    assert len(direction_anomalies) == 1
    # The observed value will be the last direction change (210-100 = 110°)
    assert direction_anomalies[0]["observed_value"] == 110.0


def test_sudden_direction_change_gradual_turn(detector):
    """Test no detection for gradual turn."""
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_004",
            "position": [100, 100],
            "speed": 100.0,
            "direction": 0.0,
            "displacement": 30.0,
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_004",
            "position": [115, 110],
            "speed": 100.0,
            "direction": 30.0,  # Gradual 30° turn
            "displacement": 30.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    direction_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.SUDDEN_DIRECTION_CHANGE.value]
    assert len(direction_anomalies) == 0


# ============================================================================
# Test: Restricted Zone Entry Detection
# ============================================================================

def test_restricted_zone_entry_rectangle():
    """Test detection of entry into rectangular restricted zone."""
    zones = [
        RestrictedZone(
            zone_id="zone_001",
            zone_type="rectangle",
            coordinates=[300, 300, 400, 400],
            name="Restricted Area"
        )
    ]
    
    config = AnomalyConfig(restricted_zones=zones)
    detector = AnomalyDetector(config)
    
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_005",
            "position": [350, 350],  # Inside zone
            "speed": 80.0,
            "direction": 45.0,
            "displacement": 25.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    zone_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.RESTRICTED_ZONE_ENTRY.value]
    assert len(zone_anomalies) == 1
    
    anomaly = zone_anomalies[0]
    assert anomaly["track_id"] == "track_005"
    assert anomaly["evidence"]["zone_id"] == "zone_001"
    assert "Restricted Area" in anomaly["explanation"]


def test_restricted_zone_entry_polygon():
    """Test detection of entry into polygonal restricted zone."""
    # Triangle zone
    zones = [
        RestrictedZone(
            zone_id="zone_002",
            zone_type="polygon",
            coordinates=[100, 100, 200, 100, 150, 200],  # Triangle
            name="No Entry"
        )
    ]
    
    config = AnomalyConfig(restricted_zones=zones)
    detector = AnomalyDetector(config)
    
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_006",
            "position": [150, 120],  # Inside triangle
            "speed": 80.0,
            "direction": 45.0,
            "displacement": 25.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    zone_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.RESTRICTED_ZONE_ENTRY.value]
    assert len(zone_anomalies) == 1


def test_restricted_zone_no_entry_outside():
    """Test no detection when object is outside restricted zone."""
    zones = [
        RestrictedZone(
            zone_id="zone_001",
            zone_type="rectangle",
            coordinates=[300, 300, 400, 400],
            name="Restricted Area"
        )
    ]
    
    config = AnomalyConfig(restricted_zones=zones)
    detector = AnomalyDetector(config)
    
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_005",
            "position": [100, 100],  # Outside zone
            "speed": 80.0,
            "direction": 45.0,
            "displacement": 25.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    zone_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.RESTRICTED_ZONE_ENTRY.value]
    assert len(zone_anomalies) == 0


def test_restricted_zone_multiple_zones():
    """Test detection with multiple restricted zones."""
    zones = [
        RestrictedZone(
            zone_id="zone_001",
            zone_type="rectangle",
            coordinates=[100, 100, 200, 200],
            name="Zone 1"
        ),
        RestrictedZone(
            zone_id="zone_002",
            zone_type="rectangle",
            coordinates=[300, 300, 400, 400],
            name="Zone 2"
        )
    ]
    
    config = AnomalyConfig(restricted_zones=zones)
    detector = AnomalyDetector(config)
    
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_007",
            "position": [150, 150],  # In zone 1
            "speed": 80.0,
            "direction": 45.0,
            "displacement": 25.0,
            "state": "moving"
        },
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_008",
            "position": [350, 350],  # In zone 2
            "speed": 80.0,
            "direction": 45.0,
            "displacement": 25.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    zone_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.RESTRICTED_ZONE_ENTRY.value]
    assert len(zone_anomalies) == 2
    
    zone_ids = {a["evidence"]["zone_id"] for a in zone_anomalies}
    assert zone_ids == {"zone_001", "zone_002"}


# ============================================================================
# Test: Multiple Tracks and Anomalies
# ============================================================================

def test_multiple_tracks_multiple_anomalies(detector):
    """Test detection of multiple anomalies across multiple tracks."""
    behaviors = [
        # Track 1: Unusual speed (frame 1)
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_001",
            "position": [100, 100],
            "speed": 200.0,  # High speed
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        },
        # Track 1: Unusual speed (frame 2)
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_001",
            "position": [150, 150],
            "speed": 205.0,  # Still high speed
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        },
        # Track 1: Unusual speed (frame 3)
        {
            "frame_id": 12,
            "timestamp": 0.40,
            "track_id": "track_001",
            "position": [200, 200],
            "speed": 202.0,  # Still high speed
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        },
        # Track 2: Loitering
        {
            "frame_id": 300,
            "timestamp": 10.0,
            "track_id": "track_002",
            "position": [200, 200],
            "speed": 0.0,
            "direction": 0.0,
            "displacement": 0.0,
            "state": "stationary",
            "stationary_duration": 11.0  # Stationary for 11 seconds
        },
        # Track 3: Normal behavior
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_003",
            "position": [300, 300],
            "speed": 80.0,  # Normal speed
            "direction": 90.0,
            "displacement": 25.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    # Should detect 2 anomalies (unusual speed and loitering)
    assert len(anomalies) >= 2
    
    track_ids = {a["track_id"] for a in anomalies}
    assert "track_001" in track_ids
    assert "track_002" in track_ids
    assert "track_003" not in track_ids  # Normal behavior


def test_single_track_multiple_anomalies(detector):
    """Test detection of multiple anomaly types for a single track."""
    zones = [
        RestrictedZone(
            zone_id="zone_001",
            zone_type="rectangle",
            coordinates=[400, 400, 500, 500],
            name="Restricted"
        )
    ]
    
    config = AnomalyConfig(
        unusual_speed_threshold=150.0,
        restricted_zones=zones
    )
    detector = AnomalyDetector(config)
    
    behaviors = [
        # Frame 1: Zone entry detected, speed counter starts
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_001",
            "position": [450, 450],  # In restricted zone
            "speed": 200.0,  # High speed
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        },
        # Frame 2: Speed counter continues
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_001",
            "position": [460, 460],  # Still in zone
            "speed": 205.0,  # Still high speed
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        },
        # Frame 3: Speed anomaly triggered
        {
            "frame_id": 12,
            "timestamp": 0.40,
            "track_id": "track_001",
            "position": [470, 470],  # Still in zone
            "speed": 202.0,  # Still high speed
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    # Zone entry is detected on each frame (3 times) + speed anomaly (1 time) = 4 total
    # This is expected behavior - zone entry reports on every frame inside zone
    assert len(anomalies) == 4
    
    anomaly_types = [a["anomaly_type"] for a in anomalies]
    assert anomaly_types.count(AnomalyType.UNUSUAL_SPEED.value) == 1
    assert anomaly_types.count(AnomalyType.RESTRICTED_ZONE_ENTRY.value) == 3


# ============================================================================
# Test: No False Positives
# ============================================================================

def test_no_false_positives_normal_behavior(detector):
    """Test that normal behavior does not trigger anomalies."""
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_001",
            "position": [100, 100],
            "speed": 80.0,  # Normal speed
            "direction": 45.0,
            "displacement": 25.0,
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_001",
            "position": [120, 120],
            "speed": 90.0,  # Gradual speed change
            "direction": 50.0,  # Gradual direction change
            "displacement": 28.0,
            "state": "moving"
        },
        {
            "frame_id": 90,
            "timestamp": 3.0,
            "track_id": "track_002",
            "position": [200, 200],
            "speed": 0.0,
            "direction": 0.0,
            "displacement": 0.0,
            "state": "stationary"  # Short stationary period
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    # Should not detect any anomalies
    assert len(anomalies) == 0


def test_no_false_positives_edge_values(detector):
    """Test that values exactly at threshold do not trigger anomalies."""
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_001",
            "position": [100, 100],
            "speed": 150.0,  # Exactly at threshold
            "direction": 45.0,
            "displacement": 45.0,
            "state": "moving"
        },
        {
            "frame_id": 300,
            "timestamp": 10.0,
            "track_id": "track_002",
            "position": [200, 200],
            "speed": 0.0,
            "direction": 0.0,
            "displacement": 0.0,
            "state": "stationary"  # Exactly 10 seconds
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    # Values at threshold should not trigger (requires >threshold)
    assert len(anomalies) == 0


# ============================================================================
# Test: Edge Cases
# ============================================================================

def test_empty_behaviors_list(detector):
    """Test handling of empty behaviors list."""
    anomalies = detector.detect([])
    assert anomalies == []


def test_single_frame_no_history(detector):
    """Test that first 2 frames of track have no speed anomaly due to temporal smoothing."""
    # Send 2 frames with high speed - should NOT trigger (need 3 consecutive)
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_new",
            "position": [100, 100],
            "speed": 200.0,  # High speed
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_new",
            "position": [150, 150],
            "speed": 210.0,  # Still high speed
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    # Should NOT detect unusual speed (need 3 consecutive frames)
    # Should not detect speed/direction change (insufficient history)
    anomaly_types = [a["anomaly_type"] for a in anomalies]
    assert AnomalyType.UNUSUAL_SPEED.value not in anomaly_types  # Changed expectation
    assert AnomalyType.SUDDEN_SPEED_CHANGE.value not in anomaly_types
    assert AnomalyType.SUDDEN_DIRECTION_CHANGE.value not in anomaly_types


def test_severity_calculation_low():
    """Test severity calculation for LOW severity (requires 3 consecutive frames)."""
    config = AnomalyConfig(unusual_speed_threshold=100.0)
    detector = AnomalyDetector(config)
    
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_001",
            "position": [100, 100],
            "speed": 110.0,  # 1.1x threshold
            "direction": 45.0,
            "displacement": 33.0,
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_001",
            "position": [133, 133],
            "speed": 112.0,  # Still 1.1x threshold
            "direction": 45.0,
            "displacement": 33.0,
            "state": "moving"
        },
        {
            "frame_id": 12,
            "timestamp": 0.40,
            "track_id": "track_001",
            "position": [166, 166],
            "speed": 111.0,  # Still 1.1x threshold
            "direction": 45.0,
            "displacement": 33.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    assert len(anomalies) == 1
    assert anomalies[0]["severity"] == Severity.LOW.value


def test_severity_calculation_medium():
    """Test severity calculation for MEDIUM severity (requires 3 consecutive frames)."""
    config = AnomalyConfig(unusual_speed_threshold=100.0)
    detector = AnomalyDetector(config)
    
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_001",
            "position": [100, 100],
            "speed": 160.0,  # 1.6x threshold
            "direction": 45.0,
            "displacement": 48.0,
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_001",
            "position": [148, 148],
            "speed": 162.0,  # Still 1.6x threshold
            "direction": 45.0,
            "displacement": 48.0,
            "state": "moving"
        },
        {
            "frame_id": 12,
            "timestamp": 0.40,
            "track_id": "track_001",
            "position": [196, 196],
            "speed": 161.0,  # Still 1.6x threshold
            "direction": 45.0,
            "displacement": 48.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    assert len(anomalies) == 1
    assert anomalies[0]["severity"] == Severity.MEDIUM.value


def test_severity_calculation_high():
    """Test severity calculation for HIGH severity (requires 3 consecutive frames)."""
    config = AnomalyConfig(unusual_speed_threshold=100.0)
    detector = AnomalyDetector(config)
    
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_001",
            "position": [100, 100],
            "speed": 250.0,  # 2.5x threshold
            "direction": 45.0,
            "displacement": 75.0,
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_001",
            "position": [175, 175],
            "speed": 252.0,  # Still 2.5x threshold
            "direction": 45.0,
            "displacement": 75.0,
            "state": "moving"
        },
        {
            "frame_id": 12,
            "timestamp": 0.40,
            "track_id": "track_001",
            "position": [250, 250],
            "speed": 251.0,  # Still 2.5x threshold
            "direction": 45.0,
            "displacement": 75.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    assert len(anomalies) == 1
    assert anomalies[0]["severity"] == Severity.HIGH.value


def test_anomaly_score_calculation():
    """Test anomaly score is properly normalized (0-1) (requires 3 consecutive frames)."""
    config = AnomalyConfig(unusual_speed_threshold=100.0)
    detector = AnomalyDetector(config)
    
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_001",
            "position": [100, 100],
            "speed": 200.0,  # 2x threshold
            "direction": 45.0,
            "displacement": 60.0,
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_001",
            "position": [160, 160],
            "speed": 202.0,  # Still 2x threshold
            "direction": 45.0,
            "displacement": 60.0,
            "state": "moving"
        },
        {
            "frame_id": 12,
            "timestamp": 0.40,
            "track_id": "track_001",
            "position": [220, 220],
            "speed": 201.0,  # Still 2x threshold
            "direction": 45.0,
            "displacement": 60.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    assert len(anomalies) == 1
    score = anomalies[0]["anomaly_score"]
    assert 0.0 <= score <= 1.0
    assert score > 0.5  # Should be high for 2x threshold


def test_unique_event_ids():
    """Test that each anomaly gets a unique event_id."""
    config = AnomalyConfig()
    detector = AnomalyDetector(config)
    
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_001",
            "position": [100, 100],
            "speed": 200.0,
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        },
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_002",
            "position": [200, 200],
            "speed": 250.0,
            "direction": 90.0,
            "displacement": 60.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    # Multiple anomalies should have unique IDs
    event_ids = [a["event_id"] for a in anomalies]
    assert len(event_ids) == len(set(event_ids))  # All unique


def test_restricted_zone_contains_point_edge():
    """Test point-in-rectangle edge cases."""
    zone = RestrictedZone(
        zone_id="zone_001",
        zone_type="rectangle",
        coordinates=[100, 100, 200, 200],
        name="Test"
    )
    
    # Points on edges should be considered inside
    assert zone.contains_point([100, 100])  # Top-left corner
    assert zone.contains_point([200, 200])  # Bottom-right corner
    assert zone.contains_point([150, 100])  # Top edge
    assert zone.contains_point([100, 150])  # Left edge
    
    # Points outside
    assert not zone.contains_point([99, 150])
    assert not zone.contains_point([201, 150])


def test_restricted_zone_polygon_edge():
    """Test point-in-polygon edge cases."""
    # Square as polygon
    zone = RestrictedZone(
        zone_id="zone_002",
        zone_type="polygon",
        coordinates=[100, 100, 200, 100, 200, 200, 100, 200],
        name="Test"
    )
    
    # Points clearly inside
    assert zone.contains_point([150, 150])
    
    # Points clearly outside
    assert not zone.contains_point([50, 50])
    assert not zone.contains_point([250, 250])


def test_missing_optional_fields(detector):
    """Test handling of behaviors with minimal fields (requires 3 consecutive frames)."""
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_001",
            "position": [100, 100],
            "speed": 200.0,
            "direction": 45.0,
            "state": "moving"
            # Missing displacement - should still work
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_001",
            "position": [150, 150],
            "speed": 205.0,
            "direction": 45.0,
            "state": "moving"
        },
        {
            "frame_id": 12,
            "timestamp": 0.40,
            "track_id": "track_001",
            "position": [200, 200],
            "speed": 202.0,
            "direction": 45.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    # Should still detect unusual speed
    assert len(anomalies) == 1
    assert anomalies[0]["anomaly_type"] == AnomalyType.UNUSUAL_SPEED.value


# ============================================================================
# Test: Anomaly Structure Validation
# ============================================================================

def test_anomaly_structure_completeness(detector):
    """Test that anomaly output contains all required fields (requires 3 consecutive frames)."""
    behaviors = [
        {
            "frame_id": 10,
            "timestamp": 0.33,
            "track_id": "track_001",
            "position": [100, 100],
            "speed": 200.0,
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        },
        {
            "frame_id": 11,
            "timestamp": 0.37,
            "track_id": "track_001",
            "position": [150, 150],
            "speed": 205.0,
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        },
        {
            "frame_id": 12,
            "timestamp": 0.40,
            "track_id": "track_001",
            "position": [200, 200],
            "speed": 202.0,
            "direction": 45.0,
            "displacement": 50.0,
            "state": "moving"
        }
    ]
    
    anomalies = detector.detect(behaviors)
    
    assert len(anomalies) == 1
    anomaly = anomalies[0]
    
    # Check all required fields are present
    required_fields = [
        "event_id",
        "track_id",
        "frame_id",
        "timestamp",
        "anomaly_type",
        "severity",
        "anomaly_score",
        "observed_value",
        "threshold",
        "current_behavior_state",
        "evidence",
        "explanation"
    ]
    
    for field in required_fields:
        assert field in anomaly, f"Missing required field: {field}"
    
    # Check evidence structure
    assert "description" in anomaly["evidence"]
    
    # Check types
    assert isinstance(anomaly["event_id"], str)
    assert isinstance(anomaly["track_id"], str)
    assert isinstance(anomaly["frame_id"], int)
    assert isinstance(anomaly["timestamp"], (int, float))
    assert isinstance(anomaly["anomaly_type"], str)
    assert isinstance(anomaly["severity"], str)
    assert isinstance(anomaly["anomaly_score"], float)
    assert isinstance(anomaly["explanation"], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
