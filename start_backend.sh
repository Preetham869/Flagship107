#!/bin/bash
# Flagship 107 - Backend Startup Script (Linux/Mac)
# Ensures processing module is available by setting PYTHONPATH

echo "Starting Flagship 107 Backend..."
echo ""

# Get the directory where this script is located (project root)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Add project root to PYTHONPATH so 'processing' module can be imported
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

echo "Project Root: ${PROJECT_ROOT}"
echo "PYTHONPATH: ${PYTHONPATH}"
echo ""

# Change to backend directory and start uvicorn
cd "${PROJECT_ROOT}/backend"
python -m uvicorn app.main:app --reload --host localhost --port 8000
