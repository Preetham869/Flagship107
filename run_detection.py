#!/usr/bin/env python3
"""
Flagship 107 - Detection Pipeline Runner
Convenience script to run object detection on videos
"""
import sys
from pathlib import Path

# Add processing module to path
sys.path.insert(0, str(Path(__file__).parent))

from processing.detection.cli import main

if __name__ == "__main__":
    main()
