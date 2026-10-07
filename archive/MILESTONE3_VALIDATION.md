# Milestone 3: Behaviour Analysis - Validation Guide

## Overview

Milestone 3 adds **behaviour analysis** on top of M2 tracking data. Instead of just knowing where objects are, the system now understands **how they're moving**.

## What is Behaviour Analysis?

Behaviour analysis examines **temporal movement patterns** to understand object behavior:

- **Temporal History**: Maintains recent positions and timestamps for each track
- **Movement Features**: Calculates speed, direction, displacement
- **Behaviour States**: Classifies movement as stationary, moving, or fast-moving
- **Configurable Thresholds**: All detection thresholds are adjustable

**Why Temporal History is Necessary:**
- Single frame can't tell you if object is moving
- Need position history to calculate speed
- Need time history to measure durations
- History enables trajectory analysis

**How Speed is Estimated:**
- Uses last 5 positions (or fewer if not available)
- Calculates distance between first and last position
- Divides by time elapsed
- Result: pixels per second

**Limitations of Pixel-based Speed:**
- Speed is in pixels, not real-world units (m/s)
- Depends on camera distance and resolution
- Same real speed appears different at different distances
- Good for relative comparisons within same video

## Installation & Setup

No additional dependencies needed - uses existing M1/M2 stack.

**Verify Installation:**
```bash
python -c "from processing.behavior import BehaviorAnalyzer; print('✅ Behavior module loaded')"
```

## Running Tests

### Run Behaviour Tests

```bash
cd processing
pytest tests/test_behavior_analyzer.py -v
```

**Expected:**
- 20+ tests covering all behaviour features
- All tests pass
- Tests for position, displacement, speed, direction, states, history

### Run All Tests (M1 + M2 + M3)

```bash
cd processing
pytest tests/ -v
```

**Expected:**
- All M1 detection tests pass
- All M2 tracking tests pass
- All M3 behaviour tests pass

## Running the Demo

### Synthetic Data Demo

The demo creates synthetic tracking data and analyzes behaviour:

```bash
cd processing
python -m processing.behavior.demo
```

**What the Demo Shows:**
1. Creates 3 synthetic tracks:
   - Person 1: Walking steadily (~50 px/s)
   - Person 2: Standing still (stationary)
   - Person 3: Running fast (~150 px/s)

2. Analyzes 150 frames (5 seconds at 30 fps)

3. Shows behaviour states at key moments

4. Prints track summaries with trajectories

5. Exports sample data to `behavior_analysis_demo.json`

**Expected Output:**
```
============================================================
Flagship 107 - Behavior Analysis Demo
============================================================

Configuration:
  Stationary threshold: 10.0 px/s
  Fast-moving threshold: 100.0 px/s
  Min stationary duration: 2.0s

Generating synthetic tracking data...
  Person 1: Walking steadily left-to-right (~50 px/s)
  Person 2: Standing still
  Person 3: Running fast diagonally (~150 px/s)

Generated 150 frames (5 seconds at 30 fps)

Frame 0 (t=0.00s):
  Track #1 (person): moving | speed=0.0 px/s | pos=100,280
  Track #2 (person): moving | speed=0.0 px/s | pos=540,200

Frame 30 (t=1.00s):
  Track #1 (person): moving | speed=50.1 px/s | pos=150,280
  Track #2 (person): stationary | speed=0.0 px/s | pos=540,200
  Track #3 (person): moving | speed=0.0 px/s | pos=50,150

...

Track Summaries:
  Track #1: Duration=4.97s, Observations=150
  Track #2: Duration=4.97s, Observations=150 (stationary)
  Track #3: Duration=3.97s, Observations=120 (fast-moving)

Demo Complete!
```

## Validation Checklist

### ✅ Core Functionality

- [ ] BehaviorAnalyzer initializes successfully
- [ ] Can process tracking data
- [ ] Calculates center positions correctly
- [ ] Calculates displacement between positions
- [ ] Estimates movement speed
- [ ] Calculates movement direction
- [ ] Detects stationary state
- [ ] Detects moving state
- [ ] Detects fast-moving state
- [ ] Maintains temporal history
- [ ] Respects max history size
- [ ] Handles empty tracking data

### ✅ Configuration

- [ ] Thresholds are configurable
- [ ] Stationary threshold works
- [ ] Fast-moving threshold works
- [ ] Min stationary duration works
- [ ] History size is configurable

### ✅ Module API

```python
from processing.behavior import BehaviorAnalyzer, BehaviorConfig

# Create configuration
config = BehaviorConfig(
    stationary_threshold=10.0,
    fast_moving_threshold=100.0,
    min_stationary_duration=2.0
)

# Create analyzer
analyzer = BehaviorAnalyzer(config)

# Analyze tracks
tracks = [...]  # From M2 tracking
behaviors = analyzer.update(tracks, timestamp=1.5)

# Get behavior features
for behavior in behaviors:
    print(f"Track {behavior['track_id']}: {behavior['state']}")
    print(f"  Speed: {behavior['speed']:.1f} px/s")
    print(f"  Direction: {behavior['direction']}")
```

### ✅ Tests

```bash
cd processing
pytest tests/test_behavior_analyzer.py -v
```

Expected tests (20+):
- test_analyzer_initialization
- test_calculate_center
- test_update_single_track
- test_displacement_calculation
- test_speed_calculation
- test_direction_calculation
- test_state_stationary
- test_state_moving
- test_state_fast_moving
- test_track_history_duration
- test_stationary_duration
- test_multiple_tracks
- test_empty_tracks
- test_get_statistics
- test_reset
- test_get_track_summary
- test_history_max_size

## Behaviour Output Format

**Per-Track Behaviour:**
```python
{
    "track_id": 3,
    "class_name": "person",
    "confidence": 0.87,
    "timestamp": 12.4,
    "position": [325.5, 180.2],
    "displacement": 14.2,        # pixels since last observation
    "speed": 52.3,               # pixels per second
    "direction": 45.0,           # degrees (0=right, 90=down)
    "state": "moving",           # stationary, moving, fast-moving
    "stationary_duration": 0.0,  # seconds (0 if not stationary)
    "total_duration": 5.2,       # total seconds tracked
    "history_length": 12         # number of observations
}
```

## Behaviour States

### Stationary
- **Condition**: Speed < 10 px/s for > 2 seconds
- **Use Case**: Detect people standing still, loitering
- **Threshold**: Configurable via `stationary_threshold`

### Moving
- **Condition**: 10 px/s ≤ Speed < 100 px/s
- **Use Case**: Normal walking, typical movement
- **Default State**: Most common state

### Fast-Moving
- **Condition**: Speed ≥ 100 px/s
- **Use Case**: Detect running, vehicles, unusual speed
- **Threshold**: Configurable via `fast_moving_threshold`

## Features Calculated

### Position (Center of Bounding Box)
```python
center_x = (bbox[0] + bbox[2]) / 2
center_y = (bbox[1] + bbox[3]) / 2
```

### Displacement (Distance Between Last Two Observations)
```python
displacement = sqrt((x2 - x1)² + (y2 - y1)²)
```

### Speed (Average Over Last 5 Positions)
```python
distance = sqrt((x_end - x_start)² + (y_end - y_start)²)
speed = distance / time_elapsed  # pixels per second
```

### Direction (Angle of Movement)
```python
angle = atan2(dy, dx) in degrees
# 0° = right, 90° = down, 180° = left, 270° = up
```

### Stationary Duration
- Tracks how long object has been below stationary threshold
- Resets to 0 when object starts moving

### Total Duration
- Time from first observation to current observation
- Useful for understanding track lifetime

## How M3 Prepares for Anomaly Detection (M4)

Behaviour analysis provides the foundation for anomaly detection:

**Temporal Features:**
- Speed history enables detecting unusual speed changes
- Direction enables detecting erratic movement
- Stationary duration enables detecting loitering

**Baseline Understanding:**
- Know what "normal" movement looks like
- Can compare current behavior to historical patterns
- States provide discrete categories for analysis

**Extensibility:**
- Current states (stationary, moving, fast-moving) are just the beginning
- M4 can add: loitering, restricted-area, unusual-pattern
- Behavior features feed into anomaly scoring

**Example for M4:**
```python
# M3 provides these features:
behavior = {
    "speed": 150.0,
    "state": "fast-moving",
    "stationary_duration": 0.0,
    "direction": 45.0
}

# M4 can detect anomalies:
if behavior["speed"] > 200:
    anomaly = "unusually_fast"
if behavior["stationary_duration"] > 300:
    anomaly = "loitering"
```

## Performance

### Memory Overhead
- Minimal: ~1-5KB per active track
- History limited to 30 observations
- Scales linearly with number of tracks

### Processing Speed
- Negligible impact on overall pipeline
- Simple calculations (< 1ms per track)
- No heavy computation or ML

### Accuracy
- Position, displacement: Exact
- Speed: Estimated from pixel movement
- Direction: Accurate when movement > 0.1 pixels
- States: Depends on threshold calibration

## Known Limitations

### Current Scope (M3)
- ✅ Movement features (speed, direction, displacement)
- ✅ Basic states (stationary, moving, fast-moving)
- ✅ Temporal history management
- ❌ No anomaly detection yet (M4)
- ❌ No event generation yet (M4)
- ❌ No loitering detection yet (M4)
- ❌ No restricted-area checking yet (M4)

### Technical Constraints
- Speed is in pixels, not real-world units
- Thresholds may need tuning per video
- Very shaky camera affects calculations
- Occlusions can cause speed spikes
- Direction undefined for stationary objects

## Troubleshooting

### Tests Fail
```bash
# Make sure M1/M2 dependencies are installed
cd processing
pip install -r requirements.txt

# Run tests with verbose output
pytest tests/test_behavior_analyzer.py -v -s
```

### "ModuleNotFoundError"
```bash
# From project root
python -c "import sys; sys.path.insert(0, '.'); from processing.behavior import BehaviorAnalyzer"
```

### Demo Doesn't Run
```bash
# Make sure you're in processing directory
cd processing
python -m processing.behavior.demo
```

### Unexpected States
- Check threshold configuration
- Verify tracking data quality
- Consider camera resolution/distance
- Tune thresholds for your scenario

## Integration with M2 Tracking

**Behaviour analysis consumes M2 tracking data:**

```python
from processing.tracking import ObjectTracker, VideoTracker
from processing.behavior import BehaviorAnalyzer, BehaviorConfig

# Step 1: Track objects (M2)
tracker = ObjectTracker()
video_tracker = VideoTracker(tracker)
stats = video_tracker.process_video("input.mp4", "output.mp4")

# Step 2: Analyze behavior (M3)
config = BehaviorConfig()
analyzer = BehaviorAnalyzer(config)

for frame_data in stats["frame_data"]:
    tracks = frame_data["tracks"]
    timestamp = frame_data["timestamp"]
    
    # Get behavior analysis
    behaviors = analyzer.update(tracks, timestamp)
    
    for behavior in behaviors:
        print(f"Track {behavior['track_id']}: {behavior['state']} @ {behavior['speed']:.1f} px/s")
```

## Success Criteria

Milestone 3 is validated when:

1. ✅ Behavior analyzer initializes successfully
2. ✅ Can process tracking data from M2
3. ✅ Calculates all movement features correctly
4. ✅ Determines behavior states based on thresholds
5. ✅ Maintains temporal history per track
6. ✅ All tests pass (20+)
7. ✅ Demo validates calculations with synthetic data
8. ✅ Configuration thresholds are adjustable
9. ✅ Module API is clean and documented
10. ✅ Extensible design for anomaly detection (M4)

---

**Updated:** 2026-10-06  
**Milestone:** 3 - Behaviour Analysis  
**Status:** Ready for Validation
