/**
 * Events Tab - M5 correlated events with improved UX
 */
import { useSelection } from '../../context/SelectionContext';
import { EmptyState } from '../LoadingStates';

const EventsTab = ({ results, onSeek }) => {
  const { selectedItem, selectEvent } = useSelection();
  const events = results.all_events || [];

  const getEventIcon = (eventType) => {
    switch (eventType) {
      case 'high_speed_activity': return '⚡';
      case 'abnormal_movement_sequence': return '⟲';
      case 'loitering_event': return '⏱';
      case 'restricted_area_intrusion': return '⛔';
      default: return '◆';
    }
  };

  const getEventLabel = (eventType) => {
    return eventType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high': return { bg: '#f4433622', color: '#f44336', border: '#f44336' };
      case 'medium': return { bg: '#ff980022', color: '#ff9800', border: '#ff9800' };
      case 'low': return { bg: '#4caf5022', color: '#4caf50', border: '#4caf50' };
      default: return { bg: '#78909c22', color: '#78909c', border: '#78909c' };
    }
  };

  // Summarize source anomaly types (group and count)
  const summarizeAnomalyTypes = (types) => {
    if (!types || types.length === 0) return [];
    
    const counts = {};
    types.forEach(type => {
      counts[type] = (counts[type] || 0) + 1;
    });

    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1]) // Sort by count descending
      .map(([type, count]) => ({ type, count }));
  };

  const handleEventClick = (event) => {
    selectEvent(event);
    onSeek?.(event.start_timestamp);
  };

  const isSelected = (event) => {
    return selectedItem?.event_id === event.event_id;
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(2);
    return `${mins}:${secs.padStart(5, '0')}`;
  };

  return (
    <div style={{ padding: '20px', maxHeight: 'calc(100vh - 400px)', overflowY: 'auto' }}>
      <h3 style={{ margin: '0 0 20px 0', color: '#eceff1', fontSize: '15px', fontWeight: '600' }}>
        Correlated Events ({events.length})
      </h3>

      {events.length === 0 ? (
        <EmptyState
          icon="◆"
          title="No Events Detected"
          message="No correlated event patterns were identified. Events are created by M5 when multiple related anomalies form a coherent pattern."
          type="success"
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {events.map((event, index) => {
            const severityStyle = getSeverityColor(event.severity);
            const selected = isSelected(event);
            const anomalySummary = summarizeAnomalyTypes(event.source_anomaly_types);
            
            return (
              <div
                key={event.event_id || index}
                style={{
                  backgroundColor: selected ? '#263238' : '#1e2832',
                  border: selected ? `2px solid #7e57c2` : `1px solid #37474f`,
                  borderLeft: `4px solid ${severityStyle.border}`,
                  borderRadius: '8px',
                  padding: '16px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onClick={() => handleEventClick(event)}
                onMouseEnter={(e) => {
                  if (!selected) {
                    e.currentTarget.style.backgroundColor = '#263238';
                    e.currentTarget.style.borderColor = '#455a64';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!selected) {
                    e.currentTarget.style.backgroundColor = '#1e2832';
                    e.currentTarget.style.borderColor = '#37474f';
                  }
                }}
              >
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '24px' }}>{getEventIcon(event.event_type)}</span>
                      <span style={{
                        fontSize: '15px',
                        fontWeight: '600',
                        color: '#eceff1'
                      }}>
                        {getEventLabel(event.event_type)}
                      </span>
                      <span style={{
                        backgroundColor: severityStyle.bg,
                        color: severityStyle.color,
                        padding: '3px 10px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: '600',
                        textTransform: 'uppercase',
                        border: `1px solid ${severityStyle.border}44`
                      }}>
                        {event.severity}
                      </span>
                      {event.confidence !== undefined && event.confidence !== null && (
                        <span style={{
                          backgroundColor: '#263238',
                          color: '#90a4ae',
                          padding: '3px 10px',
                          borderRadius: '6px',
                          fontSize: '11px',
                          fontWeight: '500'
                        }}>
                          {(event.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Time Range & Duration */}
                <div style={{ 
                  backgroundColor: '#0d1117', 
                  padding: '10px 12px', 
                  borderRadius: '6px',
                  marginBottom: '12px',
                  border: '1px solid #263238'
                }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr auto', gap: '12px', alignItems: 'center', fontSize: '12px' }}>
                    <div>
                      <div style={{ color: '#78909c', marginBottom: '2px', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Start</div>
                      <div 
                        style={{ color: '#7e57c2', fontWeight: '600', cursor: 'pointer', textDecoration: 'underline' }}
                        onClick={(e) => { e.stopPropagation(); onSeek?.(event.start_timestamp); }}
                      >
                        {formatTime(event.start_timestamp)}
                      </div>
                    </div>
                    
                    {/* Duration Bar */}
                    <div style={{ 
                      width: '80px', 
                      height: '4px', 
                      backgroundColor: '#263238', 
                      borderRadius: '2px',
                      position: 'relative',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        position: 'absolute',
                        left: 0,
                        top: 0,
                        height: '100%',
                        width: '100%',
                        backgroundColor: severityStyle.border,
                        opacity: 0.7
                      }} />
                    </div>
                    
                    <div>
                      <div style={{ color: '#78909c', marginBottom: '2px', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>End</div>
                      <div 
                        style={{ color: '#7e57c2', fontWeight: '600', cursor: 'pointer', textDecoration: 'underline' }}
                        onClick={(e) => { e.stopPropagation(); onSeek?.(event.end_timestamp); }}
                      >
                        {formatTime(event.end_timestamp)}
                      </div>
                    </div>
                    
                    <div style={{ 
                      backgroundColor: '#263238', 
                      padding: '6px 10px', 
                      borderRadius: '4px',
                      textAlign: 'center'
                    }}>
                      <div style={{ color: '#78909c', fontSize: '10px', marginBottom: '2px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Duration</div>
                      <div style={{ color: '#eceff1', fontWeight: '600', fontSize: '13px' }}>
                        {event.duration_seconds?.toFixed(2)}s
                      </div>
                    </div>
                  </div>
                </div>

                {/* Participating Tracks */}
                {event.participating_track_ids && event.participating_track_ids.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontSize: '11px', color: '#78909c', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      Participating Tracks
                    </div>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {event.participating_track_ids.map(trackId => (
                        <span key={trackId} style={{
                          backgroundColor: '#263238',
                          color: '#7e57c2',
                          padding: '4px 10px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: '500',
                          border: '1px solid #37474f'
                        }}>
                          Track #{trackId}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Source Anomalies Summary */}
                {anomalySummary.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontSize: '11px', color: '#78909c', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      Source Anomalies ({event.source_anomaly_ids?.length || anomalySummary.reduce((sum, a) => sum + a.count, 0)} total)
                    </div>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {anomalySummary.map(({ type, count }) => (
                        <span key={type} style={{
                          backgroundColor: '#0d1117',
                          color: '#ff9800',
                          padding: '5px 10px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: '500',
                          border: '1px solid #263238',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}>
                          <span>{type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                          <span style={{
                            backgroundColor: '#ff980033',
                            color: '#ff9800',
                            padding: '2px 6px',
                            borderRadius: '3px',
                            fontSize: '10px',
                            fontWeight: '700',
                            border: '1px solid #ff980044'
                          }}>
                            ×{count}
                          </span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Explanation */}
                {event.explanation && (
                  <div style={{
                    fontSize: '12px',
                    color: '#b0bec5',
                    lineHeight: '1.6',
                    padding: '10px',
                    backgroundColor: '#0d1117',
                    borderRadius: '6px',
                    border: '1px solid #263238',
                    marginBottom: '8px'
                  }}>
                    {event.explanation}
                  </div>
                )}

                {/* Expandable Evidence */}
                {event.evidence && Object.keys(event.evidence).length > 0 && (
                  <details style={{ marginTop: '8px' }}>
                    <summary style={{
                      cursor: 'pointer',
                      fontSize: '11px',
                      color: '#78909c',
                      padding: '6px 0',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                      userSelect: 'none'
                    }}>
                      ⊗ View Evidence Details
                    </summary>
                    <div style={{
                      marginTop: '8px',
                      padding: '10px',
                      backgroundColor: '#0d1117',
                      borderRadius: '6px',
                      border: '1px solid #263238',
                      fontSize: '11px',
                      fontFamily: 'monospace'
                    }}>
                      {Object.entries(event.evidence).map(([key, value]) => (
                        <div key={key} style={{ marginBottom: '4px', color: '#b0bec5' }}>
                          <span style={{ color: '#78909c' }}>{key}:</span>{' '}
                          <span style={{ color: '#eceff1' }}>
                            {typeof value === 'number' ? value.toFixed(2) : 
                             Array.isArray(value) ? value.join(', ') : 
                             typeof value === 'object' ? JSON.stringify(value) : value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default EventsTab;
