# M10 Phase 6 Implementation Plan

## Objectives

1. **Events UX**: Transform M5 events into understandable intelligence cards
2. **M6 Interactions**: Professional view handling both present/absent relationships
3. **M9 Integration**: Enable real Ollama/Qwen explanations via API
4. **Pipeline Visualization**: Show M1-M9 processing status
5. **Synchronization**: Ensure all timestamps seek video correctly

## Current State Analysis

### M5 Events (From actual data)
- 5 correlated events
- Types: high_speed_activity (3), abnormal_movement_sequence (2)
- Source anomalies: Lists like ["unusual_speed", "unusual_speed", ...] (repetitive)
- Need: Summarize as "Unusual Speed × 12, Sudden Speed Change × 2"

### M6 Interactions (From actual data)
- 0 relationships detected
- 9 entity pairs tracked
- Need: Honest analytical empty state explaining what was evaluated

### M8 Scenes (From actual data)
- 1 contextual scene available
- Contains track_summaries, movement_patterns, evidence_provenance
- Ready for M9 consumption

### M9 Status
- Module exists: processing/llm/
- Config: Ollama at localhost:11434, qwen3:8b model
- Not currently integrated into pipeline
- Need: API endpoint + frontend integration

## Implementation Order

### 1. Events Tab Redesign (30 min)
- Create EventCard component
- Summarize source anomaly types (count unique types)
- Add event type icons/labels
- Show duration visualization
- Expandable evidence section
- Click to seek + select

### 2. M6 Interactions Tab (20 min)
- Handle CASE A: Relationships exist (render cards)
- Handle CASE B: No relationships (analytical empty state)
- Show: pairs evaluated, analysis duration, threshold explanation
- Use actual m6_tracked_pairs from results

### 3. M9 Backend API (40 min)
- Create POST /api/v1/videos/{job_id}/explanation endpoint
- Load existing result
- Extract M8 scene
- Invoke M9 explanation service
- Return structured explanation
- Handle Ollama unavailable gracefully

### 4. M9 Frontend Integration (30 min)
- Redesign AIExplanationTab
- Add "Generate Explanation" button
- Show generation status/loading
- Display structured explanation with sections
- Separate Observed/Derived/AI visually
- Add evidence references with timestamp links

### 5. Intelligence Pipeline Status (15 min)
- Create PipelineStatus component
- Show M1-M9 module status
- Display in SystemStatus or separate strip
- Use actual processing state

### 6. Video Seek Synchronization (15 min)
- Verify all tabs can seek
- Test: anomaly, event, scene, track timestamps
- Ensure SelectionContext integration

### 7. Testing (30 min)
- Backend tests for M9 API
- Frontend lint
- Backend pytest
- Manual E2E with sample.mp4
- Verify Ollama generation

## File Structure

```
backend/app/api/v1/
├── videos.py                          [ADD M9 endpoint]

frontend/src/components/
├── PipelineStatus.jsx                 [NEW]
├── intelligence/
│   ├── EventsTab.jsx                  [REDESIGN]
│   ├── InteractionsTab.jsx            [ENHANCE]
│   ├── AIExplanationTab.jsx           [REDESIGN]
│   └── EventCard.jsx                  [NEW]

processing/tests/
├── test_m9_api.py                     [NEW]

backend/tests/
├── test_api.py                        [ADD M9 tests]
```

## Data Flow: M9 Integration

```
User clicks "Generate Explanation"
           ↓
POST /api/v1/videos/{job_id}/explanation
           ↓
Load result from outputs/{job_id}_result.json
           ↓
Extract M8 scene from all_scenes[0]
           ↓
Convert to ContextualScene object
           ↓
Call ExplanationGenerator.explain_scene()
           ↓
Ollama generates explanation OR fallback
           ↓
Return SceneExplanation JSON
           ↓
Frontend displays structured explanation
```

## Safety Checks

- ✓ No M1-M8 processing logic modifications
- ✓ No data invention
- ✓ Evidence-first architecture preserved
- ✓ Ollama unavailable handled gracefully
- ✓ M9 only receives M8 structured data
- ✓ No raw video analysis in M9

## Success Criteria

1. Events tab shows readable intelligence cards
2. Source anomalies summarized (not repeated lists)
3. M6 shows honest analytical empty state when no relationships
4. M9 API endpoint functional
5. Ollama/qwen3:8b generates explanation
6. AI explanation cites M1-M8 evidence
7. Pipeline status shows M1-M9 modules
8. All timestamps seek video
9. 202+ tests passing
10. Lint clean

## Time Estimate: 3-4 hours
