# Flagship 107 - Quick Start Guide

Get up and running in under 10 minutes.

## Prerequisites

âœ… Python 3.10+  
âœ… Node.js 18+  
âœ… Git  
âœ… Ollama (optional â€” for AI explanations)  

## Step 1: Clone Repository

```bash
git clone <repo-url>
cd Flagship107
```

## Step 2: Backend Setup

> **Important:** The backend imports `processing/` from the project root.  
> You must run it from the project root using the provided scripts.

```bash
# Install backend dependencies (from project root)
pip install -r backend/requirements.txt
pip install -r processing/requirements.txt

# Copy environment file
copy .env.example backend\.env      # Windows
# cp .env.example backend/.env     # Linux/Mac

# Start backend (Windows)
start_backend.bat

# OR start backend (Linux/Mac)
bash start_backend.sh

# OR start backend (any OS, from project root)
python backend/start_backend.py
```

Backend will start at: **http://localhost:8000**  
API docs at: **http://localhost:8000/docs**

> âš ï¸ Do NOT run `uvicorn app.main:app` directly from `backend/` â€” the
> `processing` module won't be on the Python path. Always use
> `start_backend.bat` / `start_backend.sh` / `backend/start_backend.py`.

## Step 3: Frontend Setup (New Terminal)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run the frontend
npm run dev
```

Frontend will start at: **http://localhost:5173**

## Step 4: Process a Video

Upload `data/sample.mp4` via the UI at http://localhost:5173, or call the API directly:

```bash
# Upload video
curl -X POST http://localhost:8000/api/v1/videos/upload \
  -F "file=@data/sample.mp4"

# Copy the job_id from the response, then start processing:
curl -X POST http://localhost:8000/api/v1/videos/<job_id>/process

# Check status (poll until "completed")
curl http://localhost:8000/api/v1/videos/<job_id>/status

# Get results (M1-M8 structured output)
curl http://localhost:8000/api/v1/videos/<job_id>/results

# Get AI explanation (M9 -- requires Ollama with qwen3:8b)
curl -X POST http://localhost:8000/api/v1/videos/<job_id>/explanation
```

## Step 5: AI Explanations (Optional - M9)

M9 uses Ollama + qwen3:8b. Install Ollama, then:

```bash
ollama pull qwen3:8b
```

If Ollama/qwen3:8b is unavailable or too slow on CPU, the system
**automatically falls back** to a deterministic M8-based narrative.
The fallback is always enabled - no manual configuration required.

## Quick Test Commands

### Backend Health Check
```bash
curl http://localhost:8000/health
```
Expected: `{"status": "healthy"}`

### Run Full Test Suite (202 tests)
```bash
# From project root
python -m pytest processing/tests/ -v --tb=line -q
```

### Run End-to-End Pipeline (no server needed)
```bash
# From project root
python run_e2e_validation.py data/sample.mp4
```

### Frontend Lint & Build
```bash
cd frontend
npm run lint
npm run build
```

## Project Structure

```
Flagship107/
â”œâ”€â”€ backend/              <- FastAPI server (port 8000)
â”‚   â”œâ”€â”€ app/              <- API routes, services, models
â”‚   â”œâ”€â”€ start_backend.py  <- Correct startup script
â”‚   â””â”€â”€ requirements.txt
â”œâ”€â”€ frontend/             <- React + Vite app (port 5173)
â”‚   â””â”€â”€ src/
â”œâ”€â”€ processing/           <- M1-M9 AI/ML pipeline
â”‚   â”œâ”€â”€ detection/        <- M1: YOLO object detection
â”‚   â”œâ”€â”€ tracking/         <- M2: Multi-object tracking
â”‚   â”œâ”€â”€ behavior/         <- M3: Behavior analysis
â”‚   â”œâ”€â”€ anomaly/          <- M4: Anomaly detection
â”‚   â”œâ”€â”€ events/           <- M5: Event correlation
â”‚   â”œâ”€â”€ interactions/     <- M6: Multi-entity interactions
â”‚   â”œâ”€â”€ context/          <- M8: Context synthesis
â”‚   â”œâ”€â”€ llm/              <- M9: LLM explanations (Ollama)
â”‚   â””â”€â”€ pipeline/         <- End-to-end orchestration
â”œâ”€â”€ data/
â”‚   â””â”€â”€ sample.mp4        <- Test video (33MB, 10s)
â”œâ”€â”€ start_backend.bat     <- Windows backend launcher
â”œâ”€â”€ start_backend.sh      <- Linux/Mac backend launcher
â””â”€â”€ .env.example          <- Environment template
```

## Common Issues

### Backend won't start
- Use `python backend/start_backend.py` from the project root (not `uvicorn` directly)
- Check Python 3.10+: `python --version`
- Install both requirements: `pip install -r backend/requirements.txt -r processing/requirements.txt`

### "No module named 'processing'"
- You are running uvicorn from `backend/` without setting PYTHONPATH
- Fix: Use `start_backend.bat` or `python backend/start_backend.py` from the project root

### Frontend won't start
- Check Node 18+: `node --version`
- Delete `node_modules` and run `npm install` again
- Check port 5173 is not in use

### M9 explanation times out
- qwen3:8b on CPU takes 60-120s per explanation -- this is expected
- The system will use the deterministic fallback automatically
- For faster results, run Ollama on a GPU machine

## Environment Variables

Key settings in `backend/.env` (copy from `.env.example`):

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
YOLO_MODEL=yolov8n.pt
MAX_VIDEO_SIZE_MB=100
UPLOAD_FOLDER=./uploads
OUTPUT_FOLDER=./outputs
```

---

**Status:** Milestones 1-9 Complete
**Pipeline:** M1->M2->M3->M4->M5->M6->M8->M9 fully operational
**Updated:** 2026-10-07

