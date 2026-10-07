"""
Tests for video processing API endpoints
"""
import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_video_bytes():
    """Sample video file bytes for testing"""
    # Create minimal valid MP4 header
    # This is a minimal MP4 with ftyp and moov boxes
    return b'\x00\x00\x00\x20\x66\x74\x79\x70\x69\x73\x6f\x6d' + b'\x00' * 1000


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Flagship 107 API"
    assert data["status"] == "operational"


class TestVideoUpload:
    """Test video upload endpoint"""
    
    def test_upload_valid_video(self, client, sample_video_bytes):
        """Test uploading a valid video file"""
        with patch('cv2.VideoCapture') as mock_cap:
            # Mock video metadata extraction
            mock_instance = Mock()
            mock_instance.isOpened.return_value = True
            mock_instance.get.side_effect = lambda prop: {
                3: 1920,  # CAP_PROP_FRAME_WIDTH
                4: 1080,  # CAP_PROP_FRAME_HEIGHT
                5: 30.0,  # CAP_PROP_FPS
                7: 300,   # CAP_PROP_FRAME_COUNT
            }.get(prop, 0)
            mock_instance.release.return_value = None
            mock_cap.return_value = mock_instance
            
            response = client.post(
                "/api/v1/videos/upload",
                files={"file": ("test_video.mp4", sample_video_bytes, "video/mp4")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            assert data["filename"] == "test_video.mp4"
            assert data["file_size"] == len(sample_video_bytes)
            assert data["video_width"] == 1920
            assert data["video_height"] == 1080
    
    def test_upload_invalid_file_type(self, client):
        """Test uploading invalid file type"""
        response = client.post(
            "/api/v1/videos/upload",
            files={"file": ("test.txt", b"not a video", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
    
    def test_upload_too_large(self, client):
        """Test uploading file that's too large"""
        large_file = b"x" * (101 * 1024 * 1024)  # 101 MB
        
        with patch('cv2.VideoCapture'):
            response = client.post(
                "/api/v1/videos/upload",
                files={"file": ("large.mp4", large_file, "video/mp4")}
            )
            
            assert response.status_code == 400
            assert "too large" in response.json()["detail"].lower()


class TestJobStatus:
    """Test job status endpoint"""
    
    def test_get_status_nonexistent_job(self, client):
        """Test getting status for non-existent job"""
        response = client.get("/api/v1/videos/fake-job-id/status")
        assert response.status_code == 404
        assert response.json()["detail"] == "Job not found"
    
    def test_get_status_after_upload(self, client, sample_video_bytes):
        """Test getting status after successful upload"""
        with patch('cv2.VideoCapture') as mock_cap:
            mock_instance = Mock()
            mock_instance.isOpened.return_value = True
            mock_instance.get.return_value = 0
            mock_instance.release.return_value = None
            mock_cap.return_value = mock_instance
            
            # Upload video
            upload_response = client.post(
                "/api/v1/videos/upload",
                files={"file": ("test.mp4", sample_video_bytes, "video/mp4")}
            )
            job_id = upload_response.json()["job_id"]
            
            # Get status
            status_response = client.get(f"/api/v1/videos/{job_id}/status")
            assert status_response.status_code == 200
            
            data = status_response.json()
            assert data["job_id"] == job_id
            assert data["status"] == "queued"


class TestProcessVideo:
    """Test video processing endpoint"""
    
    def test_process_nonexistent_job(self, client):
        """Test processing non-existent job"""
        response = client.post("/api/v1/videos/fake-job-id/process")
        assert response.status_code == 404
        assert response.json()["detail"] == "Job not found"
    
    def test_process_valid_job(self, client, sample_video_bytes):
        """Test starting processing for valid job"""
        with patch('cv2.VideoCapture') as mock_cap:
            mock_instance = Mock()
            mock_instance.isOpened.return_value = True
            mock_instance.get.return_value = 0
            mock_instance.release.return_value = None
            mock_cap.return_value = mock_instance
            
            # Upload video
            upload_response = client.post(
                "/api/v1/videos/upload",
                files={"file": ("test.mp4", sample_video_bytes, "video/mp4")}
            )
            job_id = upload_response.json()["job_id"]
            
            # Mock the video processor
            with patch('app.services.processor.video_processor.start_processing'):
                # Start processing
                process_response = client.post(
                    f"/api/v1/videos/{job_id}/process",
                    json={
                        "max_frames": 10,
                        "frame_skip": 1,
                        "confidence_threshold": 0.5,
                        "person_only": False
                    }
                )
                
                assert process_response.status_code == 200
                data = process_response.json()
                assert data["job_id"] == job_id
                assert data["status"] == "processing"


class TestGetResults:
    """Test get results endpoint"""
    
    def test_get_results_nonexistent_job(self, client):
        """Test getting results for non-existent job"""
        response = client.get("/api/v1/videos/fake-job-id/results")
        assert response.status_code == 404
    
    def test_get_results_not_completed(self, client, sample_video_bytes):
        """Test getting results before job is completed"""
        with patch('cv2.VideoCapture') as mock_cap:
            mock_instance = Mock()
            mock_instance.isOpened.return_value = True
            mock_instance.get.return_value = 0
            mock_instance.release.return_value = None
            mock_cap.return_value = mock_instance
            
            # Upload video
            upload_response = client.post(
                "/api/v1/videos/upload",
                files={"file": ("test.mp4", sample_video_bytes, "video/mp4")}
            )
            job_id = upload_response.json()["job_id"]
            
            # Try to get results (should fail - not completed)
            results_response = client.get(f"/api/v1/videos/{job_id}/results")
            assert results_response.status_code == 400
            assert "not completed" in results_response.json()["detail"].lower()


class TestGetVideo:
    """Test get video endpoint"""
    
    def test_get_video_nonexistent_job(self, client):
        """Test getting video for non-existent job"""
        response = client.get("/api/v1/videos/fake-job-id/video")
        assert response.status_code == 404


class TestGetMetadata:
    """Test get metadata endpoint"""
    
    def test_get_metadata(self, client, sample_video_bytes):
        """Test getting video metadata"""
        with patch('cv2.VideoCapture') as mock_cap:
            mock_instance = Mock()
            mock_instance.isOpened.return_value = True
            mock_instance.get.side_effect = lambda prop: {
                3: 640,   # width
                4: 480,   # height
                5: 24.0,  # fps
                7: 120,   # frame_count
            }.get(prop, 0)
            mock_instance.release.return_value = None
            mock_cap.return_value = mock_instance
            
            # Upload video
            upload_response = client.post(
                "/api/v1/videos/upload",
                files={"file": ("test.mp4", sample_video_bytes, "video/mp4")}
            )
            job_id = upload_response.json()["job_id"]
            
            # Get metadata
            metadata_response = client.get(f"/api/v1/videos/{job_id}/metadata")
            assert metadata_response.status_code == 200
            
            data = metadata_response.json()
            assert data["job_id"] == job_id
            assert data["filename"] == "test.mp4"
            assert data["width"] == 640
            assert data["height"] == 480
            assert data["fps"] == 24.0
