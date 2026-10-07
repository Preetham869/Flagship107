"""Check backend output files for Track 1 speeds"""
import json
from pathlib import Path
import datetime

outputs_dir = Path('backend/outputs')
result_files = list(outputs_dir.glob('*_result.json'))

print('=' * 80)
print('BACKEND OUTPUT FILES')
print('=' * 80)

# Sort by modification time
result_files_sorted = sorted(result_files, key=lambda f: f.stat().st_mtime, reverse=True)

for result_file in result_files_sorted:
    mod_time = datetime.datetime.fromtimestamp(result_file.stat().st_mtime)
    print(f'\n{result_file.name}')
    print(f'  Modified: {mod_time}')
    
    try:
        with open(result_file) as f:
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
        
        # Check if this matches user's values
        avg = sum(speeds) / len(speeds)
        max_speed = max(speeds)
        if abs(avg - 118.7) < 1.0 or abs(max_speed - 458.3) < 1.0:
            print('  🎯 MATCHES USER-REPORTED VALUES!')
        
    except Exception as e:
        print(f'  ❌ Error: {e}')

print('\n' + '=' * 80)
print('MOST RECENT BACKEND RESULT')
print('=' * 80)
if result_files_sorted:
    most_recent = result_files_sorted[0]
    print(f'File: {most_recent.name}')
    print(f'Modified: {datetime.datetime.fromtimestamp(most_recent.stat().st_mtime)}')
    print('\nThis is what the API would serve to the frontend.')
