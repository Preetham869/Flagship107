"""Check all result files for Track 1 speed statistics"""
import json
import os
from pathlib import Path

data_dir = Path('data')
json_files = list(data_dir.glob('*.json'))

print('=' * 80)
print('CHECKING ALL RESULT FILES FOR TRACK 1 SPEEDS')
print('=' * 80)

for json_file in sorted(json_files):
    print(f'\n{json_file.name}:')
    try:
        with open(json_file) as f:
            data = json.load(f)
        
        if 'all_behaviors' not in data:
            print('  ❌ No all_behaviors field')
            continue
        
        # Extract Track 1
        track1 = [b for frame in data['all_behaviors'] for b in frame if b.get('track_id') == 1]
        
        if not track1:
            print('  ❌ No Track 1 found')
            continue
        
        speeds = [b['speed'] for b in track1]
        
        print(f'  ✓ Track 1 observations: {len(track1)}')
        print(f'  ✓ Avg speed: {sum(speeds)/len(speeds):.1f} px/s')
        print(f'  ✓ Max speed: {max(speeds):.1f} px/s')
        
    except Exception as e:
        print(f'  ❌ Error: {e}')

print('\n' + '=' * 80)
print('CHECKING FOR 118.7 / 458.3 VALUES')
print('=' * 80)

# Search for these specific values
target_avg = 118.7
target_max = 458.3
tolerance = 0.5

for json_file in sorted(json_files):
    try:
        with open(json_file) as f:
            data = json.load(f)
        
        if 'all_behaviors' not in data:
            continue
        
        # Check all tracks
        for track_id in range(1, 10):  # Check tracks 1-9
            track = [b for frame in data['all_behaviors'] for b in frame if b.get('track_id') == track_id]
            if not track:
                continue
            
            speeds = [b['speed'] for b in track]
            avg = sum(speeds) / len(speeds)
            max_speed = max(speeds)
            
            if abs(avg - target_avg) < tolerance:
                print(f'\n🎯 MATCH FOUND: {json_file.name}')
                print(f'   Track #{track_id}')
                print(f'   Avg speed: {avg:.1f} px/s (target: {target_avg})')
                print(f'   Max speed: {max_speed:.1f} px/s (target: {target_max})')
            
            if abs(max_speed - target_max) < tolerance:
                print(f'\n🎯 MAX MATCH FOUND: {json_file.name}')
                print(f'   Track #{track_id}')
                print(f'   Avg speed: {avg:.1f} px/s (target: {target_avg})')
                print(f'   Max speed: {max_speed:.1f} px/s (target: {target_max})')
    
    except Exception as e:
        pass

print('\n' + '=' * 80)
