"""
Tests for resolution invariance and scale-aware motion metrics.

Verifies that normalized speed and bounding-box-relative metrics behave
consistently across 480p, 1080p, and 4K resolutions.
"""

import pytest
from processing.behavior import BehaviorAnalyzer, BehaviorConfig, TrackHistory
from processing.anomaly.detector import AnomalyDetector, AnomalyConfig, AnomalyType


@pytest.mark.parametrize(
    "width,height,raw_speed_factor",
    [
        (640, 480, 480.0 / 1080.0),    # 480p: scale factor = 1080/480 = 2.25
        (1920, 1080, 1.0),             # 1080p: scale factor = 1.0
        (3840, 2160, 2160.0 / 1080.0), # 4K: scale factor = 1080/2160 = 0.5
    ],
)
def test_proportional_motion_normalization(width, height, raw_speed_factor):
    """
    Verify that an identical proportional motion (e.g. 10% frame height per second)
    produces identical normalized speed across 480p, 1080p, and 4K.
    """
    analyzer = BehaviorAnalyzer()
    analyzer.set_frame_dimensions(width, height)

    # Motion equal to 108 norm-px/s in reference 1080p space
    # Raw speed scales proportionally with frame height
    target_norm_speed = 108.0
    raw_speed = target_norm_speed * (height / 1080.0)

    # Simulate 8 observations at this speed
    fps = 30.0
    dt = 1.0 / fps
    step = raw_speed * dt
    bbox_h = height * 0.25  # Person is 25% of frame height

    history = TrackHistory(track_id=1)
    for i in range(10):
        t = i * dt
        y = 100.0 + i * step
        bbox = [100.0, y, 100.0 + bbox_h * 0.4, y + bbox_h]
        history.add_observation(t, bbox, (150.0, y + bbox_h / 2))

    behavior = analyzer._analyze_track(history, 9 * dt)

    # Raw speed is proportional to resolution
    assert abs(behavior["speed"] - raw_speed) < 1.0
    # Normalized speed must be invariant across all resolutions (~108 norm-px/s)
    assert abs(behavior["normalized_speed"] - target_norm_speed) < 1.0
    # Bounding-box relative speed must also be invariant (~0.4 body-heights/sec)
    expected_bh_speed = raw_speed / bbox_h
    assert abs(behavior["speed_norm_bbox"] - expected_bh_speed) < 0.05


@pytest.mark.parametrize(
    "width,height",
    [
        (640, 480),
        (1920, 1080),
        (3840, 2160),
    ],
)
def test_normal_walking_no_anomaly_across_resolutions(width, height):
    """
    Verify that normal walking (~40 norm-px/s) generates 0 anomalies
    at 480p, 1080p, and 4K.
    """
    detector = AnomalyDetector()
    detector.set_frame_dimensions(width, height)

    # 40 norm-px/s in raw pixels for this resolution
    raw_speed = 40.0 * (height / 1080.0)
    norm_speed = 40.0

    behaviors = []
    for f in range(10):
        behaviors.append(
            {
                "frame_id": f,
                "timestamp": f * 0.033,
                "track_id": "pedestrian_1",
                "position": [100.0, 100.0 + f * 2.0],
                "speed": raw_speed,
                "normalized_speed": norm_speed,
                "state": "moving",
                "history_length": f + 1,
            }
        )

    anomalies = detector.detect(behaviors)
    # Normal walking must not trigger speed anomalies in any resolution
    assert len(anomalies) == 0


@pytest.mark.parametrize(
    "width,height",
    [
        (640, 480),
        (1920, 1080),
        (3840, 2160),
    ],
)
def test_running_triggers_anomaly_across_resolutions(width, height):
    """
    Verify that anomalous sprinting (200 norm-px/s) consistently triggers
    UNUSUAL_SPEED across 480p, 1080p, and 4K.
    """
    detector = AnomalyDetector()
    detector.set_frame_dimensions(width, height)

    raw_speed = 200.0 * (height / 1080.0)
    norm_speed = 200.0

    behaviors = []
    for f in range(10):
        behaviors.append(
            {
                "frame_id": f,
                "timestamp": f * 0.033,
                "track_id": "sprinter_1",
                "position": [100.0, 100.0 + f * 10.0],
                "speed": raw_speed,
                "normalized_speed": norm_speed,
                "state": "fast-moving",
                "history_length": f + 1,
            }
        )

    anomalies = detector.detect(behaviors)
    speed_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.UNUSUAL_SPEED.value]
    assert len(speed_anomalies) >= 1
    # Check that observed_value reflects the normalized speed scale
    assert abs(speed_anomalies[0]["observed_value"] - 200.0) < 1.0
