# Quick Start Guide - Flagship 107

## Prerequisites
- Python 3.10+ installed
- Node.js 18+ installed
- Sample video file (optional: `data/sample.mp4`)

---

## Terminal 1: Start Backend

### Option A: Use Startup Script (Recommended)

**Windows:**
```bash
# Navigate to project root
cd C:\Users\preet\OneDrive\Projects\Flagship107

# Install backend dependencies (first time only)
pip install fastapi uvicorn python-multipart pydantic pydantic-settings

# Run startup script
start_backend.bat
```

**Linux/Mac:**
```bash
# Navigate to project root
cd /path/to/Flagship107

# Install backend dependencies (first time only)
pip install fastapi uvicorn python-multipart pydantic pydantic-settings

# Make script executable (first time only)
chmod +x start_backend.sh

# Run startup script
./start_backend.sh
```

### Option B: Manual with PYTHONPATH

**Windows PowerShell:**
```powershell
# Navigate to project root
cd C:\Users\preet\OneDrive\Projects\Flagship107

# Set PYTHONPATH to include project root
$env:PYTHONPATH = "C:\Users\preet\OneDrive\Projects\Flagship107"

# Start FastAPI server from backend directory
cd backend
python -m uvicorn app.main:app --reload --host localhost --port 8000
```

**Linux/Mac Bash:**
```bash
# Navigate to project root
cd /path/to/Flagship107

# Set PYTHONPATH and start server
export PYTHONPATH="$(pwd)"
cd backend
python -m uvicorn app.main:app --reload --host localhost --port 8000
```

**Backend will start on:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**You should see:**
```
INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## Terminal 2: Start Frontend

```bash
# Navigate to project root
cd C:\Users\preet\OneDrive\Projects\Flagship107

# Navigate to frontend
cd frontend

# Install dependencies (first time only)
npm install

# Start Vite dev server
npm run dev
```

**Frontend will start on:**
- App: http://localhost:5173

**You should see:**
```
  VITE v5.0.8  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

---

## Open Application

1. Open browser to: **http://localhost:5173**
2. Click "Check Connection" - should show "healthy"
3. Click "Choose File" and select a video
4. Click "Upload Video"
5. Click "Start Processing"
6. Watch progress bar
7. View M1-M9 results!

---

## Test with Sample Video

```bash
# Use the existing sample video
# Located at: C:\Users\preet\OneDrive\Projects\Flagship107\data\sample.mp4
# (31.62MB, 2160x3840, 10.01s, 240 frames)
```

Upload this through the UI and process it!

---

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.10+)
- Install dependencies: `pip install -r requirements.txt`
- Check port 8000 not in use: `netstat -ano | findstr :8000`

### Frontend won't start
- Check Node version: `node --version` (need 18+)
- Delete node_modules and reinstall: `rm -rf node_modules; npm install`
- Check port 5173 not in use

### Upload fails
- Check backend is running (http://localhost:8000/health)
- Check CORS settings in `backend/app/core/config.py`
- Check file size < 100MB

### Processing fails
- Check M1-M9 dependencies installed (YOLO, OpenCV)
- Check sample.mp4 exists in data/ folder
- Check Ollama running (optional for M9)

---

## Stop Servers

**Backend:** Press `CTRL+C` in Terminal 1  
**Frontend:** Press `CTRL+C` in Terminal 2

---

## API Documentation

While backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## File Locations

**Uploaded videos:** `uploads/`  
**Processing results:** `outputs/`  
**Logs:** Console output

---

**Ready to process videos! 🚀**
