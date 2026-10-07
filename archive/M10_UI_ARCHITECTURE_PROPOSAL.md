# M10 Architecture Proposal: Video Intelligence Dashboard

**Date:** 2026-10-06  
**Status:** Awaiting Approval  
**Target:** HackNEX 2026 Live Demo

---

## Executive Summary

Transform Flagship 107 into a professional AI video intelligence dashboard suitable for live hackathon demonstration. The UI will showcase M1-M9 capabilities through a modern, information-dense interface that clearly distinguishes between observed facts, detected anomalies, contextual patterns, and LLM explanations.

**Core Principle:** Frontend displays data from FastAPI → M1-M9 pipeline. NO ML logic in frontend.

---

## Existing System Analysis

### Frontend (Current State)
- **Framework:** React 18 + Vite
- **Dependencies:** axios (API calls)
- **Existing Components:** VideoUpload.jsx, api.js
- **Status:** Minimal scaffold, needs full implementation

### Backend (Current State)
- **Framework:** FastAPI
- **Structure:** app/api/v1 (empty), app/core/config.py
- **Endpoints:** /health only (no video processing endpoints yet)
- **Status:** Scaffold only, needs video processing integration

### M1-M9 Pipeline (Complete)
- **Processing:** Complete M1-M9 implementation (202/202 tests passing)
- **Output:** PipelineResult with all_tracks, all_behaviors, all_anomalies, all_events, all_scenes
- **LLM:** Optional M9 with Ollama + Qwen3:8b

---

## 1. Overall UI Architecture

### Three-View Application

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   Upload    │ ──> │   Processing    │ ──> │   Dashboard      │
│    View     │     │      View       │     │   (Analysis)     │
└─────────────┘     └─────────────────┘     └──────────────────┘
     │                       │                         │
     └───────────────────────┴─────────────────────────┘
                             │
                    FastAPI Backend
                             │
                    M1-M9 Processing Pipeline
```

---

## 2. Main Views

### View 1: Upload (Entry Point)

**Purpose:** Video selection and upload

**Features:**
- Drag-and-drop or click to select
- File validation (MP4/AVI/MOV, <100MB)
- Recent videos list with status
- Quick access to processed videos

---

### View 2: Processing (Intermediate)

**Purpose:** Show M1-M9 pipeline progress

**Features:**
- Progress bars for each milestone (M1-M9)
- Current stage indicator
- Processing time
- Auto-redirect when complete

---

### View 3: Dashboard (Main Analysis)

**Purpose:** Primary intelligence interface

**Layout:** 3-Panel Design

```
┌────────────────────────────────────────────────────────────┐
│  TOP BAR: Quick Stats + Status                             │
├───────────────────────┬────────────────────────────────────┤
│                       │                                    │
│   LEFT PANEL (40%)    │    RIGHT PANEL (60%)              │
│                       │                                    │
│  ┌─────────────────┐  │  ┌──────────────────────────────┐ │
│  │  Video Player   │  │  │  Intelligence Tabs           │ │
│  │  + Overlays     │  │  │  - Overview (M1-M9 summary)  │ │
│  └─────────────────┘  │  │  - Tracks (M2 data)          │ │
│                       │  │  - Anomalies (M4 list)       │ │
│  ┌─────────────────┐  │  │  - Scenes (M8 context)       │ │
│  │  Event Timeline │  │  │  - LLM Explanation (M9)      │ │
│  │  (Interactive)  │  │  └──────────────────────────────┘ │
│  └─────────────────┘  │                                    │
│                       │                                    │
└───────────────────────┴────────────────────────────────────┘
```

---

## 3. Video Player Design

### Features

- **HTML5 video** element with custom controls
- **Overlays** (toggleable):
  - Bounding boxes (M1)
  - Track IDs (M2)
  - Trajectory lines (M3)
  - Anomaly highlights (M4)
- **Controls:** Play, pause, seek, speed (0.25x-2x)
- **Keyboard shortcuts:** Space (play/pause), ←/→ (frame step)
- **Sync:** Video position ↔ Timeline scrubber ↔ Event selection

---

## 4. Event Timeline

### Interactive Timeline

```
┌────────────────────────────────────────────────────────┐
│ Scenes:  ╠═══════════Scene 1═══════════╣              │
│          0s                          3.7s          10s │
│                                                        │
│ Anomalies:  🔴        🔴      🔴                       │
│            0.5s      1.2s    2.1s                      │
│                                                        │
│ Current: ●────────────────────────────────────────────►│
│         2.34s                                          │
└────────────────────────────────────────────────────────┘
```

**Features:**
- Scene ranges (M8 boundaries)
- Event markers (M4 anomalies, M5 events, M6 interactions)
- Click marker → jump to timestamp
- Hover → show event details tooltip
- Color coding by event type/severity

---

## 5. Intelligence Panel (Tabs)

### Tab 1: Overview

**M1-M9 Summary Statistics:**
- M1: Total detections, classes detected
- M2: Unique tracks, active entities
- M3: Behaviors analyzed, avg speed
- M4: Anomalies by type and severity
- M5: Correlated events
- M6: Entity interactions
- M8: Contextual scenes
- M9: LLM explanation status

### Tab 2: Tracks

**Track List:**
- Track ID, class name, duration
- Click track → highlight in video
- Timeline visualization per track
- Behavior summary (M3)

### Tab 3: Anomalies

**Anomaly List:**
- Time, type, track, severity
- Click → jump to timestamp
- Filter by type/severity
- "View Evidence" button → opens Evidence Panel

### Tab 4: Scenes (M8)

**Contextual Scenes:**
- Scene boundaries (start/end time)
- Participating tracks
- Detected patterns
- Activity summary
- Complexity score

### Tab 5: LLM Explanation (M9)

**Natural Language Explanation:**
- Overview paragraph
- Entity behaviors
- Pattern significance
- Anomaly explanation
- Contextual interpretation
- **Fallback notice** if Ollama unavailable
- Model badge (Qwen3:8b)
- Evidence coverage indicator

---

## 6. Evidence Panel (Modal/Drawer)

### Purpose: Show complete provenance for any claim

**Sections:**

1. **OBSERVED FACTS (M1-M7)**
   - Raw measurements
   - Detection confidence
   - No interpretation

2. **DETECTION CONFIDENCE**
   - YOLO confidence scores
   - Track stability
   - Anomaly scores

3. **SOURCE REFERENCES**
   - M1: Detection frame, bbox
   - M2: Track ID, duration
   - M3: Speed/direction measurements
   - M4: Anomaly ID, type
   - M5: Event ID (if correlated)
   - M8: Scene ID, context

4. **CONTEXT (M8)**
   - Scene type
   - Participating entities
   - Anomaly density

---

## 7. Clear Distinction Between Data Types

### Visual Design Language

**Observed Facts (M1-M7):**
- Color: Blue/Gray (neutral, factual)
- Icon: 📊
- Language: "Track #3 detected", "Speed: 66.16 px/s"

**Detected Anomalies (M4):**
- Color: Red/Orange (alert)
- Icon: ⚠️
- Language: "unusual_speed (>150 px/s threshold)"

**Contextual Patterns (M8):**
- Color: Purple (analytical)
- Icon: 🔍
- Language: "erratic_movement pattern detected"

**LLM Explanation (M9):**
- Color: Green (interpretive)
- Icon: 🧠
- Language: "may indicate", "consistent with"
- Clear badge: "[AI Generated]"

---

## 8. API Endpoints Required

### Video Management

```
POST   /api/v1/videos/upload              # Upload video file
GET    /api/v1/videos/{id}                # Get video metadata
POST   /api/v1/videos/{id}/process        # Start M1-M9 processing
GET    /api/v1/videos/{id}/status         # Get processing status
GET    /api/v1/videos/{id}/results        # Get complete results
GET    /api/v1/videos/{id}/stream         # Stream video file
DELETE /api/v1/videos/{id}                # Delete video
```

### Detailed Results

```
GET    /api/v1/videos/{id}/detections     # M1 data
GET    /api/v1/videos/{id}/tracks         # M2 data
GET    /api/v1/videos/{id}/behaviors      # M3 data
GET    /api/v1/videos/{id}/anomalies      # M4 data
GET    /api/v1/videos/{id}/events         # M5 data
GET    /api/v1/videos/{id}/scenes         # M8 data
GET    /api/v1/videos/{id}/scenes/{scene_id}/explanation  # M9
```

### System

```
GET    /health                            # Health check
GET    /api/v1/system/ollama              # Ollama status
GET    /api/v1/system/stats               # System stats
```

---

## 9. State Management

### React Context Approach

```javascript
// VideoContext: Current video, results, playback state
// UIContext: Selected tab, overlays, filters
```

**Why React Context (not Redux/Zustand):**
- Simple for single-video-at-a-time workflow
- Less boilerplate
- Sufficient for hackathon scope

---

## 10. Components to Create (~25 new)

### Layout (3)
- DashboardLayout.jsx
- TopBar.jsx
- TabPanel.jsx

### Video (4)
- VideoPlayer.jsx
- VideoOverlay.jsx
- VideoControls.jsx
- VideoScrubber.jsx

### Timeline (4)
- EventTimeline.jsx
- TimelineMarker.jsx
- SceneBar.jsx
- TimelineScrubber.jsx

### Intelligence Tabs (5)
- OverviewTab.jsx
- TracksTab.jsx
- AnomaliesTab.jsx
- ScenesTab.jsx
- ExplanationTab.jsx

### Evidence (3)
- EvidencePanel.jsx
- EvidenceSection.jsx
- SourceReference.jsx

### Processing (3)
- ProcessingView.jsx
- ProgressBar.jsx
- StageIndicator.jsx

### Upload (1)
- Update existing VideoUpload.jsx

---

## 11. Existing Components to Reuse

✓ **VideoUpload.jsx** - Minor styling updates  
✓ **api.js** - Extend with new endpoints  
✓ **App.jsx** - Restructure as router  

---

## 12. Dependencies Required

### New Dependencies (Minimal)

```json
{
  "dependencies": {
    "react-router-dom": "^6.21.0",  // Routing (Upload→Processing→Dashboard)
    "lucide-react": "^0.294.0"      // Icons (lightweight, tree-shakeable)
  }
}
```

**NOT Adding:**
- ❌ TailwindCSS (vanilla CSS faster for hackathon)
- ❌ Redux/Zustand (React Context sufficient)
- ❌ Material-UI (too generic, breaks dark theme aesthetic)
- ❌ Video.js (HTML5 video sufficient)
- ❌ Chart libraries initially (use CSS progress bars)

---

## 13. How UI Maps to M1-M9

### Data Flow

```
M1 (Detection)    → Video Overlay (bounding boxes)
                  → Overview Tab (stats)
                  → Evidence Panel (confidence)

M2 (Tracking)     → Video Overlay (track IDs)
                  → Tracks Tab (list)
                  → Timeline (track lifecycles)

M3 (Behavior)     → Tracks Tab (speed, direction, state)
                  → Evidence Panel (measurements)

M4 (Anomalies)    → Timeline (red markers)
                  → Anomalies Tab (list)
                  → Evidence Panel (threshold comparison)

M5 (Events)       → Timeline (yellow markers)
                  → Anomalies Tab (correlation)

M6 (Interactions) → Timeline (green markers)
                  → Scenes Tab (relationships)

M8 (Context)      → Timeline (scene ranges)
                  → Scenes Tab (full context)
                  → Evidence Panel (scene info)

M9 (LLM)          → Explanation Tab (natural language)
                  → Fallback indicator
```

---

## 14. Recommended Implementation Order

### Phase 1: Foundation (Days 1-2)
1. Setup react-router-dom
2. Create basic routing (Upload → Processing → Dashboard)
3. Implement VideoContext state management
4. Create DashboardLayout component

### Phase 2: Backend Integration (Days 2-3)
5. Implement FastAPI video upload endpoint
6. Implement process endpoint (calls M1-M9 pipeline)
7. Implement status endpoint (polling)
8. Implement results endpoint (return PipelineResult JSON)
9. Update frontend api.js with new endpoints

### Phase 3: Video Player (Days 3-4)
10. VideoPlayer component with HTML5 video
11. VideoControls (play, pause, seek, speed)
12. VideoOverlay (bounding boxes from M1, track IDs from M2)
13. Sync video position with timeline

### Phase 4: Timeline & Events (Days 4-5)
14. EventTimeline component
15. TimelineMarker for anomalies/events
16. SceneBar for M8 scene boundaries
17. Click to jump functionality

### Phase 5: Intelligence Panel (Days 5-6)
18. TabPanel layout
19. OverviewTab (M1-M9 summary stats)
20. TracksTab (M2 track list)
21. AnomaliesTab (M4 list with filters)
22. ScenesTab (M8 contextual scenes)
23. ExplanationTab (M9 with fallback)

### Phase 6: Evidence & Polish (Days 6-7)
24. EvidencePanel modal
25. Evidence sections (facts, confidence, sources, context)
26. ProcessingView with M1-M9 progress
27. Dark theme styling
28. Polish and testing

---

## 15. Live Demo Flow for Judge

### Optimal Demo Script (3 minutes)

**Minute 1: Upload & Process (30s)**
1. Open application → Upload View
2. Select sample.mp4 (or drag-and-drop)
3. Click "Start Processing"
4. Show M1-M9 progress bars updating
5. **Narration:** "Flagship 107 processes video through 9 AI milestones: detection, tracking, behavior analysis, anomaly detection, event correlation, interaction reasoning, calibration, contextual synthesis, and LLM explanation."

**Minute 2: Dashboard Overview (90s)**
6. Auto-navigate to Dashboard when complete
7. Play video → show bounding boxes with track IDs
8. Point to Timeline → "Events and anomalies mapped to timestamps"
9. Click anomaly marker → video jumps to exact moment
10. Show Right Panel tabs:
    - Overview: "271 detections, 4 unique tracks, 3 anomalies"
    - Tracks: "Each entity tracked with persistent ID"
    - Anomalies: "Unusual speed detected at 0.5s, Track #2"
11. **Narration:** "Real-time visualization of detected entities with persistent tracking. Timeline shows exactly when anomalies occurred."

**Minute 3: Evidence & AI Explanation (60s)**
12. Click "View Evidence" on an anomaly
13. Show Evidence Panel:
    - **Observed Facts:** "Speed: 228.54 px/s measured by M3"
    - **Threshold:** ">150 px/s configured in M4"
    - **Source:** "M1 detection → M2 track → M3 measurement → M4 anomaly"
14. Close evidence → Navigate to M9 tab
15. Show LLM Explanation:
    - "Three pedestrians observed with varied movement patterns..."
    - Point to badge: "Generated by Qwen3:8b in 1.2s"
    - "Falls back to deterministic narrative if AI unavailable"
16. **Narration:** "Complete evidence traceability from raw detection to AI-generated explanation. System clearly distinguishes observed facts from AI interpretation."

**Closing Statement:**
> "Flagship 107 provides end-to-end video intelligence: from YOLO detection to natural language explanations, all running locally with no cloud dependency. Every claim is backed by traceable evidence through our 9-stage pipeline."

---

## 16. Design Aesthetic

### Dark Professional Theme

**Color Palette:**
```
Background:     #0a0e1a (dark navy)
Surface:        #151b2e (slightly lighter)
Border:         #2a3451 (subtle borders)
Text Primary:   #e8eaef (white-ish)
Text Secondary: #9ca3af (gray)

Accents:
- Facts:        #60a5fa (blue)
- Anomalies:    #f97316 (orange)
- Patterns:     #a78bfa (purple)
- LLM:          #10b981 (green)
- Error:        #ef4444 (red)
```

**Typography:**
- Headers: Inter, 600 weight
- Body: Inter, 400 weight
- Monospace: 'Fira Code' for IDs, measurements

**UI Style:**
- Flat design (no shadows/gradients)
- Subtle borders (1px #2a3451)
- Rounded corners (4px-8px)
- Generous spacing (16px-24px margins)
- Information-dense but not cluttered

---

## 17. Technical Constraints

### Frontend Constraints
- No server-side rendering (Vite SPA)
- No real-time WebSocket (poll status endpoint)
- Single video at a time (no queue)
- No video editing (display only)

### Backend Constraints
- Synchronous processing (no background workers initially)
- Single-threaded video processing
- No database (JSON file storage)
- No authentication (local deployment)

### Performance Targets
- Upload: <5s for 100MB video
- Processing: <2x real-time (30s video in <60s)
- UI responsiveness: <100ms interaction latency
- Video playback: 30fps, no dropped frames

---

## 18. What This UI WILL NOT Do

**Out of Scope for M10:**
- ❌ Multiple video queue management
- ❌ Video editing/trimming
- ❌ Real-time camera feeds
- ❌ User authentication/authorization
- ❌ Cloud deployment
- ❌ Mobile app
- ❌ WebSocket real-time updates (will poll)
- ❌ Advanced analytics/reports
- ❌ Export to PDF/Word
- ❌ Multi-language support
- ❌ Accessibility features (WCAG) - future enhancement
- ❌ Dark/light theme toggle - dark only
- ❌ Responsive mobile layout - desktop focused

---

## Summary

### What We're Building

A **professional, dark-themed video intelligence dashboard** that:

1. ✅ Allows video upload
2. ✅ Shows M1-M9 processing progress
3. ✅ Displays video with AI overlays
4. ✅ Provides interactive event timeline
5. ✅ Shows M1-M9 intelligence in tabs
6. ✅ Enables evidence exploration
7. ✅ Displays M9 LLM explanations
8. ✅ Clearly distinguishes fact vs interpretation
9. ✅ Perfect for live hackathon demo

### Key Strengths for Demo

1. **Immediate Visual Impact:** Video with bounding boxes + track IDs
2. **Clear Value Proposition:** From raw video to natural language explanation
3. **Complete Transparency:** Evidence tracing from M1→M9
4. **Technical Depth:** Shows all 9 milestones clearly
5. **Professional Appearance:** Dark, modern, not student-project aesthetic

### Implementation Feasibility

**Estimated Effort:** 7 days for 1 developer
- Minimal new dependencies
- Reuse existing components where possible
- Focus on functionality over polish
- Leverage M1-M9 work (backend already complete)

---

**Ready for approval to proceed with implementation.**

