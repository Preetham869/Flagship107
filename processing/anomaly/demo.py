"""
Demo script for anomaly detection
Demonstrates anomaly detection on synthetic behavior data
"""
from typing import List, Dict
import json

from processing.behavior import BehaviorAnalyzer, BehaviorConfig
from processing.anomaly import (
    AnomalyDetector,
    AnomalyConfig,
    RestrictedZone,
    AnomalyType,
)


def create_synthetic_scenarios() -> List[Dict]:
    """
    Create synthetic behavior scenarios for demonstration
    
    Scenarios:
    1. Normal walking
    2. Fast running (unusual speed)
    3. Person standing still (loitering)
    4. Sudden acceleration
    5. Sudden direction change (90° turn)
    6. Person entering restricted zone
    
    Returns:
        List of behavior data frames
    """
    frames = []

    # Configure behavior analyzer
    behavior_config = BehaviorConfig()
    analyzer = BehaviorAnalyzer(behavior_config)

    fps = 30
    duration = 10  # 10 seconds

    for frame_id in range(duration * fps):
        timestamp = frame_id / fps
        tracks = []

        # Track 1: Normal walking (no anomaly)
        if frame_id >= 0:
            x = 100 + frame_id * 1.5  # ~45 px/s
            tracks.append(
                {
                    "track_id": 1,
                    "bbox": [x, 200, x + 80, 400],
                    "confidence": 0.87,
                    "class_name": "person",
                }
            )

        # Track 2: Fast running after 2 seconds (unusual speed anomaly)
        if frame_id >= 60:  # After 2 seconds
            x = 100 + (frame_id - 60) * 6  # ~180 px/s
            tracks.append(
                {
                    "track_id": 2,
                    "bbox": [x, 100, x + 80, 300],
                    "confidence": 0.92,
                    "class_name": "person",
                }
            )

        # Track 3: Stationary (loitering anomaly)
        if frame_id >= 0:
            tracks.append(
                {
                    "track_id": 3,
                    "bbox": [500, 300, 580, 500],
                    "confidence": 0.85,
                    "class_name": "person",
                }
            )

        # Track 4: Sudden acceleration after 4 seconds
        if frame_id >= 0:
            if frame_id < 120:  # First 4 seconds: slow
                x = 200 + frame_id * 0.5  # ~15 px/s
            else:  # After 4 seconds: fast
                x = 200 + 60 + (frame_id - 120) * 4  # ~120 px/s
            tracks.append(
                {
                    "track_id": 4,
                    "bbox": [x, 400, x + 80, 600],
                    "confidence": 0.88,
                    "class_name": "person",
                }
            )

        # Track 5: 90-degree turn after 5 seconds
        if frame_id >= 0:
            if frame_id < 150:  # First 5 seconds: move right
                x = 50 + frame_id * 2
                y = 50
            else:  # After 5 seconds: turn down (90 degrees)
                x = 50 + 150 * 2
                y = 50 + (frame_id - 150) * 2
            tracks.append(
                {
                    "track_id": 5,
                    "bbox": [x, y, x + 80, y + 200],
                    "confidence": 0.90,
                    "class_name": "person",
                }
            )

        # Track 6: Entering restricted zone after 3 seconds
        if frame_id >= 90:  # After 3 seconds
            # Move towards restricted zone (700-800, 100-200)
            x = 600 + (frame_id - 90) * 2
            y = 100 + (frame_id - 90) * 0.5
            tracks.append(
                {
                    "track_id": 6,
                    "bbox": [x, y, x + 80, y + 200],
                    "confidence": 0.86,
                    "class_name": "person",
                }
            )

        # Analyze behaviors
        behaviors = analyzer.update(tracks, timestamp)
        
        # Add frame_id to each behavior (required by anomaly detector)
        for behavior in behaviors:
            behavior["frame_id"] = frame_id
        
        frames.append({"frame_id": frame_id, "timestamp": timestamp, "behaviors": behaviors})

    return frames


def run_demo():
    """
    Run anomaly detection demo on synthetic data
    """
    print("=" * 70)
    print("Flagship 107 - Explainable Anomaly Detection Demo")
    print("=" * 70)
    print()

    # Configure restricted zones
    restricted_zones = [
        RestrictedZone(
            zone_id="zone_1",
            zone_type="rectangle",
            coordinates=[700, 100, 800, 200],  # Flat list [x1, y1, x2, y2]
            name="Restricted Area A",
        )
    ]

    # Configure anomaly detector
    config = AnomalyConfig(
        unusual_speed_threshold=150.0,  # > 150 px/s is unusual
        loitering_threshold=5.0,  # > 5 seconds is loitering
        speed_change_threshold=100.0,  # > 100 px/s delta is sudden
        direction_change_threshold=80.0,  # > 80° is sudden turn
        restricted_zones=restricted_zones,
    )

    print("Configuration:")
    print(f"  Unusual speed threshold: {config.unusual_speed_threshold} px/s")
    print(f"  Loitering threshold: {config.loitering_threshold}s")
    print(f"  Speed change threshold: {config.speed_change_threshold} px/s")
    print(f"  Direction change threshold: {config.direction_change_threshold}°")
    print(f"  Restricted zones: {len(config.restricted_zones)}")
    print()

    # Create detector
    detector = AnomalyDetector(config)

    # Generate synthetic data
    print("Generating synthetic behavior data...")
    print("  Track 1: Normal walking (no anomaly)")
    print("  Track 2: Fast running after 2s (unusual speed)")
    print("  Track 3: Standing still (loitering)")
    print("  Track 4: Sudden acceleration at 4s (speed change)")
    print("  Track 5: 90° turn at 5s (direction change)")
    print("  Track 6: Entering restricted zone at 3s (zone violation)")
    print()

    frames = create_synthetic_scenarios()
    print(f"Generated {len(frames)} frames (10 seconds at 30 fps)")
    print()

    # Detect anomalies
    all_anomalies = []
    anomaly_counts = {}

    for frame_data in frames:
        behaviors = frame_data["behaviors"]
        anomalies = detector.detect(behaviors)

        if anomalies:
            for anomaly in anomalies:
                all_anomalies.append(anomaly)
                anomaly_type = anomaly["anomaly_type"]
                anomaly_counts[anomaly_type] = anomaly_counts.get(anomaly_type, 0) + 1

    # Print anomaly summary
    print("=" * 70)
    print("Anomaly Detection Results")
    print("=" * 70)
    print()
    print(f"Total anomalies detected: {len(all_anomalies)}")
    print()

    if anomaly_counts:
        print("Anomalies by Type:")
        for anomaly_type, count in sorted(anomaly_counts.items()):
            print(f"  {anomaly_type}: {count}")
        print()

    # Show sample anomalies (first occurrence of each type)
    seen_types = set()
    print("Sample Anomalies (First Occurrence of Each Type):")
    print("-" * 70)

    for anomaly in all_anomalies:
        anomaly_type = anomaly["anomaly_type"]

        if anomaly_type not in seen_types:
            seen_types.add(anomaly_type)
            print(f"\n{anomaly_type.upper().replace('_', ' ')}")
            print(f"  Track: #{anomaly['track_id']}")
            print(f"  Time: {anomaly['timestamp']:.2f}s")
            print(f"  Severity: {anomaly['severity']}")
            print(f"  Score: {anomaly['anomaly_score']:.3f}")
            print(f"  Evidence:")
            for key, value in anomaly["evidence"].items():
                if isinstance(value, float):
                    print(f"    {key}: {value:.2f}")
                else:
                    print(f"    {key}: {value}")
            print(f"  Explanation: {anomaly['explanation']}")

    print()
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)

    # Export sample anomalies to JSON
    export_path = "anomaly_detection_demo.json"
    export_data = {
        "config": {
            "unusual_speed_threshold": config.unusual_speed_threshold,
            "loitering_threshold": config.loitering_threshold,
            "speed_change_threshold": config.speed_change_threshold,
            "direction_change_threshold": config.direction_change_threshold,
        },
        "anomalies": all_anomalies[:10],  # Export first 10 as sample
        "summary": {
            "total_anomalies": len(all_anomalies),
            "anomaly_counts": anomaly_counts,
        },
    }

    try:
        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)
        print(f"\nSample anomaly data exported to: {export_path}")
    except Exception as e:
        print(f"\nWarning: Could not export data: {e}")


if __name__ == "__main__":
    run_demo()
