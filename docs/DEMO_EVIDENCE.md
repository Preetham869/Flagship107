# 📸 Flagship 107 — Demo Evidence Guide

Capture **5–7 real screenshots** from the running application. Do not fabricate data or hide errors.

## 01 — Main Investigation Dashboard

Show the video player, timeline and investigation panel together.

Filename: `01-dashboard.png`

## 02 — Detection + Tracking

Show real YOLO bounding boxes, class labels and persistent track IDs.

Filename: `02-detection-tracking.png`

## 03 — Anomaly / Event Investigation

Select a real anomaly or event. Show its type, timestamp, entity/track and supporting evidence.

Filename: `03-anomaly-event.png`

## 04 — Multi-Entity Interaction

If a real interaction exists, show the participating tracks and relationship evidence. If the sample produces zero relationships, capture that honest result instead. Do not fabricate an interaction.

Filename: `04-interactions.png`

## 05 — M8 Context / Evidence

Show a contextual scene, entity summary, pattern information and provenance/evidence.

Filename: `05-context-evidence.png`

## 06 — M9 AI Explanation

Only call this a Qwen success screenshot if a real request completes with Qwen3:8b. Show the model, explanation, evidence/coverage and uncertainty. If live Qwen is unavailable, capture the actual fallback state and label it honestly.

Filename: `06-ai-explanation.png`

## 07 — Final Output

Show an annotated video result or structured event/result output.

Filename: `07-results.png`

## Recommended repository layout

```text
docs/
└── screenshots/
    ├── 01-dashboard.png
    ├── 02-detection-tracking.png
    ├── 03-anomaly-event.png
    ├── 04-interactions.png
    ├── 05-context-evidence.png
    ├── 06-ai-explanation.png
    └── 07-results.png
```

## Evidence rules

Use only screenshots from the actual current application. Do not present mocked M9 output as live Qwen output. Do not add unsupported claims about intent, threat, emotion, maliciousness or motivation.
