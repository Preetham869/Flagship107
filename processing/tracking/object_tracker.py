"""
Multi-object tracking module using YOLO's built-in tracking
Assigns persistent IDs to detected objects across frames
"""
from typing import List, Dict, Optional, Tuple
import logging

import numpy as np
import torch
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class TrackingError(Exception):
    """Custom exception for tracking errors"""

    pass


class ObjectTracker:
    """
    Multi-object tracker using YOLO's built-in tracking (ByteTrack)
    
    Provides persistent tracking IDs across video frames
    """

    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: Optional[str] = None,
        tracker_config: str = "bytetrack.yaml",
    ):
        """
        Initialize object tracker

        Args:
            model_name: YOLO model file (e.g., 'yolov8n.pt', 'yolov8s.pt')
            confidence_threshold: Minimum confidence score (0-1)
            iou_threshold: IoU threshold for NMS
            device: Device to run on ('cuda', 'cpu', or None for auto)
            tracker_config: Tracker configuration ('bytetrack.yaml' or 'botsort.yaml')
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.tracker_config = tracker_config

        # Determine device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        logger.info(f"Initializing object tracker on device: {self.device}")
        logger.info(f"Using tracker: {tracker_config}")

        try:
            # Load YOLO model
            self.model = YOLO(model_name)
            self.model.to(self.device)
            logger.info(f"YOLO model {model_name} loaded for tracking")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise TrackingError(f"Model loading failed: {e}")

        # Track statistics
        self.active_track_ids = set()
        self.total_tracks_seen = 0

    def track(
        self, frame: np.ndarray, classes: Optional[List[int]] = None, persist: bool = True
    ) -> List[Dict]:
        """
        Track objects in a single frame with persistent IDs

        Args:
            frame: Input frame as numpy array (H, W, C) in BGR format
            classes: List of class IDs to track (None for all classes)
            persist: Whether to persist tracks across frames

        Returns:
            List of tracks, each containing:
            - track_id: Persistent tracking ID
            - bbox: [x1, y1, x2, y2]
            - confidence: float
            - class_id: int
            - class_name: str
        """
        if frame is None or frame.size == 0:
            logger.warning("Empty frame provided to tracker")
            return []

        try:
            # Run tracking with YOLO
            results = self.model.track(
                frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                classes=classes,
                persist=persist,
                tracker=self.tracker_config,
                verbose=False,
                device=self.device,
            )

            tracks = []

            # Parse tracking results
            if len(results) > 0:
                result = results[0]  # Single frame result

                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes.xyxy.cpu().numpy()  # [x1, y1, x2, y2]
                    confidences = result.boxes.conf.cpu().numpy()
                    class_ids = result.boxes.cls.cpu().numpy().astype(int)

                    # Get track IDs (if available)
                    if result.boxes.id is not None:
                        track_ids = result.boxes.id.cpu().numpy().astype(int)
                    else:
                        # Fallback: use sequential IDs if tracking not available
                        track_ids = np.arange(len(boxes))

                    for box, conf, cls_id, track_id in zip(
                        boxes, confidences, class_ids, track_ids
                    ):
                        track = {
                            "track_id": int(track_id),
                            "bbox": box.tolist(),
                            "confidence": float(conf),
                            "class_id": int(cls_id),
                            "class_name": self.model.names[int(cls_id)],
                        }
                        tracks.append(track)

                        # Update statistics
                        self.active_track_ids.add(int(track_id))
                        if int(track_id) > self.total_tracks_seen:
                            self.total_tracks_seen = int(track_id)

            return tracks

        except Exception as e:
            logger.error(f"Error during tracking: {e}")
            return []

    def get_class_names(self) -> Dict[int, str]:
        """
        Get mapping of class IDs to class names

        Returns:
            Dictionary mapping class ID to class name
        """
        return self.model.names

    def get_person_class_id(self) -> int:
        """
        Get the class ID for 'person' in COCO dataset

        Returns:
            Class ID for person (typically 0)
        """
        for class_id, class_name in self.model.names.items():
            if class_name.lower() == "person":
                return class_id
        logger.warning("Person class not found in model")
        return 0  # Default to 0 for COCO

    def get_statistics(self) -> Dict:
        """
        Get tracking statistics

        Returns:
            Dictionary with tracking statistics
        """
        return {
            "active_tracks": len(self.active_track_ids),
            "total_tracks_seen": self.total_tracks_seen,
        }

    def reset(self):
        """Reset tracking state"""
        self.active_track_ids.clear()
        self.total_tracks_seen = 0
        logger.info("Tracker state reset")


def draw_tracks(
    frame: np.ndarray,
    tracks: List[Dict],
    show_id: bool = True,
    color_per_track: bool = True,
) -> np.ndarray:
    """
    Draw tracking bounding boxes and IDs on frame

    Args:
        frame: Input frame as numpy array (H, W, C)
        tracks: List of tracks from track()
        show_id: Whether to show track IDs
        color_per_track: Use unique color per track ID

    Returns:
        Annotated frame
    """
    import cv2

    annotated = frame.copy()

    # Color palette for different tracks
    colors = [
        (0, 255, 0),  # Green
        (255, 0, 0),  # Blue
        (0, 0, 255),  # Red
        (255, 255, 0),  # Cyan
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Yellow
        (128, 0, 255),  # Purple
        (255, 128, 0),  # Orange
    ]

    for track in tracks:
        bbox = track["bbox"]
        x1, y1, x2, y2 = map(int, bbox)
        track_id = track["track_id"]

        # Select color
        if color_per_track:
            color = colors[track_id % len(colors)]
        else:
            color = (0, 255, 0)

        # Draw bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

        # Prepare label
        if show_id:
            label = f"{track['class_name']} #{track_id} {track['confidence']:.2f}"
        else:
            label = f"{track['class_name']} {track['confidence']:.2f}"

        # Draw label background
        (label_width, label_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )
        cv2.rectangle(
            annotated,
            (x1, y1 - label_height - baseline - 5),
            (x1 + label_width, y1),
            color,
            -1,
        )

        # Draw label text
        cv2.putText(
            annotated,
            label,
            (x1, y1 - baseline - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

    return annotated
