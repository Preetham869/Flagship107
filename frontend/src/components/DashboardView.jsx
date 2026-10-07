/**
 * Dashboard View Component
 * Professional AI Video Intelligence Dashboard
 * Main view after processing completes - video-centric layout with evidence panel
 */
import { useState, useEffect, useCallback } from 'react';
import VideoPlayer from './VideoPlayer';
import EventTimeline from './EventTimeline';
import IntelligencePanel from './intelligence/IntelligencePanel';
import InvestigationPanel from './InvestigationPanel';
import EvidencePanel from './EvidencePanel';
import SystemStatus from './SystemStatus';
import InvestigationHeader from './InvestigationHeader';
import { getVideoUrl } from '../services/api';
import { SelectionProvider, useSelection } from '../context/SelectionContext';

const DashboardContent = ({ jobId, results, onBack }) => {
  const [currentTime, setCurrentTime] = useState(0);
  const [seekToTime, setSeekToTime] = useState(null);
  const { selectedItem, selectedType, clearSelection } = useSelection();

  const handleTimeUpdate = (time) => {
    setCurrentTime(time);
  };

  const handleSeek = useCallback((timestamp) => {
    setSeekToTime(timestamp);
    setTimeout(() => setSeekToTime(null), 100);
  }, []);

  // Auto-seek when selection changes
  useEffect(() => {
    if (!selectedItem) return;

    let timestamp = null;
    if (selectedType === 'event' && selectedItem.start_timestamp !== undefined) {
      timestamp = selectedItem.start_timestamp;
    } else if (selectedType === 'anomaly' && selectedItem.timestamp !== undefined) {
      timestamp = selectedItem.timestamp;
    } else if (selectedType === 'scene' && selectedItem.start_timestamp !== undefined) {
      timestamp = selectedItem.start_timestamp;
    } else if (selectedType === 'track' && selectedItem.first_seen !== undefined) {
      timestamp = selectedItem.first_seen;
    } else if (selectedType === 'relationship' && selectedItem.start_timestamp !== undefined) {
      timestamp = selectedItem.start_timestamp;
    }

    if (timestamp !== null) {
      handleSeek(timestamp);
    }
  }, [selectedItem, selectedType, handleSeek]);

  const videoUrl = getVideoUrl(jobId);

  return (
    <div style={{ 
      minHeight: '100vh',
      backgroundColor: '#0d1117',
      color: '#eceff1'
    }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#161b22',
        borderBottom: '1px solid #263238',
        padding: '16px 30px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.4)'
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '14px'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <h1 style={{ 
                margin: 0, 
                fontSize: '22px', 
                fontWeight: '600',
                color: '#eceff1',
                letterSpacing: '-0.3px'
              }}>
                Flagship 107
              </h1>
              <div style={{
                padding: '4px 10px',
                backgroundColor: '#7e57c222',
                border: '1px solid #7e57c244',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: '600',
                color: '#7e57c2',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                AI Video Intelligence
              </div>
            </div>
            <div style={{ fontSize: '13px', color: '#78909c', marginTop: '6px' }}>
              Validated Hackathon Prototype • HackNEX 2026
            </div>
          </div>
          <button
            onClick={onBack}
            style={{
              padding: '10px 20px',
              backgroundColor: '#263238',
              color: '#b0bec5',
              border: '1px solid #37474f',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: '500',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#2d3a42';
              e.currentTarget.style.borderColor = '#455a64';
              e.currentTarget.style.color = '#eceff1';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#263238';
              e.currentTarget.style.borderColor = '#37474f';
              e.currentTarget.style.color = '#b0bec5';
            }}
          >
            ← Back to Upload
          </button>
        </div>

        {/* System Status */}
        <SystemStatus results={results} />
      </div>

      {/* Main Content */}
      <div style={{ padding: '24px 30px' }}>
        {/* Investigation Header */}
        <InvestigationHeader />

        {/* Main Grid Layout */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1.4fr 1fr',
          gap: '24px',
          marginBottom: '24px',
          minHeight: '600px'
        }}>
          {/* Left Column: Video + Timeline */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <VideoPlayer
              videoUrl={videoUrl}
              onTimeUpdate={handleTimeUpdate}
              currentTime={seekToTime}
              selectedItem={selectedItem}
              selectedType={selectedType}
              videoMetadata={results}
              allTracks={results.all_tracks || []}
            />
            
            <EventTimeline
              anomalies={results.all_anomalies || []}
              events={results.all_events || []}
              videoDuration={results.video_duration}
              currentTime={currentTime}
              onSeek={handleSeek}
              selectedItem={selectedItem}
            />
          </div>

          {/* Right Column: Investigation/Intelligence Panel */}
          <div>
            {selectedItem ? (
              <InvestigationPanel
                results={results}
                onSeek={handleSeek}
                jobId={jobId}
              />
            ) : (
              <IntelligencePanel
                results={results}
                onSeek={handleSeek}
                jobId={jobId}
              />
            )}
          </div>
        </div>

        {/* Evidence Panel (Conditional Bottom Panel) */}
        {selectedItem && (
          <div style={{ marginBottom: '24px' }}>
            <EvidencePanel
              item={selectedItem}
              type={selectedType}
              onClose={clearSelection}
              onSeek={handleSeek}
            />
          </div>
        )}

        {/* Full Results (Collapsible) */}
        <div style={{
          backgroundColor: '#161b22',
          borderRadius: '8px',
          border: '1px solid #263238',
          overflow: 'hidden',
          boxShadow: '0 2px 8px rgba(0,0,0,0.4)'
        }}>
          <details>
            <summary style={{ 
              cursor: 'pointer', 
              padding: '16px 20px',
              backgroundColor: '#1e2832',
              fontWeight: '500',
              fontSize: '13px',
              color: '#b0bec5',
              userSelect: 'none',
              borderBottom: '1px solid #263238'
            }}>
              Full JSON Results (Developer View)
            </summary>
            <pre style={{ 
              backgroundColor: '#0d1117', 
              color: '#b0bec5', 
              padding: '20px', 
              margin: 0,
              overflow: 'auto',
              maxHeight: '500px',
              fontSize: '11px',
              fontFamily: '"Consolas", "Monaco", "Courier New", monospace',
              lineHeight: '1.5'
            }}>
              {JSON.stringify(results, null, 2)}
            </pre>
          </details>
        </div>
      </div>
    </div>
  );
};

// Wrapper with SelectionProvider
const DashboardView = (props) => (
  <SelectionProvider>
    <DashboardContent {...props} />
  </SelectionProvider>
);

export default DashboardView;
