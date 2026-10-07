"""
Tests for YOLO detector
"""
import pytest
import numpy as np
from processing.detection.yolo_detector import YOLODetector, draw_detections


@pytest.fixture
def detector():
    """Create a detector instance for testing"""
    # Use CPU for testing to avoid GPU requirements
    return YOLODetector(model_name="yolov8n.pt", device="cpu")


def test_detector_initialization(detector):
    """Test detector can be initialized"""
    assert detector is not None
    assert detector.device == "cpu"
    assert detector.confidence_threshold == 0.5


def test_detect_empty_frame(detector):
    """Test detection on empty frame"""
    empty_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detector.detect(empty_frame)
    assert isinstance(detections, list)
    # Empty frame should have no detections
    assert len(detections) == 0


def test_detect_returns_correct_structure(detector):
    """Test that detections have correct structure"""
    # Create a simple test frame (blank, but valid)
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    detections = detector.detect(frame)

    # Even if no detections, should return list
    assert isinstance(detections, list)

    # If there are detections, check structure
    for det in detections:
        assert "bbox" in det
        assert "confidence" in det
        assert "class_id" in det
        assert "class_name" in det
        assert len(det["bbox"]) == 4


def test_get_class_names(detector):
    """Test getting class names"""
    class_names = detector.get_class_names()
    assert isinstance(class_names, dict)
    assert len(class_names) > 0
    # COCO dataset should have 'person' class
    assert "person" in class_names.values()


def test_get_person_class_id(detector):
    """Test getting person class ID"""
    person_id = detector.get_person_class_id()
    assert isinstance(person_id, int)
    assert person_id >= 0


def test_draw_detections_empty():
    """Test drawing with no detections"""
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    detections = []
    annotated = draw_detections(frame, detections)
    assert annotated.shape == frame.shape
    # Should be identical since no detections
    assert np.array_equal(annotated, frame)


def test_draw_detections_with_detection():
    """Test drawing with a sample detection"""
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
    detections = [
        {
            "bbox": [100, 100, 200, 200],
            "confidence": 0.85,
            "class_id": 0,
            "class_name": "person",
        }
    ]
    annotated = draw_detections(frame, detections)
    assert annotated.shape == frame.shape
    # Should be different since we drew on it
    assert not np.array_equal(annotated, frame)


def test_detect_with_none_frame(detector):
    """Test detection handles None frame gracefully"""
    detections = detector.detect(None)
    assert isinstance(detections, list)
    assert len(detections) == 0
