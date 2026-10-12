"""
Job management service for video processing
Handles job state, file storage, and processing coordination
"""
import asyncio
import json
import logging
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List
import cv2

from app.models.job import JobStatus, ProcessingProgress, ExplanationStatus
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
        
        # AI Explanation state
        self.explanation_status = ExplanationStatus.NOT_GENERATED
        self.explanation_stage: Optional[str] = None
        self.explanation_error: Optional[str] = None
        self.explanation_result: Optional[Dict[str, Any]] = None
        self.previous_explanation_result: Optional[Dict[str, Any]] = None
        self.explanation_task: Optional[asyncio.Task] = None
        
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
        
        # Configure allowed search roots for uploads and outputs
        backend_root = Path(__file__).parent.parent.parent.resolve()
        project_root = backend_root.parent.resolve()
        
        self.allowed_upload_dirs: List[Path] = [
            self.upload_dir.resolve(),
            (backend_root / "uploads").resolve(),
            (project_root / "uploads").resolve(),
        ]
        self.allowed_output_dirs: List[Path] = [
            self.output_dir.resolve(),
            (backend_root / "outputs").resolve(),
            (project_root / "outputs").resolve(),
        ]
        
        logger.info(f"JobManager initialized: uploads={self.upload_dir}, outputs={self.output_dir}")

    def is_safe_path(self, path: Path) -> bool:
        """Verify that resolved file path is strictly within permitted directories"""
        try:
            resolved = path.resolve()
            for allowed in self.allowed_upload_dirs:
                if resolved.is_relative_to(allowed) and resolved.is_file():
                    return True
        except (ValueError, RuntimeError):
            pass
        return False

    def find_video_file(self, job_id: str) -> Optional[Path]:
        """
        Locate video file for job_id safely on disk across primary and fallback directories.
        Guards against directory traversal.
        """
        if not re.match(r'^[a-zA-Z0-9_-]+$', job_id):
            return None

        # Check in-memory job first
        if job_id in self.jobs and self.jobs[job_id].file_path and self.jobs[job_id].file_path.exists():
            return self.jobs[job_id].file_path

        allowed_exts = [".mp4", ".avi", ".mov", ".mkv", ".webm"]

        for search_dir in self.allowed_upload_dirs:
            if not search_dir.exists():
                continue
            for ext in allowed_exts:
                candidate = (search_dir / f"{job_id}{ext}").resolve()
                try:
                    if candidate.is_relative_to(search_dir) and candidate.is_file():
                        return candidate
                except (ValueError, RuntimeError):
                    continue

        return None
    
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
        """Get job by ID, reconstructing from disk if available"""
        if job_id in self.jobs:
            return self.jobs[job_id]

        video_path = self.find_video_file(job_id)
        if video_path and video_path.exists():
            job = Job(
                job_id=job_id,
                filename=video_path.name,
                file_path=video_path,
                file_size=video_path.stat().st_size,
            )
            # Reconnect result and explanation if already on disk
            res = await self.get_result(job_id)
            if res:
                job.result = res
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                job.progress.percent_complete = 100.0
                job.progress.stage = "completed"

            # Check explanation
            exp = await self.get_explanation(job_id)
            if exp:
                job.explanation_result = exp
                job.explanation_status = ExplanationStatus.COMPLETED
                job.explanation_stage = "Completed"

            self.jobs[job_id] = job
            logger.info(f"Reconstructed job {job_id} from disk files")
            return job

        return None
    
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
        """Get processing result from memory or disk"""
        if job_id in self.jobs and self.jobs[job_id].result:
            return self.jobs[job_id].result

        if not re.match(r'^[a-zA-Z0-9_-]+$', job_id):
            return None

        for out_dir in self.allowed_output_dirs:
            if not out_dir.exists():
                continue
            candidate = (out_dir / f"{job_id}_result.json").resolve()
            try:
                if candidate.is_relative_to(out_dir) and candidate.is_file():
                    with open(candidate, "r") as f:
                        res = json.load(f)
                        if job_id in self.jobs:
                            self.jobs[job_id].result = res
                        return res
            except Exception as e:
                logger.warning(f"Failed to read result file {candidate}: {e}")

        return None
    
    async def update_explanation_status(
        self,
        job_id: str,
        status: ExplanationStatus,
        stage: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """Update job explanation status"""
        async with self._lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                job.explanation_status = status
                if stage is not None:
                    job.explanation_stage = stage
                if error is not None:
                    job.explanation_error = error
                elif status in (ExplanationStatus.GENERATING, ExplanationStatus.COMPLETED):
                    job.explanation_error = None

                logger.info(
                    f"Job {job_id} explanation status: {status.value} (stage={stage}, error={error})"
                )

    async def save_explanation(self, job_id: str, explanation: Dict[str, Any]):
        """Save AI explanation result to disk and job state"""
        async with self._lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                explanation_path = self.output_dir / f"{job_id}_explanation.json"
                with open(explanation_path, "w") as f:
                    json.dump(explanation, f, indent=2, default=str)

                job.explanation_result = explanation
                job.explanation_status = ExplanationStatus.COMPLETED
                job.explanation_stage = "Completed"
                job.explanation_error = None
                logger.info(f"Saved explanation for job {job_id} to {explanation_path}")

    async def get_explanation(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get cached explanation or load from disk across permitted output directories"""
        job = await self.get_job(job_id)
        if not job:
            return None

        if job.explanation_result:
            return job.explanation_result

        for out_dir in self.allowed_output_dirs:
            if not out_dir.exists():
                continue
            explanation_path = (out_dir / f"{job_id}_explanation.json").resolve()
            if explanation_path.exists() and explanation_path.is_file():
                try:
                    with open(explanation_path, "r") as f:
                        exp = json.load(f)
                        job.explanation_result = exp
                        job.explanation_status = ExplanationStatus.COMPLETED
                        job.explanation_stage = "Completed"
                        return exp
                except Exception as e:
                    logger.warning(f"Failed to read explanation file for job {job_id}: {e}")

        return None

    async def get_explanation_state(self, job_id: str) -> Dict[str, Any]:
        """Get full explanation state including recovery from disk"""
        job = await self.get_job(job_id)
        if not job:
            return {
                "status": ExplanationStatus.NOT_GENERATED.value,
                "stage": None,
                "error": "Job not found",
                "report": None,
                "previous_report": None,
            }

        # Check if explanation already exists on disk
        if not job.explanation_result:
            explanation_path = self.output_dir / f"{job_id}_explanation.json"
            if explanation_path.exists():
                try:
                    with open(explanation_path) as f:
                        job.explanation_result = json.load(f)
                        job.explanation_status = ExplanationStatus.COMPLETED
                        job.explanation_stage = "Completed"
                except Exception as e:
                    logger.warning(f"Failed to recover explanation from file: {e}")

        return {
            "status": job.explanation_status.value,
            "stage": job.explanation_stage,
            "error": job.explanation_error,
            "report": job.explanation_result,
            "previous_report": job.previous_explanation_result,
        }

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

                # Delete explanation file
                explanation_path = self.output_dir / f"{job_id}_explanation.json"
                if explanation_path.exists():
                    explanation_path.unlink()
                
                # Remove from memory
                del self.jobs[job_id]
                logger.info(f"Cleaned up job {job_id}")


# Global singleton instance
job_manager = JobManager()
