# Milestone 5 Validation: Event Understanding and Temporal Correlation

**Date:** 2026-10-06  
**Status:** ✅ COMPLETED

## Overview

Milestone 5 implements an event correlation engine that groups M4 anomaly observations into meaningful higher-level events. This addresses the alert spam problem by consolidating repeated observations and correlating related anomalies into coherent events with temporal context.

## Implementation Summary

### Components Created

1. **`processing/events/correlator.py`** (~700 lines)
   - `EventCorrelator` class with temporal correlation logic
   - `EventConfig` for configurable parameters
   - `EventType` and `EventSeverity` enums
   - `CorrelatedEvent` dataclass with complete schema
   - 4 event detection methods
   - Severity and confidence calculation

2. **`processing/events/demo.py`** (~600 lines)
   - Synthetic single-track scenario generator
   - Synthetic multi-track scenario generator
   - Comparison of M4 raw anomalies vs M5 correlated events
   - JSON export for inspection

3. **`processing/tests/test_event_correlator.py`** (~900 lines)
   - 23 comprehensive tests
   - Coverage for all event types
   - Temporal grouping tests
   - Edge cases and multi-track scenarios

## Test Results

```
Platform: Windows (win32), Python 3.14.2, pytest 9.1.1
Total Tests: 102 (M1: 12, M2: 13, M3: 22, M4: 32, M5: 23)
Result: ✅ 102 passed in 3.54s
```

### M5 Test Coverage

#### Core Functionality (2 tests)
- ✅ Empty anomalies list handling
- ✅ Single anomaly (no correlation criteria met)

#### Temporal Grouping (2 tests)
- ✅ Anomalies within temporal window are grouped
- ✅ Anomalies outside temporal window are separated

#### Restricted Area Intrusion (3 tests)
- ✅ Single zone entry creates intrusion event
- ✅ Zone entry with other anomalies creates enhanced event
- ✅ Repeated zone entries are deduplicated (20 → 1 event)

#### Loitering Events (2 tests)
- ✅ Multiple loitering observations consolidated
- ✅ Short duration doesn't create event

#### High-Speed Activity (3 tests)
- ✅ Multiple speed anomalies create high-speed event
- ✅ Insufficient count doesn't create event
- ✅ Speed + speed_change anomalies combined

#### Abnormal Movement Sequence (2 tests)
- ✅ Multiple movement types create sequence event
- ✅ Single movement type doesn't create sequence

#### Multi-Track Separation (1 test)
- ✅ Different tracks create separate events

#### Severity Calculation (3 tests)
- ✅ All HIGH anomalies → HIGH event
- ✅ Majority MEDIUM → MEDIUM event
- ✅ All LOW → LOW event

#### Confidence Calculation (1 test)
- ✅ Confidence calculated correctly (0-1 range)

#### Event Serialization (1 test)
- ✅ Event to_dict() produces complete structure

#### Complex Scenarios (3 tests)
- ✅ Single track with multiple event types
- ✅ Overlapping temporal windows
- ✅ Statistics retrieval

## Demo Results

### Single Track Scenario

**Track #7 Complex Sequence:**
1. Enters restricted zone (10.5s)
2. Repeated zone alerts (11-25s)
3. Unusual speed inside zone (12-18s)
4. Sudden direction change (16s)
5. Sudden acceleration after exit (27s)
6. Loitering with repeated alerts (30-45s)

**M4 Raw Anomalies:** 75 alerts
- restricted_zone_entry: 16
- unusual_speed: 7
- sudden_direction_change: 1
- sudden_speed_change: 1
- loitering: 50

**M5 Correlated Events:** 4 events
1. **RESTRICTED_AREA_INTRUSION**
   - Duration: 34.2s
   - Severity: HIGH
   - Confidence: 0.662
   - Source anomalies: 75 (all types within temporal window)
   - Explanation: Entered zone, remained 34.2s with unusual speed and direction change

2. **LOITERING_EVENT**
   - Duration: 14.7s
   - Severity: LOW
   - Confidence: 0.556
   - Source anomalies: 50
   - Explanation: Consolidated 50 repeated loitering observations

3. **HIGH_SPEED_ACTIVITY**
   - Duration: 15.0s
   - Severity: HIGH
   - Confidence: 0.815
   - Source anomalies: 8
   - Explanation: Sustained high-speed with max 180.0 px/s

4. **ABNORMAL_MOVEMENT_SEQUENCE**
   - Duration: 15.0s
   - Severity: HIGH
   - Confidence: 0.752
   - Source anomalies: 9
   - Explanation: Multiple movement types in sequence

**Reduction Rate:** 94.7% (75 → 4 alerts)

### Multi-Track Scenario

**Three Simultaneous Tracks:**
- Track #3: High-speed activity (5-12s)
- Track #5: Loitering (20-35s)
- Track #7: Complex intrusion (10-45s)

**M4 Raw Anomalies:** 115 alerts
**M5 Correlated Events:** 6 events
- Track #3: 1 HIGH_SPEED_ACTIVITY
- Track #5: 1 LOITERING_EVENT
- Track #7: 4 events (intrusion, loitering, speed, movement)

**Reduction Rate:** 94.8% (115 → 6 alerts)

## Success Criteria Verification

### ✅ Functional Requirements

1. **Temporal Correlation**
   - Groups anomalies within configurable window (default 30s)
   - Separates anomalies outside window into different events
   - Handles overlapping windows correctly

2. **Event Lifecycle**
   - ✅ start_timestamp, end_timestamp, duration_seconds
   - ✅ participating_track_ids (list, ready for multi-entity)
   - ✅ source_anomaly_ids (constituent anomalies)
   - ✅ event_type (from taxonomy)
   - ✅ severity (derived from anomalies)
   - ✅ confidence (deterministic calculation)
   - ✅ evidence (structured dict)
   - ✅ explanation (human-readable)

3. **Event Taxonomy**
   - ✅ RESTRICTED_AREA_INTRUSION: Zone entry + related anomalies
   - ✅ LOITERING_EVENT: Consolidated stationary observations
   - ✅ HIGH_SPEED_ACTIVITY: Sustained unusual speed
   - ✅ ABNORMAL_MOVEMENT_SEQUENCE: Multiple movement types

4. **Deduplication**
   - ✅ 16 zone entries → 1 intrusion event
   - ✅ 50 loitering alerts → 1 loitering event
   - ✅ 7 speed alerts → 1 high-speed event
   - ✅ Overall: ~95% alert reduction

5. **Event Severity**
   - Deterministic logic:
     - Any HIGH anomaly → HIGH event
     - Majority MEDIUM → MEDIUM event
     - Otherwise → LOW event
   - ✅ Calculated from constituent anomalies
   - ✅ Explanation documents why

6. **Event Confidence**
   - Formula: `min(1.0, avg_anomaly_score * (1 + log(factor)/10))`
   - Factor: number of unique types or observations
   - ✅ Deterministic (no randomness)
   - ✅ Range: 0.0 - 1.0
   - ✅ Documented calculation

7. **Multi-Anomaly Correlation**
   - ✅ Zone entry + speed + direction change → enhanced intrusion
   - ✅ Speed + speed_change → high-speed activity
   - ✅ Multiple movement types → movement sequence

8. **Multi-Entity Foundation**
   - ✅ participating_track_ids is a list
   - ✅ Tracks properly separated (no cross-contamination)
   - ✅ Architecture supports future multi-track events

9. **Explainability (WHO/WHEN/WHAT/HOW LONG/WHY/EVIDENCE)**
   - ✅ WHO: participating_track_ids
   - ✅ WHEN: start_timestamp, end_timestamp
   - ✅ WHAT: event_type
   - ✅ HOW LONG: duration_seconds
   - ✅ WHY: explanation field
   - ✅ WHAT EVIDENCE: evidence dict + source_anomaly_ids

10. **Configurability**
    - ✅ temporal_window (default 30.0s)
    - ✅ min_loitering_duration (default 5.0s)
    - ✅ min_high_speed_count (default 3)
    - ✅ min_movement_sequence (default 2)
    - ✅ max_repeated_anomalies (default 5)

### ✅ Technical Requirements

1. **Module Separation**
   - M3: Behavior measurement
   - M4: Anomaly detection
   - M5: Event correlation ← New, separate module
   - No duplication of M3/M4 logic

2. **Testing**
   - 23 comprehensive tests
   - All event types covered
   - Temporal grouping validated
   - Deduplication verified
   - Edge cases handled
   - Multi-track separation confirmed

3. **Demo**
   - ✅ Single track: 75 → 4 (94.7% reduction)
   - ✅ Multi track: 115 → 6 (94.8% reduction)
   - ✅ Clear before/after comparison
   - ✅ JSON export for inspection

### ✅ Integration Requirements

1. **M1-M4 Still Pass**
   - All 79 previous tests still pass
   - No breaking changes
   - Clean module boundaries

2. **Consumes M4 Output**
   - Takes list of M4 anomaly dicts
   - Uses all M4 fields correctly
   - No modification of M4 data

## Architecture Validation

### Data Flow
```
M1: YOLO Detection
    ↓
M2: Multi-Object Tracking (persistent IDs)
    ↓
M3: Behavior Analysis (speed, direction, states)
    ↓
M4: Anomaly Detection (rule-based observations)
    ↓
M5: Event Correlation (temporal grouping, deduplication)
    ↓
Meaningful high-level events with reduced alert volume
```

### Module Structure
```
processing/events/
├── __init__.py          # Exports
├── correlator.py        # EventCorrelator, event detection logic
└── demo.py              # Synthetic demos
```

### Key Design Decisions

1. **Temporal Windows** - Configurable time-based grouping (default 30s)
2. **Event Taxonomy** - 4 focused types (not dozens of superficial ones)
3. **Deduplication** - Consolidate repeated same-type observations
4. **Multi-Anomaly** - Correlate different anomaly types into single event
5. **Severity Derivation** - Calculate from constituent anomalies deterministically
6. **Confidence Formula** - `avg_score * (1 + log(factor)/10)` capped at 1.0
7. **Multi-Entity Ready** - participating_track_ids is list, not single value

## Event Schema

```python
{
    "event_id": str,                     # UUID
    "event_type": str,                    # EventType enum value
    "start_timestamp": float,             # Seconds
    "end_timestamp": float,               # Seconds
    "duration_seconds": float,            # end - start
    "participating_track_ids": List[str], # Which tracks involved
    "source_anomaly_ids": List[str],      # M4 anomaly event_ids
    "source_anomaly_types": List[str],    # Types of anomalies
    "severity": str,                      # LOW/MEDIUM/HIGH
    "confidence": float,                  # 0.0 - 1.0
    "evidence": Dict,                     # Type-specific evidence
    "explanation": str                    # Human-readable
}
```

## Examples

### Example 1: Restricted Area Intrusion

```json
{
  "event_id": "16ce9377-be7c-4a32-bbbf-f8cb46d5895b",
  "event_type": "restricted_area_intrusion",
  "start_timestamp": 10.5,
  "end_timestamp": 44.7,
  "duration_seconds": 34.2,
  "participating_track_ids": ["7"],
  "source_anomaly_ids": ["anom_1000", "anom_1001", ..., "anom_1074"],
  "source_anomaly_types": [
    "restricted_zone_entry",
    "unusual_speed",
    "sudden_direction_change",
    "sudden_speed_change",
    "loitering"
  ],
  "severity": "high",
  "confidence": 0.662,
  "evidence": {
    "zone_name": "Secure Server Room",
    "zone_id": "zone_001",
    "anomaly_count": 75,
    "zone_entry_count": 16,
    "other_anomaly_types": [
      "unusual_speed",
      "sudden_direction_change",
      "sudden_speed_change",
      "loitering"
    ]
  },
  "explanation": "Track #7 entered restricted zone 'Secure Server Room' and remained inside for 34.2 seconds with unusual speed, sudden direction change. Consolidated 16 zone entry observation(s) and 59 related anomaly/anomalies."
}
```

### Example 2: Loitering Event

```json
{
  "event_id": "71927ab7-0389-47b3-b37f-2513a06e3326",
  "event_type": "loitering_event",
  "start_timestamp": 30.0,
  "end_timestamp": 44.7,
  "duration_seconds": 14.7,
  "participating_track_ids": ["7"],
  "source_anomaly_ids": ["anom_1025", ..., "anom_1074"],
  "source_anomaly_types": ["loitering"],
  "severity": "low",
  "confidence": 0.556,
  "evidence": {
    "loitering_duration": 14.7,
    "observation_count": 50,
    "position": [850, 200],
    "deduplication_note": "Consolidated 50 repeated loitering observations"
  },
  "explanation": "Track #7 remained stationary for 14.7 seconds at position [850, 200]. This event consolidates 50 repeated loitering observations to reduce alert spam."
}
```

## Known Limitations (Intentional for MVP)

1. **Single-Entity Events Only** - Multi-person interaction recognition deferred
2. **No LLM Reasoning** - Explanations are template-based (Ollama integration is M6)
3. **No Pose/Activity Recognition** - Deep learning models deferred
4. **No FastAPI Endpoints** - Backend integration deferred
5. **No React Dashboard** - Frontend visualization deferred
6. **No Database** - JSON output only for MVP
7. **No WebSocket** - Real-time updates deferred
8. **Simple Correlation** - Advanced event graph/sequences deferred

## Files Created/Modified

### Created
- `processing/events/__init__.py`
- `processing/events/correlator.py` (~700 lines)
- `processing/events/demo.py` (~600 lines)
- `processing/tests/test_event_correlator.py` (~900 lines, 23 tests)
- `MILESTONE5_VALIDATION.md` (this document)

### Modified
- `MILESTONE_TRACKER.md` (marked M5 complete, updated status)

## Run Commands

### Run All Tests
```bash
cd c:\Users\preet\OneDrive\Projects\Flagship107
pytest processing/tests/ -v
```

### Run M5 Tests Only
```bash
pytest processing/tests/test_event_correlator.py -v
```

### Run Demo
```bash
python -m processing.events.demo
```

## Comparison: M4 vs M5

| Aspect | M4 (Raw Anomalies) | M5 (Correlated Events) |
|--------|-------------------|------------------------|
| **Output** | Individual observations | Grouped meaningful events |
| **Volume** | 115 alerts | 6 events (94.8% reduction) |
| **Context** | Single timestamp | Time range (start/end/duration) |
| **Explanation** | Why this observation | What happened overall |
| **Spam** | Repeated alerts | Deduplicated |
| **Correlation** | Independent | Related anomalies grouped |
| **Multi-type** | Single anomaly type | Multiple types combined |

## Conclusion

✅ **Milestone 5 is COMPLETE**

- 4 event types implemented with clear taxonomy
- Temporal correlation with configurable windows
- Deduplication reduces alert volume by ~95%
- Multi-anomaly correlation working
- Event severity and confidence calculated deterministically
- Complete explainable schema (WHO/WHEN/WHAT/HOW LONG/WHY/EVIDENCE)
- 23 comprehensive tests (100% pass rate)
- Demo validates single and multi-track scenarios
- M1-M4 tests still pass (no regressions)

**Major Achievement:** Transforms hundreds of raw anomaly observations into a small number of actionable, contextualized events with clear explanations and supporting evidence.

**Ready to proceed to M6: AI Explanations (Ollama/Qwen) when requested.**

---

**Validated by:** AI Agent (Kiro)  
**Date:** 2026-10-06
