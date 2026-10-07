"""
Object detection module - YOLO integration

Main exports:
    YOLODetector: Object detector using YOLOv8
    VideoProcessor: Video processing pipeline
    get_video_info: Get video file information
"""

from processing.detection.yolo_detector import YOLODetector, draw_detections
from processing.detection.video_processor import (
    VideoProcessor,
    get_video_info,
    VideoProcessingError,
)

__all__ = [
    "YOLODetector",
    "draw_detections",
    "VideoProcessor",
    "get_video_info",
    "VideoProcessingError",
]
