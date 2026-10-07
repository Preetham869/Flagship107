"""
End-to-end video intelligence pipeline (M1-M6)

Orchestrates the complete processing flow:
Video → Detection (M1) → Tracking (M2) → Behavior (M3) → 
Anomaly (M4) → Events (M5) → Interactions (M6)
"""

from processing.pipeline.e2e_pipeline import EndToEndPipeline, PipelineConfig, PipelineResult

__all__ = ["EndToEndPipeline", "PipelineConfig", "PipelineResult"]
