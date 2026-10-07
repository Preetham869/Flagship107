/**
 * Video upload component
 * Handles file selection and upload to backend
 */
import { useState } from 'react';
import { uploadVideo } from '../services/api';

const VideoUpload = ({ onUploadComplete }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setError(null);
      
      // Validate file type
      const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm'];
      if (!validTypes.includes(file.type)) {
        setError('Please select a valid video file (mp4, avi, mov, mkv, webm)');
        return;
      }

      // Validate file size (100MB max for MVP)
      const maxSize = 100 * 1024 * 1024; // 100MB
      if (file.size > maxSize) {
        setError('File size must be less than 100MB');
        return;
      }

      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      const response = await uploadVideo(selectedFile, (percent) => {
        setProgress(percent);
      });

      setUploading(false);
      onUploadComplete?.(response);
      
    } catch (err) {
      setUploading(false);
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
      console.error('Upload error:', err);
    }
  };

  return (
    <div className="video-upload">
      <h3>Upload Video</h3>
      <input
        type="file"
        accept="video/*"
        onChange={handleFileChange}
        disabled={uploading}
      />
      {error && (
        <div className="error-message" style={{ color: 'red', marginTop: '10px' }}>
          {error}
        </div>
      )}
      {selectedFile && (
        <div className="file-info">
          <p>Selected: {selectedFile.name}</p>
          <p>Size: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
        </div>
      )}
      {selectedFile && !uploading && !error && (
        <button onClick={handleUpload}>Upload Video</button>
      )}
      {uploading && (
        <div className="upload-progress">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <p>Uploading: {progress}%</p>
        </div>
      )}
    </div>
  );
};

export default VideoUpload;
