"""
Integration tests for end-to-end pipeline (M1-M6)
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
import tempfile

from processing.pipeline import EndToEndPipeline, PipelineConfig


def create_test_video(width=640, height=480, fps=30, num_frames=10):
    """Create a simple test video"""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        video_path = f.name
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
    
    for i in range(num_frames):
        # Create frame with moving object
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Draw a moving rectangle (simulate person)
        x = int(100 + i * 20)
        y = 200
        cv2.rectangle(frame, (x, y), (x + 100, y + 150), (255, 255, 255), -1)
        writer.write(frame)
    
    writer.release()
    return video_path


def test_pipeline_initialization():
    """Test pipeline can be initialized"""
    config = PipelineConfig()
    pipeline = EndToEndPipeline(config)
    
    assert pipeline.tracker is not None
    assert pipeline.behavior_analyzer is not None
    assert pipeline.anomaly_detector is not None
    assert pipeline.event_correlator is not None
    assert pipeline.interaction_detector is not None


def test_pipeline_with_short_video():
    """Test pipeline processes short video"""
    # Create test video
    video_path = create_test_video(num_frames=10)
    
    try:
        config = PipelineConfig(max_frames=10)
        pipeline = EndToEndPipeline(config)
        
        result = pipeline.process_video(video_path)
        
        # Verify result structure
        assert result.video_path == video_path
        assert result.frames_processed > 0
        assert result.frames_processed <= 10
        assert result.processing_time > 0
        
        # All M1-M6 statistics should exist
        assert result.m1_total_detections >= 0
        assert result.m2_unique_tracks >= 0
        assert result.m3_total_behaviors >= 0
        assert result.m4_total_anomalies >= 0
        assert result.m5_correlated_events >= 0
        assert result.m6_total_relationships >= 0
        
    finally:
        # Clean up
        Path(video_path).unlink(missing_ok=True)


def test_pipeline_with_empty_video():
    """Test pipeline handles video with no detections"""
    # Create empty black video
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        video_path = f.name
    
    try:
        width, height, fps = 320, 240, 10
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
        
        # Write 5 black frames
        for _ in range(5):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            writer.write(frame)
        writer.release()
        
        # Process
        config = PipelineConfig(max_frames=5)
        pipeline = EndToEndPipeline(config)
        result = pipeline.process_video(video_path)
        
        # Should complete without errors
        assert result.frames_processed == 5
        # May have 0 detections
        assert result.m1_total_detections >= 0
        # Should have 0 tracks/behaviors/anomalies
        assert result.m2_unique_tracks == 0
        assert result.m3_total_behaviors == 0
        assert result.m4_total_anomalies == 0
        assert result.m5_correlated_events == 0
        assert result.m6_total_relationships == 0
        
    finally:
        Path(video_path).unlink(missing_ok=True)


def test_pipeline_timestamp_consistency():
    """Test timestamps are consistent across pipeline stages"""
    video_path = create_test_video(num_frames=5)
    
    try:
        config = PipelineConfig(max_frames=5)
        pipeline = EndToEndPipeline(config)
        result = pipeline.process_video(video_path)
        
        # Check timestamp progression in behaviors
        if result.all_behaviors:
            for frame_behaviors in result.all_behaviors:
                if frame_behaviors:
                    timestamps = [b['timestamp'] for b in frame_behaviors]
                    # All behaviors in same frame should have same timestamp
                    assert len(set(timestamps)) <= 1, "Behaviors in same frame should have same timestamp"
        
        # Check anomaly timestamps
        if result.all_anomalies:
            timestamps = [a['timestamp'] for a in result.all_anomalies]
            # Timestamps should be non-negative
            assert all(t >= 0 for t in timestamps), "Timestamps should be non-negative"
        
    finally:
        Path(video_path).unlink(missing_ok=True)


def test_pipeline_track_id_persistence():
    """Test track IDs persist across frames"""
    video_path = create_test_video(num_frames=10)
    
    try:
        config = PipelineConfig(max_frames=10)
        pipeline = EndToEndPipeline(config)
        result = pipeline.process_video(video_path)
        
        # Collect all track IDs
        all_track_ids = set()
        for frame_tracks in result.all_tracks:
            for track in frame_tracks:
                all_track_ids.add(track['track_id'])
        
        # Should match unique_tracks count
        assert len(all_track_ids) == result.m2_unique_tracks
        
        # Track IDs should be consistent type (str or int)
        if all_track_ids:
            track_id_types = {type(tid) for tid in all_track_ids}
            assert len(track_id_types) == 1, "Track IDs should have consistent type"
        
    finally:
        Path(video_path).unlink(missing_ok=True)


def test_pipeline_with_frame_skip():
    """Test pipeline correctly handles frame skipping"""
    video_path = create_test_video(num_frames=20)
    
    try:
        # Process with skip=2 (every other frame)
        config = PipelineConfig(frame_skip=2, max_frames=20)
        pipeline = EndToEndPipeline(config)
        result = pipeline.process_video(video_path)
        
        # Should process approximately half the frames
        assert result.frames_processed <= 10
        assert result.frames_skipped >= result.frames_processed
        
    finally:
        Path(video_path).unlink(missing_ok=True)


def test_pipeline_result_serialization():
    """Test pipeline result can be serialized to JSON"""
    video_path = create_test_video(num_frames=5)
    
    try:
        config = PipelineConfig(max_frames=5)
        pipeline = EndToEndPipeline(config)
        result = pipeline.process_video(video_path)
        
        # Should be able to convert to dict
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        
        # Should have all required keys
        assert 'video_path' in result_dict
        assert 'm1_total_detections' in result_dict
        assert 'm2_unique_tracks' in result_dict
        assert 'm3_total_behaviors' in result_dict
        assert 'm4_total_anomalies' in result_dict
        assert 'm5_correlated_events' in result_dict
        assert 'm6_total_relationships' in result_dict
        
        # Test JSON serialization
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name
        
        result.to_json(json_path)
        assert Path(json_path).exists()
        Path(json_path).unlink()
        
    finally:
        Path(video_path).unlink(missing_ok=True)


def test_pipeline_with_max_frames():
    """Test pipeline respects max_frames limit"""
    video_path = create_test_video(num_frames=50)
    
    try:
        config = PipelineConfig(max_frames=10)
        pipeline = EndToEndPipeline(config)
        result = pipeline.process_video(video_path)
        
        # Should stop at max_frames
        assert result.frames_processed <= 10
        
    finally:
        Path(video_path).unlink(missing_ok=True)


def test_pipeline_config_defaults():
    """Test pipeline configuration defaults"""
    config = PipelineConfig()
    
    assert config.confidence_threshold == 0.5
    assert config.frame_skip == 1
    assert config.model_name == "yolov8n.pt"
    assert config.behavior_config is not None
    assert config.anomaly_config is not None
    assert config.event_config is not None
    assert config.interaction_config is not None


def test_pipeline_person_only_mode():
    """Test pipeline can be configured for person-only tracking"""
    config = PipelineConfig(person_only=True)
    pipeline = EndToEndPipeline(config)
    
    # Should have track_classes set
    assert pipeline.track_classes is not None
    assert len(pipeline.track_classes) == 1


def test_pipeline_stages_integration():
    """Test data flows correctly between pipeline stages"""
    video_path = create_test_video(num_frames=10)
    
    try:
        config = PipelineConfig(max_frames=10)
        pipeline = EndToEndPipeline(config)
        result = pipeline.process_video(video_path)
        
        # If we have detections, we should have tracking
        if result.m1_total_detections > 0:
            assert result.m2_total_track_observations > 0
        
        # If we have tracking, we should have behaviors
        if result.m2_total_track_observations > 0:
            assert result.m3_total_behaviors > 0
        
        # Behaviors feed into anomalies (may be 0)
        assert result.m4_total_anomalies >= 0
        
        # Anomalies feed into events
        if result.m4_total_anomalies > 0:
            # May or may not have events (depends on correlation logic)
            assert result.m5_correlated_events >= 0
        
        # Behaviors feed into interactions (requires 2+ entities)
        assert result.m6_total_relationships >= 0
        
    finally:
        Path(video_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
