/**
 * Evidence Panel Component
 * Displays provenance, evidence, and metadata for selected items
 * Shows clear distinction between Observed, Derived, and AI-generated data
 */

const EvidencePanel = ({ item, type, onClose, onSeek }) => {
  if (!item) return null;

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high': return '#d32f2f';
      case 'medium': return '#f57c00';
      case 'low': return '#388e3c';
      default: return '#757575';
    }
  };

  const formatTimestamp = (timestamp) => {
    if (timestamp === undefined || timestamp === null) return 'N/A';
    const mins = Math.floor(timestamp / 60);
    const secs = (timestamp % 60).toFixed(2);
    return `${mins}:${secs.padStart(5, '0')}`;
  };

  const renderAnomalyEvidence = (anomaly) => (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '20px', borderBottom: '2px solid #37474f', paddingBottom: '15px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: '11px', color: '#90a4ae', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Anomaly Detection
            </div>
            <div style={{ fontSize: '18px', fontWeight: '600', color: '#eceff1', marginBottom: '8px' }}>
              {anomaly.anomaly_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </div>
            <div style={{ fontSize: '13px', color: '#b0bec5' }}>
              Track #{anomaly.track_id} • {formatTimestamp(anomaly.timestamp)}
            </div>
          </div>
          <div style={{
            padding: '6px 14px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            backgroundColor: getSeverityColor(anomaly.severity) + '22',
            color: getSeverityColor(anomaly.severity),
            border: `1px solid ${getSeverityColor(anomaly.severity)}44`
          }}>
            {anomaly.severity?.toUpperCase()}
          </div>
        </div>
      </div>

      {/* Observed Data */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ 
          fontSize: '12px', 
          fontWeight: '600', 
          color: '#b0bec5', 
          marginBottom: '10px',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          ⊕ Observed Measurements
        </div>
        <div style={{ backgroundColor: '#263238', padding: '12px', borderRadius: '6px', fontSize: '13px', lineHeight: '1.6' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '8px', color: '#cfd8dc' }}>
            <span style={{ color: '#90a4ae' }}>Timestamp:</span>
            <span 
              onClick={() => onSeek?.(anomaly.timestamp)}
              style={{ color: '#58a6ff', cursor: 'pointer', textDecoration: 'underline' }}
            >
              {formatTimestamp(anomaly.timestamp)} ({anomaly.timestamp.toFixed(3)}s)
            </span>
            
            <span style={{ color: '#90a4ae' }}>Track ID:</span>
            <span>{anomaly.track_id}</span>
            
            {anomaly.frame_id !== null && anomaly.frame_id !== undefined && (
              <>
                <span style={{ color: '#90a4ae' }}>Frame ID:</span>
                <span>{anomaly.frame_id}</span>
              </>
            )}
            
            <span style={{ color: '#90a4ae' }}>Anomaly Score:</span>
            <span>{(anomaly.anomaly_score * 100).toFixed(1)}%</span>
            
            {anomaly.observed_value !== null && anomaly.observed_value !== undefined && (
              <>
                <span style={{ color: '#90a4ae' }}>Observed Value:</span>
                <span>{anomaly.observed_value.toFixed(2)}</span>
              </>
            )}
            
            {anomaly.threshold !== null && anomaly.threshold !== undefined && (
              <>
                <span style={{ color: '#90a4ae' }}>Threshold:</span>
                <span>{anomaly.threshold.toFixed(2)}</span>
              </>
            )}
            
            {anomaly.current_behavior_state && (
              <>
                <span style={{ color: '#90a4ae' }}>Behavior State:</span>
                <span>{anomaly.current_behavior_state.replace(/_/g, ' ')}</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Derived Evidence */}
      {anomaly.evidence && Object.keys(anomaly.evidence).length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ 
            fontSize: '12px', 
            fontWeight: '600', 
            color: '#b0bec5', 
            marginBottom: '10px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            ⊗ Derived Evidence (M4 Analysis)
          </div>
          <div style={{ backgroundColor: '#263238', padding: '12px', borderRadius: '6px', fontSize: '13px' }}>
            {Object.entries(anomaly.evidence).map(([key, value]) => (
              <div key={key} style={{ marginBottom: '6px', color: '#cfd8dc' }}>
                <span style={{ color: '#90a4ae' }}>{key.replace(/_/g, ' ')}:</span>{' '}
                <span style={{ color: '#eceff1' }}>
                  {typeof value === 'number' ? value.toFixed(2) : value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Explanation */}
      {anomaly.explanation && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ 
            fontSize: '12px', 
            fontWeight: '600', 
            color: '#b0bec5', 
            marginBottom: '10px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            ◈ System Explanation
          </div>
          <div style={{ 
            backgroundColor: '#1a237e22', 
            border: '1px solid #3949ab44',
            padding: '12px', 
            borderRadius: '6px', 
            fontSize: '13px', 
            lineHeight: '1.7',
            color: '#cfd8dc'
          }}>
            {anomaly.explanation}
          </div>
        </div>
      )}

      {/* Provenance */}
      <div style={{ borderTop: '1px solid #37474f', paddingTop: '12px', marginTop: '15px' }}>
        <div style={{ fontSize: '11px', color: '#78909c', display: 'flex', justifyContent: 'space-between' }}>
          <span>Source Module: <strong>M4 Anomaly Detection</strong></span>
          <span>Event ID: {anomaly.event_id}</span>
        </div>
      </div>
    </div>
  );

  const renderEventEvidence = (event) => (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '20px', borderBottom: '2px solid #37474f', paddingBottom: '15px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: '11px', color: '#90a4ae', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Correlated Event
            </div>
            <div style={{ fontSize: '18px', fontWeight: '600', color: '#eceff1', marginBottom: '8px' }}>
              {event.event_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </div>
            <div style={{ fontSize: '13px', color: '#b0bec5' }}>
              {formatTimestamp(event.start_timestamp)} - {formatTimestamp(event.end_timestamp)} • {event.duration_seconds.toFixed(2)}s duration
            </div>
          </div>
          <div style={{
            padding: '6px 14px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            backgroundColor: getSeverityColor(event.severity) + '22',
            color: getSeverityColor(event.severity),
            border: `1px solid ${getSeverityColor(event.severity)}44`
          }}>
            {event.severity?.toUpperCase()}
          </div>
        </div>
      </div>

      {/* Observed Data */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ 
          fontSize: '12px', 
          fontWeight: '600', 
          color: '#b0bec5', 
          marginBottom: '10px',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          ⊕ Observed Measurements
        </div>
        <div style={{ backgroundColor: '#263238', padding: '12px', borderRadius: '6px', fontSize: '13px', lineHeight: '1.6' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '8px', color: '#cfd8dc' }}>
            <span style={{ color: '#90a4ae' }}>Start Time:</span>
            <span 
              onClick={() => onSeek?.(event.start_timestamp)}
              style={{ color: '#58a6ff', cursor: 'pointer', textDecoration: 'underline' }}
            >
              {formatTimestamp(event.start_timestamp)} ({event.start_timestamp.toFixed(3)}s)
            </span>
            
            <span style={{ color: '#90a4ae' }}>End Time:</span>
            <span 
              onClick={() => onSeek?.(event.end_timestamp)}
              style={{ color: '#58a6ff', cursor: 'pointer', textDecoration: 'underline' }}
            >
              {formatTimestamp(event.end_timestamp)} ({event.end_timestamp.toFixed(3)}s)
            </span>
            
            <span style={{ color: '#90a4ae' }}>Duration:</span>
            <span>{event.duration_seconds.toFixed(2)}s</span>
            
            <span style={{ color: '#90a4ae' }}>Participating Tracks:</span>
            <span>{event.participating_track_ids.join(', ')}</span>
            
            <span style={{ color: '#90a4ae' }}>Confidence:</span>
            <span>{(event.confidence * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {/* Source Anomalies */}
      {event.source_anomaly_ids && event.source_anomaly_ids.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ 
            fontSize: '12px', 
            fontWeight: '600', 
            color: '#b0bec5', 
            marginBottom: '10px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            ⊗ Derived from Anomalies (M5 Correlation)
          </div>
          <div style={{ backgroundColor: '#263238', padding: '12px', borderRadius: '6px', fontSize: '13px' }}>
            <div style={{ color: '#cfd8dc', marginBottom: '8px' }}>
              Correlated {event.source_anomaly_ids.length} anomaly observation(s):
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {event.source_anomaly_types.map((type, index) => (
                <span key={index} style={{
                  padding: '4px 8px',
                  backgroundColor: '#37474f',
                  borderRadius: '4px',
                  fontSize: '11px',
                  color: '#b0bec5'
                }}>
                  {type.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Evidence */}
      {event.evidence && Object.keys(event.evidence).length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ 
            fontSize: '12px', 
            fontWeight: '600', 
            color: '#b0bec5', 
            marginBottom: '10px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            ⊗ Supporting Evidence
          </div>
          <div style={{ backgroundColor: '#263238', padding: '12px', borderRadius: '6px', fontSize: '13px' }}>
            {Object.entries(event.evidence).map(([key, value]) => (
              <div key={key} style={{ marginBottom: '6px', color: '#cfd8dc' }}>
                <span style={{ color: '#90a4ae' }}>{key.replace(/_/g, ' ')}:</span>{' '}
                <span style={{ color: '#eceff1' }}>
                  {typeof value === 'number' ? value.toFixed(2) : 
                   Array.isArray(value) ? value.join(', ') : 
                   typeof value === 'object' ? JSON.stringify(value) : value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explanation */}
      {event.explanation && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ 
            fontSize: '12px', 
            fontWeight: '600', 
            color: '#b0bec5', 
            marginBottom: '10px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            ◈ System Explanation
          </div>
          <div style={{ 
            backgroundColor: '#1a237e22', 
            border: '1px solid #3949ab44',
            padding: '12px', 
            borderRadius: '6px', 
            fontSize: '13px', 
            lineHeight: '1.7',
            color: '#cfd8dc'
          }}>
            {event.explanation}
          </div>
        </div>
      )}

      {/* Provenance */}
      <div style={{ borderTop: '1px solid #37474f', paddingTop: '12px', marginTop: '15px' }}>
        <div style={{ fontSize: '11px', color: '#78909c', display: 'flex', justifyContent: 'space-between' }}>
          <span>Source Module: <strong>M5 Event Correlation</strong></span>
          <span>Event ID: {event.event_id}</span>
        </div>
      </div>
    </div>
  );

  const renderSceneEvidence = (scene) => (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '20px', borderBottom: '2px solid #37474f', paddingBottom: '15px' }}>
        <div>
          <div style={{ fontSize: '11px', color: '#90a4ae', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Contextual Scene
          </div>
          <div style={{ fontSize: '18px', fontWeight: '600', color: '#eceff1', marginBottom: '8px' }}>
            Scene #{scene.scene_number}
          </div>
          <div style={{ fontSize: '13px', color: '#b0bec5' }}>
            {formatTimestamp(scene.start_timestamp)} - {formatTimestamp(scene.end_timestamp)} • {scene.duration_seconds.toFixed(2)}s duration
          </div>
        </div>
      </div>

      {/* Scene Summary */}
      {scene.scene_summary && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ 
            fontSize: '12px', 
            fontWeight: '600', 
            color: '#b0bec5', 
            marginBottom: '10px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            ⊗ Scene Summary (M8 Synthesis)
          </div>
          <div style={{ 
            backgroundColor: '#1a237e22', 
            border: '1px solid #3949ab44',
            padding: '12px', 
            borderRadius: '6px', 
            fontSize: '13px', 
            lineHeight: '1.7',
            color: '#cfd8dc'
          }}>
            {scene.scene_summary}
          </div>
        </div>
      )}

      {/* Key Observations */}
      {scene.key_observations && scene.key_observations.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ 
            fontSize: '12px', 
            fontWeight: '600', 
            color: '#b0bec5', 
            marginBottom: '10px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            ⊕ Key Observations
          </div>
          <div style={{ backgroundColor: '#263238', padding: '12px', borderRadius: '6px', fontSize: '13px' }}>
            <ul style={{ margin: 0, paddingLeft: '20px', color: '#cfd8dc', lineHeight: '1.7' }}>
              {scene.key_observations.map((obs, idx) => (
                <li key={idx}>{obs}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Track Summaries */}
      {scene.track_summaries && Object.keys(scene.track_summaries).length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ 
            fontSize: '12px', 
            fontWeight: '600', 
            color: '#b0bec5', 
            marginBottom: '10px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            ⊕ Track Summaries
          </div>
          <div style={{ backgroundColor: '#263238', padding: '12px', borderRadius: '6px', fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {Object.entries(scene.track_summaries).map(([trackId, summary]) => (
              <div key={trackId} style={{ color: '#cfd8dc' }}>
                <div style={{ fontWeight: '600', color: '#58a6ff', marginBottom: '4px' }}>
                  Track {trackId}:
                </div>
                <div style={{ paddingLeft: '12px', fontSize: '12px' }}>
                  {summary}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evidence Provenance */}
      {scene.evidence_provenance && scene.evidence_provenance.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ 
            fontSize: '12px', 
            fontWeight: '600', 
            color: '#b0bec5', 
            marginBottom: '10px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            ⊗ Evidence Provenance
          </div>
          <div style={{ backgroundColor: '#263238', padding: '12px', borderRadius: '6px', fontSize: '11px' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {scene.evidence_provenance.map((source, idx) => (
                <span key={idx} style={{
                  padding: '4px 8px',
                  backgroundColor: '#37474f',
                  borderRadius: '4px',
                  color: '#b0bec5'
                }}>
                  {source}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Provenance */}
      <div style={{ borderTop: '1px solid #37474f', paddingTop: '12px', marginTop: '15px' }}>
        <div style={{ fontSize: '11px', color: '#78909c', display: 'flex', justifyContent: 'space-between' }}>
          <span>Source Module: <strong>M8 Contextual Synthesis</strong></span>
          <span>Scene ID: {scene.scene_id}</span>
        </div>
      </div>
    </div>
  );

  const renderTrackEvidence = (track) => (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '20px', borderBottom: '2px solid #37474f', paddingBottom: '15px' }}>
        <div>
          <div style={{ fontSize: '11px', color: '#90a4ae', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Tracked Entity
          </div>
          <div style={{ fontSize: '18px', fontWeight: '600', color: '#eceff1', marginBottom: '8px' }}>
            Track #{track.track_id}
          </div>
          <div style={{ fontSize: '13px', color: '#b0bec5' }}>
            {track.class_name} • {track.observations} observations • {track.duration.toFixed(2)}s duration
          </div>
        </div>
      </div>

      {/* Observed Data */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ 
          fontSize: '12px', 
          fontWeight: '600', 
          color: '#b0bec5', 
          marginBottom: '10px',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          ⊕ Tracking Metrics (M2 + M3)
        </div>
        <div style={{ backgroundColor: '#263238', padding: '12px', borderRadius: '6px', fontSize: '13px', lineHeight: '1.6' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '8px', color: '#cfd8dc' }}>
            <span style={{ color: '#90a4ae' }}>First Seen:</span>
            <span 
              onClick={() => onSeek?.(track.first_timestamp)}
              style={{ color: '#58a6ff', cursor: 'pointer', textDecoration: 'underline' }}
            >
              {formatTimestamp(track.first_timestamp)} ({track.first_timestamp.toFixed(3)}s)
            </span>
            
            <span style={{ color: '#90a4ae' }}>Last Seen:</span>
            <span 
              onClick={() => onSeek?.(track.last_timestamp)}
              style={{ color: '#58a6ff', cursor: 'pointer', textDecoration: 'underline' }}
            >
              {formatTimestamp(track.last_timestamp)} ({track.last_timestamp.toFixed(3)}s)
            </span>
            
            <span style={{ color: '#90a4ae' }}>Observations:</span>
            <span>{track.observations} frames</span>
            
            <span style={{ color: '#90a4ae' }}>Average Speed:</span>
            <span>{track.avg_speed.toFixed(1)} px/s</span>
            
            <span style={{ color: '#90a4ae' }}>Maximum Speed:</span>
            <span>{track.max_speed.toFixed(1)} px/s</span>
            
            {track.states_list && track.states_list.length > 0 && (
              <>
                <span style={{ color: '#90a4ae' }}>Behavior States:</span>
                <span>{track.states_list.join(', ')}</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Provenance */}
      <div style={{ borderTop: '1px solid #37474f', paddingTop: '12px', marginTop: '15px' }}>
        <div style={{ fontSize: '11px', color: '#78909c' }}>
          Source Modules: <strong>M2 Tracking + M3 Behaviour Analysis</strong>
        </div>
      </div>
    </div>
  );

  return (
    <div style={{
      backgroundColor: '#1e2832',
      borderTop: '2px solid #37474f',
      color: '#eceff1',
      boxShadow: '0 -4px 12px rgba(0,0,0,0.4)'
    }}>
      <div style={{
        padding: '20px 30px',
        maxHeight: '400px',
        overflowY: 'auto'
      }}>
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '15px',
            right: '25px',
            background: 'none',
            border: 'none',
            color: '#90a4ae',
            fontSize: '24px',
            cursor: 'pointer',
            padding: '5px 10px',
            lineHeight: '1',
            transition: 'color 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.color = '#eceff1'}
          onMouseLeave={(e) => e.currentTarget.style.color = '#90a4ae'}
          title="Close evidence panel"
        >
          ×
        </button>

        {/* Content */}
        {type === 'anomaly' && renderAnomalyEvidence(item)}
        {type === 'event' && renderEventEvidence(item)}
        {type === 'scene' && renderSceneEvidence(item)}
        {type === 'track' && renderTrackEvidence(item)}
      </div>
    </div>
  );
};

export default EvidencePanel;
