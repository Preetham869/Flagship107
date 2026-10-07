"""
Multi-object tracking module

Main exports:
    ObjectTracker: Multi-object tracker using YOLO tracking
    VideoTracker: Video processing pipeline with tracking
    draw_tracks: Draw tracking annotations on frames
"""

from processing.tracking.object_tracker import (
    ObjectTracker,
    draw_tracks,
    TrackingError,
)
from processing.tracking.video_tracker import VideoTracker, get_video_info

__all__ = [
    "ObjectTracker",
    "draw_tracks",
    "TrackingError",
    "VideoTracker",
    "get_video_info",
]
