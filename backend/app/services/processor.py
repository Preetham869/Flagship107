"""
Video processing service
Wraps the M1-M9 pipeline for API usage
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from app.services.job_manager import job_manager, JobStatus
from app.models.job import ProcessRequest
from processing.pipeline.e2e_pipeline import EndToEndPipeline, PipelineConfig

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Video processing service
    Manages pipeline execution and progress tracking
    """
    
    def __init__(self):
        self._processing_tasks: Dict[str, asyncio.Task] = {}
    
    async def process_video(self, job_id: str, request: ProcessRequest):
        """
        Process a video asynchronously
        
        Args:
            job_id: Job identifier
            request: Processing configuration
        """
        # Get job
        job = await job_manager.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        # Update status
        await job_manager.update_status(job_id, JobStatus.PROCESSING)
        
        try:
            # Run processing in executor (blocking operation)
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self._run_pipeline,
                job_id,
                str(job.file_path),
                request,
            )
            
            # Save result
            await job_manager.save_result(job_id, result)
            await job_manager.update_status(job_id, JobStatus.COMPLETED)
            
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            logger.error(f"Job {job_id}: {error_msg}", exc_info=True)
            await job_manager.update_status(job_id, JobStatus.FAILED, error=error_msg)
    
    def _run_pipeline(self, job_id: str, video_path: str, request: ProcessRequest) -> Dict[str, Any]:
        """
        Run the M1-M9 pipeline (blocking operation)
        
        Args:
            job_id: Job identifier
            video_path: Path to video file
            request: Processing configuration
            
        Returns:
            Pipeline result dictionary
        """
        # Create pipeline config
        config = PipelineConfig(
            confidence_threshold=request.confidence_threshold,
            frame_skip=request.frame_skip,
            max_frames=request.max_frames,
            person_only=request.person_only,
        )
        
        # Initialize pipeline
        logger.info(f"Initializing pipeline for job {job_id}")
        pipeline = EndToEndPipeline(config)
        
        # Progress callback
        def progress_callback(current_frame: int, total_frames: int):
            # Update progress (runs in executor thread, schedule coroutine)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                job_manager.update_progress(job_id, current_frame, total_frames)
            )
            loop.close()
        
        # Process video
        logger.info(f"Processing video for job {job_id}: {video_path}")
        result = pipeline.process_video(
            video_path=video_path,
            progress_callback=progress_callback,
        )
        
        # Convert to dictionary
        result_dict = result.to_dict()
        
        logger.info(f"Job {job_id} pipeline completed: {result.frames_processed} frames, {result.m1_total_detections} detections")
        
        return result_dict
    
    def start_processing(self, job_id: str, request: ProcessRequest):
        """
        Start processing in background
        
        Args:
            job_id: Job identifier
            request: Processing configuration
        """
        task = asyncio.create_task(self.process_video(job_id, request))
        self._processing_tasks[job_id] = task
        return task
    
    def is_processing(self, job_id: str) -> bool:
        """Check if job is currently processing"""
        return job_id in self._processing_tasks and not self._processing_tasks[job_id].done()


# Global singleton instance
video_processor = VideoProcessor()
