# Milestone 2: Multi-Object Tracking - Validation Guide

## Installation & Setup

### Dependencies

All tracking dependencies are already included in `processing/requirements.txt` from Milestone 1. No additional installation needed.

**Verify Installation:**
```bash
python -c "from processing.tracking import ObjectTracker; print('✅ Tracking module loaded')"
```

## Running Multi-Object Tracking

### Basic Usage

```bash
# From project root
python run_tracking.py path/to/video.mp4
```

**Expected Output:**
- Progress bar showing frame processing
- Output video saved as `video_tracked.mp4`
- JSON file saved as `video_tracked.json`
- Processing statistics displayed

### Advanced Options

```bash
# Track only people
python run_tracking.py video.mp4 --person-only

# Custom output path
python run_tracking.py video.mp4 -o outputs/my_tracked.mp4

# Use BoT-SORT instead of ByteTrack
python run_tracking.py video.mp4 --tracker botsort.yaml

# Use better YOLO model (more accurate, slower)
python run_tracking.py video.mp4 -m yolov8s.pt

# Adjust confidence threshold
python run_tracking.py video.mp4 -c 0.6

# Process every 2nd frame (faster)
python run_tracking.py video.mp4 --skip 2

# Don't export JSON data
python run_tracking.py video.mp4 --no-export

# Force CPU mode
python run_tracking.py video.mp4 --device cpu

# Get video information
python run_tracking.py video.mp4 --info
```

## Running Tests

### Run All Tracking Tests

```bash
cd processing
pytest tests/test_object_tracker.py tests/test_video_tracker.py -v
```

**Expected:**
- All tests pass
- Tests cover tracker initialization, tracking logic, drawing, statistics
- No GPU required for tests

### Run Specific Test Suites

```bash
# Test object tracker
pytest tests/test_object_tracker.py -v

# Test video tracker
pytest tests/test_video_tracker.py -v
```

## Validation Checklist

### ✅ Core Functionality

- [ ] ObjectTracker initializes successfully
- [ ] Can track objects in a frame
- [ ] Track IDs persist across frames
- [ ] Outputs tracked video with IDs
- [ ] Handles missing video file gracefully
- [ ] GPU acceleration works (if CUDA available)
- [ ] CPU fallback works
- [ ] JSON export contains tracking data

### ✅ Command-Line Interface

- [ ] `python run_tracking.py --help` shows usage
- [ ] Can process video with default settings
- [ ] `--person-only` flag works
- [ ] `--output` specifies custom output path
- [ ] `--tracker` switches between ByteTrack/BoT-SORT
- [ ] `--confidence` adjusts detection threshold
- [ ] `--info` shows video information
- [ ] `--device cpu` forces CPU mode
- [ ] `--no-export` skips JSON export
- [ ] Progress bar updates during processing

### ✅ Module API

```python
from processing.tracking import ObjectTracker, VideoTracker

# Test tracker initialization
tracker = ObjectTracker(model_name="yolov8n.pt", confidence_threshold=0.5)
assert tracker is not None

# Test tracking on frame
import numpy as np
frame = np.zeros((480, 640, 3), dtype='uint8')
tracks = tracker.track(frame)
assert isinstance(tracks, list)

# Test video tracker
video_tracker = VideoTracker(tracker)
assert video_tracker is not None
```

### ✅ Tracking Data Structure

**Track Format:**
```python
track = {
    "track_id": 1,              # Persistent ID
    "bbox": [x1, y1, x2, y2],   # Bounding box
    "confidence": 0.87,          # Confidence score
    "class_id": 0,              # COCO class ID
    "class_name": "person"       # Class name
}
```

**Statistics Format:**
```python
stats = {
    "processed_frames": 300,
    "unique_track_count": 3,
    "total_tracks": 450,
    "frame_data": [...],         # Per-frame tracking data
    "tracker_stats": {...},      # Tracker statistics
}
```

### ✅ Tests

- [ ] All pytest tests pass
- [ ] No GPU required for tests
- [ ] Test coverage for core functions
- [ ] Error cases handled

## Expected Output

### Tracked Video Features

**Visual Annotations:**
- Bounding boxes with unique colors per track
- Track IDs displayed (e.g., "Person #1", "Person #2")
- Class name and confidence shown
- Colors persist across frames for same ID

**JSON Export (`video_tracked.json`):**
- Frame-by-frame tracking data
- Track IDs, bounding boxes, confidences
- Timestamps for each frame
- Unique track statistics

### Processing Statistics

```
Tracking Complete!
============================================================
Processed frames: 300
Unique tracks: 3
Total detections: 450
Average tracks per frame: 1.50
Output video: video_tracked.mp4
Tracking data: video_tracked.json
============================================================
```

## Performance Expectations

### Processing Speed (YOLOv8n on CPU)
- 720p video: ~4-8 FPS tracking (slightly slower than detection)
- 1080p video: ~2-5 FPS tracking
- Real-time factor: 3-5x (30s video in 90-150s)

### Processing Speed (YOLOv8n on GPU)
- 720p video: ~25-50 FPS tracking
- 1080p video: ~15-30 FPS tracking
- Real-time factor: 0.6-1.2x (near real-time)

### Memory Usage
- Similar to detection (Milestone 1)
- Tracking adds minimal overhead (~50-100MB)
- Scales with number of simultaneous tracks

## Tracking Features

### ByteTrack (Default)
- Fast and efficient
- Good for simple scenarios
- Robust to occlusions
- Used by default

### BoT-SORT
- More accurate ID maintenance
- Better for crowded scenes
- Slightly slower
- Use with `--tracker botsort.yaml`

### Track ID Assignment
- IDs start from 1
- Persistent across frames
- Survive brief occlusions (~10-30 frames)
- New IDs assigned when tracks reappear after long absence

## Known Limitations

### Current Scope (Milestone 2)
- ✅ Persistent track IDs
- ✅ Track visualization
- ✅ JSON export
- ❌ No behavior analysis yet (Milestone 3)
- ❌ No anomaly detection yet (Milestone 3)
- ❌ No timeline view yet (Milestone 5/6)

### Technical Notes
- Tracking performance depends on scene complexity
- More objects = slower processing
- Occlusions can cause ID switches in difficult cases
- Fast motion may challenge tracker
- CPU tracking is functional but slow

## Troubleshooting

### "ModuleNotFoundError: No module named 'ultralytics'"
Already installed from Milestone 1. If needed:
```bash
cd processing
pip install ultralytics
```

### "Failed to open video"
- Check file path is correct
- Verify video format is supported (MP4, AVI, MOV, etc.)
- Try with absolute path

### Slow Tracking
- Use GPU if available: remove `--device cpu`
- Skip frames: `--skip 2` or `--skip 3`
- Use faster model: `yolov8n.pt` (default, fastest)
- Lower confidence: `--confidence 0.3`

### ID Switches
- Increase model size: `--model yolov8s.pt` or larger
- Use BoT-SORT: `--tracker botsort.yaml`
- Ensure good lighting and resolution

## Differences from Detection (M1)

| Feature | Detection (M1) | Tracking (M2) |
|---------|---------------|---------------|
| **IDs** | No persistent IDs | Persistent track IDs |
| **Visualization** | Same color for all | Unique color per track |
| **Labels** | "person 0.87" | "Person #1 0.87" |
| **JSON Export** | Not implemented | Full track data |
| **API** | `YOLODetector` | `ObjectTracker` |
| **CLI** | `run_detection.py` | `run_tracking.py` |
| **Speed** | Faster | Slightly slower |

## Success Criteria

Milestone 2 is validated when:

1. ✅ ObjectTracker loads successfully
2. ✅ Can process video with persistent IDs
3. ✅ Same object maintains same ID across frames
4. ✅ Output video shows unique colors per track
5. ✅ Track IDs displayed in labels
6. ✅ JSON export contains tracking data
7. ✅ Command-line interface works with all options
8. ✅ Tests pass with pytest
9. ✅ Error handling for invalid inputs
10. ✅ Module API is clean and ready for Milestone 3

## Module Integration

**For Milestone 3 (Behavior Analysis):**

Tracking data is now available for behavioral analysis:

```python
from processing.tracking import ObjectTracker, VideoTracker

# Process video with tracking
tracker = ObjectTracker()
video_tracker = VideoTracker(tracker)
stats = video_tracker.process_video("input.mp4", "output.mp4")

# Access track data for analysis
for frame_data in stats["frame_data"]:
    frame_id = frame_data["frame_id"]
    timestamp = frame_data["timestamp"]
    
    for track in frame_data["tracks"]:
        track_id = track["track_id"]
        bbox = track["bbox"]
        # Analyze track positions, velocities, patterns...
```

---

**Updated:** 2026-10-06  
**Milestone:** 2 - Multi-Object Tracking  
**Status:** Ready for Validation
