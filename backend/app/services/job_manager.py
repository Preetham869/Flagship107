"""
Job management service for video processing
Handles job state, file storage, and processing coordination
"""
import asyncio
import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import cv2

from app.models.job import JobStatus, ProcessingProgress
from app.core.config import settings

logger = logging.getLogger(__name__)


class Job:
    """Represents a video processing job"""
    
    def __init__(
        self,
        job_id: str,
        filename: str,
        file_path: Path,
        file_size: int,
    ):
        self.job_id = job_id
        self.filename = filename
        self.file_path = file_path
        self.file_size = file_size
        self.status = JobStatus.QUEUED
        self.progress = ProcessingProgress()
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        
        # Video metadata
        self.video_duration: Optional[float] = None
        self.video_width: Optional[int] = None
        self.video_height: Optional[int] = None
        self.video_fps: Optional[float] = None
        
        # Extract video metadata
        self._extract_video_metadata()
    
    def _extract_video_metadata(self):
        """Extract basic video metadata using OpenCV"""
        try:
            cap = cv2.VideoCapture(str(self.file_path))
            if cap.isOpened():
                self.video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                self.video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.video_fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if self.video_fps > 0:
                    self.video_duration = total_frames / self.video_fps
                cap.release()
        except Exception as e:
            logger.warning(f"Failed to extract video metadata: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            "job_id": self.job_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "status": self.status.value,
            "progress": self.progress.percent_complete,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "video_duration": self.video_duration,
            "video_width": self.video_width,
            "video_height": self.video_height,
            "video_fps": self.video_fps,
        }


class JobManager:
    """
    Manages video processing jobs
    Thread-safe job storage and processing coordination
    """
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self._lock = asyncio.Lock()
        
        # Ensure directories exist
        self.upload_dir = Path(settings.UPLOAD_FOLDER)
        self.output_dir = Path(settings.OUTPUT_FOLDER)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"JobManager initialized: uploads={self.upload_dir}, outputs={self.output_dir}")
    
    async def create_job(self, filename: str, file_content: bytes) -> Job:
        """
        Create a new job and save uploaded video
        
        Args:
            filename: Original filename
            file_content: Video file bytes
            
        Returns:
            Created Job object
        """
        async with self._lock:
            # Generate unique job ID
            job_id = str(uuid.uuid4())
            
            # Save file with job ID prefix
            file_ext = Path(filename).suffix or ".mp4"
            safe_filename = f"{job_id}{file_ext}"
            file_path = self.upload_dir / safe_filename
            
            # Write file
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # Create job
            job = Job(
                job_id=job_id,
                filename=filename,
                file_path=file_path,
                file_size=len(file_content),
            )
            
            self.jobs[job_id] = job
            logger.info(f"Created job {job_id} for {filename} ({len(file_content)} bytes)")
            
            return job
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    async def update_status(self, job_id: str, status: JobStatus, error: Optional[str] = None):
        """Update job status"""
        async with self._lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                job.status = status
                
                if status == JobStatus.PROCESSING and not job.started_at:
                    job.started_at = datetime.now()
                elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
                    job.completed_at = datetime.now()
                
                if error:
                    job.error = error
                
                logger.info(f"Job {job_id} status: {status.value}" + (f" - {error}" if error else ""))
    
    async def update_progress(self, job_id: str, current_frame: int, total_frames: int, stage: str = "processing"):
        """Update job processing progress"""
        async with self._lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                job.progress.current_frame = current_frame
                job.progress.total_frames = total_frames
                job.progress.stage = stage
                
                if total_frames > 0:
                    job.progress.percent_complete = (current_frame / total_frames) * 100
    
    async def save_result(self, job_id: str, result: Dict[str, Any]):
        """
        Save processing result to JSON file
        
        Args:
            job_id: Job identifier
            result: Pipeline result dictionary
        """
        async with self._lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                
                # Save result to file
                result_path = self.output_dir / f"{job_id}_result.json"
                with open(result_path, "w") as f:
                    json.dump(result, f, indent=2, default=str)
                
                # Store reference
                job.result = result
                logger.info(f"Saved result for job {job_id} to {result_path}")
    
    async def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get processing result for a job
        
        Returns:
            Result dictionary or None if not available
        """
        job = await self.get_job(job_id)
        if not job:
            return None
        
        # Return cached result if available
        if job.result:
            return job.result
        
        # Try loading from file
        result_path = self.output_dir / f"{job_id}_result.json"
        if result_path.exists():
            with open(result_path) as f:
                job.result = json.load(f)
                return job.result
        
        return None
    
    async def cleanup_job(self, job_id: str):
        """Delete job files (for future use)"""
        async with self._lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                
                # Delete video file
                if job.file_path.exists():
                    job.file_path.unlink()
                
                # Delete result file
                result_path = self.output_dir / f"{job_id}_result.json"
                if result_path.exists():
                    result_path.unlink()
                
                # Remove from memory
                del self.jobs[job_id]
                logger.info(f"Cleaned up job {job_id}")


# Global singleton instance
job_manager = JobManager()
