#!/usr/bin/env python3
"""
Backend startup script
Ensures processing module is importable by adding project root to sys.path
"""
import sys
import os
from pathlib import Path

# Add project root to Python path (for 'processing' imports)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Change to backend directory (for 'app' imports to work properly)
backend_dir = Path(__file__).parent
os.chdir(backend_dir)

# Now run uvicorn
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8000,
        reload=True,
        reload_dirs=[str(backend_dir / "app")],
    )
