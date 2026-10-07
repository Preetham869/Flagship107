"""
Tests for video processor
"""
import pytest
from pathlib import Path
from processing.detection.video_processor import (
    VideoProcessor,
    get_video_info,
    VideoProcessingError,
)
from processing.detection.yolo_detector import YOLODetector


@pytest.fixture
def detector():
    """Create a detector instance for testing"""
    return YOLODetector(model_name="yolov8n.pt", device="cpu")


@pytest.fixture
def processor(detector):
    """Create a video processor instance"""
    return VideoProcessor(detector)


def test_processor_initialization(processor):
    """Test processor can be initialized"""
    assert processor is not None
    assert processor.detector is not None


def test_get_video_info_nonexistent():
    """Test getting info for nonexistent video"""
    with pytest.raises(VideoProcessingError):
        get_video_info("nonexistent_video.mp4")


def test_process_video_nonexistent(processor):
    """Test processing nonexistent video"""
    with pytest.raises(VideoProcessingError):
        processor.process_video(
            "nonexistent_input.mp4",
            "nonexistent_output.mp4",
        )


def test_extract_frames_nonexistent(processor):
    """Test extracting frames from nonexistent video"""
    with pytest.raises(VideoProcessingError):
        processor.extract_frames("nonexistent_video.mp4", "output_dir")
