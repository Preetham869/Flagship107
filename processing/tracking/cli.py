"""
Command-line interface for video tracking pipeline
"""
import argparse
import logging
import sys
from pathlib import Path

from processing.tracking.object_tracker import ObjectTracker
from processing.tracking.video_tracker import VideoTracker, get_video_info, TrackingError

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
        description="Flagship 107 - Video Multi-Object Tracking Pipeline"
    )
    parser.add_argument("input_video", type=str, help="Path to input video file")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Path to output video file (default: input_tracked.mp4)",
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
        help="Track only people (class 0)",
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
        "--tracker",
        type=str,
        default="bytetrack.yaml",
        choices=["bytetrack.yaml", "botsort.yaml"],
        help="Tracker configuration (default: bytetrack.yaml)",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Don't export tracking data to JSON",
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
        except TrackingError as e:
            logger.error(f"Failed to get video info: {e}")
            sys.exit(1)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.parent / f"{input_path.stem}_tracked.mp4"

    logger.info("=" * 60)
    logger.info("Flagship 107 - Video Multi-Object Tracking")
    logger.info("=" * 60)
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Model: {args.model}")
    logger.info(f"Confidence: {args.confidence}")
    logger.info(f"Tracker: {args.tracker}")
    logger.info(f"Device: {args.device or 'auto'}")
    logger.info("=" * 60)

    try:
        # Initialize tracker
        logger.info("Loading YOLO model with tracking...")
        tracker = ObjectTracker(
            model_name=args.model,
            confidence_threshold=args.confidence,
            device=args.device,
            tracker_config=args.tracker,
        )

        # Determine classes to track
        track_classes = None
        if args.person_only:
            person_class_id = tracker.get_person_class_id()
            track_classes = [person_class_id]
            logger.info(f"Tracking only people (class {person_class_id})")

        # Initialize video tracker
        video_tracker = VideoTracker(tracker, track_classes=track_classes)

        # Process video
        logger.info("Processing video with tracking...")
        stats = video_tracker.process_video(
            str(input_path),
            str(output_path),
            progress_callback=progress_callback,
            frame_skip=args.skip,
            export_data=not args.no_export,
        )

        print()  # New line after progress
        logger.info("=" * 60)
        logger.info("Tracking Complete!")
        logger.info("=" * 60)
        logger.info(f"Processed frames: {stats['processed_frames']}")
        logger.info(f"Unique tracks: {stats['unique_track_count']}")
        logger.info(f"Total detections: {stats['total_tracks']}")
        if stats["processed_frames"] > 0:
            avg_tracks = stats["total_tracks"] / stats["processed_frames"]
            logger.info(f"Average tracks per frame: {avg_tracks:.2f}")
        logger.info(f"Output video: {output_path}")
        if not args.no_export:
            json_path = output_path.with_suffix(".json")
            logger.info(f"Tracking data: {json_path}")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
