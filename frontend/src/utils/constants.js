/**
 * Application constants
 */

export const VIDEO_CONFIG = {
  MAX_SIZE_MB: 100,
  ALLOWED_TYPES: ['video/mp4', 'video/avi', 'video/mov', 'video/mkv'],
  ALLOWED_EXTENSIONS: ['.mp4', '.avi', '.mov', '.mkv'],
};

export const API_ENDPOINTS = {
  HEALTH: '/health',
  ROOT: '/',
  VIDEOS_UPLOAD: '/api/v1/videos/upload',
  VIDEOS_STATUS: '/api/v1/videos/:id/status',
  VIDEOS_PROCESS: '/api/v1/videos/:id/process',
  VIDEOS_RESULTS: '/api/v1/videos/:id/results',
  VIDEOS_DETECTIONS: '/api/v1/videos/:id/detections',
  VIDEOS_ANOMALIES: '/api/v1/videos/:id/anomalies',
};

export const PROCESSING_STATUS = {
  IDLE: 'idle',
  UPLOADING: 'uploading',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
};

export const ANOMALY_TYPES = {
  SUDDEN_APPEARANCE: 'sudden_appearance',
  UNUSUAL_SPEED: 'unusual_speed',
  LOITERING: 'loitering',
  RESTRICTED_AREA: 'restricted_area',
};

export const SEVERITY_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
};
