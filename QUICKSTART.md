# Flagship 107 - Quick Start Guide

Get up and running in 5 minutes.

## Prerequisites

✅ Python 3.10+  
✅ Node.js 18+  
✅ Git  

## Step 1: Clone & Setup (If not already done)

```bash
cd c:\Users\preet\OneDrive\Projects\Flagship107
```

Project structure is already created. You're ready to go!

## Step 2: Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy ..\.env.example .env

# Run the backend
uvicorn app.main:app --reload
```

Backend will start at: **http://localhost:8000**  
API docs at: **http://localhost:8000/docs**

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

## Step 4: Verify Integration

1. Open browser: http://localhost:5173
2. Click "Check Connection" button
3. Status should change to **healthy** ✅

## Quick Test Commands

### Backend Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### Backend Root
```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "name": "Flagship 107 API",
  "version": "0.1.0",
  "status": "operational"
}
```

### Run Backend Tests
```bash
cd backend
pytest
```

Expected: 2 tests pass ✅

## Project Structure Overview

```
Flagship107/
├── backend/          ← FastAPI server (port 8000)
├── frontend/         ← React app (port 5173)
├── processing/       ← AI/ML engines (called by backend)
├── data/samples/     ← Place test videos here
├── README.md         ← Detailed documentation
├── AGENTS.md         ← Architecture & coding guidelines
└── MILESTONE_TRACKER.md  ← Development progress
```

## Next Steps

### For Development

**Milestone 1: Hello Detection**
- Implement video upload API
- Add YOLO object detection
- Display results on frontend

See `MILESTONE_TRACKER.md` for detailed tasks.

### For Understanding

Read in this order:
1. `README.md` - Project overview
2. `AGENTS.md` - Architecture details
3. `MILESTONE_TRACKER.md` - Development plan

## Common Issues

### Backend won't start
- Check if Python 3.10+ is installed: `python --version`
- Check if venv is activated: prompt should show `(venv)`
- Try: `pip install --upgrade pip` then reinstall requirements

### Frontend won't start
- Check if Node 18+ is installed: `node --version`
- Delete `node_modules` and `package-lock.json`, run `npm install` again
- Check port 5173 is not in use

### Connection fails
- Ensure backend is running on port 8000
- Ensure frontend is running on port 5173
- Check firewall/antivirus not blocking ports

## Useful Commands

### Backend
```bash
# Format code
black app/

# Lint code
flake8 app/

# Run with specific port
uvicorn app.main:app --reload --port 8001
```

### Frontend
```bash
# Lint code
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Key settings in `.env`:

```env
# Backend
BACKEND_PORT=8000

# Processing
MAX_VIDEO_SIZE_MB=100
YOLO_MODEL=yolov8n.pt

# AI
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:latest
```

## Support

- Check `README.md` for detailed setup
- Check `AGENTS.md` for architecture
- Check `MILESTONE_TRACKER.md` for development status

---

**Status:** Milestone 0 Complete ✅  
**Next:** Milestone 1 - Hello Detection  
**Updated:** 2026-10-06
