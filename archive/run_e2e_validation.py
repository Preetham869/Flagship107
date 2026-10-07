#!/usr/bin/env python3
"""
Flagship 107 - End-to-End Video Intelligence Pipeline Validation

Runs complete M1-M6 pipeline on real video and produces validation report.
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add processing module to path
sys.path.insert(0, str(Path(__file__).parent))

from processing.pipeline import EndToEndPipeline, PipelineConfig

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


def generate_validation_report(result, output_path: str):
    """
    Generate human-readable validation report
    
    Args:
        result: PipelineResult
        output_path: Path to save report
    """
    with open(output_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("FLAGSHIP 107 - END-TO-END PIPELINE VALIDATION REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Video: {result.video_path}\n\n")
        
        # Video Information
        f.write("=" * 80 + "\n")
        f.write("VIDEO INFORMATION\n")
        f.write("=" * 80 + "\n")
        f.write(f"Resolution: {result.video_width}x{result.video_height}\n")
        f.write(f"FPS: {result.video_fps:.2f}\n")
        f.write(f"Total Frames: {result.video_total_frames}\n")
        f.write(f"Duration: {result.video_duration:.2f} seconds\n")
        f.write(f"Frames Processed: {result.frames_processed}\n")
        f.write(f"Frames Skipped: {result.frames_skipped}\n")
        f.write(f"Processing Time: {result.processing_time:.2f} seconds\n")
        fps_processing = result.frames_processed / result.processing_time if result.processing_time > 0 else 0
        f.write(f"Processing FPS: {fps_processing:.2f}\n\n")
        
        # M1: Detection
        f.write("=" * 80 + "\n")
        f.write("M1: OBJECT DETECTION\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Detections: {result.m1_total_detections}\n")
        f.write(f"Average Detections per Frame: {result.m1_avg_detections_per_frame:.2f}\n")
        f.write("\nDetections by Class:\n")
        for class_name, count in sorted(result.m1_detections_by_class.items()):
            f.write(f"  {class_name}: {count}\n")
        f.write("\n")
        
        # M2: Tracking
        f.write("=" * 80 + "\n")
        f.write("M2: MULTI-OBJECT TRACKING\n")
        f.write("=" * 80 + "\n")
        f.write(f"Unique Track IDs: {result.m2_unique_tracks}\n")
        f.write(f"Total Track Observations: {result.m2_total_track_observations}\n")
        f.write(f"Average Tracks per Frame: {result.m2_avg_tracks_per_frame:.2f}\n")
        if result.m2_track_duration_stats:
            f.write("\nTrack Duration Statistics:\n")
            f.write(f"  Min Duration: {result.m2_track_duration_stats['min']:.2f}s\n")
            f.write(f"  Max Duration: {result.m2_track_duration_stats['max']:.2f}s\n")
            f.write(f"  Avg Duration: {result.m2_track_duration_stats['avg']:.2f}s\n")
        f.write("\n")
        
        # M3: Behavior
        f.write("=" * 80 + "\n")
        f.write("M3: BEHAVIOR ANALYSIS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Behavior Updates: {result.m3_total_behaviors}\n")
        f.write(f"Average Speed: {result.m3_avg_speed:.2f} px/s\n")
        f.write(f"Max Speed: {result.m3_max_speed:.2f} px/s\n")
        f.write("\nStates Observed:\n")
        for state, count in sorted(result.m3_states_observed.items()):
            f.write(f"  {state}: {count}\n")
        f.write("\n")
        
        # M4: Anomaly Detection
        f.write("=" * 80 + "\n")
        f.write("M4: ANOMALY DETECTION\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Anomalies: {result.m4_total_anomalies}\n")
        f.write("\nAnomalies by Type:\n")
        for anom_type, count in sorted(result.m4_anomalies_by_type.items()):
            f.write(f"  {anom_type}: {count}\n")
        f.write("\nSeverity Distribution:\n")
        for severity, count in sorted(result.m4_severity_distribution.items()):
            f.write(f"  {severity}: {count}\n")
        f.write("\n")
        
        # M5: Event Correlation
        f.write("=" * 80 + "\n")
        f.write("M5: EVENT CORRELATION\n")
        f.write("=" * 80 + "\n")
        f.write(f"Raw Anomalies: {result.m5_total_raw_anomalies}\n")
        f.write(f"Correlated Events: {result.m5_correlated_events}\n")
        if result.m5_total_raw_anomalies > 0:
            reduction = (1 - result.m5_compression_ratio) * 100
            f.write(f"Alert Reduction: {reduction:.1f}%\n")
            f.write(f"Compression Ratio: {result.m5_compression_ratio:.3f}\n")
        f.write("\nEvents by Type:\n")
        for event_type, count in sorted(result.m5_events_by_type.items()):
            f.write(f"  {event_type}: {count}\n")
        f.write("\nEvent Severity Distribution:\n")
        for severity, count in sorted(result.m5_event_severity_distribution.items()):
            f.write(f"  {severity}: {count}\n")
        f.write("\n")
        
        # M6: Interactions
        f.write("=" * 80 + "\n")
        f.write("M6: MULTI-ENTITY INTERACTIONS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total Relationships: {result.m6_total_relationships}\n")
        f.write(f"Tracked Pairs: {result.m6_tracked_pairs}\n")
        f.write(f"Groups Formed: {result.m6_groups_formed}\n")
        f.write("\nRelationships by Type:\n")
        for rel_type, count in sorted(result.m6_relationships_by_type.items()):
            f.write(f"  {rel_type}: {count}\n")
        f.write("\n")
        
        # Summary
        f.write("=" * 80 + "\n")
        f.write("PIPELINE SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"[OK] M1: Detection - {result.m1_total_detections} detections\n")
        f.write(f"[OK] M2: Tracking - {result.m2_unique_tracks} tracks\n")
        f.write(f"[OK] M3: Behavior - {result.m3_total_behaviors} updates\n")
        f.write(f"[OK] M4: Anomalies - {result.m4_total_anomalies} detected\n")
        f.write(f"[OK] M5: Events - {result.m5_correlated_events} correlated\n")
        f.write(f"[OK] M6: Interactions - {result.m6_total_relationships} relationships\n")
        f.write("\n")
        f.write(f"Total Processing Time: {result.processing_time:.2f}s\n")
        f.write(f"Processing Speed: {fps_processing:.2f} FPS\n")
        f.write("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Flagship 107 - End-to-End Pipeline Validation"
    )
    parser.add_argument(
        "input_video",
        type=str,
        help="Path to input video file"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Path to output annotated video (optional)"
    )
    parser.add_argument(
        "--json",
        type=str,
        help="Path to save JSON results (default: <input>_e2e_result.json)"
    )
    parser.add_argument(
        "--report",
        type=str,
        help="Path to save validation report (default: <input>_e2e_report.txt)"
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default="yolov8n.pt",
        help="YOLO model name (default: yolov8n.pt)"
    )
    parser.add_argument(
        "-c", "--confidence",
        type=float,
        default=0.5,
        help="Confidence threshold (default: 0.5)"
    )
    parser.add_argument(
        "--person-only",
        action="store_true",
        help="Track only people"
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=1,
        help="Process every Nth frame (default: 1)"
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        help="Maximum frames to process (for testing)"
    )
    parser.add_argument(
        "--device",
        type=str,
        help="Device to use (cuda/cpu, default: auto)"
    )
    
    args = parser.parse_args()
    
    # Validate input
    input_path = Path(args.input_video)
    if not input_path.exists():
        logger.error(f"Input video not found: {input_path}")
        sys.exit(1)
    
    # Determine output paths
    output_video_path = args.output
    
    if args.json:
        json_path = Path(args.json)
    else:
        json_path = input_path.parent / f"{input_path.stem}_e2e_result.json"
    
    if args.report:
        report_path = Path(args.report)
    else:
        report_path = input_path.parent / f"{input_path.stem}_e2e_report.txt"
    
    # Print header
    print("=" * 80)
    print("FLAGSHIP 107 - END-TO-END PIPELINE VALIDATION")
    print("=" * 80)
    print(f"Input Video: {input_path}")
    print(f"Model: {args.model}")
    print(f"Confidence: {args.confidence}")
    print(f"Frame Skip: {args.skip}")
    if args.max_frames:
        print(f"Max Frames: {args.max_frames}")
    if output_video_path:
        print(f"Output Video: {output_video_path}")
    print(f"JSON Output: {json_path}")
    print(f"Report Output: {report_path}")
    print("=" * 80)
    print()
    
    try:
        # Create pipeline
        config = PipelineConfig(
            model_name=args.model,
            confidence_threshold=args.confidence,
            device=args.device,
            person_only=args.person_only,
            frame_skip=args.skip,
            max_frames=args.max_frames,
        )
        
        pipeline = EndToEndPipeline(config)
        
        # Process video
        logger.info("Processing video through M1-M6 pipeline...")
        result = pipeline.process_video(
            str(input_path),
            output_video_path=output_video_path,
            progress_callback=progress_callback,
        )
        
        print()  # New line after progress
        print()
        
        # Save JSON results
        logger.info(f"Saving JSON results to {json_path}")
        result.to_json(str(json_path))
        
        # Generate validation report
        logger.info(f"Generating validation report to {report_path}")
        generate_validation_report(result, str(report_path))
        
        # Print summary
        print("=" * 80)
        print("VALIDATION COMPLETE!")
        print("=" * 80)
        print(f"✅ M1: {result.m1_total_detections} detections")
        print(f"✅ M2: {result.m2_unique_tracks} unique tracks")
        print(f"✅ M3: {result.m3_total_behaviors} behavior updates")
        print(f"✅ M4: {result.m4_total_anomalies} anomalies")
        print(f"✅ M5: {result.m5_correlated_events} events")
        print(f"✅ M6: {result.m6_total_relationships} relationships")
        print()
        print(f"Processing Time: {result.processing_time:.2f}s")
        print(f"Output Files:")
        print(f"  - JSON: {json_path}")
        print(f"  - Report: {report_path}")
        if output_video_path:
            print(f"  - Video: {output_video_path}")
        print("=" * 80)
        
    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
