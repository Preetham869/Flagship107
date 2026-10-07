"""
Video processing API endpoints
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Path as PathParam
from fastapi.responses import JSONResponse, FileResponse

from app.models.job import (
    VideoUploadResponse,
    ProcessRequest,
    JobStatusResponse,
    JobStatus,
)
from app.services.job_manager import job_manager
from app.services.processor import video_processor
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["videos"])


# Supported video formats
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
ALLOWED_MIME_TYPES = {
    "video/mp4",
    "video/x-msvideo",
    "video/quicktime",
    "video/x-matroska",
    "video/webm",
}


def validate_video_file(file: UploadFile):
    """Validate uploaded video file"""
    # Check content type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    # Check file extension
    from pathlib import Path
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file for processing
    
    Args:
        file: Video file (mp4, avi, mov, mkv, webm)
        
    Returns:
        VideoUploadResponse with job_id
    """
    logger.info(f"Received upload request: {file.filename} ({file.content_type})")
    
    # Validate file
    validate_video_file(file)
    
    # Read file content
    content = await file.read()
    
    # Check file size
    max_size = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_VIDEO_SIZE_MB}MB"
        )
    
    # Create job
    try:
        job = await job_manager.create_job(file.filename, content)
        
        return VideoUploadResponse(
            job_id=job.job_id,
            filename=job.filename,
            file_size=job.file_size,
            video_duration=job.video_duration,
            video_width=job.video_width,
            video_height=job.video_height,
            video_fps=job.video_fps,
            created_at=job.created_at,
        )
    
    except Exception as e:
        logger.error(f"Failed to create job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload video: {str(e)}")


@router.post("/{job_id}/process")
async def process_video(
    job_id: str = PathParam(..., description="Job identifier"),
    request: ProcessRequest = ProcessRequest(),
):
    """
    Start processing a video
    
    Args:
        job_id: Job identifier from upload
        request: Processing configuration
        
    Returns:
        Job status
    """
    logger.info(f"Processing request for job {job_id}")
    
    # Get job
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if already processing or completed
    if job.status == JobStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="Job already processing")
    
    if job.status == JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job already completed")
    
    # Start processing
    try:
        video_processor.start_processing(job_id, request)
        
        return JobStatusResponse(
            job_id=job.job_id,
            status=JobStatus.PROCESSING,
            progress=0.0,
            message="Processing started",
            created_at=job.created_at,
            started_at=job.started_at,
        )
    
    except Exception as e:
        logger.error(f"Failed to start processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str = PathParam(..., description="Job identifier")):
    """
    Get processing status for a job
    
    Args:
        job_id: Job identifier
        
    Returns:
        JobStatusResponse
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress.percent_complete if job.status == JobStatus.PROCESSING else None,
        message=f"Stage: {job.progress.stage}" if job.status == JobStatus.PROCESSING else None,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/{job_id}/results")
async def get_job_results(job_id: str = PathParam(..., description="Job identifier")) -> Dict[str, Any]:
    """
    Get processing results for a completed job
    
    Args:
        job_id: Job identifier
        
    Returns:
        Pipeline result JSON
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {job.status.value}"
        )
    
    # Get result
    result = await job_manager.get_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")
    
    return result


@router.get("/{job_id}/video")
async def get_video(job_id: str = PathParam(..., description="Job identifier")):
    """
    Get original uploaded video
    
    Args:
        job_id: Job identifier
        
    Returns:
        Video file
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not job.file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        path=str(job.file_path),
        media_type="video/mp4",
        filename=job.filename,
    )


@router.get("/{job_id}/metadata")
async def get_video_metadata(job_id: str = PathParam(..., description="Job identifier")) -> Dict[str, Any]:
    """
    Get video metadata
    
    Args:
        job_id: Job identifier
        
    Returns:
        Video metadata
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "filename": job.filename,
        "file_size": job.file_size,
        "duration": job.video_duration,
        "width": job.video_width,
        "height": job.video_height,
        "fps": job.video_fps,
    }


@router.post("/{job_id}/explanation")
async def generate_explanation(job_id: str = PathParam(..., description="Job identifier")) -> Dict[str, Any]:
    """
    Generate M9 AI explanation for a completed job's M8 scene
    
    This endpoint:
    1. Loads existing M1-M8 processing results (does NOT rerun pipeline)
    2. Extracts the M8 contextual scene
    3. Invokes Ollama/qwen3:8b LLM to generate natural language explanation
    4. Returns structured explanation with observed/derived sections
    
    Args:
        job_id: Job identifier (must have completed processing)
        
    Returns:
        SceneExplanation with LLM-generated narrative
        
    Raises:
        404: Job not found or results not available
        400: Job not completed or no M8 scene available
        503: Ollama/LLM service unavailable
    """
    logger.info(f"Generating M9 explanation for job {job_id}")
    
    # 1. Validate job exists and is completed
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {job.status.value}. Complete processing first."
        )
    
    # 2. Load existing results
    result = await job_manager.get_result(job_id)
    if not result:
        raise HTTPException(status_code=404, detail="Results not found")
    
    # 3. Extract M8 scene
    all_scenes = result.get("all_scenes", [])
    if not all_scenes or len(all_scenes) == 0:
        raise HTTPException(
            status_code=400,
            detail="No M8 contextual scene available. Processing may have failed at M8 stage."
        )
    
    # Use first scene (MVP processes single-scene videos)
    scene_dict = all_scenes[0]
    
    # 4. Convert to ContextualScene object
    try:
        from processing.context.schemas import ContextualScene
        scene = ContextualScene.from_dict(scene_dict)
    except Exception as e:
        logger.error(f"Failed to parse M8 scene: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse M8 scene data: {str(e)}"
        )
    
    # 5. Generate explanation via ExplanationGenerator
    try:
        from processing.llm.explanations import ExplanationGenerator
        from processing.llm.client import ProviderUnavailableError, ModelNotFoundError
        
        generator = ExplanationGenerator()
        explanation = await generator.explain_scene(scene)
        
        # Convert to dict for JSON response
        return explanation.to_dict()
        
    except ProviderUnavailableError as e:
        logger.error(f"Ollama unavailable: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"LLM service unavailable: {str(e)}. Ensure Ollama is running at http://localhost:11434"
        )
    
    except ModelNotFoundError as e:
        logger.error(f"Model not found: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Model not available: {str(e)}. Run 'ollama pull qwen3:8b' to download the model"
        )
    
    except Exception as e:
        logger.error(f"Failed to generate explanation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate explanation: {str(e)}"
        )
