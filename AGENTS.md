# AI Agent Guidelines for Flagship 107

This document provides architectural context, coding conventions, and constraints for AI coding agents working on the Flagship 107 project.

## Project Overview

**Project Name:** Flagship 107  
**Purpose:** AI-powered video intelligence and behavioral anomaly detection platform  
**Target:** HackNEX 2026 Problem Statement HNX26PSI07  
**Phase:** MVP Development (Hackathon)

## Core Requirements

The system must:
1. Detect and track people/objects in video
2. Understand behavioral patterns
3. Distinguish normal vs unusual behavior
4. Identify meaningful events
5. Associate events with entities and timestamps

## Architecture Principles

### 1. Three-Layer Architecture

```
┌─────────────────────────────────────────┐
│           Frontend (React)               │
│  - Video player                          │
│  - Real-time visualization               │
│  - Timeline view                         │
└─────────────┬───────────────────────────┘
              │ REST API / WebSocket
┌─────────────▼───────────────────────────┐
│         Backend (FastAPI)                │
│  - API endpoints                         │
│  - WebSocket server                      │
│  - Job queue management                  │
│  - Result storage                        │
└─────────────┬───────────────────────────┘
              │ Internal calls
┌─────────────▼───────────────────────────┐
│      Processing Engines (Python)         │
│  - YOLO detection                        │
│  - Multi-object tracking                 │
│  - Anomaly detection                     │
│  - Ollama AI explanations                │
└─────────────────────────────────────────┘
```

### 2. Modularity

Each component must be:
- **Independent**: Can run standalone for testing
- **Replaceable**: Can swap implementations without breaking others
- **Testable**: Unit tests for core functions
- **Documented**: Clear docstrings and type hints

### 3. Data Flow

```
Video Upload → Frame Extraction → Detection → Tracking → 
Behavior Analysis → Anomaly Detection → Event Extraction → 
AI Explanation → Results JSON → Frontend Display
```

## Technology Stack

### Backend (Python)
- **Framework:** FastAPI 0.104+
- **Video Processing:** OpenCV 4.8+
- **Object Detection:** Ultralytics YOLO (YOLOv8)
- **Tracking:** BoT-SORT or ByteTrack
- **AI:** Ollama + Qwen2.5
- **Async:** asyncio, aiofiles

### Frontend (JavaScript/TypeScript)
- **Framework:** React 18
- **Build Tool:** Vite 5
- **State Management:** React Context (or Zustand if needed)
- **HTTP Client:** axios
- **WebSocket:** native WebSocket API
- **Styling:** TailwindCSS (planned)

### Infrastructure
- **Containerization:** Docker + Docker Compose
- **Version Control:** Git + GitHub

## Coding Conventions

### Python

**Style Guide:**
- Follow PEP 8
- Use type hints for all functions
- Maximum line length: 88 characters (Black default)
- Use meaningful variable names

**Example:**
```python
from typing import List, Dict, Optional
import numpy as np

async def detect_objects(
    frame: np.ndarray,
    confidence: float = 0.5
) -> List[Dict[str, any]]:
    """
    Detect objects in a video frame using YOLO.
    
    Args:
        frame: Input frame as numpy array (H, W, C)
        confidence: Minimum confidence threshold (0-1)
    
    Returns:
        List of detections with bbox, class, confidence
    """
    # Implementation here
    pass
```

**File Organization:**
- One class per file (unless tightly coupled)
- Group related functions in modules
- Keep files under 300 lines

**Error Handling:**
```python
# Use specific exceptions
class VideoProcessingError(Exception):
    pass

# Log errors appropriately
import logging
logger = logging.getLogger(__name__)

try:
    result = process_video(path)
except VideoProcessingError as e:
    logger.error(f"Processing failed: {e}")
    raise
```

### JavaScript/React

**Style Guide:**
- Use functional components with hooks
- Use arrow functions for components
- Destructure props
- Use const for immutable, let for mutable

**Example:**
```javascript
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const VideoPlayer = ({ videoUrl, onFrameChange }) => {
  const [currentFrame, setCurrentFrame] = useState(0);
  
  useEffect(() => {
    // Side effects here
  }, [videoUrl]);
  
  return (
    <div className="video-player">
      {/* JSX here */}
    </div>
  );
};

VideoPlayer.propTypes = {
  videoUrl: PropTypes.string.isRequired,
  onFrameChange: PropTypes.func,
};

export default VideoPlayer;
```

**Component Organization:**
```
components/
├── VideoPlayer/
│   ├── VideoPlayer.jsx
│   ├── VideoPlayer.test.jsx
│   └── index.js
```

## Important Constraints

### MVP Scope

**INCLUDE:**
- Video file upload (not real-time camera)
- Person detection and tracking
- Basic anomaly detection (sudden appearance, unusual speed, loitering)
- Bounding box visualization
- Timeline view
- JSON export

**EXCLUDE (Post-MVP):**
- Real-time camera feeds
- User authentication/authorization
- Database persistence (use JSON files)
- Cloud deployment
- Advanced ML models
- Mobile app

### Performance Targets

- Video processing: < 2x real-time (e.g., 30s video in < 60s)
- API response: < 200ms for status checks
- Frontend: 60fps rendering
- Max video size: 100MB for MVP

### Security Considerations

**For MVP:**
- Basic input validation
- File type checking
- Size limits
- CORS configuration

**Post-MVP:**
- JWT authentication
- Rate limiting
- Input sanitization
- Secure file storage

## Data Models

### Detection Result
```python
{
  "frame_id": 123,
  "timestamp": 4.1,  # seconds
  "detections": [
    {
      "track_id": "person_001",
      "class": "person",
      "confidence": 0.89,
      "bbox": [x1, y1, x2, y2],
      "center": [cx, cy]
    }
  ]
}
```

### Anomaly Event
```python
{
  "event_id": "evt_001",
  "type": "sudden_appearance",
  "severity": "medium",  # low, medium, high
  "track_id": "person_001",
  "start_frame": 100,
  "end_frame": 150,
  "start_time": 3.33,
  "end_time": 5.0,
  "description": "Person suddenly appeared in frame",
  "explanation": "AI-generated explanation from Ollama"
}
```

### Behavioral Pattern
```python
{
  "track_id": "person_001",
  "pattern": "loitering",
  "confidence": 0.75,
  "duration": 30.5,  # seconds
  "location": [x, y],
  "radius": 50  # pixels
}
```

## API Design

### RESTful Endpoints

```
POST   /api/v1/videos/upload          # Upload video file
GET    /api/v1/videos/{id}            # Get video metadata
POST   /api/v1/videos/{id}/process    # Start processing
GET    /api/v1/videos/{id}/status     # Processing status
GET    /api/v1/videos/{id}/results    # Get results JSON
GET    /api/v1/videos/{id}/detections # Paginated detections
GET    /api/v1/videos/{id}/anomalies  # Get anomalies
DELETE /api/v1/videos/{id}            # Delete video
```

### WebSocket Events

```
Client → Server:
  - subscribe: Subscribe to video processing updates
  - unsubscribe: Unsubscribe from updates

Server → Client:
  - processing_started
  - frame_processed: { frame_id, progress }
  - detection_update: { frame_id, detections }
  - anomaly_detected: { event }
  - processing_complete
  - error: { message }
```

## Development Workflow

### 1. Before Starting a Task

- Read this document
- Check the current milestone in README.md
- Review related code if modifying existing features
- Check for open issues/TODOs

### 2. During Development

- Write code in small, testable chunks
- Add type hints (Python) or PropTypes (React)
- Write docstrings for functions
- Handle errors gracefully
- Log important events

### 3. After Completing a Task

- Test manually with sample video
- Run automated tests if available
- Update documentation if API/interface changed
- Commit with clear message

### Git Commit Messages

Format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

Examples:
```
feat(detection): add YOLO object detection service
fix(api): handle empty video upload
docs(readme): update setup instructions
refactor(tracking): simplify track ID assignment
```

## Testing Strategy

### Backend Tests
```python
# tests/test_detection.py
import pytest
from app.services.detection import detect_objects

def test_detect_objects_returns_list():
    frame = load_sample_frame()
    results = detect_objects(frame)
    assert isinstance(results, list)

def test_detect_objects_with_no_detections():
    blank_frame = np.zeros((480, 640, 3))
    results = detect_objects(blank_frame)
    assert len(results) == 0
```

### Frontend Tests
```javascript
// VideoPlayer.test.jsx
import { render, screen } from '@testing-library/react';
import VideoPlayer from './VideoPlayer';

test('renders video player', () => {
  render(<VideoPlayer videoUrl="/test.mp4" />);
  const player = screen.getByRole('video');
  expect(player).toBeInTheDocument();
});
```

## Common Pitfalls to Avoid

### Python
- ❌ Loading entire video into memory
- ✅ Process frame by frame
- ❌ Blocking operations in async functions
- ✅ Use async/await properly
- ❌ Hardcoded paths
- ✅ Use environment variables

### React
- ❌ Storing large data in state
- ✅ Use refs or external storage
- ❌ Unnecessary re-renders
- ✅ Memoization with useMemo/useCallback
- ❌ Direct DOM manipulation
- ✅ Use React refs

### General
- ❌ No error handling
- ✅ Try-catch with specific exceptions
- ❌ Magic numbers
- ✅ Named constants
- ❌ No logging
- ✅ Structured logging with levels

## Resource References

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Ultralytics YOLO](https://docs.ultralytics.com/)
- [OpenCV Python](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [React Docs](https://react.dev/)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)

### Sample Videos for Testing
- Store in `data/samples/` directory
- Use short videos (5-30 seconds)
- Varied scenarios: indoor, outdoor, crowded, sparse

## Questions?

If you're unsure about:
- **Architecture decisions**: Consult this document first
- **Implementation details**: Check existing similar code
- **New features**: Ensure they align with MVP scope
- **Performance issues**: Profile before optimizing

## Future Enhancements (Post-MVP)

Track these in separate issues:
- Real-time camera support
- Advanced anomaly detection (ML-based)
- Database integration (PostgreSQL)
- User authentication
- Cloud deployment (AWS/Azure)
- Mobile app
- Advanced behavioral analysis
- Custom alert rules
- Multi-camera support
- Integration with external systems

---

**Last Updated:** 2026-10-06  
**Version:** 1.0 (Milestone 0)
