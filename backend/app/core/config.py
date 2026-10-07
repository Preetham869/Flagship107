"""
Application configuration management
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Server
    BACKEND_HOST: str = Field(default="localhost")
    BACKEND_PORT: int = Field(default=8000)
    FRONTEND_URL: str = Field(default="http://localhost:5173")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )
    
    # Processing
    MAX_VIDEO_SIZE_MB: int = Field(default=100)
    PROCESSING_THREADS: int = Field(default=4)
    FRAME_SAMPLE_RATE: int = Field(default=1)
    
    # Storage
    UPLOAD_FOLDER: str = Field(default="./uploads")
    OUTPUT_FOLDER: str = Field(default="./outputs")
    TEMP_FOLDER: str = Field(default="./temp")
    
    # AI Configuration
    OLLAMA_HOST: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="qwen2.5:latest")
    
    # YOLO Configuration
    YOLO_MODEL: str = Field(default="yolov8n.pt")
    YOLO_CONFIDENCE: float = Field(default=0.5)
    YOLO_IOU: float = Field(default=0.45)
    
    # Development
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")
    SECRET_KEY: str = Field(default="change-me-in-production")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
