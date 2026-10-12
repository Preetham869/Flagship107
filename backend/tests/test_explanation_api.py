"""
Tests for AI Explanation API endpoints and caching behavior
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app
from app.models.job import JobStatus, ExplanationStatus
from app.services.job_manager import job_manager

client = TestClient(app)


async def _create_completed_mock_job(tmp_path):
    """Create a mock job in COMPLETED status with mock result and scene"""
    video_path = tmp_path / "test_sample.mp4"
    video_path.write_bytes(b"mock video content")
    
    job = await job_manager.create_job("test_sample.mp4", b"mock video content")
    job.status = JobStatus.COMPLETED
    
    mock_result = {
        "video_duration": 15.5,
        "video_width": 1920,
        "video_height": 1080,
        "video_fps": 30.0,
        "frames_processed": 465,
        "m1_total_detections": 120,
        "m2_unique_tracks": 2,
        "m3_avg_speed": 45.2,
        "m3_max_speed": 98.4,
        "m4_total_anomalies": 1,
        "m5_correlated_events": 0,
        "m8_total_scenes": 1,
        "all_tracks": [],
        "all_behaviors": [
            [
                {
                    "track_id": 1,
                    "class_name": "person",
                    "timestamp": 1.0,
                    "speed": 40.0,
                    "state": "walking"
                }
            ]
        ],
        "all_anomalies": [
            {
                "anomaly_id": "anom_01",
                "track_id": 1,
                "timestamp": 2.5,
                "anomaly_type": "unusual_speed",
                "severity": "medium",
                "evidence": {"current_speed": 98.4}
            }
        ],
        "all_events": [],
        "all_scenes": [
            {
                "scene_id": "scene_001",
                "scene_number": 1,
                "start_frame": 0,
                "end_frame": 465,
                "start_timestamp": 0.0,
                "end_timestamp": 15.5,
                "summary": "Scene with walking entity",
                "participating_track_ids": ["1"],
                "track_summaries": [],
                "source_anomalies": [],
                "movement_patterns": ["linear_traversal"],
                "spatial_patterns": [],
            }
        ],
    }
    await job_manager.save_result(job.job_id, mock_result)
    return job


def test_get_explanation_not_found():
    response = client.get("/api/v1/videos/nonexistent-id/explanation")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_explanation_flow_caching_and_status(tmp_path):
    job = await _create_completed_mock_job(tmp_path)
    job_id = job.job_id

    # 1. Initially NOT_GENERATED
    resp = client.get(f"/api/v1/videos/{job_id}/explanation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "not_generated"
    assert data["report"] is None

    # 2. Save a report directly to simulate completed report
    mock_report = {
        "executive_summary": "Test executive summary",
        "video_overview": {"duration": 15.5},
        "chronological_events": [],
        "track_analyses": [],
        "evidence_and_limitations": {},
        "final_assessment": "Test assessment",
        "has_anomalies": True,
    }
    await job_manager.save_explanation(job_id, mock_report)

    # 3. GET should now return COMPLETED with report
    resp2 = client.get(f"/api/v1/videos/{job_id}/explanation")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "completed"
    assert data2["report"]["executive_summary"] == "Test executive summary"

    # 4. POST without force_regenerate returns cached report immediately
    resp3 = client.post(f"/api/v1/videos/{job_id}/explanation", json={"force_regenerate": False})
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert data3["status"] == "completed"
    assert data3["report"]["executive_summary"] == "Test executive summary"
