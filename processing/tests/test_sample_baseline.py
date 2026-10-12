"""
End-to-end baseline test for data/sample.mp4.

Validates that normal pedestrian walking in 4K resolution does NOT trigger
false unusual_speed or sudden_speed_change anomalies, while preserving
all object detections and tracks.
"""

from pathlib import Path
import pytest
from processing.pipeline import EndToEndPipeline, PipelineConfig


def test_sample_normal_walking_baseline():
    """Verify that data/sample.mp4 produces 0 false anomalies in full pipeline."""
    video_path = Path("data/sample.mp4")
    if not video_path.exists():
        pytest.skip("data/sample.mp4 not found")

    config = PipelineConfig()
    pipeline = EndToEndPipeline(config)
    result = pipeline.process_video(str(video_path))

    # Verify pipeline execution
    assert result.frames_processed == 240
    assert result.video_width == 2160
    assert result.video_height == 3840
    assert result.m1_total_detections > 500  # Tracks pedestrians reliably
    assert result.m2_unique_tracks >= 3

    # Verify zero false anomalies and zero false correlated events
    assert result.m4_total_anomalies == 0, f"Expected 0 anomalies, got {result.m4_total_anomalies}: {result.all_anomalies}"
    assert result.m5_correlated_events == 0, f"Expected 0 events, got {result.m5_correlated_events}: {result.all_events}"
    assert len(result.all_anomalies) == 0
    assert len(result.all_events) == 0
