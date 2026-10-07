"""
Command-line interface for video detection pipeline
"""
import argparse
import logging
import sys
from pathlib import Path

from processing.detection.yolo_detector import YOLODetector
from processing.detection.video_processor import (
    VideoProcessor,
    get_video_info,
    VideoProcessingError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def progress_callback(current: int, total: int):
    """Display progress"""
    percent = (current / total) * 100
    print(f"\rProgress: {current}/{total} frames ({percent:.1f}%)", end="", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Flagship 107 - Video Object Detection Pipeline"
    )
    parser.add_argument("input_video", type=str, help="Path to input video file")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Path to output video file (default: input_annotated.mp4)",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="yolov8n.pt",
        help="YOLO model name (default: yolov8n.pt)",
    )
    parser.add_argument(
        "-c",
        "--confidence",
        type=float,
        default=0.5,
        help="Confidence threshold (default: 0.5)",
    )
    parser.add_argument(
        "--person-only",
        action="store_true",
        help="Detect only people (class 0)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device to use (cuda/cpu, default: auto)",
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=1,
        help="Process every Nth frame (default: 1)",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show video info and exit",
    )

    args = parser.parse_args()

    # Validate input
    input_path = Path(args.input_video)
    if not input_path.exists():
        logger.error(f"Input video not found: {input_path}")
        sys.exit(1)

    # Show video info if requested
    if args.info:
        try:
            info = get_video_info(str(input_path))
            print("\nVideo Information:")
            print(f"  Path: {info['path']}")
            print(f"  Resolution: {info['width']}x{info['height']}")
            print(f"  FPS: {info['fps']:.2f}")
            print(f"  Frames: {info['total_frames']}")
            print(f"  Duration: {info['duration_seconds']:.2f} seconds")
            print(f"  Size: {info['size_bytes'] / (1024*1024):.2f} MB")
            sys.exit(0)
        except VideoProcessingError as e:
            logger.error(f"Failed to get video info: {e}")
            sys.exit(1)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.parent / f"{input_path.stem}_annotated.mp4"

    logger.info("=" * 60)
    logger.info("Flagship 107 - Video Object Detection")
    logger.info("=" * 60)
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Model: {args.model}")
    logger.info(f"Confidence: {args.confidence}")
    logger.info(f"Device: {args.device or 'auto'}")
    logger.info("=" * 60)

    try:
        # Initialize detector
        logger.info("Loading YOLO model...")
        detector = YOLODetector(
            model_name=args.model,
            confidence_threshold=args.confidence,
            device=args.device,
        )

        # Determine classes to detect
        detect_classes = None
        if args.person_only:
            person_class_id = detector.get_person_class_id()
            detect_classes = [person_class_id]
            logger.info(f"Detecting only people (class {person_class_id})")

        # Initialize processor
        processor = VideoProcessor(detector, detect_classes=detect_classes)

        # Process video
        logger.info("Processing video...")
        stats = processor.process_video(
            str(input_path),
            str(output_path),
            progress_callback=progress_callback,
            frame_skip=args.skip,
        )

        print()  # New line after progress
        logger.info("=" * 60)
        logger.info("Processing Complete!")
        logger.info("=" * 60)
        logger.info(f"Processed frames: {stats['processed_frames']}")
        logger.info(f"Total detections: {stats['total_detections']}")
        if stats["processed_frames"] > 0:
            avg_det = stats["total_detections"] / stats["processed_frames"]
            logger.info(f"Average detections per frame: {avg_det:.2f}")
        logger.info(f"Output saved to: {output_path}")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
