# M10 Phase 5 Implementation Plan

## Current State Analysis

### Existing Components (Phase 3 & 4)
- ✓ VideoPlayer.jsx - basic video playback
- ✓ EventTimeline.jsx - timeline with anomaly/event markers
- ✓ DashboardView.jsx - 2-column grid layout
- ✓ IntelligencePanel.jsx - 8 tabbed interface
- ✓ 8 intelligence tabs (Overview, Tracks, Behaviour, Anomalies, Events, Interactions, Scenes, AI)

### Backend Schema Confirmed
- All M1-M9 data available
- Anomalies: event_id, track_id, timestamp, type, severity, score, evidence, explanation
- Events: event_id, type, start/end timestamps, tracks, source_anomalies, severity, confidence, evidence, explanation
- Scenes: scene_id, timestamps, tracks, summary, observations, evidence_provenance
- Relationships: entity IDs, relationship_type, timestamps, distance, confidence

### Gaps to Fill (Phase 5)
1. No evidence/provenance panel component
2. No unified selection state across components
3. Video area too small, layout not professional
4. Timeline basic, needs clustering/improvements
5. Visual design still looks like React demo
6. No system status display
7. No loading/error states
8. Intelligence tabs need refinement

## Implementation Plan

### 1. Core Infrastructure (30 min)

**Create SelectionContext.jsx**
- Global selection state (selectedAnomaly, selectedEvent, selectedTrack, selectedScene)
- Selection actions (selectAnomaly, selectEvent, clearSelection)
- Propagate to all components

**Create EvidencePanel.jsx**
- Reusable evidence display component
- Show provenance clearly (Observed/Derived/AI)
- Timestamp linking
- Structured evidence display
- Source module labels (M3/M4/M5/M6/M8)

### 2. Enhanced Video Area (20 min)

**Redesign VideoPlayer.jsx**
- Professional dark panel design
- Add metadata display (resolution, FPS)
- Add selected item indicator overlay
- Improve progress bar styling
- Better controls layout

### 3. Enhanced Timeline (25 min)

**Redesign EventTimeline.jsx**
- Clustering for nearby markers
- Hover previews
- Selection state integration
- Severity visual differentiation
- Better empty states
- Professional dark design

### 4. Dashboard Layout Redesign (30 min)

**Redesign DashboardView.jsx**
- NEW LAYOUT:
  - TOP: Header with system status
  - MAIN LEFT: Large video + timeline
  - MAIN RIGHT: Intelligence tabs
  - BOTTOM: Evidence panel (conditional)
- Add SystemStatus component
- Professional dark theme
- Responsive breakpoints

### 5. Intelligence Tab Enhancements (40 min)

**Update AnomaliesTab.jsx**
- Click anomaly → select + seek + show evidence
- Better cards with all fields
- Improved filters

**Update EventsTab.jsx**
- Click event → select + seek + show evidence
- Show source anomalies
- Duration visualization

**Update TracksTab.jsx**
- Click track → select + highlight related items
- Show related anomalies/events

**Update ScenesTab.jsx**
- Click scene → select + seek + show evidence
- Better provenance display

**Update AIExplanationTab.jsx**
- Clear separation: Observed / Patterns / AI / Evidence
- Better unavailable state

### 6. Professional Visual Design (20 min)

**Create theme.css**
- Dark charcoal/navy palette
- Purple accent (#673AB7)
- Typography system
- Spacing system
- Shadow system
- Hover states

**Update all components**
- Apply consistent theme
- Remove demo-style colors
- Professional card styling
- Subtle animations

### 7. Loading/Error States (15 min)

**Create LoadingStates.jsx**
- Upload spinner
- Processing progress
- Loading skeleton
- Empty states
- Error states

### 8. Testing & Validation (15 min)

- npm run lint
- pytest backend tests
- Manual verification
- Documentation

## File Structure

```
frontend/src/
├── components/
│   ├── DashboardView.jsx          [MAJOR REDESIGN]
│   ├── VideoPlayer.jsx             [ENHANCE]
│   ├── EventTimeline.jsx           [ENHANCE]
│   ├── EvidencePanel.jsx           [NEW]
│   ├── SystemStatus.jsx            [NEW]
│   ├── LoadingStates.jsx           [NEW]
│   ├── intelligence/
│   │   ├── IntelligencePanel.jsx  [MINOR]
│   │   ├── AnomaliesTab.jsx       [ENHANCE]
│   │   ├── EventsTab.jsx          [ENHANCE]
│   │   ├── TracksTab.jsx          [ENHANCE]
│   │   ├── ScenesTab.jsx          [ENHANCE]
│   │   ├── AIExplanationTab.jsx   [ENHANCE]
│   │   └── ...                    [MINOR]
├── context/
│   └── SelectionContext.jsx       [NEW]
├── styles/
│   └── theme.css                  [NEW]
```

## Key Design Decisions

1. **Selection State**: React Context for global selection (avoid prop drilling)
2. **Evidence Panel**: Conditional bottom panel, not modal (better for analysis workflow)
3. **Layout**: Video-centric with side intelligence panel
4. **Theme**: CSS variables for consistency, no UI library
5. **Performance**: Only render evidence panel when item selected
6. **Responsive**: Min-width 1280px, graceful degradation below

## Implementation Order

1. SelectionContext + EvidencePanel (foundation)
2. DashboardView layout redesign
3. VideoPlayer + Timeline enhancements
4. Intelligence tab enhancements
5. Visual theme application
6. Loading/error states
7. Testing + docs

## Success Criteria

- ✓ Evidence panel shows provenance clearly
- ✓ Clicking any item seeks video and shows evidence
- ✓ Selection state synchronized across all components
- ✓ Professional dark video analytics aesthetic
- ✓ Timeline usable with many markers
- ✓ All existing functionality preserved
- ✓ npm run lint passes
- ✓ All 202 pytest tests pass
- ✓ No fake data, no new unnecessary dependencies

## Estimated Time: 3-4 hours
