# Flagship 107

AI-powered video intelligence and behavioral anomaly detection platform for HackNEX 2026 (Problem Statement HNX26PSI07).

## Features

- Real-time object detection and tracking (YOLO)
- Multi-object tracking with unique IDs
- Behavioral pattern analysis
- Anomaly detection
- Event extraction and timeline generation
- AI-powered explanations (Ollama/Qwen)

## Tech Stack

**Backend:**
- Python 3.10+
- FastAPI
- OpenCV
- Ultralytics YOLO
- WebSockets

**Frontend:**
- React 18
- Vite
- TailwindCSS (planned)

**AI/ML:**
- YOLOv8 for detection
- BoT-SORT/ByteTrack for tracking
- Ollama + Qwen for explanations

**Infrastructure:**
- Docker
- Docker Compose

## Project Structure

```
Flagship107/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── services/    # Business logic
│   │   ├── models/      # Data models
│   │   └── utils/       # Utilities
│   ├── tests/
│   └── requirements.txt
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── utils/
│   └── package.json
├── processing/          # AI/ML processing
│   ├── detection/
│   ├── tracking/
│   ├── anomaly/
│   └── requirements.txt
└── docker-compose.yml
```

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- Node.js 18+ and npm
- Docker and Docker Compose (optional)
- Git

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/macOS: `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Copy `.env.example` to `.env` and configure:
   ```bash
   cp ../.env.example .env
   ```

6. Run the development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. API documentation available at: http://localhost:8000/docs

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open browser at: http://localhost:5173

### Processing Module Setup

1. Navigate to the processing directory:
   ```bash
   cd processing
   ```

2. Install dependencies (includes Ultralytics YOLO):
   ```bash
   pip install -r requirements.txt
   ```

3. YOLO models will auto-download on first use

4. Test the detection pipeline:
   ```bash
   # From project root
   python run_detection.py --help
   ```

### Docker Setup (Alternative)

1. Build and start all services:
   ```bash
   docker-compose up --build
   ```

2. Services will be available at:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Running Object Detection (Milestone 1)

### Quick Start - Detection Pipeline

Flagship 107 can detect objects in videos using YOLO!

**1. Install Dependencies:**
```bash
cd processing
pip install -r requirements.txt
```

**2. Run Detection on a Video:**
```bash
# From project root
python run_detection.py path/to/your/video.mp4
```

**3. Advanced Options:**
```bash
# Detect only people
python run_detection.py video.mp4 --person-only

# Custom output path
python run_detection.py video.mp4 -o output/annotated.mp4

# Use different YOLO model (s/m/l/x for better accuracy)
python run_detection.py video.mp4 -m yolov8s.pt

# Adjust confidence threshold
python run_detection.py video.mp4 -c 0.7

# Get video information
python run_detection.py video.mp4 --info
```

**Output:**
- Annotated video saved with `_annotated.mp4` suffix
- Bounding boxes, class labels, and confidence scores

### Detection Module API

```python
from processing.detection import YOLODetector, VideoProcessor

# Initialize detector
detector = YOLODetector(model_name="yolov8n.pt", confidence_threshold=0.5)

# Process video
processor = VideoProcessor(detector)
stats = processor.process_video("input.mp4", "output.mp4")
```

---

## Running Multi-Object Tracking (Milestone 2) ⭐ NEW

### What is Multi-Object Tracking?

Multi-object tracking assigns **persistent IDs** to detected objects across video frames. Instead of just detecting "a person" in each frame, tracking identifies **"Person #1"** and maintains that ID throughout the video, even through occlusions.

**Why Persistent IDs Matter:**
- Track individual movements and behaviors over time
- Distinguish between multiple people in the same scene
- Enable behavior analysis (Milestone 3)
- Count unique individuals (not just detections per frame)

### Quick Start - Tracking Pipeline

**1. Run Tracking on a Video:**
```bash
# From project root
python run_tracking.py path/to/your/video.mp4
```

**Output:**
- Annotated video saved with `_tracked.mp4` suffix
- Bounding boxes with unique colors per track
- Track IDs displayed (e.g., "Person #1", "Person #2")
- JSON file with detailed tracking data

**2. Advanced Tracking Options:**
```bash
# Track only people
python run_tracking.py video.mp4 --person-only

# Custom output path
python run_tracking.py video.mp4 -o output/tracked.mp4

# Use ByteTrack (default) or BoT-SORT
python run_tracking.py video.mp4 --tracker bytetrack.yaml
python run_tracking.py video.mp4 --tracker botsort.yaml

# Use better YOLO model for accuracy
python run_tracking.py video.mp4 -m yolov8s.pt

# Adjust confidence threshold
python run_tracking.py video.mp4 -c 0.6

# Don't export JSON data
python run_tracking.py video.mp4 --no-export

# Get video information
python run_tracking.py video.mp4 --info
```

### Tracking Output

**Annotated Video:**
- Unique color per track ID
- Labels show: "Person #1 0.87" (class, ID, confidence)
- Persistent IDs across frames

**JSON Export (`video_tracked.json`):**
```json
{
  "processed_frames": 300,
  "unique_track_count": 3,
  "total_tracks": 450,
  "frame_data": [
    {
      "frame_id": 0,
      "timestamp": 0.0,
      "tracks": [
        {
          "track_id": 1,
          "bbox": [120, 80, 250, 350],
          "confidence": 0.87,
          "class_id": 0,
          "class_name": "person"
        }
      ]
    }
  ]
}
```

### Tracking Module API

```python
from processing.tracking import ObjectTracker, VideoTracker

# Initialize tracker
tracker = ObjectTracker(
    model_name="yolov8n.pt",
    confidence_threshold=0.5,
    tracker_config="bytetrack.yaml"
)

# Process video with tracking
video_tracker = VideoTracker(tracker)
stats = video_tracker.process_video("input.mp4", "output.mp4")

print(f"Unique tracks: {stats['unique_track_count']}")
```

### Tracking Features

✅ **Implemented (Milestone 2):**
- Persistent track IDs across frames
- YOLO's built-in tracking (ByteTrack/BoT-SORT)
- GPU acceleration with CPU fallback
- Track visualization with unique colors
- JSON export of tracking data
- Track statistics (unique tracks, detections per frame)
- Person-only tracking mode
- Modular API for behavior analysis

**Tracking vs Detection:**
- **Detection (M1)**: Finds objects in each frame independently
- **Tracking (M2)**: Links detections across frames with persistent IDs

---

## Behaviour Analysis (Milestone 3) ⭐ NEW

### What is Behaviour Analysis?

Behaviour analysis examines **temporal movement patterns** to understand how objects move:

**Key Concepts:**
- **Temporal History**: Maintains recent positions/timestamps for each track
- **Movement Features**: Calculates speed, direction, displacement
- **Behaviour States**: Classifies as stationary, moving, or fast-moving
- **Configurable Thresholds**: All detection thresholds are adjustable

**Why Temporal History Matters:**
- Single frame can't determine if object is moving
- Need position history to calculate velocity
- Need time history to measure durations
- Enables trajectory analysis for anomaly detection

### Running the Demo

**Quick Demo with Synthetic Data:**
```bash
cd processing
python -m processing.behavior.demo
```

**What the Demo Shows:**
- Creates 3 synthetic people (walking, stationary, running)
- Analyzes 5 seconds of movement
- Calculates speed, direction, and states
- Shows behaviour at key moments
- Exports sample data to JSON

**Expected Output:**
```
Frame 0 (t=0.00s):
  Track #1 (person): moving | speed=0.0 px/s
  Track #2 (person): moving | speed=0.0 px/s

Frame 60 (t=2.00s):
  Track #1 (person): moving | speed=50.1 px/s
  Track #2 (person): stationary | speed=0.0 px/s
  Track #3 (person): fast-moving | speed=150.2 px/s
```

### Behaviour Module API

```python
from processing.behavior import BehaviorAnalyzer, BehaviorConfig

# Configure thresholds
config = BehaviorConfig(
    stationary_threshold=10.0,     # < 10 px/s is stationary
    fast_moving_threshold=100.0,   # > 100 px/s is fast-moving
    min_stationary_duration=2.0    # Must be still for 2s
)

# Create analyzer
analyzer = BehaviorAnalyzer(config)

# Analyze tracks from M2
tracks = [...]  # From ObjectTracker
behaviors = analyzer.update(tracks, timestamp=1.5)

# Get behavior features
for behavior in behaviors:
    print(f"Track {behavior['track_id']}: {behavior['state']}")
    print(f"  Speed: {behavior['speed']:.1f} px/s")
    print(f"  Direction: {behavior['direction']:.0f}°")
    print(f"  Position: {behavior['position']}")
```

### Behaviour Features Calculated

**Position (Center of Bounding Box)**
```python
center = ((x1 + x2) / 2, (y1 + y2) / 2)
```

**Displacement (Distance Between Observations)**
```python
displacement = sqrt((x2 - x1)² + (y2 - y1)²)
```

**Speed (Pixels Per Second)**
```python
# Uses last 5 positions for smoothing
distance = sqrt((x_end - x_start)² + (y_end - y_start)²)
speed = distance / time_elapsed
```

**Direction (Degrees)**
```python
# 0° = right, 90° = down, 180° = left, 270° = up
direction = atan2(dy, dx) converted to degrees
```

**State (Based on Thresholds)**
- **Stationary**: Speed < 10 px/s for > 2 seconds
- **Moving**: 10 ≤ Speed < 100 px/s
- **Fast-Moving**: Speed ≥ 100 px/s

### Behaviour Output Format

```python
{
    "track_id": 3,
    "class_name": "person",
    "confidence": 0.87,
    "timestamp": 12.4,
    "position": [325.5, 180.2],
    "displacement": 14.2,        # pixels since last frame
    "speed": 52.3,               # pixels per second
    "direction": 45.0,           # degrees
    "state": "moving",           # stationary/moving/fast-moving
    "stationary_duration": 0.0,  # seconds stationary
    "total_duration": 5.2,       # total tracking time
    "history_length": 12         # observations stored
}
```

### Integration: M2 Tracking → M3 Behaviour

```python
from processing.tracking import ObjectTracker, VideoTracker
from processing.behavior import BehaviorAnalyzer, BehaviorConfig

# Step 1: Track objects (M2)
tracker = ObjectTracker()
video_tracker = VideoTracker(tracker)
tracking_stats = video_tracker.process_video("input.mp4", "tracked.mp4")

# Step 2: Analyze behavior (M3)
config = BehaviorConfig()
analyzer = BehaviorAnalyzer(config)

for frame_data in tracking_stats["frame_data"]:
    tracks = frame_data["tracks"]
    timestamp = frame_data["timestamp"]
    
    # Analyze movement patterns
    behaviors = analyzer.update(tracks, timestamp)
    
    for behavior in behaviors:
        if behavior["state"] == "stationary":
            print(f"Track {behavior['track_id']} standing still for {behavior['stationary_duration']:.1f}s")
        elif behavior["state"] == "fast-moving":
            print(f"Track {behavior['track_id']} moving fast at {behavior['speed']:.1f} px/s")
```

### How M3 Prepares for Anomaly Detection

Behaviour analysis provides the foundation for M4:

**Temporal Features:**
- Speed history → Detect unusual speed changes
- Direction → Detect erratic movement
- Stationary duration → Detect loitering

**Baseline Understanding:**
- Know what "normal" movement looks like
- Compare current to historical patterns
- States provide discrete categories

**Extensibility:**
- Current: stationary, moving, fast-moving
- M4 will add: loitering, restricted-area, unusual-pattern
- Behaviour features feed anomaly scoring

### Limitations of Pixel-Based Speed

**Important:**
- Speed is in **pixels per second**, not real-world units (m/s)
- Same speed appears different at different camera distances
- Closer objects move more pixels for same real speed
- Farther objects move fewer pixels

**Use Cases:**
- ✅ Relative comparisons within same video
- ✅ Detecting fast vs slow movement
- ✅ Identifying state changes
- ❌ Cross-video absolute speed comparison
- ❌ Real-world speed estimation without calibration

**Example:**
- Person walking at camera: ~50-100 px/s
- Same person far from camera: ~10-20 px/s
- Thresholds need tuning per camera setup

## Development Workflow

### Running Tests

**Processing Module:**
```bash
cd processing
pytest tests/
```

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd frontend
npm run test
```

### Code Style

**Python:**
- Follow PEP 8
- Use black for formatting: `black .`
- Use flake8 for linting: `flake8 .`

**JavaScript/React:**
- Use ESLint: `npm run lint`
- Use Prettier: `npm run format`

## MVP Scope

### ✅ Milestones 1-9 (COMPLETED)
- ✅ M1: Object Detection (YOLO)
- ✅ M2: Multi-object Tracking with persistent IDs (ByteTrack/BoT-SORT)
- ✅ M3: Behavioral Analysis (speed, direction, states)
- ✅ M4: Anomaly Detection (unusual speed, direction, etc)
- ✅ M5: Event Extraction (clustering anomalies)
- ✅ M6: Interactions (relationship tracking)
- ✅ M8: Context Synthesis (scene understanding)
- ✅ M9: AI Explanations (Ollama + Qwen3:8b with deterministic fallback)
- ✅ Full Stack Integration (FastAPI backend + React frontend)

**Not in MVP:**
- Real-time camera feeds
- User authentication
- Database persistence
- Cloud deployment
- Advanced ML models

## Contributing

This is a hackathon project. For AI coding agents working on this project, please refer to `AGENTS.md` for architecture details and coding conventions.

## License

MIT License (to be confirmed)

## Team

Built for HackNEX 2026

## Acknowledgments

- Ultralytics YOLO team
- FastAPI framework
- React and Vite communities
