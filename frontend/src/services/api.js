/**
 * API service for backend communication
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth tokens here in future
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getRoot = async () => {
  const response = await api.get('/');
  return response.data;
};

// Video API endpoints
export const uploadVideo = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/api/v1/videos/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      );
      onProgress?.(percentCompleted);
    },
  });

  return response.data;
};

export const processVideo = async (jobId, options = {}) => {
  const response = await api.post(`/api/v1/videos/${jobId}/process`, {
    max_frames: options.maxFrames || null,
    frame_skip: options.frameSkip || 1,
    confidence_threshold: options.confidenceThreshold || 0.5,
    person_only: options.personOnly || false,
  });
  return response.data;
};

export const getJobStatus = async (jobId) => {
  const response = await api.get(`/api/v1/videos/${jobId}/status`);
  return response.data;
};

export const getJobResults = async (jobId) => {
  const response = await api.get(`/api/v1/videos/${jobId}/results`);
  return response.data;
};

export const getVideoUrl = (jobId) => {
  return `${API_BASE_URL}/api/v1/videos/${jobId}/video`;
};

export const getVideoMetadata = async (jobId) => {
  const response = await api.get(`/api/v1/videos/${jobId}/metadata`);
  return response.data;
};

export default api;
