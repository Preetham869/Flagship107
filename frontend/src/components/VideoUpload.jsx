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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div 
        style={{
          border: '2px dashed #30363d',
          borderRadius: '8px',
          padding: '40px 20px',
          textAlign: 'center',
          backgroundColor: '#0d1117',
          transition: 'border-color 0.2s ease',
          cursor: uploading ? 'not-allowed' : 'pointer'
        }}
        onClick={() => !uploading && document.getElementById('video-upload-input').click()}
        onDragOver={(e) => { e.preventDefault(); e.currentTarget.style.borderColor = '#58a6ff'; }}
        onDragLeave={(e) => { e.currentTarget.style.borderColor = '#30363d'; }}
        onDrop={(e) => {
          e.preventDefault();
          e.currentTarget.style.borderColor = '#30363d';
          if (uploading) return;
          const file = e.dataTransfer.files[0];
          if (file) handleFileChange({ target: { files: [file] } });
        }}
      >
        <input
          id="video-upload-input"
          type="file"
          accept="video/*"
          onChange={handleFileChange}
          disabled={uploading}
          style={{ display: 'none' }}
        />
        <svg style={{ width: '48px', height: '48px', color: '#8b949e', marginBottom: '16px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <div style={{ color: '#c9d1d9', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
          Click to upload or drag and drop
        </div>
        <div style={{ color: '#8b949e', fontSize: '12px' }}>
          MP4, AVI, MOV, MKV up to 100MB
        </div>
      </div>

      {error && (
        <div style={{ color: '#ff7b72', fontSize: '13px', padding: '8px 12px', backgroundColor: 'rgba(248, 81, 73, 0.1)', borderRadius: '6px', border: '1px solid rgba(248, 81, 73, 0.4)' }}>
          {error}
        </div>
      )}

      {selectedFile && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          backgroundColor: '#161b22',
          padding: '12px 16px',
          borderRadius: '6px',
          border: '1px solid #30363d',
          fontSize: '13px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', overflow: 'hidden' }}>
            <svg style={{ width: '20px', height: '20px', color: '#58a6ff', flexShrink: 0 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              <div style={{ color: '#c9d1d9', fontWeight: '500' }}>{selectedFile.name}</div>
              <div style={{ color: '#8b949e', fontSize: '11px', marginTop: '2px' }}>{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</div>
            </div>
          </div>
          
          {uploading ? (
            <div style={{ color: '#8b949e', fontWeight: '500' }}>{progress}%</div>
          ) : !error && (
            <button 
              onClick={handleUpload}
              style={{
                backgroundColor: '#238636',
                color: '#ffffff',
                border: '1px solid rgba(240, 246, 252, 0.1)',
                borderRadius: '6px',
                padding: '6px 12px',
                fontSize: '12px',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              Upload
            </button>
          )}
        </div>
      )}

      {uploading && (
        <div style={{ 
          width: '100%', 
          height: '6px', 
          backgroundColor: '#21262d',
          borderRadius: '3px',
          overflow: 'hidden'
        }}>
          <div style={{ 
            width: `${progress}%`, 
            height: '100%', 
            backgroundColor: '#58a6ff',
            transition: 'width 0.2s ease-out'
          }} />
        </div>
      )}
    </div>
  );
};

export default VideoUpload;
