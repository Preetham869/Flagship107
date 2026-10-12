"""
Video processing API endpoints
"""
import logging
import mimetypes
import re
from typing import Dict, Any, Optional
import asyncio
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Path as PathParam, BackgroundTasks, Request, Response
from fastapi.responses import StreamingResponse, FileResponse

from app.models.job import (
    VideoUploadResponse,
    ProcessRequest,
    JobStatusResponse,
    JobStatus,
    ExplanationStatus,
    ExplanationRequest,
    ExplanationStatusResponse,
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
async def get_video(
    request: Request,
    job_id: str = PathParam(..., description="Job identifier"),
):
    """
    Get original uploaded video with HTTP Byte-Range support for streaming and seeking.
    
    Supports:
    - 200 OK with Accept-Ranges for standard requests
    - 206 Partial Content for Range requests (e.g. bytes=0-, bytes=1024-2048)
    - 416 Range Not Satisfiable for out-of-bounds ranges
    - Path safety validation preventing directory traversal
    - Dynamic MIME type detection
    
    Args:
        request: FastAPI Request containing optional Range header
        job_id: Job identifier
        
    Returns:
        StreamingResponse (206) or FileResponse (200)
    """
    job = await job_manager.get_job(job_id)
    file_path: Optional[Path] = None
    filename: str = f"{job_id}.mp4"

    if job and job.file_path and job.file_path.exists():
        file_path = job.file_path
        filename = job.filename
    else:
        file_path = job_manager.find_video_file(job_id)
        if file_path:
            filename = file_path.name

    if not file_path or not file_path.exists():
        logger.warning(f"Video file not found for job {job_id}")
        raise HTTPException(status_code=404, detail="Video file not found")

    resolved_path = file_path.resolve()
    if not job_manager.is_safe_path(resolved_path):
        logger.error(f"Access denied to file outside permitted storage: {resolved_path}")
        raise HTTPException(status_code=403, detail="Access denied")

    file_size = resolved_path.stat().st_size
    mime_type, _ = mimetypes.guess_type(str(resolved_path))
    content_type = mime_type or "video/mp4"

    # Sanitize filename for header
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)

    range_header = request.headers.get("Range")

    if not range_header:
        # Full content response with byte-range capability advertised
        return FileResponse(
            path=str(resolved_path),
            media_type=content_type,
            filename=safe_filename,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
                "Content-Disposition": f'inline; filename="{safe_filename}"',
            },
        )

    # Parse Range: bytes=start-end
    range_match = re.match(r"^bytes=(\d*)-(\d*)$", range_header.strip())
    if not range_match:
        return Response(
            status_code=416,
            headers={"Content-Range": f"bytes */{file_size}"},
            content="Range Not Satisfiable",
        )

    start_str, end_str = range_match.groups()

    if start_str and end_str:
        start = int(start_str)
        end = int(end_str)
    elif start_str:
        start = int(start_str)
        end = file_size - 1
    elif end_str:
        start = max(0, file_size - int(end_str))
        end = file_size - 1
    else:
        start = 0
        end = file_size - 1

    if start >= file_size or start > end:
        return Response(
            status_code=416,
            headers={"Content-Range": f"bytes */{file_size}"},
            content="Range Not Satisfiable",
        )

    end = min(end, file_size - 1)
    chunk_size = (end - start) + 1

    def file_chunk_generator(path: Path, offset: int, length: int, block_size: int = 256 * 1024):
        with open(path, "rb") as f:
            f.seek(offset)
            bytes_left = length
            while bytes_left > 0:
                to_read = min(bytes_left, block_size)
                data = f.read(to_read)
                if not data:
                    break
                bytes_left -= len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(chunk_size),
        "Content-Type": content_type,
        "Content-Disposition": f'inline; filename="{safe_filename}"',
    }

    return StreamingResponse(
        file_chunk_generator(resolved_path, start, chunk_size),
        status_code=206,
        headers=headers,
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


async def _run_explanation_background(job_id: str):
    """Background task for generating AI investigation report"""
    logger.info(f"Starting background explanation generation for job {job_id}")
    try:
        await job_manager.update_explanation_status(
            job_id, ExplanationStatus.GENERATING, stage="Extracting scene evidence & telemetry"
        )
        
        result = await job_manager.get_result(job_id)
        if not result:
            await job_manager.update_explanation_status(
                job_id, ExplanationStatus.FAILED, error="Processing results not found"
            )
            return

        all_scenes = result.get("all_scenes", [])
        from processing.context.schemas import ContextualScene
        if all_scenes and len(all_scenes) > 0:
            scene = ContextualScene.from_dict(all_scenes[0])
        else:
            # Construct baseline scene representing empty / zero-anomaly video
            scene = ContextualScene(
                scene_id=f"scene_{job_id[:8]}",
                scene_number=1,
                start_frame=0,
                end_frame=int(result.get("frames_processed") or 0),
                start_timestamp=0.0,
                end_timestamp=float(result.get("video_duration") or 0.0),
                summary="Baseline video scene without segmented anomalies",
            )

        await job_manager.update_explanation_status(
            job_id, ExplanationStatus.GENERATING, stage="Querying local Ollama model (qwen3:8b)"
        )

        from processing.llm.explanations import ExplanationGenerator
        from processing.llm.investigation_report import build_investigation_report

        generator = ExplanationGenerator()
        explanation = await generator.explain_scene(scene)

        await job_manager.update_explanation_status(
            job_id, ExplanationStatus.GENERATING, stage="Structuring evidence report"
        )

        report = build_investigation_report(result, explanation.to_dict())
        await job_manager.save_explanation(job_id, report)
        logger.info(f"Successfully generated and saved explanation report for job {job_id}")

    except Exception as e:
        logger.error(f"Failed to generate explanation in background for {job_id}: {e}", exc_info=True)
        # Attempt deterministic fallback report so evidence workflow is preserved
        try:
            result = await job_manager.get_result(job_id)
            if result:
                from processing.llm.investigation_report import build_investigation_report
                fallback_report = build_investigation_report(
                    result,
                    scene_explanation={
                        "model_name": "deterministic-fallback",
                        "model_version": "v1.0",
                        "is_fallback": True,
                        "fallback_reason": str(e),
                        "overview": "Deterministic evidence-driven analysis (Ollama inference unavailable).",
                    }
                )
                await job_manager.save_explanation(job_id, fallback_report)
                logger.info(f"Saved deterministic fallback report for job {job_id} after error: {e}")
                return
        except Exception as fallback_err:
            logger.error(f"Fallback generation also failed for {job_id}: {fallback_err}")
            
        await job_manager.update_explanation_status(
            job_id, ExplanationStatus.FAILED, error=str(e)
        )


@router.get("/{job_id}/explanation", response_model=ExplanationStatusResponse)
async def get_explanation(
    job_id: str = PathParam(..., description="Job identifier")
) -> ExplanationStatusResponse:
    """
    Get status or cached result of AI investigation explanation
    
    Args:
        job_id: Job identifier
        
    Returns:
        ExplanationStatusResponse with status, stage, error, report, and previous_report
    """
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    state = await job_manager.get_explanation_state(job_id)
    return ExplanationStatusResponse(
        job_id=job_id,
        status=state["status"],
        stage=state["stage"],
        error=state["error"],
        report=state["report"],
        previous_report=state["previous_report"],
    )


@router.post("/{job_id}/explanation")
async def generate_explanation(
    job_id: str = PathParam(..., description="Job identifier"),
    request: ExplanationRequest = ExplanationRequest(),
) -> Dict[str, Any]:
    """
    Start or retrieve AI investigation report generation
    
    - Reuses existing cached report if available and force_regenerate is False
    - Dispatches asynchronous background generation to keep event loop free
    - Prevents duplicate simultaneous generation requests
    - Preserves previous report during regeneration
    
    Args:
        job_id: Job identifier (must have completed processing)
        request: Explanation configuration (force_regenerate flag)
        
    Returns:
        Explanation status dictionary and report if already available
    """
    logger.info(f"Received explanation request for job {job_id} (force_regenerate={request.force_regenerate})")
    
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {job.status.value}. Complete processing first."
        )
    
    # Check if existing report is available and regeneration is not requested
    existing_report = await job_manager.get_explanation(job_id)
    if existing_report and not request.force_regenerate:
        logger.info(f"Returning cached explanation report for job {job_id}")
        return {
            "status": ExplanationStatus.COMPLETED.value,
            "report": existing_report,
            **existing_report,
        }
    
    # If already generating, prevent duplicate concurrent runs
    if job.explanation_status == ExplanationStatus.GENERATING:
        logger.info(f"Explanation for job {job_id} is already generating, returning current status")
        return {
            "job_id": job_id,
            "status": ExplanationStatus.GENERATING.value,
            "stage": job.explanation_stage,
            "message": "Explanation generation already in progress",
            "previous_report": job.previous_explanation_result or existing_report,
        }
    
    # If regenerating, preserve previous report
    if request.force_regenerate and existing_report:
        job.previous_explanation_result = existing_report
    
    # Update status to queued
    await job_manager.update_explanation_status(
        job_id, ExplanationStatus.QUEUED, stage="Queued for generation"
    )
    
    # Launch background task
    asyncio.create_task(_run_explanation_background(job_id))
    
    return {
        "job_id": job_id,
        "status": ExplanationStatus.QUEUED.value,
        "stage": "Queued for generation",
        "message": "Explanation generation started in background",
        "previous_report": job.previous_explanation_result,
    }
