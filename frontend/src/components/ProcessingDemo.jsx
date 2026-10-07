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

  // If we have results, switch entirely to DashboardView
  if (results && currentJob) {
    return <DashboardView jobId={currentJob.job_id} results={results} onBack={handleReset} />;
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0d1117',
      color: '#eceff1',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#161b22',
        borderBottom: '1px solid #263238',
        padding: '16px 30px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.4)'
      }}>
        <h1 style={{ margin: 0, fontSize: '22px', fontWeight: '600', letterSpacing: '-0.3px' }}>
          Flagship 107
        </h1>
        <div style={{
          padding: '4px 10px',
          backgroundColor: '#58a6ff22',
          border: '1px solid #58a6ff44',
          borderRadius: '6px',
          fontSize: '11px',
          fontWeight: '600',
          color: '#58a6ff',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          AI Video Intelligence
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px'
      }}>
        <div style={{
          backgroundColor: '#161b22',
          border: '1px solid #30363d',
          borderRadius: '12px',
          padding: '40px',
          width: '100%',
          maxWidth: '600px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.5)'
        }}>
          <h2 style={{ marginTop: 0, marginBottom: '8px', fontSize: '24px', fontWeight: '500' }}>
            New Investigation
          </h2>
          <p style={{ color: '#8b949e', fontSize: '14px', marginBottom: '32px' }}>
            Upload a video to initiate automated behavioral analysis and anomaly detection.
          </p>

          {/* Step 1: Upload */}
          {!currentJob && (
            <VideoUpload onUploadComplete={handleUploadComplete} />
          )}

          {/* Step 2: Start Processing */}
          {currentJob && !polling && !results && (
            <div>
              <div style={{
                backgroundColor: '#0d1117',
                border: '1px solid #30363d',
                borderRadius: '8px',
                padding: '16px',
                marginBottom: '24px'
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '13px' }}>
                  <div style={{ color: '#8b949e' }}>Job ID</div>
                  <div style={{ fontFamily: 'monospace' }}>{currentJob.job_id.split('-')[0]}...</div>
                  
                  <div style={{ color: '#8b949e' }}>Filename</div>
                  <div>{currentJob.filename}</div>
                  
                  <div style={{ color: '#8b949e' }}>Duration</div>
                  <div>{currentJob.video_duration?.toFixed(2)}s</div>
                  
                  <div style={{ color: '#8b949e' }}>Resolution</div>
                  <div>{currentJob.video_width}x{currentJob.video_height}</div>
                  
                  <div style={{ color: '#8b949e' }}>Framerate</div>
                  <div>{currentJob.video_fps?.toFixed(2)} FPS</div>
                </div>
              </div>
              
              <div style={{ display: 'flex', gap: '12px' }}>
                <button 
                  onClick={handleStartProcessing} 
                  style={{
                    flex: 1,
                    backgroundColor: '#238636',
                    color: '#ffffff',
                    border: '1px solid rgba(240, 246, 252, 0.1)',
                    borderRadius: '6px',
                    padding: '10px 16px',
                    fontSize: '14px',
                    fontWeight: '500',
                    cursor: 'pointer'
                  }}
                >
                  Start Processing Pipeline
                </button>
                <button 
                  onClick={handleReset} 
                  style={{
                    backgroundColor: '#21262d',
                    color: '#c9d1d9',
                    border: '1px solid #30363d',
                    borderRadius: '6px',
                    padding: '10px 16px',
                    fontSize: '14px',
                    fontWeight: '500',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Processing Status */}
          {polling && status && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', fontSize: '14px' }}>
                <strong style={{ color: '#c9d1d9' }}>
                  {status.status === 'processing' ? 'Processing Pipeline Active' : 'Finalizing...'}
                </strong>
                <span style={{ color: '#8b949e' }}>
                  {status.progress !== null && status.progress !== undefined 
                    ? `${status.progress.toFixed(1)}%` 
                    : ''}
                </span>
              </div>
              
              {status.progress !== null && status.progress !== undefined && (
                <div style={{ 
                  width: '100%', 
                  height: '8px', 
                  backgroundColor: '#21262d',
                  borderRadius: '4px',
                  overflow: 'hidden',
                  marginBottom: '16px',
                  border: '1px solid #30363d'
                }}>
                  <div style={{ 
                    width: `${status.progress}%`, 
                    height: '100%', 
                    backgroundColor: '#238636',
                    transition: 'width 0.3s ease-out'
                  }} />
                </div>
              )}
              
              {status.message && (
                <div style={{ fontSize: '13px', color: '#8b949e', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ 
                    display: 'inline-block', 
                    width: '12px', 
                    height: '12px', 
                    border: '2px solid #238636', 
                    borderTopColor: 'transparent',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></span>
                  {status.message}
                </div>
              )}
              
              <style>{`
                @keyframes spin { 100% { transform: rotate(360deg); } }
              `}</style>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div style={{ 
              backgroundColor: 'rgba(248, 81, 73, 0.1)', 
              border: '1px solid rgba(248, 81, 73, 0.4)',
              color: '#ff7b72', 
              padding: '16px', 
              borderRadius: '6px',
              marginTop: '24px',
              fontSize: '13px'
            }}>
              <strong>Error:</strong> {error}
              <button 
                onClick={handleReset}
                style={{
                  display: 'block',
                  marginTop: '12px',
                  backgroundColor: 'transparent',
                  border: '1px solid #ff7b72',
                  color: '#ff7b72',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProcessingDemo;
