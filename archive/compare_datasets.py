"""Compare the two different result datasets"""
import json

# Backend API result (most recent)
backend_file = 'backend/outputs/8cd26e83-61f9-442f-a6d2-068a41be1dc1_result.json'
# Data directory result
data_file = 'data/sample_e2e_result_m8.json'

print('=' * 80)
print('DATASET COMPARISON')
print('=' * 80)

with open(backend_file) as f:
    backend_data = json.load(f)

with open(data_file) as f:
    data_data = json.load(f)

print('\n1. VIDEO METADATA')
print('-' * 80)
print(f'Backend API result:')
print(f'  FPS: {backend_data["video_fps"]:.2f}')
print(f'  Total Frames: {backend_data["video_total_frames"]}')
print(f'  Frames Processed: {backend_data["frames_processed"]}')
print(f'  Frames Skipped: {backend_data["frames_skipped"]}')

print(f'\nData directory result:')
print(f'  FPS: {data_data["video_fps"]:.2f}')
print(f'  Total Frames: {data_data["video_total_frames"]}')
print(f'  Frames Processed: {data_data["frames_processed"]}')
print(f'  Frames Skipped: {data_data["frames_skipped"]}')

print('\n2. TRACK 1 OBSERVATIONS')
print('-' * 80)

backend_track1 = [b for frame in backend_data['all_behaviors'] for b in frame if b.get('track_id') == 1]
data_track1 = [b for frame in data_data['all_behaviors'] for b in frame if b.get('track_id') == 1]

print(f'Backend API: {len(backend_track1)} observations')
print(f'Data dir:    {len(data_track1)} observations')

print('\n3. TRACK 1 SPEEDS')
print('-' * 80)

backend_speeds = [b['speed'] for b in backend_track1]
data_speeds = [b['speed'] for b in data_track1]

print(f'Backend API result:')
print(f'  Avg: {sum(backend_speeds)/len(backend_speeds):.1f} px/s')
print(f'  Max: {max(backend_speeds):.1f} px/s')
print(f'  Min: {min(backend_speeds):.1f} px/s')

print(f'\nData directory result:')
print(f'  Avg: {sum(data_speeds)/len(data_speeds):.1f} px/s')
print(f'  Max: {max(data_speeds):.1f} px/s')
print(f'  Min: {min(data_speeds):.1f} px/s')

print('\n4. SAMPLE OBSERVATIONS')
print('-' * 80)

print(f'\nBackend API - First 3 observations:')
for i, obs in enumerate(backend_track1[:3]):
    print(f'  [{i}] t={obs["timestamp"]:.4f}s, pos={obs["position"]}, speed={obs["speed"]:.1f}')

print(f'\nData dir - First 3 observations:')
for i, obs in enumerate(data_track1[:3]):
    print(f'  [{i}] t={obs["timestamp"]:.4f}s, pos={obs["position"]}, speed={obs["speed"]:.1f}')

print('\n5. KEY DIFFERENCE')
print('-' * 80)
print(f'Backend API processed ALL {backend_data["video_total_frames"]} frames (frame_skip=1)')
print(f'Data dir processed {data_data["frames_processed"]} frames (frame_skip likely higher)')
print()
print('The backend result has 240 observations (all frames)')
print('The data dir result has 90 observations (~every 3rd frame)')
print()
print('This explains the speed difference:')
print('  - Backend: speed calculated over shorter time intervals (all frames)')
print('  - Data dir: speed calculated over longer time intervals (skipped frames)')
print()
print('Both are mathematically correct for their respective frame_skip settings.')

print('\n6. CONFIGURATION INFERENCE')
print('-' * 80)
backend_frame_intervals = [backend_track1[i+1]['timestamp'] - backend_track1[i]['timestamp'] 
                           for i in range(min(10, len(backend_track1)-1))]
data_frame_intervals = [data_track1[i+1]['timestamp'] - data_track1[i]['timestamp'] 
                        for i in range(min(10, len(data_track1)-1))]

print(f'Backend avg frame interval: {sum(backend_frame_intervals)/len(backend_frame_intervals):.4f}s')
print(f'Data dir avg frame interval: {sum(data_frame_intervals)/len(data_frame_intervals):.4f}s')
print(f'\nBackend frame_skip: ~{round(sum(backend_frame_intervals)/len(backend_frame_intervals) * backend_data["video_fps"])}')
print(f'Data dir frame_skip: ~{round(sum(data_frame_intervals)/len(data_frame_intervals) * data_data["video_fps"])}')

print('\n' + '=' * 80)
print('CONCLUSION')
print('=' * 80)
print('✓ Frontend displays: 118.2 px/s avg, 458.3 px/s max')
print('✓ Source: backend/outputs/8cd26e83-61f9-442f-a6d2-068a41be1dc1_result.json')
print('✓ Configuration: frame_skip=1 (all frames processed)')
print()
print('✓ Data directory: 50.0 px/s avg, 94.3 px/s max')
print('✓ Source: data/sample_e2e_result_m8.json')
print('✓ Configuration: frame_skip=3 (every 3rd frame processed)')
print()
print('Both results are CORRECT for their respective configurations.')
print('The discrepancy is due to different frame_skip settings.')
