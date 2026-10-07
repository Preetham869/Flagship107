"""
Tests for video tracker
"""
import pytest
from pathlib import Path
from processing.tracking.video_tracker import (
    VideoTracker,
    get_video_info,
    TrackingError,
)
from processing.tracking.object_tracker import ObjectTracker


@pytest.fixture
def tracker():
    """Create a tracker instance for testing"""
    return ObjectTracker(model_name="yolov8n.pt", device="cpu")


@pytest.fixture
def video_tracker(tracker):
    """Create a video tracker instance"""
    return VideoTracker(tracker)


def test_video_tracker_initialization(video_tracker):
    """Test video tracker can be initialized"""
    assert video_tracker is not None
    assert video_tracker.tracker is not None


def test_get_video_info_nonexistent():
    """Test getting info for nonexistent video"""
    with pytest.raises(TrackingError):
        get_video_info("nonexistent_video.mp4")


def test_process_video_nonexistent(video_tracker):
    """Test processing nonexistent video"""
    with pytest.raises(TrackingError):
        video_tracker.process_video(
            "nonexistent_input.mp4",
            "nonexistent_output.mp4",
        )
