"""
Video processing pipeline for object detection
Handles frame extraction, detection, and output video generation
"""
from typing import List, Dict, Optional, Callable
import logging
from pathlib import Path

import cv2
import numpy as np

from processing.detection.yolo_detector import YOLODetector, draw_detections

logger = logging.getLogger(__name__)


class VideoProcessingError(Exception):
    """Custom exception for video processing errors"""

    pass


class VideoProcessor:
    """
    Video processing pipeline for object detection
    """

    def __init__(
        self,
        detector: YOLODetector,
        detect_classes: Optional[List[int]] = None,
    ):
        """
        Initialize video processor

        Args:
            detector: Initialized YOLODetector instance
            detect_classes: List of class IDs to detect (None for all)
        """
        self.detector = detector
        self.detect_classes = detect_classes

    def process_video(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        frame_skip: int = 1,
    ) -> Dict:
        """
        Process video file with object detection

        Args:
            input_path: Path to input video file
            output_path: Path to save annotated output video
            progress_callback: Optional callback(current_frame, total_frames)
            frame_skip: Process every Nth frame (1 = every frame)

        Returns:
            Processing results with statistics

        Raises:
            VideoProcessingError: If video processing fails
        """
        input_path = Path(input_path)
        output_path = Path(output_path)

        # Validate input
        if not input_path.exists():
            raise VideoProcessingError(f"Input video not found: {input_path}")

        logger.info(f"Processing video: {input_path}")

        # Open video
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise VideoProcessingError(f"Failed to open video: {input_path}")

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        logger.info(
            f"Video properties: {width}x{height}, {fps} FPS, {total_frames} frames"
        )

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

        if not out.isOpened():
            cap.release()
            raise VideoProcessingError(f"Failed to create output video: {output_path}")

        # Processing statistics
        stats = {
            "total_frames": total_frames,
            "processed_frames": 0,
            "total_detections": 0,
            "detections_per_frame": [],
            "fps": fps,
            "resolution": (width, height),
            "input_path": str(input_path),
            "output_path": str(output_path),
        }

        try:
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Skip frames if requested
                if frame_idx % frame_skip == 0:
                    # Detect objects
                    detections = self.detector.detect(frame, classes=self.detect_classes)

                    # Draw annotations
                    annotated_frame = draw_detections(frame, detections)

                    # Update statistics
                    stats["detections_per_frame"].append(len(detections))
                    stats["total_detections"] += len(detections)
                else:
                    # Use original frame without detection
                    annotated_frame = frame

                # Write frame
                out.write(annotated_frame)

                frame_idx += 1
                stats["processed_frames"] = frame_idx

                # Progress callback
                if progress_callback:
                    progress_callback(frame_idx, total_frames)

                # Log progress
                if frame_idx % 30 == 0:
                    logger.info(f"Processed {frame_idx}/{total_frames} frames")

        except Exception as e:
            logger.error(f"Error during video processing: {e}")
            raise VideoProcessingError(f"Video processing failed: {e}")

        finally:
            cap.release()
            out.release()

        logger.info(
            f"Processing complete: {stats['processed_frames']} frames, "
            f"{stats['total_detections']} total detections"
        )

        return stats

    def extract_frames(
        self,
        video_path: str,
        output_dir: str,
        sample_rate: int = 1,
        max_frames: Optional[int] = None,
    ) -> List[str]:
        """
        Extract frames from video

        Args:
            video_path: Path to input video
            output_dir: Directory to save extracted frames
            sample_rate: Extract every Nth frame
            max_frames: Maximum number of frames to extract

        Returns:
            List of paths to extracted frame images

        Raises:
            VideoProcessingError: If extraction fails
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)

        if not video_path.exists():
            raise VideoProcessingError(f"Video not found: {video_path}")

        output_dir.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise VideoProcessingError(f"Failed to open video: {video_path}")

        frame_paths = []
        frame_idx = 0
        saved_count = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Check if we should save this frame
                if frame_idx % sample_rate == 0:
                    frame_filename = output_dir / f"frame_{frame_idx:06d}.jpg"
                    cv2.imwrite(str(frame_filename), frame)
                    frame_paths.append(str(frame_filename))
                    saved_count += 1

                    if max_frames and saved_count >= max_frames:
                        break

                frame_idx += 1

        finally:
            cap.release()

        logger.info(f"Extracted {saved_count} frames to {output_dir}")
        return frame_paths


def get_video_info(video_path: str) -> Dict:
    """
    Get video file information

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with video properties

    Raises:
        VideoProcessingError: If video cannot be read
    """
    video_path = Path(video_path)

    if not video_path.exists():
        raise VideoProcessingError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise VideoProcessingError(f"Failed to open video: {video_path}")

    try:
        info = {
            "path": str(video_path),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "duration_seconds": cap.get(cv2.CAP_PROP_FRAME_COUNT)
            / cap.get(cv2.CAP_PROP_FPS),
            "size_bytes": video_path.stat().st_size,
        }
    finally:
        cap.release()

    return info
