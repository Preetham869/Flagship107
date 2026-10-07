#!/usr/bin/env python3
"""Analyze anomalies from real video results"""

import json
from collections import Counter

# Load results
with open('data/sample_e2e_result.json', 'r') as f:
    data = json.load(f)

print("=" * 80)
print("ANOMALY ANALYSIS FROM REAL VIDEO (sample.mp4)")
print("=" * 80)
print()

# Overview
print(f"Total anomalies: {len(data['all_anomalies'])}")
print(f"Anomaly types: {data['m4_anomalies_by_type']}")
print(f"Severity distribution: {data['m4_severity_distribution']}")
print()

# Analyze by track
track_anomalies = Counter()
for a in data['all_anomalies']:
    track_anomalies[a['track_id']] += 1

print(f"Anomalies by track: {dict(track_anomalies)}")
print()

# Sample direction change anomalies
print("=" * 80)
print("DIRECTION CHANGE ANOMALIES (first 10)")
print("=" * 80)
direction_anomalies = [a for a in data['all_anomalies'] if a['anomaly_type'] == 'sudden_direction_change']
for i, a in enumerate(direction_anomalies[:10]):
    print(f"\n{i+1}. Track {a['track_id']} at t={a['timestamp']:.2f}s")
    print(f"   Severity: {a['severity']}")
    print(f"   Change: {a['evidence']['change_degrees']:.1f}°")
    print(f"   From {a['evidence']['previous_direction']:.1f}° to {a['evidence']['current_direction']:.1f}°")
    print(f"   Score: {a['anomaly_score']:.3f}")

# Sample speed anomalies
print()
print("=" * 80)
print("UNUSUAL SPEED ANOMALIES (first 10)")
print("=" * 80)
speed_anomalies = [a for a in data['all_anomalies'] if a['anomaly_type'] == 'unusual_speed']
for i, a in enumerate(speed_anomalies[:10]):
    print(f"\n{i+1}. Track {a['track_id']} at t={a['timestamp']:.2f}s")
    print(f"   Severity: {a['severity']}")
    print(f"   Speed: {a['observed_value']:.1f} px/s (threshold: {a['threshold']} px/s)")
    print(f"   Score: {a['anomaly_score']:.3f}")

# Check behavior data for one track to see jitter
print()
print("=" * 80)
print("BEHAVIOR SAMPLE (Track 1, first 10 frames)")
print("=" * 80)
track_1_behaviors = []
for frame_behaviors in data['all_behaviors']:
    for b in frame_behaviors:
        if b['track_id'] == 1:
            track_1_behaviors.append(b)

for i, b in enumerate(track_1_behaviors[:10]):
    print(f"\nFrame {i}: t={b['timestamp']:.2f}s")
    print(f"  Position: ({b['position'][0]:.1f}, {b['position'][1]:.1f})")
    print(f"  Speed: {b['speed']:.1f} px/s")
    if b['direction'] is not None:
        print(f"  Direction: {b['direction']:.1f}°")
    print(f"  State: {b['state']}")
