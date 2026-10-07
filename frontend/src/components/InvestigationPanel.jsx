/**
 * Investigation Panel
 * Shows detailed evidence and context for selected investigation target
 */
import { useSelection } from '../context/SelectionContext';

const InvestigationPanel = ({ results, onSeek }) => {
  const { selectedItem, selectedType } = useSelection();

  if (!selectedItem) {
    return (
      <div style={{
        backgroundColor: '#161b22',
        border: '1px solid #263238',
        borderRadius: '8px',
        padding: '40px 30px',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.4 }}>🔍</div>
        <div style={{ fontSize: '16px', fontWeight: '600', color: '#a0aab8', marginBottom: '8px' }}>
          No Item Selected
        </div>
        <div style={{ fontSize: '13px', color: '#6b7485' }}>
          Select an anomaly, event, track, or scene from the timeline or intelligence tabs
        </div>
      </div>
    );
  }

  // Render based on selection type
  switch (selectedType) {
    case 'event':
      return <EventInvestigation event={selectedItem} />;
    case 'anomaly':
      return <AnomalyInvestigation anomaly={selectedItem} />;
    case 'track':
      return <TrackInvestigation track={selectedItem} results={results} onSeek={onSeek} />;
    case 'scene':
      return <SceneInvestigation scene={selectedItem} />;
    default:
      return <div>Investigation details for {selectedType}</div>;
  }
};

// Event Investigation Component
const EventInvestigation = ({ event }) => {
  return (
    <div style={{
      backgroundColor: '#161b22',
      border: '1px solid #263238',
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        backgroundColor: '#1e2832',
        borderBottom: '1px solid #263238'
      }}>
        <div style={{ fontSize: '16px', fontWeight: '600', color: '#e0e6ed' }}>
          Event Investigation
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: '20px' }}>
        {/* Observed Section */}
        <InvestigationSection title="Observed Evidence" icon="📊">
          <InfoRow label="Event Type" value={event.event_type?.replace(/_/g, ' ')} />
          <InfoRow label="Time Range" value={`${event.start_timestamp?.toFixed(2)}s → ${event.end_timestamp?.toFixed(2)}s`} />
          <InfoRow label="Duration" value={`${((event.end_timestamp - event.start_timestamp) || 0).toFixed(2)}s`} />
          <InfoRow label="Tracks Involved" value={event.track_ids?.map(id => `#${id}`).join(', ') || 'N/A'} />
          <InfoRow label="Source Anomalies" value={`${event.source_anomaly_ids?.length || 0} anomalies`} />
          
          {event.source_anomaly_types && event.source_anomaly_types.length > 0 && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ fontSize: '12px', color: '#8b95a8', marginBottom: '6px' }}>
                Anomaly Types:
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {(() => {
                  const counts = {};
                  event.source_anomaly_types.forEach(type => {
                    counts[type] = (counts[type] || 0) + 1;
                  });
                  return Object.entries(counts).map(([type, count]) => (
                    <span
                      key={type}
                      style={{
                        padding: '4px 10px',
                        backgroundColor: '#ff980022',
                        border: '1px solid #ff980044',
                        borderRadius: '4px',
                        fontSize: '11px',
                        color: '#ffb74d'
                      }}
                    >
                      {type.replace(/_/g, ' ')} × {count}
                    </span>
                  ));
                })()}
              </div>
            </div>
          )}
        </InvestigationSection>

        {/* Derived Section */}
        <InvestigationSection title="Derived Analysis" icon="🔍">
          <InfoRow label="Severity" value={event.severity} badge={true} badgeColor={getSeverityColor(event.severity)} />
          <InfoRow label="Confidence" value={event.confidence !== undefined ? `${(event.confidence * 100).toFixed(0)}%` : 'N/A'} />
          <InfoRow label="Source Module" value="M5: Event Correlation" />
          
          {event.description && (
            <div style={{
              marginTop: '12px',
              padding: '12px',
              backgroundColor: '#0d1220',
              borderRadius: '6px',
              border: '1px solid #1a2332',
              fontSize: '13px',
              color: '#d4dae3',
              lineHeight: '1.6'
            }}>
              {event.description}
            </div>
          )}
        </InvestigationSection>

        {/* Evidence Chain */}
        <InvestigationSection title="Evidence Chain" icon="🔗">
          <EvidenceChain 
            steps={[
              { module: 'M1', label: 'Detection', description: 'Object detected in video frames' },
              { module: 'M2', label: 'Tracking', description: `Track ID: ${event.track_ids?.[0] || '?'}` },
              { module: 'M3', label: 'Behavior', description: 'Speed/direction measurements' },
              { module: 'M4', label: 'Anomaly', description: `${event.source_anomaly_ids?.length || 0} anomalies detected` },
              { module: 'M5', label: 'Event', description: 'Correlated into event', active: true },
            ]}
          />
        </InvestigationSection>
      </div>
    </div>
  );
};

// Anomaly Investigation Component
const AnomalyInvestigation = ({ anomaly }) => {
  return (
    <div style={{
      backgroundColor: '#161b22',
      border: '1px solid #263238',
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      <div style={{
        padding: '16px 20px',
        backgroundColor: '#1e2832',
        borderBottom: '1px solid #263238'
      }}>
        <div style={{ fontSize: '16px', fontWeight: '600', color: '#e0e6ed' }}>
          Anomaly Investigation
        </div>
      </div>

      <div style={{ padding: '20px' }}>
        <InvestigationSection title="Observed Evidence" icon="📊">
          <InfoRow label="Anomaly Type" value={anomaly.anomaly_type?.replace(/_/g, ' ')} />
          <InfoRow label="Timestamp" value={`${anomaly.timestamp?.toFixed(2)}s`} />
          <InfoRow label="Track ID" value={`#${anomaly.track_id}`} />
          <InfoRow label="Frame ID" value={anomaly.frame_id || 'N/A'} />
          
          {anomaly.evidence && (
            <div style={{ marginTop: '12px' }}>
              {anomaly.evidence.previous_speed !== undefined && (
                <InfoRow label="Previous Speed" value={`${anomaly.evidence.previous_speed.toFixed(1)} px/s`} />
              )}
              {anomaly.evidence.current_speed !== undefined && (
                <InfoRow label="Current Speed" value={`${anomaly.evidence.current_speed.toFixed(1)} px/s`} />
              )}
              {anomaly.evidence.speed_change !== undefined && (
                <InfoRow label="Speed Change" value={`${anomaly.evidence.speed_change.toFixed(1)} px/s`} />
              )}
            </div>
          )}
        </InvestigationSection>

        <InvestigationSection title="Derived Analysis" icon="🔍">
          <InfoRow label="Severity" value={anomaly.severity} badge={true} badgeColor={getSeverityColor(anomaly.severity)} />
          <InfoRow label="Anomaly Score" value={anomaly.anomaly_score !== undefined ? `${(anomaly.anomaly_score * 100).toFixed(0)}%` : 'N/A'} />
          <InfoRow label="Source Module" value="M4: Anomaly Detection" />
          
          {anomaly.description && (
            <div style={{
              marginTop: '12px',
              padding: '12px',
              backgroundColor: '#0d1220',
              borderRadius: '6px',
              border: '1px solid #1a2332',
              fontSize: '13px',
              color: '#d4dae3',
              lineHeight: '1.6'
            }}>
              {anomaly.description}
            </div>
          )}
        </InvestigationSection>

        <InvestigationSection title="Evidence Chain" icon="🔗">
          <EvidenceChain 
            steps={[
              { module: 'M1', label: 'Detection', description: 'Object detected' },
              { module: 'M2', label: 'Tracking', description: `Track #${anomaly.track_id}` },
              { module: 'M3', label: 'Behavior', description: 'Speed measured' },
              { module: 'M4', label: 'Anomaly', description: 'Flagged as unusual', active: true },
            ]}
          />
        </InvestigationSection>
      </div>
    </div>
  );
};

// Track Investigation Component
const TrackInvestigation = ({ track, results, onSeek }) => {
  // Find related anomalies
  const relatedAnomalies = (results.all_anomalies || []).filter(
    a => a.track_id === (track.track_id || track.id)
  );

  return (
    <div style={{
      backgroundColor: '#161b22',
      border: '1px solid #263238',
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      <div style={{
        padding: '16px 20px',
        backgroundColor: '#1e2832',
        borderBottom: '1px solid #263238'
      }}>
        <div style={{ fontSize: '16px', fontWeight: '600', color: '#e0e6ed' }}>
          Track Investigation
        </div>
      </div>

      <div style={{ padding: '20px' }}>
        <InvestigationSection title="Track Information" icon="👤">
          <InfoRow label="Track ID" value={`#${track.track_id || track.id}`} />
          <InfoRow label="Class" value={track.class_name || 'Unknown'} />
          <InfoRow label="First Seen" value={track.first_seen !== undefined ? `${track.first_seen.toFixed(2)}s` : 'N/A'} />
          <InfoRow label="Last Seen" value={track.last_seen !== undefined ? `${track.last_seen.toFixed(2)}s` : 'N/A'} />
          <InfoRow label="Duration" value={track.duration !== undefined ? `${track.duration.toFixed(2)}s` : 'N/A'} />
          <InfoRow label="Observations" value={track.observation_count || 'N/A'} />
        </InvestigationSection>

        <InvestigationSection title="Behavior Metrics" icon="📈">
          <InfoRow label="Avg Speed" value={track.avg_speed !== undefined ? `${track.avg_speed.toFixed(1)} px/s` : 'N/A'} />
          <InfoRow label="Max Speed" value={track.max_speed !== undefined ? `${track.max_speed.toFixed(1)} px/s` : 'N/A'} />
          <InfoRow label="Dominant State" value={track.dominant_state || 'N/A'} />
          <InfoRow label="Trajectory" value={track.trajectory_type || 'N/A'} />
        </InvestigationSection>

        <InvestigationSection title="Related Anomalies" icon="⚠">
          {relatedAnomalies.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {relatedAnomalies.map((anomaly, idx) => (
                <div
                  key={idx}
                  onClick={() => onSeek?.(anomaly.timestamp)}
                  style={{
                    padding: '10px 12px',
                    backgroundColor: '#0d1220',
                    border: '1px solid #1a2332',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#1a2332';
                    e.currentTarget.style.borderColor = '#243447';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#0d1220';
                    e.currentTarget.style.borderColor = '#1a2332';
                  }}
                >
                  <div style={{ fontSize: '13px', color: '#d4dae3', fontWeight: '500', marginBottom: '4px' }}>
                    {anomaly.anomaly_type?.replace(/_/g, ' ')}
                  </div>
                  <div style={{ fontSize: '11px', color: '#8b95a8' }}>
                    {anomaly.timestamp.toFixed(2)}s • {anomaly.severity}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ fontSize: '13px', color: '#6b7485', fontStyle: 'italic' }}>
              No anomalies detected for this track
            </div>
          )}
        </InvestigationSection>
      </div>
    </div>
  );
};

// Scene Investigation Component
const SceneInvestigation = ({ scene }) => {
  return (
    <div style={{
      backgroundColor: '#161b22',
      border: '1px solid #263238',
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      <div style={{
        padding: '16px 20px',
        backgroundColor: '#1e2832',
        borderBottom: '1px solid #263238'
      }}>
        <div style={{ fontSize: '16px', fontWeight: '600', color: '#e0e6ed' }}>
          Scene Investigation
        </div>
      </div>

      <div style={{ padding: '20px' }}>
        <InvestigationSection title="Scene Overview" icon="◈">
          <InfoRow label="Scene Number" value={`#${scene.scene_number}`} />
          <InfoRow label="Time Range" value={`${scene.start_timestamp?.toFixed(2)}s → ${scene.end_timestamp?.toFixed(2)}s`} />
          <InfoRow label="Duration" value={`${scene.duration_seconds?.toFixed(2)}s`} />
          <InfoRow label="Participating Tracks" value={scene.participating_track_ids?.map(id => `#${id}`).join(', ') || 'N/A'} />
          <InfoRow label="Scene Type" value={scene.scene_type?.replace(/_/g, ' ')} />
          <InfoRow label="Complexity" value={scene.complexity_score?.toFixed(1)} />
        </InvestigationSection>

        {scene.summary && (
          <InvestigationSection title="Scene Summary" icon="📝">
            <div style={{
              padding: '12px',
              backgroundColor: '#0d1220',
              borderRadius: '6px',
              border: '1px solid #1a2332',
              fontSize: '13px',
              color: '#d4dae3',
              lineHeight: '1.6'
            }}>
              {scene.summary}
            </div>
          </InvestigationSection>
        )}
      </div>
    </div>
  );
};

// Helper Components
const InvestigationSection = ({ title, icon, children }) => (
  <div style={{ marginBottom: '20px' }}>
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      marginBottom: '12px',
      paddingBottom: '8px',
      borderBottom: '1px solid #263238'
    }}>
      <span style={{ fontSize: '18px' }}>{icon}</span>
      <div style={{ fontSize: '14px', fontWeight: '600', color: '#a0aab8' }}>
        {title}
      </div>
    </div>
    <div>{children}</div>
  </div>
);

const InfoRow = ({ label, value, badge, badgeColor }) => (
  <div style={{
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 0',
    fontSize: '13px'
  }}>
    <div style={{ color: '#8b95a8' }}>{label}</div>
    {badge ? (
      <div style={{
        padding: '4px 10px',
        backgroundColor: `${badgeColor}22`,
        border: `1px solid ${badgeColor}44`,
        borderRadius: '4px',
        color: badgeColor,
        fontWeight: '500',
        textTransform: 'capitalize'
      }}>
        {value}
      </div>
    ) : (
      <div style={{ color: '#d4dae3', fontWeight: '500', textTransform: 'capitalize' }}>
        {value}
      </div>
    )}
  </div>
);

const EvidenceChain = ({ steps }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
    {steps.map((step, idx) => (
      <div key={idx}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '10px 12px',
          backgroundColor: step.active ? '#58a6ff22' : '#0d1220',
          border: step.active ? '1px solid #58a6ff44' : '1px solid #1a2332',
          borderRadius: '6px'
        }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            backgroundColor: step.active ? '#58a6ff' : '#263238',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '11px',
            fontWeight: '600',
            flexShrink: 0
          }}>
            {step.module}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '13px', fontWeight: '600', color: '#e0e6ed', marginBottom: '2px' }}>
              {step.label}
            </div>
            <div style={{ fontSize: '11px', color: '#8b95a8' }}>
              {step.description}
            </div>
          </div>
        </div>
        {idx < steps.length - 1 && (
          <div style={{
            width: '2px',
            height: '12px',
            backgroundColor: '#263238',
            marginLeft: '27px'
          }} />
        )}
      </div>
    ))}
  </div>
);

const getSeverityColor = (severity) => {
  switch (severity?.toLowerCase()) {
    case 'high': return '#f44336';
    case 'medium': return '#ff9800';
    case 'low': return '#ffb74d';
    default: return '#78909c';
  }
};

export default InvestigationPanel;
