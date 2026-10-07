# 🚩 Flagship 107 — Quick Start

Get from a fresh clone to the working investigation dashboard.

## 1. Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- Git
- Ollama for local M9 explanations

## 2. Clone

```bash
git clone https://github.com/Preetham869/Flagship107.git
cd Flagship107
```

## 3. Backend + processing dependencies

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..

cd processing
pip install -r requirements.txt
cd ..
```

## 4. Local AI

```powershell
ollama pull qwen3:8b
ollama list
```

M1-M8 work without Ollama. M9 has fallback behaviour when local generation is unavailable.

## 5. Start backend

Preferred Windows command:

```powershell
.\backend\start_backend.bat
```

Or from the repository root:

```powershell
$env:PYTHONPATH = (Get-Location).Path
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend: **http://localhost:8000**  
API docs: **http://localhost:8000/docs**

## 6. Start frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend: **http://localhost:5173**

## 7. Investigation flow

**Upload → Process → Detection → Tracking → Behaviour → Anomaly → Event → Interaction → Context → AI Explanation**

1. Upload a video.
2. Start processing.
3. Inspect tracks and behaviour.
4. Select anomalies/events.
5. Inspect interactions and contextual evidence.
6. Generate M9 explanation when Ollama is available.

## 8. Validate the processing pipeline

```powershell
python run_e2e_validation.py data/sample.mp4
```

## 9. Regression checks

```powershell
python -m pytest processing/tests/ -v --tb=line -q
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## 10. Troubleshooting

**Backend import errors:** start from the repository root or use `backend/start_backend.bat`.

**Ollama unavailable:** M1-M8 can still run. Check with `ollama list` and confirm `qwen3:8b` exists.

**Frontend dependency errors:** run `npm install` inside `frontend`.

**YOLO weights missing:** Ultralytics downloads pretrained weights when first required and internet access is available.

## Read next

1. README.md
2. MILESTONE_TRACKER.md
3. AGENTS.md
4. Validation documents

> **Important:** mocked M9 tests are not evidence of successful live Qwen generation. The repository distinguishes live Qwen, validated M9 logic, and deterministic fallback.
