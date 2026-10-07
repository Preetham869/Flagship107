# Milestone 1: Hello Detection - Validation Guide

## Installation & Setup

### Step 1: Install Processing Dependencies

```bash
cd processing
pip install -r requirements.txt
```

This installs:
- OpenCV (video processing)
- Ultralytics YOLO (object detection)
- NumPy (array operations)
- PyTorch (deep learning backend)

**Expected:** Installation completes without errors. First YOLO model download happens automatically on first run.

### Step 2: Verify YOLO Model Loading

```bash
python -c "from processing.detection import YOLODetector; d = YOLODetector(device='cpu'); print('✅ YOLO loaded successfully')"
```

**Expected Output:**
```
Ultralytics YOLOv8.x.x ...
YOLOv8n summary: ...
✅ YOLO loaded successfully
```

## Running Detection Pipeline

### Basic Usage

```bash
# From project root
python run_detection.py path/to/video.mp4
```

**Expected:**
- Progress bar showing frame processing
- Output video saved as `video_annotated.mp4`
- Processing statistics displayed

### Test with Sample Video

If you have a sample video in `data/samples/`:

```bash
python run_detection.py data/samples/sample.mp4 -o outputs/detected.mp4
```

### Without a Video File

If no video is available, test the API directly:

```bash
python -c "
from processing.detection import YOLODetector, draw_detections
import numpy as np

# Create detector
detector = YOLODetector(device='cpu')

# Create test frame
frame = np.random.randint(0, 255, (480, 640, 3), dtype='uint8')

# Run detection
detections = detector.detect(frame)
print(f'Detector working: Found {len(detections)} objects')

# Test drawing
annotated = draw_detections(frame, detections)
print(f'Drawing working: Output shape {annotated.shape}')
print('✅ All components working')
"
```

## Running Tests

### Run All Tests

```bash
cd processing
pytest tests/ -v
```

**Expected:**
- All tests pass
- Test coverage for detector and processor
- CPU-only tests (no GPU required)

### Run Specific Test Suites

```bash
# Test YOLO detector
pytest tests/test_yolo_detector.py -v

# Test video processor
pytest tests/test_video_processor.py -v
```

## Validation Checklist

### ✅ Core Functionality

- [ ] YOLO model loads successfully
- [ ] Can detect objects in a frame
- [ ] Can process video file end-to-end
- [ ] Outputs annotated video with bounding boxes
- [ ] Handles missing video file gracefully
- [ ] GPU acceleration works (if CUDA available)
- [ ] CPU fallback works

### ✅ Command-Line Interface

- [ ] `python run_detection.py --help` shows usage
- [ ] Can process video with default settings
- [ ] `--person-only` flag works
- [ ] `--output` specifies custom output path
- [ ] `--confidence` adjusts detection threshold
- [ ] `--info` shows video information
- [ ] `--device cpu` forces CPU mode
- [ ] Progress bar updates during processing

### ✅ Module API

```python
from processing.detection import YOLODetector, VideoProcessor

# Test detector initialization
detector = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.5)
assert detector is not None

# Test detection on frame
import numpy as np
frame = np.zeros((480, 640, 3), dtype='uint8')
detections = detector.detect(frame)
assert isinstance(detections, list)

# Test video processor
processor = VideoProcessor(detector)
assert processor is not None
```

### ✅ Tests

- [ ] All pytest tests pass
- [ ] No GPU required for tests
- [ ] Test coverage for core functions
- [ ] Error cases handled

## Expected Output Structure

### Detection Result Format

```python
detection = {
    "bbox": [x1, y1, x2, y2],  # Bounding box coordinates
    "confidence": 0.87,          # Confidence score (0-1)
    "class_id": 0,              # COCO class ID
    "class_name": "person"       # Human-readable class name
}
```

### Processing Statistics

```python
stats = {
    "total_frames": 300,
    "processed_frames": 300,
    "total_detections": 450,
    "detections_per_frame": [1, 2, 1, 2, ...],
    "fps": 30.0,
    "resolution": (1920, 1080),
    "input_path": "input.mp4",
    "output_path": "output.mp4"
}
```

## Device Testing

### CPU Mode (Always Works)
```bash
python run_detection.py video.mp4 --device cpu
```

### GPU Mode (If CUDA Available)
```bash
python run_detection.py video.mp4 --device cuda
```

**Check GPU availability:**
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
```

## Performance Expectations

### Processing Speed (YOLOv8n on CPU)
- 720p video: ~5-10 FPS processing
- 1080p video: ~3-7 FPS processing
- Real-time factor: 2-4x (e.g., 30s video in 60-120s)

### Processing Speed (YOLOv8n on GPU)
- 720p video: ~30-60 FPS processing
- 1080p video: ~20-40 FPS processing
- Real-time factor: 0.5-1x (faster than real-time)

### Output File Size
- Similar to input video size
- Slightly larger due to annotations
- Codec: MP4V

## Known Limitations

### Current Scope
- ✅ Frame-by-frame detection
- ✅ Single video processing
- ❌ No tracking yet (Milestone 2)
- ❌ No anomaly detection yet (Milestone 3)
- ❌ No real-time streaming yet (Milestone 5)

### Technical Notes
- YOLO model downloads ~6MB on first run
- Requires ~2GB RAM for processing
- GPU processing requires CUDA-compatible GPU
- Output codec is MP4V (widely compatible)

## Troubleshooting

### "ModuleNotFoundError: No module named 'ultralytics'"
```bash
cd processing
pip install ultralytics
```

### "Failed to open video"
- Check file path is correct
- Verify video format is supported (MP4, AVI, MOV, etc.)
- Try with absolute path

### "CUDA out of memory"
```bash
# Use CPU instead
python run_detection.py video.mp4 --device cpu

# Or process every 2nd frame
python run_detection.py video.mp4 --skip 2
```

### Slow Processing
- Use smaller model: `yolov8n.pt` (fastest)
- Skip frames: `--skip 2` or `--skip 3`
- Use GPU if available: `--device cuda`
- Lower confidence: `--confidence 0.3` (fewer detections)

## Success Criteria

Milestone 1 is validated when:

1. ✅ YOLO model loads without errors
2. ✅ Can process a video file end-to-end
3. ✅ Output video contains bounding boxes and labels
4. ✅ Command-line interface works with all options
5. ✅ Tests pass with pytest
6. ✅ Error handling works for invalid inputs
7. ✅ Documentation is updated with usage examples
8. ✅ Module API is clean and reusable for Milestone 2

## Next Steps (Milestone 2)

After validation, proceed to Milestone 2: Multi-Object Tracking
- Add BoT-SORT or ByteTrack integration
- Assign persistent track IDs across frames
- Track appearance/disappearance events
- Visualize track history

---

**Updated:** 2026-10-06  
**Milestone:** 1 - Hello Detection  
**Status:** Ready for Validation
