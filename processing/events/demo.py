"""
Event Correlation Demo (Milestone 5)

Demonstrates the difference between M4 raw anomalies and M5 correlated events.
"""

import json
from typing import List, Dict
from processing.events.correlator import (
    EventCorrelator,
    EventConfig,
)


def create_synthetic_scenario() -> List[Dict]:
    """
    Create a synthetic scenario demonstrating event correlation
    
    Scenario: Track #7 performs a complex sequence
    1. Normal movement (0-10s)
    2. Enters restricted zone (10.5s)
    3. Multiple zone alerts (11-25s) - should consolidate
    4. Unusual speed inside zone (12-18s)
    5. Sudden direction change (16s)
    6. Exits zone (25s)
    7. Sudden acceleration (27s)
    8. Loitering (30-45s) - many repeated observations
    9. Normal movement resumes
    
    This should produce:
    - 1 RESTRICTED_AREA_INTRUSION event (not 15+ separate zone alerts)
    - 1 LOITERING_EVENT (not 149 separate loitering alerts)
    - 1 ABNORMAL_MOVEMENT_SEQUENCE (grouping related movement anomalies)
    
    Total: ~3 meaningful events instead of ~170 raw anomaly alerts
    """

    anomalies = []
    event_id_counter = 1000

    # Phase 1: Enter restricted zone (10.5s)
    anomalies.append(
        {
            "event_id": f"anom_{event_id_counter}",
            "track_id": "7",
            "frame_id": 315,
            "timestamp": 10.5,
            "anomaly_type": "restricted_zone_entry",
            "severity": "high",
            "anomaly_score": 0.8,
            "evidence": {
                "zone_id": "zone_001",
                "zone_name": "Secure Server Room",
                "position": [710, 150],
            },
            "observed_value": "(710.0, 150.0)",
            "threshold": "Zone zone_001",
            "current_behavior_state": "moving",
            "explanation": "Track entered restricted zone 'Secure Server Room'",
        }
    )
    event_id_counter += 1

    # Phase 2: Repeated zone entry alerts (11-25s) - 15 alerts
    for i in range(15):
        timestamp = 11.0 + i * 1.0
        anomalies.append(
            {
                "event_id": f"anom_{event_id_counter}",
                "track_id": "7",
                "frame_id": 315 + i * 30,
                "timestamp": timestamp,
                "anomaly_type": "restricted_zone_entry",
                "severity": "high",
                "anomaly_score": 0.8,
                "evidence": {
                    "zone_id": "zone_001",
                    "zone_name": "Secure Server Room",
                    "position": [710 + i * 2, 150 + i],
                },
                "observed_value": f"({710 + i * 2:.1f}, {150 + i:.1f})",
                "threshold": "Zone zone_001",
                "current_behavior_state": "moving",
                "explanation": "Track still in restricted zone",
            }
        )
        event_id_counter += 1

    # Phase 3: Unusual speed inside zone (12-18s) - 7 alerts
    for i in range(7):
        timestamp = 12.0 + i * 1.0
        anomalies.append(
            {
                "event_id": f"anom_{event_id_counter}",
                "track_id": "7",
                "frame_id": 360 + i * 30,
                "timestamp": timestamp,
                "anomaly_type": "unusual_speed",
                "severity": "medium",
                "anomaly_score": 0.65,
                "evidence": {
                    "observed_speed": 180.0,
                    "position": [720 + i * 5, 155 + i],
                    "description": "High speed: 180.0 px/s",
                },
                "observed_value": 180.0,
                "threshold": 150.0,
                "current_behavior_state": "fast_moving",
                "explanation": "Track moving at 180.0 px/s inside zone",
            }
        )
        event_id_counter += 1

    # Phase 4: Sudden direction change (16s)
    anomalies.append(
        {
            "event_id": f"anom_{event_id_counter}",
            "track_id": "7",
            "frame_id": 480,
            "timestamp": 16.0,
            "anomaly_type": "sudden_direction_change",
            "severity": "medium",
            "anomaly_score": 0.70,
            "evidence": {
                "previous_direction": 45.0,
                "current_direction": 180.0,
                "change_degrees": 135.0,
                "description": "Turned 135.0 degrees",
            },
            "observed_value": 135.0,
            "threshold": 90.0,
            "current_behavior_state": "moving",
            "explanation": "Track suddenly changed direction by 135 degrees",
        }
    )
    event_id_counter += 1

    # Phase 5: Sudden speed change (acceleration at 27s, after leaving zone)
    anomalies.append(
        {
            "event_id": f"anom_{event_id_counter}",
            "track_id": "7",
            "frame_id": 810,
            "timestamp": 27.0,
            "anomaly_type": "sudden_speed_change",
            "severity": "high",
            "anomaly_score": 0.85,
            "evidence": {
                "previous_speed": 50.0,
                "current_speed": 200.0,
                "change_delta": 150.0,
                "threshold": 100.0,
                "description": "Sudden acceleration: speed changed by 150.0 px/s",
            },
            "observed_value": 150.0,
            "threshold": 100.0,
            "current_behavior_state": "fast_moving",
            "explanation": "Track suddenly accelerated from 50 to 200 px/s",
        }
    )
    event_id_counter += 1

    # Phase 6: Loitering (30-45s) - 50 repeated alerts (simulating M4 spam)
    for i in range(50):
        timestamp = 30.0 + i * 0.3
        anomalies.append(
            {
                "event_id": f"anom_{event_id_counter}",
                "track_id": "7",
                "frame_id": 900 + i * 9,
                "timestamp": timestamp,
                "anomaly_type": "loitering",
                "severity": "low",
                "anomaly_score": 0.40,
                "evidence": {
                    "stationary_duration": 5.0 + i * 0.3,
                    "position": [850, 200],
                    "description": f"Stationary for {5.0 + i * 0.3:.1f}s",
                },
                "observed_value": 5.0 + i * 0.3,
                "threshold": 5.0,
                "current_behavior_state": "stationary",
                "explanation": f"Track stationary for {5.0 + i * 0.3:.1f}s",
            }
        )
        event_id_counter += 1

    return anomalies


def create_multi_track_scenario() -> List[Dict]:
    """
    Create scenario with multiple tracks to test track separation
    
    Track #3: High-speed sequence (5-12s)
    Track #5: Loitering (20-35s)
    Track #7: Complex intrusion (as above)
    
    Should produce separate events for each track
    """
    # Get track 7 scenario
    track7_anomalies = create_synthetic_scenario()

    # Add track 3: high-speed activity
    track3_anomalies = []
    for i in range(10):
        timestamp = 5.0 + i * 0.7
        track3_anomalies.append(
            {
                "event_id": f"anom_t3_{i}",
                "track_id": "3",
                "frame_id": 150 + i * 21,
                "timestamp": timestamp,
                "anomaly_type": "unusual_speed",
                "severity": "high",
                "anomaly_score": 0.75,
                "evidence": {
                    "observed_speed": 220.0,
                    "position": [100 + i * 10, 300],
                    "description": "High speed: 220.0 px/s",
                },
                "observed_value": 220.0,
                "threshold": 150.0,
                "current_behavior_state": "fast_moving",
                "explanation": "Track moving very fast",
            }
        )

    # Add track 5: loitering
    track5_anomalies = []
    for i in range(30):
        timestamp = 20.0 + i * 0.5
        track5_anomalies.append(
            {
                "event_id": f"anom_t5_{i}",
                "track_id": "5",
                "frame_id": 600 + i * 15,
                "timestamp": timestamp,
                "anomaly_type": "loitering",
                "severity": "medium",
                "anomaly_score": 0.55,
                "evidence": {
                    "stationary_duration": 5.0 + i * 0.5,
                    "position": [400, 400],
                    "description": f"Stationary for {5.0 + i * 0.5:.1f}s",
                },
                "observed_value": 5.0 + i * 0.5,
                "threshold": 5.0,
                "current_behavior_state": "stationary",
                "explanation": f"Track stationary for {5.0 + i * 0.5:.1f}s",
            }
        )

    return track7_anomalies + track3_anomalies + track5_anomalies


def print_anomaly_summary(anomalies: List[Dict]):
    """Print summary of raw M4 anomalies"""
    print(f"Total raw anomalies: {len(anomalies)}")
    print()

    # Group by track
    from collections import defaultdict

    track_counts = defaultdict(lambda: defaultdict(int))
    for anom in anomalies:
        track_id = anom["track_id"]
        anom_type = anom["anomaly_type"]
        track_counts[track_id][anom_type] += 1

    print("Anomalies by Track:")
    for track_id in sorted(track_counts.keys()):
        print(f"  Track #{track_id}:")
        for anom_type, count in sorted(track_counts[track_id].items()):
            print(f"    {anom_type}: {count}")
    print()


def print_event_summary(events: List):
    """Print summary of M5 correlated events"""
    print(f"Total correlated events: {len(events)}")
    print()

    if not events:
        return

    print("Events by Type:")
    from collections import defaultdict

    type_counts = defaultdict(int)
    for event in events:
        type_counts[event.event_type.value] += 1

    for event_type, count in sorted(type_counts.items()):
        print(f"  {event_type}: {count}")
    print()


def print_detailed_events(events: List):
    """Print detailed information for each event"""
    print("=" * 80)
    print("DETAILED CORRELATED EVENTS")
    print("=" * 80)
    print()

    for i, event in enumerate(events, 1):
        print(f"Event {i}: {event.event_type.value.upper().replace('_', ' ')}")
        print("-" * 80)
        print(f"  Event ID: {event.event_id}")
        print(f"  Track(s): {', '.join(f'#{tid}' for tid in event.participating_track_ids)}")
        print(f"  Time: {event.start_timestamp:.2f}s - {event.end_timestamp:.2f}s")
        print(f"  Duration: {event.duration_seconds:.2f}s")
        print(f"  Severity: {event.severity.value.upper()}")
        print(f"  Confidence: {event.confidence:.3f}")
        print(f"  Source Anomalies: {len(event.source_anomaly_ids)}")
        print(f"  Anomaly Types: {', '.join(set(event.source_anomaly_types))}")
        print(f"  Evidence:")
        for key, value in event.evidence.items():
            if isinstance(value, (list, dict)):
                print(f"    {key}: {value}")
            elif isinstance(value, float):
                print(f"    {key}: {value:.2f}")
            else:
                print(f"    {key}: {value}")
        print(f"  Explanation:")
        print(f"    {event.explanation}")
        print()


def run_single_track_demo():
    """Run demo with single complex track"""
    print("=" * 80)
    print("Milestone 5: Event Correlation Demo (Single Track)")
    print("=" * 80)
    print()

    print("Scenario: Track #7 Complex Sequence")
    print("  1. Enters restricted zone (10.5s)")
    print("  2. Remains in zone with repeated alerts (11-25s)")
    print("  3. Exhibits unusual speed inside zone (12-18s)")
    print("  4. Sudden direction change (16s)")
    print("  5. Sudden acceleration after exit (27s)")
    print("  6. Loitering with repeated alerts (30-45s)")
    print()

    # Generate anomalies
    anomalies = create_synthetic_scenario()

    print("=" * 80)
    print("M4 RAW ANOMALIES (Alert Spam)")
    print("=" * 80)
    print()
    print_anomaly_summary(anomalies)

    # Configure correlator
    config = EventConfig(
        temporal_window=30.0,  # Group anomalies within 30 seconds
        min_loitering_duration=5.0,
        min_high_speed_count=3,
        min_movement_sequence=2,
        max_repeated_anomalies=5,
    )

    correlator = EventCorrelator(config)

    # Correlate events
    events = correlator.correlate(anomalies)

    print("=" * 80)
    print("M5 CORRELATED EVENTS (Meaningful Summary)")
    print("=" * 80)
    print()
    print_event_summary(events)

    print("Reduction Rate:")
    if events:
        reduction = (1 - len(events) / len(anomalies)) * 100
        print(f"  {len(anomalies)} raw anomalies → {len(events)} correlated events")
        print(f"  {reduction:.1f}% reduction in alert volume")
    print()

    # Print detailed events
    print_detailed_events(events)

    # Export to JSON
    export_data = {
        "scenario": "single_track_complex_sequence",
        "raw_anomalies": {
            "count": len(anomalies),
            "sample": anomalies[:3],  # First 3 for brevity
        },
        "correlated_events": {
            "count": len(events),
            "events": [event.to_dict() for event in events],
        },
        "reduction_percentage": (1 - len(events) / len(anomalies)) * 100
        if events
        else 0,
    }

    with open("event_correlation_single_track_demo.json", "w") as f:
        json.dump(export_data, f, indent=2)

    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print(f"Exported to: event_correlation_single_track_demo.json")
    print()


def run_multi_track_demo():
    """Run demo with multiple tracks"""
    print("=" * 80)
    print("Milestone 5: Event Correlation Demo (Multiple Tracks)")
    print("=" * 80)
    print()

    print("Scenario: Three Simultaneous Tracks")
    print("  Track #3: High-speed activity (5-12s)")
    print("  Track #5: Loitering (20-35s)")
    print("  Track #7: Complex restricted area intrusion (10-45s)")
    print()

    # Generate anomalies
    anomalies = create_multi_track_scenario()

    print("=" * 80)
    print("M4 RAW ANOMALIES")
    print("=" * 80)
    print()
    print_anomaly_summary(anomalies)

    # Configure correlator
    config = EventConfig(
        temporal_window=30.0,
        min_loitering_duration=5.0,
        min_high_speed_count=3,
        min_movement_sequence=2,
        max_repeated_anomalies=5,
    )

    correlator = EventCorrelator(config)

    # Correlate events
    events = correlator.correlate(anomalies)

    print("=" * 80)
    print("M5 CORRELATED EVENTS")
    print("=" * 80)
    print()
    print_event_summary(events)

    print("Reduction Rate:")
    if events:
        reduction = (1 - len(events) / len(anomalies)) * 100
        print(f"  {len(anomalies)} raw anomalies → {len(events)} correlated events")
        print(f"  {reduction:.1f}% reduction in alert volume")
    print()

    # Print detailed events
    print_detailed_events(events)

    # Export to JSON
    export_data = {
        "scenario": "multi_track",
        "raw_anomalies": {"count": len(anomalies)},
        "correlated_events": {
            "count": len(events),
            "events": [event.to_dict() for event in events],
        },
        "reduction_percentage": (1 - len(events) / len(anomalies)) * 100
        if events
        else 0,
    }

    with open("event_correlation_multi_track_demo.json", "w") as f:
        json.dump(export_data, f, indent=2)

    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print(f"Exported to: event_correlation_multi_track_demo.json")
    print()


if __name__ == "__main__":
    print("\n")
    run_single_track_demo()
    print("\n\n")
    run_multi_track_demo()
