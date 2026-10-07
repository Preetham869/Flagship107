#!/usr/bin/env python3
"""Examine M8 contextual scene results"""

import json

with open('data/sample_e2e_result_m8.json', 'r') as f:
    data = json.load(f)

print('=' * 80)
print('M8 CONTEXTUAL SCENES EXAMINATION')
print('=' * 80)
print(f'Total Scenes: {data.get("m8_total_scenes", 0)}')
print(f'Avg Scene Duration: {data.get("m8_avg_scene_duration", 0):.2f}s')
print()

scenes = data.get('all_scenes', [])
for i, scene in enumerate(scenes, 1):
    print(f'\nScene {i}: {scene["scene_id"]}')
    print(f'  Time Range: {scene["start_timestamp"]:.2f}s - {scene["end_timestamp"]:.2f}s')
    print(f'  Duration: {scene["duration_seconds"]:.2f}s')
    print(f'  Frame Range: {scene["start_frame"]} - {scene["end_frame"]}')
    print(f'  Participating Tracks: {scene["participating_track_ids"]}')
    print(f'  Scene Type: {scene["scene_type"]}')
    print(f'  Complexity Score: {scene.get("complexity_score", 0):.2f}')
    print(f'  Track Summaries: {len(scene["track_summaries"])}')
    
    # Movement patterns
    movement = scene.get("movement_patterns", {})
    spatial = scene.get("spatial_patterns", {})
    temporal = scene.get("temporal_patterns", {})
    
    print(f'\n  Movement Patterns: {movement}')
    print(f'  Spatial Patterns: {spatial}')
    print(f'  Temporal Patterns: {temporal}')
    
    # Track summaries
    for ts in scene['track_summaries']:
        print(f'\n    Track: {ts["track_id"]}')
        print(f'      First Seen: {ts.get("first_timestamp", 0):.2f}s (frame {ts.get("first_frame", 0)})')
        print(f'      Last Seen: {ts.get("last_timestamp", 0):.2f}s (frame {ts.get("last_frame", 0)})')
        print(f'      Duration: {ts.get("duration", 0):.2f}s')
        print(f'      Observations: {ts.get("observation_count", 0)}')
        print(f'      States: {ts.get("states_observed", {})}')
        print(f'      Avg Speed: {ts.get("avg_speed", 0):.2f} px/s')
        print(f'      Max Speed: {ts.get("max_speed", 0):.2f} px/s')
        print(f'      Distance Traveled: {ts.get("total_distance", 0):.2f} px')
        
        # Anomalies
        track_anomalies = ts.get("anomalies", [])
        if track_anomalies:
            print(f'      Anomalies: {len(track_anomalies)}')
            for anom in track_anomalies:
                print(f'        - {anom.get("type", "unknown")} (severity: {anom.get("severity", "unknown")})')
    
    # Scene description and key observations
    print(f'\n  Summary: {scene.get("summary", "N/A")}')
    print(f'  Description: {scene.get("description", "N/A")}')
    
    key_obs = scene.get("key_observations", [])
    if key_obs:
        print(f'  Key Observations:')
        for obs in key_obs:
            print(f'    - {obs}')
    
    # Evidence
    evidence = scene.get("evidence", {})
    print(f'\n  Evidence Summary:')
    print(f'    Source Anomalies: {len(scene.get("source_anomalies", []))}')
    print(f'    Source Events: {len(scene.get("source_events", []))}')
    print(f'    Source Relationships: {len(scene.get("source_relationships", []))}')

print()
print('=' * 80)
print('M1-M7 SUMMARY')
print('=' * 80)
print(f'M1 Total Detections: {data.get("m1_total_detections", 0)}')
print(f'M2 Unique Tracks: {data.get("m2_unique_tracks", 0)}')
print(f'M3 Total Behaviors: {data.get("m3_total_behaviors", 0)}')
print(f'M4 Total Anomalies: {data.get("m4_total_anomalies", 0)}')
print(f'M5 Correlated Events: {data.get("m5_correlated_events", 0)}')
print(f'M6 Relationships: {data.get("m6_total_relationships", 0)}')
