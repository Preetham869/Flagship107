"""
Tests for object tracker
"""
import pytest
import numpy as np
from processing.tracking.object_tracker import ObjectTracker, draw_tracks, TrackingError


@pytest.fixture
def tracker():
    """Create a tracker instance for testing"""
    # Use CPU for testing to avoid GPU requirements
    return ObjectTracker(model_name="yolov8n.pt", device="cpu")


def test_tracker_initialization(tracker):
    """Test tracker can be initialized"""
    assert tracker is not None
    assert tracker.device == "cpu"
    assert tracker.confidence_threshold == 0.5
    assert tracker.tracker_config == "bytetrack.yaml"


def test_track_empty_frame(tracker):
    """Test tracking on empty frame"""
    empty_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    tracks = tracker.track(empty_frame)
    assert isinstance(tracks, list)
    # Empty frame should have no tracks
    assert len(tracks) == 0


def test_track_returns_correct_structure(tracker):
    """Test that tracks have correct structure"""
    # Create a simple test frame
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    tracks = tracker.track(frame)

    # Even if no tracks, should return list
    assert isinstance(tracks, list)

    # If there are tracks, check structure
    for track in tracks:
        assert "track_id" in track
        assert "bbox" in track
        assert "confidence" in track
        assert "class_id" in track
        assert "class_name" in track
        assert len(track["bbox"]) == 4
        assert isinstance(track["track_id"], int)


def test_get_class_names(tracker):
    """Test getting class names"""
    class_names = tracker.get_class_names()
    assert isinstance(class_names, dict)
    assert len(class_names) > 0
    # COCO dataset should have 'person' class
    assert "person" in class_names.values()


def test_get_person_class_id(tracker):
    """Test getting person class ID"""
    person_id = tracker.get_person_class_id()
    assert isinstance(person_id, int)
    assert person_id >= 0


def test_get_statistics(tracker):
    """Test getting tracker statistics"""
    stats = tracker.get_statistics()
    assert isinstance(stats, dict)
    assert "active_tracks" in stats
    assert "total_tracks_seen" in stats
    assert stats["active_tracks"] >= 0
    assert stats["total_tracks_seen"] >= 0


def test_reset(tracker):
    """Test tracker reset"""
    # Add some data to tracker
    tracker.active_track_ids.add(1)
    tracker.total_tracks_seen = 5

    # Reset
    tracker.reset()

    # Check reset worked
    assert len(tracker.active_track_ids) == 0
    assert tracker.total_tracks_seen == 0


def test_draw_tracks_empty():
    """Test drawing with no tracks"""
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    tracks = []
    annotated = draw_tracks(frame, tracks)
    assert annotated.shape == frame.shape
    # Should be identical since no tracks
    assert np.array_equal(annotated, frame)


def test_draw_tracks_with_track():
    """Test drawing with a sample track"""
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    tracks = [
        {
            "track_id": 1,
            "bbox": [100, 100, 200, 200],
            "confidence": 0.85,
            "class_id": 0,
            "class_name": "person",
        }
    ]
    annotated = draw_tracks(frame, tracks, show_id=True)
    assert annotated.shape == frame.shape
    # Should be different since we drew on it
    assert not np.array_equal(annotated, frame)


def test_track_with_none_frame(tracker):
    """Test tracking handles None frame gracefully"""
    tracks = tracker.track(None)
    assert isinstance(tracks, list)
    assert len(tracks) == 0
