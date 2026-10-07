/**
 * Event Timeline Component
 * Interactive timeline with anomaly/event markers, clustering, and selection state
 */
import { useState, useMemo } from 'react';
import { useSelection } from '../context/SelectionContext';

const EventTimeline = ({ 
  anomalies = [], 
  events = [], 
  videoDuration,
  currentTime,
  onSeek,
  selectedItem
}) => {
  const [hoveredItem, setHoveredItem] = useState(null);
  const { selectAnomaly, selectEvent } = useSelection();

  const getPositionPercent = (timestamp) => {
    if (!videoDuration || videoDuration <= 0) return 0;
    return (timestamp / videoDuration) * 100;
  };

  // Cluster nearby markers to improve readability
  const clusterMarkers = useMemo(() => {
    const cluster = (items, type) => {
      if (items.length === 0) return [];
      
      const CLUSTER_THRESHOLD_PERCENT = 2; // 2% of timeline width
      const sorted = [...items].sort((a, b) => {
        const aTime = a.timestamp || a.start_timestamp;
        const bTime = b.timestamp || b.start_timestamp;
        return aTime - bTime;
      });

      const clusters = [];
      let currentCluster = [sorted[0]];

      for (let i = 1; i < sorted.length; i++) {
        const prevTime = currentCluster[currentCluster.length - 1].timestamp || 
                        currentCluster[currentCluster.length - 1].start_timestamp;
        const currTime = sorted[i].timestamp || sorted[i].start_timestamp;
        
        const prevPos = getPositionPercent(prevTime);
        const currPos = getPositionPercent(currTime);

        if (currPos - prevPos < CLUSTER_THRESHOLD_PERCENT) {
          currentCluster.push(sorted[i]);
        } else {
          clusters.push({ items: currentCluster, type });
          currentCluster = [sorted[i]];
        }
      }
      clusters.push({ items: currentCluster, type });
      
      return clusters;
    };

    return {
      anomalies: cluster(anomalies, 'anomaly'),
      events: cluster(events, 'event')
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [anomalies, events, videoDuration]);

  if (!videoDuration || videoDuration <= 0) {
    return (
      <div style={{ 
        padding: '30px', 
        textAlign: 'center', 
        color: '#78909c',
        backgroundColor: '#1e2832',
        borderRadius: '8px',
        border: '1px solid #263238'
      }}>
        No timeline data available
      </div>
    );
  }

  const handleTimelineClick = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const timestamp = percentage * videoDuration;
    onSeek?.(timestamp);
  };

  const getSeverityColor = (severity, isEvent = false) => {
    if (isEvent) return '#4caf50';
    switch (severity?.toLowerCase()) {
      case 'high': return '#f44336';
      case 'medium': return '#ff9800';
      case 'low': return '#ffb74d';
      default: return '#ffa726';
    }
  };

  const isItemSelected = (item) => {
    if (!selectedItem) return false;
    return selectedItem.event_id === item.event_id ||
           selectedItem.scene_id === item.scene_id ||
           selectedItem.track_id === item.track_id;
  };

  const renderCluster = (cluster, index) => {
    const firstItem = cluster.items[0];
    const timestamp = firstItem.timestamp || firstItem.start_timestamp;
    const position = getPositionPercent(timestamp);
    const isEvent = cluster.type === 'event';
    const isCluster = cluster.items.length > 1;
    const isSelected = cluster.items.some(item => isItemSelected(item));
    const isHovered = hoveredItem && cluster.items.some(item => 
      (item.event_id && item.event_id === hoveredItem.event_id)
    );

    const severity = firstItem.severity || 'medium';
    const color = getSeverityColor(severity, isEvent);

    return (
      <div
        key={`${cluster.type}-${index}`}
        onClick={(e) => {
          e.stopPropagation();
          // Select first item in cluster
          if (cluster.type === 'event') {
            selectEvent(firstItem);
          } else {
            selectAnomaly(firstItem);
          }
          onSeek?.(timestamp);
        }}
        onMouseEnter={() => setHoveredItem(firstItem)}
        onMouseLeave={() => setHoveredItem(null)}
        style={{
          position: 'absolute',
          left: `${position}%`,
          top: isEvent ? '65%' : '35%',
          transform: isEvent ? 'translate(-50%, -50%) rotate(45deg)' : 'translate(-50%, -50%)',
          width: (isSelected || isHovered) ? '18px' : isCluster ? '16px' : '12px',
          height: (isSelected || isHovered) ? '18px' : isCluster ? '16px' : '12px',
          backgroundColor: color,
          border: (isSelected || isHovered) ? `3px solid #fff` : `2px solid rgba(255,255,255,0.8)`,
          borderRadius: isEvent ? '2px' : '50%',
          cursor: 'pointer',
          zIndex: (isSelected || isHovered) ? 30 : (isCluster ? 20 : 10),
          boxShadow: `0 2px 8px ${color}88, 0 0 ${isCluster ? '12' : '8'}px ${color}44`,
          transition: 'all 0.2s',
          ...(!isEvent && {
            boxShadow: `0 0 0 ${(isSelected || isHovered) ? '6px' : isCluster ? '4px' : '2px'} ${color}22, 0 2px 8px ${color}88`
          })
        }}
        title={`${isCluster ? `${cluster.items.length}× ` : ''}${
          isEvent ? firstItem.event_type : firstItem.anomaly_type
        } at ${timestamp.toFixed(2)}s`}
      >
        {isCluster && (
          <div style={{
            position: 'absolute',
            top: '-8px',
            right: '-8px',
            backgroundColor: '#fff',
            color: color,
            borderRadius: '50%',
            width: '16px',
            height: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '9px',
            fontWeight: '700',
            border: `2px solid ${color}`,
            transform: isEvent ? 'rotate(-45deg)' : 'none',
            zIndex: 1
          }}>
            {cluster.items.length}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ 
      backgroundColor: '#1e2832', 
      padding: '20px 24px',
      borderRadius: '8px',
      border: '1px solid #263238',
      boxShadow: '0 2px 8px rgba(0,0,0,0.4)'
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '18px'
      }}>
        <h3 style={{ 
          margin: 0, 
          fontSize: '15px', 
          fontWeight: '600',
          color: '#eceff1',
          letterSpacing: '0.3px'
        }}>
          Event Timeline
        </h3>
        
        {/* Legend */}
        <div style={{ 
          display: 'flex', 
          gap: '20px', 
          fontSize: '11px',
          color: '#90a4ae'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{
              width: '10px',
              height: '10px',
              backgroundColor: '#ff9800',
              borderRadius: '50%',
              border: '2px solid rgba(255,255,255,0.8)',
              boxShadow: '0 0 4px #ff980066'
            }} />
            <span>Anomaly ({anomalies.length})</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{
              width: '10px',
              height: '10px',
              backgroundColor: '#4caf50',
              transform: 'rotate(45deg)',
              border: '2px solid rgba(255,255,255,0.8)',
              boxShadow: '0 0 4px #4caf5066'
            }} />
            <span>Event ({events.length})</span>
          </div>
        </div>
      </div>

      {/* Timeline Bar */}
      <div
        onClick={handleTimelineClick}
        style={{
          position: 'relative',
          width: '100%',
          height: '70px',
          backgroundColor: '#0d1117',
          borderRadius: '8px',
          cursor: 'pointer',
          border: '1px solid #263238',
          boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.3)'
        }}
      >
        {/* Current playback position */}
        {currentTime !== undefined && currentTime !== null && (
          <div style={{
            position: 'absolute',
            left: `${getPositionPercent(currentTime)}%`,
            top: 0,
            bottom: 0,
            width: '3px',
            backgroundColor: '#7e57c2',
            zIndex: 50,
            boxShadow: '0 0 8px #7e57c2aa',
            pointerEvents: 'none'
          }}>
            <div style={{
              position: 'absolute',
              top: '-6px',
              left: '50%',
              transform: 'translateX(-50%)',
              width: '0',
              height: '0',
              borderLeft: '6px solid transparent',
              borderRight: '6px solid transparent',
              borderTop: '8px solid #7e57c2'
            }} />
          </div>
        )}

        {/* Render clustered anomaly markers */}
        {clusterMarkers.anomalies.map((cluster, index) => renderCluster(cluster, index))}

        {/* Render clustered event markers */}
        {clusterMarkers.events.map((cluster, index) => renderCluster(cluster, index))}
      </div>

      {/* Hovered Item Preview */}
      {hoveredItem && (
        <div style={{
          marginTop: '15px',
          backgroundColor: '#263238',
          padding: '12px 16px',
          borderRadius: '6px',
          fontSize: '12px',
          border: '1px solid #37474f',
          color: '#b0bec5'
        }}>
          <div style={{ fontWeight: '600', color: '#eceff1', marginBottom: '4px' }}>
            {hoveredItem.event_type ? 
              hoveredItem.event_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 
              hoveredItem.anomaly_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
            }
          </div>
          <div>
            <span style={{ color: '#78909c' }}>Time:</span> {
              formatTimestamp(hoveredItem.timestamp || hoveredItem.start_timestamp)
            }
            {' • '}
            <span style={{ color: '#78909c' }}>Severity:</span>{' '}
            <span style={{ 
              color: getSeverityColor(hoveredItem.severity, !!hoveredItem.event_type),
              fontWeight: '500'
            }}>
              {hoveredItem.severity}
            </span>
          </div>
        </div>
      )}

      {/* Empty state */}
      {anomalies.length === 0 && events.length === 0 && (
        <div style={{ 
          textAlign: 'center', 
          padding: '30px 20px', 
          color: '#78909c',
          fontSize: '13px',
          marginTop: '15px'
        }}>
          No anomalies or events detected in this video
        </div>
      )}
    </div>
  );
};

const formatTimestamp = (timestamp) => {
  const mins = Math.floor(timestamp / 60);
  const secs = (timestamp % 60).toFixed(2);
  return `${mins}:${secs.padStart(5, '0')}`;
};

export default EventTimeline;
