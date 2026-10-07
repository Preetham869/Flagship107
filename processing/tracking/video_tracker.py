"""
Video tracking pipeline for multi-object tracking
Handles frame-by-frame tracking with persistent IDs
"""
from typing import List, Dict, Optional, Callable
import logging
from pathlib import Path

import cv2
import numpy as np

from processing.tracking.object_tracker import ObjectTracker, draw_tracks, TrackingError

logger = logging.getLogger(__name__)


class VideoTracker:
    """
    Video processing pipeline with object tracking
    """

    def __init__(
        self,
        tracker: ObjectTracker,
        track_classes: Optional[List[int]] = None,
    ):
        """
        Initialize video tracker

        Args:
            tracker: Initialized ObjectTracker instance
            track_classes: List of class IDs to track (None for all)
        """
        self.tracker = tracker
        self.track_classes = track_classes

    def process_video(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        frame_skip: int = 1,
        export_data: bool = True,
    ) -> Dict:
        """
        Process video file with object tracking

        Args:
            input_path: Path to input video file
            output_path: Path to save annotated output video
            progress_callback: Optional callback(current_frame, total_frames)
            frame_skip: Process every Nth frame (1 = every frame)
            export_data: Whether to export tracking data to JSON

        Returns:
            Processing results with statistics and track data

        Raises:
            TrackingError: If video processing fails
        """
        input_path = Path(input_path)
        output_path = Path(output_path)

        # Validate input
        if not input_path.exists():
            raise TrackingError(f"Input video not found: {input_path}")

        logger.info(f"Processing video with tracking: {input_path}")

        # Open video
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise TrackingError(f"Failed to open video: {input_path}")

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
            raise TrackingError(f"Failed to create output video: {output_path}")

        # Processing statistics
        stats = {
            "total_frames": total_frames,
            "processed_frames": 0,
            "total_tracks": 0,
            "unique_track_ids": set(),
            "tracks_per_frame": [],
            "frame_data": [],  # Detailed per-frame tracking data
            "fps": fps,
            "resolution": (width, height),
            "input_path": str(input_path),
            "output_path": str(output_path),
        }

        # Reset tracker for fresh video
        self.tracker.reset()

        try:
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Calculate timestamp
                timestamp = frame_idx / fps

                # Track objects (skip tracking on skipped frames but still write frame)
                if frame_idx % frame_skip == 0:
                    # Track objects with persistent IDs
                    tracks = self.tracker.track(frame, classes=self.track_classes)

                    # Draw annotations
                    annotated_frame = draw_tracks(frame, tracks, show_id=True)

                    # Update statistics
                    stats["tracks_per_frame"].append(len(tracks))
                    stats["total_tracks"] += len(tracks)

                    # Record unique track IDs
                    for track in tracks:
                        stats["unique_track_ids"].add(track["track_id"])

                    # Store frame data if export requested
                    if export_data:
                        frame_data = {
                            "frame_id": frame_idx,
                            "timestamp": timestamp,
                            "tracks": tracks,
                        }
                        stats["frame_data"].append(frame_data)
                else:
                    # Use original frame without tracking
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
            logger.error(f"Error during video tracking: {e}")
            raise TrackingError(f"Video tracking failed: {e}")

        finally:
            cap.release()
            out.release()

        # Get tracker statistics
        tracker_stats = self.tracker.get_statistics()
        stats["tracker_stats"] = tracker_stats
        stats["unique_track_count"] = len(stats["unique_track_ids"])

        logger.info(
            f"Tracking complete: {stats['processed_frames']} frames, "
            f"{stats['unique_track_count']} unique tracks"
        )

        # Export tracking data to JSON if requested
        if export_data:
            self._export_tracking_data(stats, output_path)

        return stats

    def _export_tracking_data(self, stats: Dict, video_path: Path):
        """
        Export tracking data to JSON file

        Args:
            stats: Statistics dictionary with frame_data
            video_path: Path to output video (JSON will be saved alongside)
        """
        import json

        # Convert set to list for JSON serialization
        export_stats = stats.copy()
        export_stats["unique_track_ids"] = list(stats["unique_track_ids"])

        json_path = video_path.with_suffix(".json")

        try:
            with open(json_path, "w") as f:
                json.dump(export_stats, f, indent=2)
            logger.info(f"Tracking data exported to: {json_path}")
        except Exception as e:
            logger.warning(f"Failed to export tracking data: {e}")


def get_video_info(video_path: str) -> Dict:
    """
    Get video file information

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with video properties

    Raises:
        TrackingError: If video cannot be read
    """
    video_path = Path(video_path)

    if not video_path.exists():
        raise TrackingError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise TrackingError(f"Failed to open video: {video_path}")

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
