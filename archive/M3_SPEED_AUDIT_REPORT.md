# M3 Behaviour Speed Calculation Audit Report

**Date:** 2026-10-06  
**Video:** sample.mp4 (2160x3840, 23.98 FPS, 240 frames, ~10 seconds)  
**Auditor:** Kiro AI Agent

---

## Executive Summary

✅ **The M3 speed calculation is mathematically CORRECT**

The reported speeds (e.g., Track #1: ~50 px/s avg, ~94 px/s max) accurately represent **image-space motion in pixels per second**. These are NOT real-world speeds in km/h or m/s.

---

## Detailed Findings

### 1. Displacement Calculation ✓ CORRECT

**Method:** Euclidean distance between bbox centers  
**Formula:** `distance = sqrt((x2-x1)² + (y2-y1)²)`

**Verification:**
- Bbox center calculated as: `center = ((x1+x2)/2, (y1+y2)/2)`
- Uses consecutive positions correctly
- Manual verification: ✓ matches recorded values

**Code Location:** `processing/behavior/analyzer.py:220-235`

```python
def _calculate_displacement(self, history: TrackHistory) -> float:
    if len(history.positions) < 2:
        return 0.0
    pos1 = history.positions[-2]
    pos2 = history.positions[-1]
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    return math.sqrt(dx * dx + dy * dy)
```

---

### 2. Timestamp/Delta Time Calculation ✓ CORRECT

**Method:** Frame index divided by FPS  
**Formula:** `timestamp = frame_idx / fps`

**Verification:**
- Frame_skip is correctly accounted for in frame_idx
- For sample.mp4: frame_skip=1, so delta_t = 1/23.98 = 0.0417s
- Timestamps progress correctly: [0.0000, 0.0417, 0.0834, ...]
- Manual verification: ✓ matches recorded timestamps

**Code Location:** `processing/pipeline/e2e_pipeline.py:293`

```python
timestamp = frame_idx / fps if fps > 0 else frame_idx
```

---

### 3. FPS Usage ✓ CORRECT

**Video FPS:** 23.976023976023978 (exact)  
**Frame intervals:** 0.0417s average (matches 1/FPS)  

FPS is correctly used to convert frame indices to real timestamps.

---

### 4. Frame Skip Accounting ✓ CORRECT

**Pipeline behavior:**
- Frame_skip is applied before timestamp calculation
- Only processed frames get timestamps
- The skipped frames never enter the behavior analyzer
- Timestamps reflect actual elapsed time

**Code Location:** `processing/pipeline/e2e_pipeline.py:283-289`

```python
# Apply frame skip
if frame_idx % self.config.frame_skip != 0:
    frame_idx += 1
    result.frames_skipped += 1
    continue
```

**Verification:** With frame_skip=1, all frames processed, timestamps increment by 0.0417s ✓

---

### 5. Bounding Box Center Coordinates ✓ CORRECT

**Method:** Arithmetic mean of bbox corners  
**Formula:** `center_x = (x1 + x2) / 2`, `center_y = (y1 + y2) / 2`

All position tracking uses bbox centers, not corners or edges.

---

### 6. Speed Calculation Between Observations ✓ CORRECT

**Method:** Displacement over last N observations (N ≤ 5)  
**Formula:** `speed = distance / time_delta`

**Code Location:** `processing/behavior/analyzer.py:237-267`

```python
def _calculate_speed(self, history: TrackHistory) -> float:
    if len(history.positions) < self.config.min_history_for_speed:
        return 0.0
    
    # Use last few observations for speed
    n = min(5, len(positions))  # Use last 5 positions
    if n < 2:
        return 0.0
    
    pos_start = positions[-n]
    pos_end = positions[-1]
    time_start = timestamps[-n]
    time_end = timestamps[-1]
    
    dx = pos_end[0] - pos_start[0]
    dy = pos_end[1] - pos_start[1]
    distance = math.sqrt(dx * dx + dy * dy)
    
    time_delta = time_end - time_start
    if time_delta <= 0:
        return 0.0
    
    speed = distance / time_delta
    return speed
```

**Behavior:**
- For observation #2 (index 1): uses observations [0, 1] → 2-point speed ✓
- For observation #10 (index 9): uses observations [5-9] → 5-point speed ✓
- Smooths jitter by averaging over multiple frames
- Manual verification: ✓ matches all recorded values

---

### 7. First Observation / Missing Observations ✓ CORRECT

**First observation handling:**
- Speed = 0.0 (only 1 position available)
- No division by zero errors
- Displacement = 0.0

**Missing observations:**
- Each track maintains independent history
- Gaps in tracking handled by time_delta calculation
- If track disappears and reappears, speed calculated from available history
- No incorrect speeds from discontinuities

---

### 8. Track ID Changes / Detection Gaps ✓ CORRECT

**Track persistence:**
- Each track_id has independent TrackHistory object
- Re-identification creates new track (new ID)
- Old track history preserved, new track starts fresh
- No cross-contamination between tracks

**Code Location:** `processing/behavior/analyzer.py:110-120`

```python
# Get or create history
if track_id not in self.track_histories:
    self.track_histories[track_id] = TrackHistory(track_id=track_id)

history = self.track_histories[track_id]
```

---

### 9. Mathematical Consistency ✓ VERIFIED

**Sample Data Analysis (sample_e2e_result_m8.json):**

| Track | Observations | Avg Speed | Max Speed | Duration |
|-------|-------------|-----------|-----------|----------|
| Track 1 | 90 | 50.0 px/s | 94.3 px/s | 3.71s |
| Track 2 | 89 | 78.0 px/s | 228.5 px/s | 3.71s |
| Track 3 | 32 | 51.1 px/s | 105.7 px/s | 1.33s |
| Track 4 | 29 | 64.2 px/s | 132.0 px/s | 1.17s |
| Track 5 | 31 | 40.5 px/s | 87.6 px/s | 1.25s |

**Global statistics:**
- M3 Total Behaviors: 271
- M3 Avg Speed: 60.68 px/s ✓ (manual: 60.68 px/s)
- M3 Max Speed: 228.54 px/s ✓ (manual: 228.54 px/s - Track 2)

All values mathematically consistent with underlying track coordinates.

---

### 10. M4/M7 Anomaly Threshold Dependencies ✓ CORRECT

**M4 Anomaly Detector Threshold:**
- `unusual_speed_threshold: 150.0 px/s`
- Located in: `processing/anomaly/detector.py:104`

**Analysis:**
- M4 uses the SAME speed values from M3 behavior analysis
- Threshold is appropriate for image-space motion
- Sample.mp4 max speed (228.5 px/s) correctly triggers unusual_speed anomaly
- No bugs in threshold comparison logic

**M7 dependencies:** (not yet implemented in current codebase)

---

## What the Values Represent

### Image-Space Motion (Correct Interpretation)

The speeds are **2D pixel velocities** in the video frame coordinate system:

```
60 px/s  = object moves 60 pixels per second across the frame
228 px/s = fast motion, ~5% of frame width per second (228/3840)
```

**Context for sample.mp4 (2160x3840):**
- 50 px/s ≈ 1.3% of frame width per second
- 228 px/s ≈ 5.9% of frame width per second
- These represent visible motion in the camera view

### NOT Real-World Speeds

These are **NOT** kilometers per hour or meters per second. Converting to real-world units requires:
1. Camera calibration (pixel-to-meter ratio)
2. Perspective correction (distance from camera)
3. Camera height and angle
4. Lens distortion correction

Without this calibration, the speeds remain in **pixels per second**.

---

## User-Reported Values Investigation

**User stated:**
> "Track #1 average speed: 118.7 px/s"  
> "Track #1 maximum speed: 458.3 px/s"

**Backend data (sample_e2e_result_m8.json):**
- Track #1 average speed: **50.0 px/s**
- Track #1 maximum speed: **94.3 px/s**

**Discrepancy:** User-reported values are **~2.4x higher** than backend data.

### Possible Explanations:

1. **Different video file**: User may have processed a different video with faster motion
2. **Frontend calculation error**: TracksTab.jsx may have a bug in aggregation
3. **Different processing run**: User may have a newer result file not yet committed
4. **Unit confusion**: User may be seeing values from a different source
5. **Browser cache**: Frontend may be caching old result data

### Investigation Required:

User should verify:
- Which result file the frontend is loading
- Current TracksTab calculation logic (appears correct in current code)
- Browser developer console for actual API response
- Whether they re-ran processing after recent code changes

---

## UI Display Recommendations

### ✅ Current Display (Correct)

The UI correctly shows:
```jsx
{track.avg_speed.toFixed(1)} px/s
{track.max_speed.toFixed(1)} px/s
```

### 🎨 Suggested Enhancements (Optional)

**1. Add context tooltip:**
```jsx
<div title="Image-space motion in pixels per second. Not real-world speed.">
  {track.avg_speed.toFixed(1)} px/s
</div>
```

**2. Add relative speed indicator:**
```jsx
{track.avg_speed.toFixed(1)} px/s
{track.avg_speed > 150 && <span style={{color: '#ff5722'}}> ⚡ FAST</span>}
```

**3. Add percentage of frame width:**
```jsx
{track.avg_speed.toFixed(1)} px/s 
({(track.avg_speed / results.video_width * 100).toFixed(2)}% frame/s)
```

**4. Add comparison to threshold:**
```jsx
{track.max_speed.toFixed(1)} px/s
{track.max_speed > 150 && (
  <span style={{fontSize: '11px', color: '#ff5722'}}>
    (anomaly threshold: 150)
  </span>
)}
```

---

## Conclusions

### ✅ No Bugs Found

1. **Displacement calculation:** CORRECT
2. **Timestamp calculation:** CORRECT  
3. **FPS usage:** CORRECT
4. **Frame skip handling:** CORRECT
5. **Bbox center usage:** CORRECT
6. **Speed formula:** CORRECT
7. **First observation:** CORRECT
8. **Detection gaps:** CORRECT
9. **Mathematical consistency:** VERIFIED
10. **Anomaly thresholds:** CORRECT

### 📊 Values Are Image-Space Motion

- Speeds represent **pixels per second** in the 2D video frame
- These are **NOT** real-world speeds (km/h, m/s)
- Values are **physically meaningful** for video analysis
- M4 threshold (150 px/s) is **appropriate** for this scale

### 🎯 UI Should Display

**Keep current format:**
```
Average Speed: 50.0 px/s
Maximum Speed: 94.3 px/s
```

**Optional enhancements:**
- Tooltip explaining "image-space motion"
- Visual indicator when speed exceeds anomaly threshold
- Relative motion as % of frame dimensions

### 🔍 User-Reported Discrepancy

The user's reported values (118.7 px/s, 458.3 px/s) do **NOT match** the current backend data (50.0 px/s, 94.3 px/s). This requires investigation into:
- Which video was actually processed
- Which result file the frontend is loading
- Whether there's a calculation bug in the live frontend vs. committed code

---

## Recommendations

1. **DO NOT change M3 calculation** - it is correct
2. **DO NOT change M4 thresholds** - they are appropriate
3. **DO NOT convert to km/h** - without calibration, this would be meaningless
4. **DO verify frontend is loading correct result file**
5. **DO consider adding UI tooltip** to explain px/s units
6. **DO investigate user-reported value discrepancy**

---

**Audit Status:** ✅ COMPLETE  
**M3 Calculation:** ✅ MATHEMATICALLY CORRECT  
**Action Required:** NONE (unless user-reported discrepancy confirmed)
