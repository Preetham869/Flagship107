"""
YOLO-based object detection module
Detects people and objects in video frames using Ultralytics YOLOv8
"""
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path

import numpy as np
import torch
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class YOLODetector:
    """
    YOLOv8 object detector with GPU/CPU fallback
    """

    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: Optional[str] = None,
    ):
        """
        Initialize YOLO detector

        Args:
            model_name: YOLO model file (e.g., 'yolov8n.pt', 'yolov8s.pt')
            confidence_threshold: Minimum confidence score (0-1)
            iou_threshold: IoU threshold for NMS
            device: Device to run on ('cuda', 'cpu', or None for auto)
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold

        # Determine device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        logger.info(f"Initializing YOLO detector on device: {self.device}")

        try:
            # Load YOLO model
            self.model = YOLO(model_name)
            self.model.to(self.device)
            logger.info(f"YOLO model {model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise

    def detect(
        self, frame: np.ndarray, classes: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Detect objects in a single frame

        Args:
            frame: Input frame as numpy array (H, W, C) in BGR format
            classes: List of class IDs to detect (None for all classes)

        Returns:
            List of detections, each containing:
            - bbox: [x1, y1, x2, y2]
            - confidence: float
            - class_id: int
            - class_name: str
        """
        if frame is None or frame.size == 0:
            logger.warning("Empty frame provided to detector")
            return []

        try:
            # Run inference
            results = self.model.predict(
                frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                classes=classes,
                verbose=False,
                device=self.device,
            )

            detections = []

            # Parse results
            if len(results) > 0:
                result = results[0]  # Single frame result

                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes.xyxy.cpu().numpy()  # [x1, y1, x2, y2]
                    confidences = result.boxes.conf.cpu().numpy()
                    class_ids = result.boxes.cls.cpu().numpy().astype(int)

                    for box, conf, cls_id in zip(boxes, confidences, class_ids):
                        detection = {
                            "bbox": box.tolist(),
                            "confidence": float(conf),
                            "class_id": int(cls_id),
                            "class_name": self.model.names[int(cls_id)],
                        }
                        detections.append(detection)

            return detections

        except Exception as e:
            logger.error(f"Error during detection: {e}")
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


def draw_detections(
    frame: np.ndarray,
    detections: List[Dict],
    color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> np.ndarray:
    """
    Draw bounding boxes and labels on frame

    Args:
        frame: Input frame as numpy array (H, W, C)
        detections: List of detections from detect()
        color: BGR color tuple for bounding boxes
        thickness: Line thickness

    Returns:
        Annotated frame
    """
    import cv2

    annotated = frame.copy()

    for det in detections:
        bbox = det["bbox"]
        x1, y1, x2, y2 = map(int, bbox)

        # Draw bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

        # Prepare label
        label = f"{det['class_name']} {det['confidence']:.2f}"

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
