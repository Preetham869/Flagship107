"""
Tests for behavior analyzer
"""
import pytest
import math
from processing.behavior import BehaviorAnalyzer, BehaviorConfig, TrackHistory


@pytest.fixture
def analyzer():
    """Create a behavior analyzer for testing"""
    config = BehaviorConfig(
        stationary_threshold=10.0,
        fast_moving_threshold=100.0,
        min_stationary_duration=2.0,
    )
    return BehaviorAnalyzer(config)


@pytest.fixture
def sample_track():
    """Create a sample track for testing"""
    return {
        "track_id": 1,
        "bbox": [100, 100, 200, 200],
        "confidence": 0.87,
        "class_name": "person",
    }


def test_analyzer_initialization(analyzer):
    """Test analyzer can be initialized"""
    assert analyzer is not None
    assert analyzer.config is not None
    assert len(analyzer.track_histories) == 0


def test_calculate_center(analyzer):
    """Test center calculation"""
    bbox = [100, 100, 200, 200]
    center = analyzer._calculate_center(bbox)
    assert center == (150, 150)


def test_calculate_center_non_square(analyzer):
    """Test center calculation for non-square box"""
    bbox = [50, 100, 150, 300]
    center = analyzer._calculate_center(bbox)
    assert center == (100, 200)


def test_update_single_track(analyzer, sample_track):
    """Test updating with single track"""
    behaviors = analyzer.update([sample_track], timestamp=0.0)

    assert len(behaviors) == 1
    behavior = behaviors[0]

    assert behavior["track_id"] == 1
    assert behavior["class_name"] == "person"
    assert behavior["confidence"] == 0.87
    assert "position" in behavior
    assert "speed" in behavior
    assert "state" in behavior


def test_displacement_calculation(analyzer):
    """Test displacement calculation"""
    history = TrackHistory(track_id=1)

    # Add two positions
    history.add_observation(0.0, [100, 100, 200, 200], (150, 150))
    history.add_observation(1.0, [110, 110, 210, 210], (160, 160))

    displacement = analyzer._calculate_displacement(history)

    # sqrt((10)^2 + (10)^2) = sqrt(200) ≈ 14.14
    assert abs(displacement - 14.14) < 0.1


def test_displacement_single_position(analyzer):
    """Test displacement with single position"""
    history = TrackHistory(track_id=1)
    history.add_observation(0.0, [100, 100, 200, 200], (150, 150))

    displacement = analyzer._calculate_displacement(history)
    assert displacement == 0.0


def test_speed_calculation(analyzer):
    """Test speed calculation"""
    history = TrackHistory(track_id=1)

    # Add positions with movement
    history.add_observation(0.0, [100, 100, 200, 200], (150, 150))
    history.add_observation(1.0, [200, 200, 300, 300], (250, 250))

    speed = analyzer._calculate_speed(history)

    # Distance = sqrt((100)^2 + (100)^2) = sqrt(20000) ≈ 141.42
    # Time = 1.0 second
    # Speed ≈ 141.42 px/s
    assert abs(speed - 141.42) < 1.0


def test_speed_insufficient_history(analyzer):
    """Test speed with insufficient history"""
    history = TrackHistory(track_id=1)
    history.add_observation(0.0, [100, 100, 200, 200], (150, 150))

    speed = analyzer._calculate_speed(history)
    assert speed == 0.0


def test_direction_calculation(analyzer):
    """Test direction calculation"""
    history = TrackHistory(track_id=1)

    # Movement to the right
    history.add_observation(0.0, [100, 100, 200, 200], (150, 150))
    history.add_observation(1.0, [200, 100, 300, 200], (250, 150))

    direction = analyzer._calculate_direction(history)

    # Moving right should be close to 0 degrees
    assert direction is not None
    assert abs(direction - 0.0) < 1.0


def test_direction_downward(analyzer):
    """Test downward direction"""
    history = TrackHistory(track_id=1)

    # Movement downward
    history.add_observation(0.0, [100, 100, 200, 200], (150, 150))
    history.add_observation(1.0, [100, 200, 200, 300], (150, 250))

    direction = analyzer._calculate_direction(history)

    # Moving down should be close to 90 degrees
    assert direction is not None
    assert abs(direction - 90.0) < 1.0


def test_direction_no_movement(analyzer):
    """Test direction with no movement"""
    history = TrackHistory(track_id=1)

    # No movement
    history.add_observation(0.0, [100, 100, 200, 200], (150, 150))
    history.add_observation(1.0, [100, 100, 200, 200], (150, 150))

    direction = analyzer._calculate_direction(history)

    # No movement should return None
    assert direction is None


def test_state_stationary(analyzer):
    """Test stationary state detection"""
    history = TrackHistory(track_id=1)

    # Very slow movement (< 10 px/s) for at least 2 seconds
    history.add_observation(0.0, [100, 100, 200, 200], (150, 150))
    history.add_observation(1.0, [101, 101, 201, 201], (151, 151))
    history.add_observation(2.0, [102, 102, 202, 202], (152, 152))
    history.add_observation(2.5, [103, 103, 203, 203], (153, 153))

    # Mark as stationary from start
    history.stationary_start_time = 0.0

    speed = analyzer._calculate_speed(history)
    state = analyzer._determine_state(speed, history, 2.5)

    assert speed < 10.0
    assert state == "stationary"


def test_state_moving(analyzer):
    """Test moving state detection"""
    history = TrackHistory(track_id=1)

    # Moderate movement (10-100 px/s)
    history.add_observation(0.0, [100, 100, 200, 200], (150, 150))
    history.add_observation(1.0, [150, 150, 250, 250], (200, 200))

    speed = analyzer._calculate_speed(history)
    state = analyzer._determine_state(speed, history, 1.0)

    assert 10.0 <= speed < 100.0
    assert state == "moving"


def test_state_fast_moving(analyzer):
    """Test fast-moving state detection"""
    history = TrackHistory(track_id=1)

    # Fast movement (> 100 px/s)
    history.add_observation(0.0, [100, 100, 200, 200], (150, 150))
    history.add_observation(1.0, [250, 250, 350, 350], (300, 300))

    speed = analyzer._calculate_speed(history)
    state = analyzer._determine_state(speed, history, 1.0)

    assert speed >= 100.0
    assert state == "fast-moving"


def test_track_history_duration(analyzer):
    """Test track duration calculation"""
    history = TrackHistory(track_id=1)

    history.add_observation(0.0, [100, 100, 200, 200], (150, 150))
    history.add_observation(5.0, [200, 200, 300, 300], (250, 250))

    duration = history.get_duration()
    assert duration == 5.0


def test_stationary_duration(analyzer):
    """Test stationary duration tracking"""
    history = TrackHistory(track_id=1)
    history.stationary_start_time = 2.0

    duration = history.get_stationary_duration(7.0)
    assert duration == 5.0


def test_multiple_tracks(analyzer):
    """Test analyzing multiple tracks"""
    tracks = [
        {"track_id": 1, "bbox": [100, 100, 200, 200], "confidence": 0.87, "class_name": "person"},
        {"track_id": 2, "bbox": [300, 300, 400, 400], "confidence": 0.92, "class_name": "person"},
    ]

    behaviors = analyzer.update(tracks, timestamp=0.0)

    assert len(behaviors) == 2
    assert behaviors[0]["track_id"] == 1
    assert behaviors[1]["track_id"] == 2


def test_empty_tracks(analyzer):
    """Test with empty track list"""
    behaviors = analyzer.update([], timestamp=0.0)
    assert len(behaviors) == 0


def test_get_statistics(analyzer, sample_track):
    """Test getting analyzer statistics"""
    analyzer.update([sample_track], timestamp=0.0)

    stats = analyzer.get_statistics()
    assert stats["total_tracks"] == 1
    assert stats["active_tracks"] == 1


def test_reset(analyzer, sample_track):
    """Test resetting analyzer"""
    analyzer.update([sample_track], timestamp=0.0)
    assert len(analyzer.track_histories) == 1

    analyzer.reset()
    assert len(analyzer.track_histories) == 0


def test_get_track_summary(analyzer):
    """Test getting track summary"""
    track = {"track_id": 1, "bbox": [100, 100, 200, 200], "confidence": 0.87, "class_name": "person"}

    analyzer.update([track], timestamp=0.0)
    track["bbox"] = [150, 150, 250, 250]
    analyzer.update([track], timestamp=1.0)

    summary = analyzer.get_track_summary(1)

    assert summary is not None
    assert summary["track_id"] == 1
    assert summary["observation_count"] == 2
    assert "trajectory_bounds" in summary


def test_history_max_size():
    """Test that history respects max size"""
    history = TrackHistory(track_id=1)

    # Add more than max size
    for i in range(50):
        history.add_observation(float(i), [100, 100, 200, 200], (150 + i, 150 + i))

    # Should only keep last 30 (default max_len)
    assert len(history.positions) == 30
    assert len(history.timestamps) == 30
