# 🚩 Flagship 107

> **Offline Video Intelligence for Evidence-Grounded Behaviour Understanding**

Flagship 107 turns video into structured, traceable behavioural evidence through a staged offline pipeline.

## ⭐ Core Pipeline

**Video → M1 Detection → M2 Tracking → M3 Behaviour → M4 Anomalies → M5 Events → M6 Interactions → M7 Calibration → M8 Context → M9 Local AI Explanation → M10 Investigation Dashboard**

### The key architectural idea

**The LLM is a narrator, not the detector.** M1-M8 perform the measurable computer-vision and reasoning work. M9 receives structured evidence and turns it into an investigator-friendly explanation. It must not invent track IDs, timestamps, measurements, events, intent, emotion, threat, guilt, or motivation.

## 🔥 What the system does

| Layer | Capability |
|---|---|
| M1 | YOLO object detection with CPU/GPU fallback |
| M2 | Persistent tracking with ByteTrack / BoT-SORT |
| M3 | Speed, direction, displacement and temporal behaviour |
| M4 | Explainable rule-based anomaly detection |
| M5 | Temporal event correlation and deduplication |
| M6 | Multi-entity spatial/temporal interaction reasoning |
| M7 | Temporal calibration and noise reduction |
| M8 | Contextual scenes, patterns and evidence provenance |
| M9 | Ollama + Qwen3:8b explanation with deterministic fallback |
| M10 | Investigation dashboard and evidence-driven workflow |

## 🧠 Evidence-first architecture

```text
Raw Video
   ↓
M1-M7: measure + reason
   ↓
M8: structured contextual evidence
   ↓
M9: local LLM narration
   ↓
M10: investigator-facing results
```

M9 does **not** inspect raw video independently. It receives structured M8 evidence. This keeps detection and measurement deterministic and makes AI output traceable.

## 🔍 Evidence and provenance

The pipeline preserves, where available:

- track IDs
- frame IDs and timestamps
- object classes
- speed and direction measurements
- durations
- anomaly types and severity
- event IDs and source anomalies
- relationship types
- contextual scene and pattern evidence

M9 validates generated output against available evidence and can fall back to deterministic evidence-based explanations.

## 📊 Current milestone status

| Milestone | Status |
|---|:---:|
| M1 Detection | ✅ |
| M2 Tracking | ✅ |
| M3 Behaviour | ✅ |
| M4 Anomaly Detection | ✅ |
| M5 Event Correlation | ✅ |
| M6 Interaction Reasoning | ✅ |
| M7 Calibration / Hardening | ✅ |
| M8 Context Synthesis | ✅ |
| M9 Local AI Explanation | 🟡 |
| M10 Investigation Dashboard | ✅ |

**M9 note:** automated M9 tests and fallback are validated. Real Qwen generation is environment-dependent and must not be confused with mocked tests or fallback execution.

## 🖥️ Investigation workflow

The dashboard is designed around:

**event/track/scene → timestamp → entity → evidence → explanation**

It includes video, timeline navigation, tracks, anomalies, events, interactions, scenes, evidence context and AI explanation views.

## ⚙️ Technology

**Frontend:** React 18, Vite, Axios, ESLint  
**Backend:** Python, FastAPI, Uvicorn, Pydantic  
**Computer Vision:** OpenCV, Ultralytics YOLO, ByteTrack / BoT-SORT  
**Local AI:** Ollama, Qwen3:8b  
**Testing:** Pytest, Pytest-asyncio

## 🚀 Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- Git
- Ollama for local M9 generation
- NVIDIA GPU is optional; CPU fallback is supported

### Clone

```bash
git clone https://github.com/Preetham869/Flagship107.git
cd Flagship107
```

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
```

### Processing dependencies

```powershell
cd processing
pip install -r requirements.txt
cd ..
```

### Ollama / Qwen3:8b

```powershell
ollama pull qwen3:8b
ollama list
```

M1-M8 do not require Ollama.

### Start backend

Preferred Windows startup:

```powershell
.\backend\start_backend.bat
```

If starting Uvicorn directly from the repository root:

```powershell
$env:PYTHONPATH = (Get-Location).Path
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**.

## 🎬 Run the application

1. Open the frontend.
2. Upload a video.
3. Start processing.
4. Inspect detections and persistent tracks.
5. Inspect behaviour measurements.
6. Select anomalies and events.
7. Inspect interactions when present.
8. Inspect contextual scenes and evidence.
9. Generate an M9 explanation when Ollama is available.

## 🧪 Validation

Processing regression suite:

```bash
python -m pytest processing/tests/ -v --tb=line -q
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

Real-video validation tooling processes the supplied sample video and produces structured JSON/report/video artifacts.

## 🤖 M9 local AI

Qwen3:8b receives structured contextual evidence rather than raw video. The explanation layer applies constraints against unsupported track IDs, timestamps, measurements, causal claims and prohibited intent/emotion/threat language.

If Ollama is unavailable, too slow, or a response fails validation, deterministic fallback output can preserve the evidence-driven workflow.

## ⚠️ Limitations

- Movement speed is measured in **pixels/second**, not calibrated real-world speed.
- Accuracy depends on video quality, camera angle and model performance.
- Thresholds require calibration for different camera environments.
- Interaction detection requires sufficient temporal observations.
- Local Qwen generation depends on Ollama/model performance.
- The system does not claim to infer human intent, emotion, guilt, maliciousness or motivation.

## 📚 External resources

The project uses open-source technologies and pretrained resources including Ultralytics YOLO, OpenCV, FastAPI, React, Vite, Ollama, Qwen3:8b and tracking components available through the YOLO stack. Their respective licenses and terms apply.

## 📁 Repository guide

- **README.md**: project architecture, scope and setup
- **QUICKSTART.md**: shortest run instructions
- **MILESTONE_TRACKER.md**: implementation and validation state
- **AGENTS.md**: development/architecture guidance
- **docs/DEMO_EVIDENCE.md**: recommended visual evidence for reviewers

## 🏁 Project goal

A reproducible, offline-first, evidence-grounded video intelligence prototype that prioritizes **working core pipeline → reproducibility → evidence → explainability → honest limitations**.
