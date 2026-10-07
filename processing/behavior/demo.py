"""
Demo script for behavior analysis
Demonstrates behavior calculations on synthetic tracking data
"""
from typing import List, Dict
import json

from processing.behavior import BehaviorAnalyzer, BehaviorConfig


def create_synthetic_tracks() -> List[Dict]:
    """
    Create synthetic tracking data for demonstration
    
    Returns:
        List of frame data with tracks
    """
    frame_data = []

    # Scenario: 3 people
    # Person 1: Walks steadily from left to right
    # Person 2: Stands still
    # Person 3: Runs fast diagonally

    fps = 30
    total_frames = 150  # 5 seconds

    for frame_id in range(total_frames):
        timestamp = frame_id / fps
        tracks = []

        # Person 1: Walking (moderate speed, ~50 px/s)
        if frame_id >= 0:
            x = 100 + frame_id * 1.67  # ~50 px/s at 30 fps
            tracks.append(
                {
                    "track_id": 1,
                    "bbox": [x, 200, x + 80, 400],
                    "confidence": 0.87,
                    "class_name": "person",
                }
            )

        # Person 2: Stationary
        if frame_id >= 0:
            tracks.append(
                {
                    "track_id": 2,
                    "bbox": [500, 100, 580, 300],
                    "confidence": 0.92,
                    "class_name": "person",
                }
            )

        # Person 3: Running fast (150 px/s)
        if frame_id >= 30:  # Starts after 1 second
            x = 50 + (frame_id - 30) * 5  # ~150 px/s
            y = 50 + (frame_id - 30) * 3  # Diagonal
            tracks.append(
                {
                    "track_id": 3,
                    "bbox": [x, y, x + 80, y + 200],
                    "confidence": 0.85,
                    "class_name": "person",
                }
            )

        frame_data.append({"frame_id": frame_id, "timestamp": timestamp, "tracks": tracks})

    return frame_data


def analyze_synthetic_data():
    """
    Run behavior analysis on synthetic tracking data
    """
    print("=" * 60)
    print("Flagship 107 - Behavior Analysis Demo")
    print("=" * 60)
    print()

    # Create configuration
    config = BehaviorConfig(
        stationary_threshold=10.0,  # < 10 px/s is stationary
        fast_moving_threshold=100.0,  # > 100 px/s is fast-moving
        min_stationary_duration=2.0,  # 2 seconds to be "stationary"
    )

    print("Configuration:")
    print(f"  Stationary threshold: {config.stationary_threshold} px/s")
    print(f"  Fast-moving threshold: {config.fast_moving_threshold} px/s")
    print(f"  Min stationary duration: {config.min_stationary_duration}s")
    print()

    # Create analyzer
    analyzer = BehaviorAnalyzer(config)

    # Generate synthetic data
    print("Generating synthetic tracking data...")
    print("  Person 1: Walking steadily left-to-right (~50 px/s)")
    print("  Person 2: Standing still")
    print("  Person 3: Running fast diagonally (~150 px/s)")
    print()

    frame_data = create_synthetic_tracks()
    print(f"Generated {len(frame_data)} frames (5 seconds at 30 fps)")
    print()

    # Analyze frame by frame
    all_behaviors = []
    sample_frames = [0, 30, 60, 90, 120, 149]  # Sample at key moments

    for frame_info in frame_data:
        frame_id = frame_info["frame_id"]
        timestamp = frame_info["timestamp"]
        tracks = frame_info["tracks"]

        # Analyze behaviors
        behaviors = analyzer.update(tracks, timestamp)

        # Store for export
        all_behaviors.append(
            {"frame_id": frame_id, "timestamp": timestamp, "behaviors": behaviors}
        )

        # Print sample frames
        if frame_id in sample_frames:
            print(f"Frame {frame_id} (t={timestamp:.2f}s):")
            for behavior in behaviors:
                print(
                    f"  Track #{behavior['track_id']} ({behavior['class_name']}): "
                    f"{behavior['state']} | "
                    f"speed={behavior['speed']:.1f} px/s | "
                    f"pos={behavior['position'][0]:.0f},{behavior['position'][1]:.0f}"
                )
            print()

    # Print final summaries
    print("=" * 60)
    print("Track Summaries:")
    print("=" * 60)

    for track_id in [1, 2, 3]:
        summary = analyzer.get_track_summary(track_id)
        if summary:
            print(f"\nTrack #{track_id}:")
            print(f"  Duration: {summary['total_duration']:.2f}s")
            print(f"  Observations: {summary['observation_count']}")
            print(
                f"  Start: ({summary['start_position'][0]:.0f}, {summary['start_position'][1]:.0f})"
            )
            print(
                f"  End: ({summary['end_position'][0]:.0f}, {summary['end_position'][1]:.0f})"
            )
            bounds = summary["trajectory_bounds"]
            print(
                f"  Bounds: X[{bounds['min_x']:.0f}-{bounds['max_x']:.0f}], "
                f"Y[{bounds['min_y']:.0f}-{bounds['max_y']:.0f}]"
            )

    # Analyzer statistics
    stats = analyzer.get_statistics()
    print(f"\nAnalyzer Statistics:")
    print(f"  Total tracks: {stats['total_tracks']}")
    print(f"  Active tracks: {stats['active_tracks']}")

    print()
    print("=" * 60)
    print("Demo Complete!")
    print("=" * 60)

    # Export to JSON
    export_path = "behavior_analysis_demo.json"
    export_data = {
        "config": {
            "stationary_threshold": config.stationary_threshold,
            "fast_moving_threshold": config.fast_moving_threshold,
            "min_stationary_duration": config.min_stationary_duration,
        },
        "frame_data": all_behaviors[:10],  # Export first 10 frames as sample
        "statistics": stats,
    }

    try:
        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)
        print(f"\nSample behavior data exported to: {export_path}")
    except Exception as e:
        print(f"\nWarning: Could not export data: {e}")


if __name__ == "__main__":
    analyze_synthetic_data()
