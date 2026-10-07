import json

data = json.load(open('backend/outputs/8cd26e83-61f9-442f-a6d2-068a41be1dc1_result.json'))

print('=== M5 EVENT SAMPLE ===')
if data.get('all_events'):
    event = data['all_events'][0]
    print(json.dumps(event, indent=2))
    print(f'\nSource anomaly types: {event.get("source_anomaly_types", [])}')
    print(f'Unique types: {set(event.get("source_anomaly_types", []))}')

print('\n=== M6 RELATIONSHIPS ===')
print(f'Total: {len(data.get("all_relationships", []))}')
print(f'M6 total from stats: {data.get("m6_total_relationships", 0)}')
print(f'M6 tracked pairs: {data.get("m6_tracked_pairs", 0)}')

print('\n=== M8 SCENE EXISTS ===')
print(f'Total scenes: {len(data.get("all_scenes", []))}')
if data.get('all_scenes'):
    scene = data['all_scenes'][0]
    print(f'Scene keys: {list(scene.keys())}')
    print(f'Has track_summaries: {isinstance(scene.get("track_summaries"), dict)}')
