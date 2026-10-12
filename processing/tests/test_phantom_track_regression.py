"""
Regression tests for phantom track identity collisions and temporal discontinuity.

Validates:
1. Unconfirmed detections (boxes.id is None) do not reuse track_id 0 across frames.
2. Confirmed ByteTrack IDs remain positive and preserved.
3. Long observation gaps do not produce synthetic displacement, speed, or direction vectors.
4. Consecutive observations after a reset cleanly establish a new trajectory.
5. AnomalyDetector rejects direction changes across observation gaps and purges stale buffer entries.
"""

from unittest.mock import MagicMock
import numpy as np
import torch
import pytest

from processing.tracking.object_tracker import ObjectTracker
from processing.behavior.analyzer import BehaviorAnalyzer, BehaviorConfig, TrackHistory
from processing.anomaly.detector import AnomalyDetector, AnomalyConfig, AnomalyType


class DummyBoxes:
    """Mock for Ultralytics YOLO Result.boxes"""
    def __init__(self, xyxy, conf, cls, track_id=None):
        self.xyxy = torch.tensor(xyxy, dtype=torch.float32)
        self.conf = torch.tensor(conf, dtype=torch.float32)
        self.cls = torch.tensor(cls, dtype=torch.float32)
        self.id = torch.tensor(track_id, dtype=torch.float32) if track_id is not None else None

    def __len__(self):
        return len(self.xyxy)


class DummyResult:
    """Mock for Ultralytics YOLO Result"""
    def __init__(self, boxes):
        self.boxes = boxes


def test_unconfirmed_detections_do_not_reuse_track_id_zero():
    """Verify that detections without ByteTrack IDs never assign or collide on track_id 0."""
    tracker = ObjectTracker(device="cpu")
    
    # Mock YOLO model.track to return unconfirmed detection (boxes.id is None)
    dummy_boxes_1 = DummyBoxes(
        xyxy=[[10.0, 10.0, 50.0, 50.0]],
        conf=[0.75],
        cls=[0],
        track_id=None,
    )
    dummy_boxes_2 = DummyBoxes(
        xyxy=[[100.0, 100.0, 150.0, 150.0]],
        conf=[0.80],
        cls=[0],
        track_id=None,
    )

    frame = np.zeros((240, 320, 3), dtype=np.uint8)

    # Default behavior: unconfirmed detections are excluded from persistent tracks
    tracker.model.track = MagicMock(return_value=[DummyResult(dummy_boxes_1)])
    tracks_1 = tracker.track(frame)
    assert len(tracks_1) == 0, "Unconfirmed detections should be excluded by default"

    # When include_unconfirmed=True, unique non-colliding negative IDs are assigned
    tracker.model.track = MagicMock(return_value=[DummyResult(dummy_boxes_1)])
    tracks_unconf_1 = tracker.track(frame, include_unconfirmed=True)
    assert len(tracks_unconf_1) == 1
    assert tracks_unconf_1[0]["track_id"] != 0, "Track ID must not be 0"
    assert tracks_unconf_1[0]["track_id"] < 0, "Unconfirmed track ID should be negative"
    assert tracks_unconf_1[0]["confirmed"] is False

    tracker.model.track = MagicMock(return_value=[DummyResult(dummy_boxes_2)])
    tracks_unconf_2 = tracker.track(frame, include_unconfirmed=True)
    assert len(tracks_unconf_2) == 1
    assert tracks_unconf_2[0]["track_id"] != 0, "Track ID must not be 0"
    assert tracks_unconf_2[0]["track_id"] != tracks_unconf_1[0]["track_id"], (
        "Unconfirmed detections in different frames must not share IDs"
    )


def test_confirmed_bytetrack_ids_preserved():
    """Verify that confirmed ByteTrack IDs are passed through without modification."""
    tracker = ObjectTracker(device="cpu")
    dummy_boxes = DummyBoxes(
        xyxy=[[20.0, 30.0, 80.0, 120.0]],
        conf=[0.92],
        cls=[0],
        track_id=[42],
    )
    tracker.model.track = MagicMock(return_value=[DummyResult(dummy_boxes)])
    frame = np.zeros((240, 320, 3), dtype=np.uint8)

    tracks = tracker.track(frame)
    assert len(tracks) == 1
    assert tracks[0]["track_id"] == 42
    assert tracks[0]["confirmed"] is True
    assert 42 in tracker.active_track_ids


def test_observation_gap_suppresses_synthetic_displacement_and_direction():
    """Verify that an observation gap (> max_observation_gap) resets kinematics."""
    analyzer = BehaviorAnalyzer(BehaviorConfig(max_observation_gap=1.0))
    track = {
        "track_id": 1,
        "bbox": [10.0, 10.0, 30.0, 30.0],
        "confidence": 0.9,
        "class_name": "person",
        "confirmed": True,
    }

    # First observation at t=0.0
    b0 = analyzer.update([track], timestamp=0.0)
    assert len(b0) == 1
    assert b0[0]["displacement"] == 0.0
    assert b0[0]["speed"] == 0.0
    assert b0[0]["direction"] is None

    # Second observation at t=5.0 (gap of 5.0s > 1.0s max gap)
    track_moved = {
        "track_id": 1,
        "bbox": [110.0, 110.0, 130.0, 130.0],  # 100px jump across gap
        "confidence": 0.9,
        "class_name": "person",
        "confirmed": True,
    }
    b1 = analyzer.update([track_moved], timestamp=5.0)
    assert len(b1) == 1
    # Across the gap, displacement and speed must not be calculated
    assert b1[0]["displacement"] == 0.0
    assert b1[0]["speed"] == 0.0
    assert b1[0]["direction"] is None
    assert b1[0]["history_length"] == 1


def test_consecutive_observations_after_reset_establish_new_trajectory():
    """Verify that after a gap reset, subsequent consecutive observations track normally."""
    analyzer = BehaviorAnalyzer(BehaviorConfig(max_observation_gap=1.0))
    track = {
        "track_id": 2,
        "bbox": [0.0, 0.0, 20.0, 20.0],
        "confidence": 0.9,
        "class_name": "person",
        "confirmed": True,
    }

    # Observation at t=0.0
    analyzer.update([track], timestamp=0.0)

    # Observation at t=10.0 (gap -> reset)
    track_at_10 = dict(track, bbox=[100.0, 100.0, 120.0, 120.0])
    b_at_10 = analyzer.update([track_at_10], timestamp=10.0)
    assert b_at_10[0]["displacement"] == 0.0
    assert b_at_10[0]["history_length"] == 1

    # Observation at t=10.05 (consecutive: dt=0.05s <= 1.0s)
    track_at_10_05 = dict(track, bbox=[110.0, 100.0, 130.0, 120.0])  # moved 10px right
    b_at_10_05 = analyzer.update([track_at_10_05], timestamp=10.05)
    assert b_at_10_05[0]["displacement"] == pytest.approx(10.0, abs=0.1)
    assert b_at_10_05[0]["direction"] == pytest.approx(0.0, abs=1.0)  # 0 deg = moving right
    assert b_at_10_05[0]["speed"] == pytest.approx(200.0, abs=5.0)  # 10px / 0.05s = 200px/s
    assert b_at_10_05[0]["history_length"] == 2


def test_direction_change_anomaly_rejected_across_gap():
    """Verify that AnomalyDetector rejects direction changes across observation gaps."""
    detector = AnomalyDetector(AnomalyConfig(max_observation_gap=1.0))

    # Observation at t=0.0 moving east (0 deg)
    b0 = {
        "track_id": 1,
        "frame_id": 0,
        "timestamp": 0.0,
        "position": [100.0, 100.0],
        "speed": 50.0,
        "direction": 0.0,
        "displacement": 25.0,
        "state": "moving",
        "history_length": 5,
    }
    anomalies_0 = detector.detect([b0])
    assert len(anomalies_0) == 0

    # Observation at t=5.0 with apparent 180° turn across a 5.0s gap
    b1 = {
        "track_id": 1,
        "frame_id": 150,
        "timestamp": 5.0,
        "position": [75.0, 100.0],
        "speed": 50.0,
        "direction": 180.0,
        "displacement": 25.0,
        "state": "moving",
        "history_length": 5,
    }
    anomalies_1 = detector.detect([b1])
    # Must not trigger direction anomaly across gap
    dir_anomalies = [a for a in anomalies_1 if a["anomaly_type"] == AnomalyType.SUDDEN_DIRECTION_CHANGE.value]
    assert len(dir_anomalies) == 0


def test_direction_change_buffer_purges_stale_entries():
    """Verify that buffered direction-change evidence does not span across a gap."""
    detector = AnomalyDetector(AnomalyConfig(max_observation_gap=1.0))

    # Event 1 at t=0.0
    b0 = {
        "track_id": 1,
        "frame_id": 0,
        "timestamp": 0.0,
        "position": [100.0, 100.0],
        "speed": 50.0,
        "direction": 0.0,
        "displacement": 25.0,
        "state": "moving",
        "history_length": 5,
    }
    detector.detect([b0])

    # Event 2 at t=0.033 with 95° turn -> enters buffer (1st entry)
    b1 = {
        "track_id": 1,
        "frame_id": 1,
        "timestamp": 0.033,
        "position": [100.0, 125.0],
        "speed": 50.0,
        "direction": 95.0,
        "displacement": 25.0,
        "state": "moving",
        "history_length": 5,
    }
    detector.detect([b1])
    assert len(detector.direction_change_buffer.get(1, [])) == 1

    # Event 3 at t=6.0 (gap of ~6.0s) with 95° turn -> stale entry must be purged
    b2 = {
        "track_id": 1,
        "frame_id": 180,
        "timestamp": 6.0,
        "position": [100.0, 150.0],
        "speed": 50.0,
        "direction": 190.0,
        "displacement": 25.0,
        "state": "moving",
        "history_length": 5,
    }
    anomalies = detector.detect([b2])
    dir_anomalies = [a for a in anomalies if a["anomaly_type"] == AnomalyType.SUDDEN_DIRECTION_CHANGE.value]
    assert len(dir_anomalies) == 0, "Stale buffer entry from 6 seconds ago must not contribute to anomaly trigger"
