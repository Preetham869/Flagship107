"""
Job models for video processing
"""
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class JobStatus(str, Enum):
    """Video processing job status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExplanationStatus(str, Enum):
    """AI investigation explanation generation status"""
    NOT_GENERATED = "not_generated"
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoUploadResponse(BaseModel):
    """Response from video upload"""
    job_id: str = Field(..., description="Unique job identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    video_duration: Optional[float] = Field(None, description="Video duration in seconds")
    video_width: Optional[int] = Field(None, description="Video width in pixels")
    video_height: Optional[int] = Field(None, description="Video height in pixels")
    video_fps: Optional[float] = Field(None, description="Video FPS")
    created_at: datetime = Field(default_factory=datetime.now)


class ProcessRequest(BaseModel):
    """Request to start processing a video"""
    max_frames: Optional[int] = Field(None, description="Maximum frames to process (for testing)")
    frame_skip: int = Field(1, description="Process every Nth frame", ge=1)
    confidence_threshold: float = Field(0.5, description="Detection confidence threshold", ge=0.0, le=1.0)
    person_only: bool = Field(False, description="Track only people")


class JobStatusResponse(BaseModel):
    """Response for job status check"""
    job_id: str
    status: JobStatus
    progress: Optional[float] = Field(None, description="Processing progress (0-100)", ge=0, le=100)
    message: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ProcessingProgress(BaseModel):
    """Processing progress information"""
    current_frame: int = 0
    total_frames: int = 0
    percent_complete: float = 0.0
    stage: str = "initializing"


class ExplanationRequest(BaseModel):
    """Request to start or regenerate an AI explanation"""
    force_regenerate: bool = Field(False, description="Whether to recompute even if a cached report exists")


class ExplanationStatusResponse(BaseModel):
    """Response for explanation status check and report delivery"""
    job_id: str
    status: ExplanationStatus
    stage: Optional[str] = None
    error: Optional[str] = None
    report: Optional[Dict[str, Any]] = None
    previous_report: Optional[Dict[str, Any]] = None
    fingerprint: Optional[str] = None

