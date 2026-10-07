"""
Audit M3 Speed Calculation
Verify speed calculations are mathematically correct
"""
import json

# Load sample result
with open('data/sample_e2e_result_m8.json') as f:
    data = json.load(f)

print('=' * 80)
print('VIDEO METADATA')
print('=' * 80)
print(f'FPS: {data["video_fps"]}')
print(f'Total Frames: {data["video_total_frames"]}')
print(f'Duration: {data["video_duration"]:.2f}s')
print()

# Get Track 1 behaviors
track1 = [b for frame in data['all_behaviors'] for b in frame if b['track_id'] == 1]

print('=' * 80)
print('TRACK 1 TIMESTAMP ANALYSIS')
print('=' * 80)
print(f'Total observations: {len(track1)}')
timestamps = [b['timestamp'] for b in track1]
intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
print(f'Timestamp intervals (first 10): {[f"{x:.4f}" for x in intervals[:10]]}')
print(f'Average interval: {sum(intervals)/len(intervals):.4f}s')
print(f'Expected interval if frame_skip=1: {1/data["video_fps"]:.4f}s')
print()

# Manual verification of speed calculation
print('=' * 80)
print('MANUAL SPEED VERIFICATION')
print('=' * 80)
print('\nObservation #2 (index 1):')
obs1 = track1[0]
obs2 = track1[1]
print(f'  t1={obs1["timestamp"]:.6f}s, pos1={obs1["position"]}')
print(f'  t2={obs2["timestamp"]:.6f}s, pos2={obs2["position"]}')

dx = obs2['position'][0] - obs1['position'][0]
dy = obs2['position'][1] - obs1['position'][1]
distance = (dx**2 + dy**2)**0.5
dt = obs2['timestamp'] - obs1['timestamp']
speed_manual = distance / dt
print(f'  dx={dx:.2f}px, dy={dy:.2f}px')
print(f'  distance={distance:.2f}px, dt={dt:.6f}s')
print(f'  Manual speed: {speed_manual:.2f} px/s')
print(f'  Recorded speed: {obs2["speed"]:.2f} px/s')
print(f'  Match: {"✓" if abs(speed_manual - obs2["speed"]) < 0.01 else "✗"}')

print('\nObservation #10 (index 9):')
obs9 = track1[8]
obs10 = track1[9]
print(f'  t9={obs9["timestamp"]:.6f}s, pos9={obs9["position"]}')
print(f'  t10={obs10["timestamp"]:.6f}s, pos10={obs10["position"]}')

# The speed calculation uses last 5 positions (or fewer)
# For observation #10, it should use observations 5-10 (index 4-9)
n = min(5, len(track1[:10]))
start_obs = track1[10-n]
end_obs = track1[9]

dx = end_obs['position'][0] - start_obs['position'][0]
dy = end_obs['position'][1] - start_obs['position'][1]
distance = (dx**2 + dy**2)**0.5
dt = end_obs['timestamp'] - start_obs['timestamp']
speed_manual = distance / dt

print(f'  Speed uses last {n} observations (indices {10-n} to 9)')
print(f'  start: t={start_obs["timestamp"]:.6f}s, pos={start_obs["position"]}')
print(f'  end: t={end_obs["timestamp"]:.6f}s, pos={end_obs["position"]}')
print(f'  distance={distance:.2f}px, dt={dt:.6f}s')
print(f'  Manual speed: {speed_manual:.2f} px/s')
print(f'  Recorded speed: {obs10["speed"]:.2f} px/s')
print(f'  Match: {"✓" if abs(speed_manual - obs10["speed"]) < 0.01 else "✗"}')

print()
print('=' * 80)
print('TRACK 1 SPEED STATISTICS')
print('=' * 80)
speeds = [b['speed'] for b in track1]
print(f'Min: {min(speeds):.2f} px/s')
print(f'Max: {max(speeds):.2f} px/s')
print(f'Average: {sum(speeds)/len(speeds):.2f} px/s')
print(f'Median: {sorted(speeds)[len(speeds)//2]:.2f} px/s')

# Check M3 global statistics
print()
print('=' * 80)
print('M3 GLOBAL STATISTICS')
print('=' * 80)
print(f'M3 Total Behaviors: {data["m3_total_behaviors"]}')
print(f'M3 Avg Speed (global): {data["m3_avg_speed"]:.2f} px/s')
print(f'M3 Max Speed (global): {data["m3_max_speed"]:.2f} px/s')

# Verify global max speed
all_speeds = []
for frame_behaviors in data['all_behaviors']:
    for b in frame_behaviors:
        all_speeds.append(b['speed'])

print(f'\nManual verification:')
print(f'  Total behavior observations: {len(all_speeds)}')
print(f'  Manual avg speed: {sum(all_speeds)/len(all_speeds):.2f} px/s')
print(f'  Manual max speed: {max(all_speeds):.2f} px/s')
print(f'  Match avg: {"✓" if abs(data["m3_avg_speed"] - sum(all_speeds)/len(all_speeds)) < 0.01 else "✗"}')
print(f'  Match max: {"✓" if abs(data["m3_max_speed"] - max(all_speeds)) < 0.01 else "✗"}')

# Check which track had max speed
max_speed_behavior = max([b for frame in data['all_behaviors'] for b in frame], key=lambda x: x['speed'])
print(f'\nMax speed observation:')
print(f'  Track ID: {max_speed_behavior["track_id"]}')
print(f'  Speed: {max_speed_behavior["speed"]:.2f} px/s')
print(f'  Timestamp: {max_speed_behavior["timestamp"]:.2f}s')
print(f'  Position: {max_speed_behavior["position"]}')
print(f'  Displacement: {max_speed_behavior["displacement"]:.2f}px')

print()
print('=' * 80)
print('FRAME SKIP ANALYSIS')
print('=' * 80)
# Check if frame_skip is consistent
first_frame_behaviors = data['all_behaviors'][0]
second_frame_behaviors = data['all_behaviors'][1]
if first_frame_behaviors and second_frame_behaviors:
    t1 = first_frame_behaviors[0]['timestamp']
    t2 = second_frame_behaviors[0]['timestamp']
    dt = t2 - t1
    inferred_frame_skip = round(dt * data['video_fps'])
    print(f'First processed frame timestamp: {t1:.6f}s')
    print(f'Second processed frame timestamp: {t2:.6f}s')
    print(f'Time delta: {dt:.6f}s')
    print(f'Inferred frame_skip: {inferred_frame_skip}')

print()
print('=' * 80)
print('CONCLUSION')
print('=' * 80)
print('The speed calculation appears to be:')
print('1. Based on bbox center coordinates (px)')
print('2. Calculated over last N observations (up to 5)')
print('3. Using actual timestamp deltas')
print('4. Accounting for frame_skip correctly in timestamp')
print('5. Result is in pixels per second (image-space motion)')
print()
print('These are NOT real-world speeds!')
print('They represent motion in the 2D video frame.')
print(f'Video resolution: {data["video_width"]}x{data["video_height"]}')
print()
print('For context:')
print('  - 60 px/s = object moves 60 pixels per second in the frame')
print('  - 228 px/s = fast motion across ~1/10 frame width per second')
