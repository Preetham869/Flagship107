/**
 * Processing Demo Component
 * Demonstrates upload -> process -> status -> results workflow
 */
import { useState, useEffect } from 'react';
import VideoUpload from './VideoUpload';
import DashboardView from './DashboardView';
import { processVideo, getJobStatus, getJobResults } from '../services/api';

const ProcessingDemo = () => {
  const [currentJob, setCurrentJob] = useState(null);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [polling, setPolling] = useState(false);

  // Poll job status
  useEffect(() => {
    if (!currentJob || !polling) return;

    const pollInterval = setInterval(async () => {
      try {
        const statusData = await getJobStatus(currentJob.job_id);
        setStatus(statusData);

        // If completed, fetch results and stop polling
        if (statusData.status === 'completed') {
          setPolling(false);
          const resultsData = await getJobResults(currentJob.job_id);
          setResults(resultsData);
        }

        // If failed, stop polling
        if (statusData.status === 'failed') {
          setPolling(false);
          setError(statusData.error || 'Processing failed');
        }
      } catch (err) {
        console.error('Status polling error:', err);
        setError('Failed to check status');
        setPolling(false);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [currentJob, polling]);

  const handleUploadComplete = (uploadResponse) => {
    console.log('Upload complete:', uploadResponse);
    setCurrentJob(uploadResponse);
    setStatus(null);
    setResults(null);
    setError(null);
  };

  const handleStartProcessing = async () => {
    if (!currentJob) return;

    setError(null);
    setPolling(true);

    try {
      const response = await processVideo(currentJob.job_id, {
        frameSkip: 1,
        confidenceThreshold: 0.5,
        personOnly: false,
      });
      
      setStatus(response);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start processing');
      setPolling(false);
      console.error('Processing error:', err);
    }
  };

  const handleReset = () => {
    setCurrentJob(null);
    setStatus(null);
    setResults(null);
    setError(null);
    setPolling(false);
  };

  return (
    <div className="processing-demo" style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Video Processing Demo</h2>

      {/* Step 1: Upload */}
      {!currentJob && (
        <div className="step">
          <h3>Step 1: Upload Video</h3>
          <VideoUpload onUploadComplete={handleUploadComplete} />
        </div>
      )}

      {/* Step 2: Start Processing */}
      {currentJob && !polling && !results && (
        <div className="step">
          <h3>Step 2: Start Processing</h3>
          <div className="job-info">
            <p><strong>Job ID:</strong> {currentJob.job_id}</p>
            <p><strong>Filename:</strong> {currentJob.filename}</p>
            <p><strong>Duration:</strong> {currentJob.video_duration?.toFixed(2)}s</p>
            <p><strong>Resolution:</strong> {currentJob.video_width}x{currentJob.video_height}</p>
            <p><strong>FPS:</strong> {currentJob.video_fps?.toFixed(2)}</p>
          </div>
          <button onClick={handleStartProcessing} style={{ marginTop: '10px' }}>
            Start Processing
          </button>
          <button onClick={handleReset} style={{ marginLeft: '10px', marginTop: '10px' }}>
            Upload Different Video
          </button>
        </div>
      )}

      {/* Step 3: Processing Status */}
      {polling && status && (
        <div className="step">
          <h3>Step 3: Processing...</h3>
          <div className="status-info">
            <p><strong>Status:</strong> {status.status}</p>
            {status.progress !== null && status.progress !== undefined && (
              <div>
                <p><strong>Progress:</strong> {status.progress.toFixed(1)}%</p>
                <div className="progress-bar" style={{ 
                  width: '100%', 
                  height: '20px', 
                  backgroundColor: '#ddd',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{ 
                    width: `${status.progress}%`, 
                    height: '100%', 
                    backgroundColor: '#4CAF50',
                    transition: 'width 0.3s'
                  }} />
                </div>
              </div>
            )}
            {status.message && <p><strong>Message:</strong> {status.message}</p>}
          </div>
        </div>
      )}

      {/* Step 4: Dashboard View with Video Player and Timeline */}
      {results && currentJob && (
        <DashboardView
          jobId={currentJob.job_id}
          results={results}
          onBack={handleReset}
        />
      )}

      {/* Error Display */}
      {error && (
        <div className="error" style={{ 
          backgroundColor: '#ffebee', 
          color: '#c62828', 
          padding: '15px', 
          borderRadius: '4px',
          marginTop: '15px'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
};

export default ProcessingDemo;
