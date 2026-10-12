/**
 * Event Timeline Component
 * Interactive, high-contrast timeline with anomaly/event markers,
 * scene boundaries, track activity indicators, clustering, and synchronized selection.
 */
import { useState, useMemo, useCallback } from 'react';
import { useSelection } from '../context/SelectionContext';
import { getTrackColor } from '../utils/trackColors';

const EventTimeline = ({
  anomalies = [],
  events = [],
  scenes = [],
  videoDuration = 0,
  currentTime = 0,
  onSeek,
  selectedItem,
}) => {
  const [hoveredItem, setHoveredItem] = useState(null);
  const [showAnomalies, setShowAnomalies] = useState(true);
  const [showEvents, setShowEvents] = useState(true);

  const { selectAnomaly, selectEvent } = useSelection();

  const getPositionPercent = useCallback((timestamp) => {
    if (!videoDuration || videoDuration <= 0) return 0;
    return Math.max(0, Math.min(100, (timestamp / videoDuration) * 100));
  }, [videoDuration]);

  // Clustered markers to prevent overlapping DOM elements
  const clusterMarkers = useMemo(() => {
    const cluster = (items, type) => {
      if (!items || items.length === 0) return [];

      const CLUSTER_THRESHOLD_PERCENT = 2.0; // 2% width threshold
      const sorted = [...items].sort((a, b) => {
        const aTime = a.timestamp ?? a.start_timestamp ?? 0;
        const bTime = b.timestamp ?? b.start_timestamp ?? 0;
        return aTime - bTime;
      });

      const clusters = [];
      let currentCluster = [sorted[0]];

      for (let i = 1; i < sorted.length; i++) {
        const prevTime = currentCluster[currentCluster.length - 1].timestamp ??
                        currentCluster[currentCluster.length - 1].start_timestamp ?? 0;
        const currTime = sorted[i].timestamp ?? sorted[i].start_timestamp ?? 0;

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
      anomalies: showAnomalies ? cluster(anomalies, 'anomaly') : [],
      events: showEvents ? cluster(events, 'event') : [],
    };
  }, [anomalies, events, showAnomalies, showEvents, getPositionPercent]);

  if (!videoDuration || videoDuration <= 0) {
    return (
      <div style={{
        padding: '24px',
        textAlign: 'center',
        color: '#8b949e',
        backgroundColor: '#161b22',
        borderRadius: '8px',
        border: '1px solid #30363d',
        fontSize: '13px',
      }}>
        Video timeline loading or duration unavailable.
      </div>
    );
  }

  const handleTimelineClick = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    const timestamp = percentage * videoDuration;
    onSeek?.(timestamp);
  };

  const getSeverityColor = (severity, isEvent = false) => {
    if (isEvent) return '#2ea043'; // Green for correlated events
    switch (severity?.toLowerCase()) {
      case 'high': return '#f85149'; // Red
      case 'medium': return '#d29922'; // Amber
      case 'low': return '#e3b341'; // Light Amber
      default: return '#58a6ff';
    }
  };

  const isItemSelected = (item) => {
    if (!selectedItem) return false;
    return (
      (selectedItem.event_id && selectedItem.event_id === item.event_id) ||
      (selectedItem.anomaly_id && selectedItem.anomaly_id === item.anomaly_id) ||
      (selectedItem.scene_id && selectedItem.scene_id === item.scene_id)
    );
  };

  const renderCluster = (cluster, index) => {
    const firstItem = cluster.items[0];
    const timestamp = firstItem.timestamp ?? firstItem.start_timestamp ?? 0;
    const position = getPositionPercent(timestamp);
    const isEvent = cluster.type === 'event';
    const isCluster = cluster.items.length > 1;
    const isSelected = cluster.items.some(isItemSelected);
    const isHovered = hoveredItem && cluster.items.includes(hoveredItem);

    const severity = firstItem.severity || 'medium';
    const color = getSeverityColor(severity, isEvent);

    return (
      <div
        key={`${cluster.type}-${index}`}
        onClick={(e) => {
          e.stopPropagation();
          if (isEvent) {
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
          top: isEvent ? '68%' : '32%',
          transform: isEvent ? 'translate(-50%, -50%) rotate(45deg)' : 'translate(-50%, -50%)',
          width: isSelected || isHovered ? '18px' : isCluster ? '15px' : '12px',
          height: isSelected || isHovered ? '18px' : isCluster ? '15px' : '12px',
          backgroundColor: color,
          border: isSelected || isHovered ? '3px solid #ffffff' : '2px solid rgba(255,255,255,0.85)',
          borderRadius: isEvent ? '3px' : '50%',
          cursor: 'pointer',
          zIndex: isSelected || isHovered ? 40 : isCluster ? 25 : 15,
          boxShadow: isSelected || isHovered ? `0 0 12px ${color}` : `0 2px 6px ${color}88`,
          transition: 'transform 0.15s, width 0.15s, height 0.15s',
        }}
        title={`${isCluster ? `${cluster.items.length}× ` : ''}${
          isEvent ? firstItem.event_type : firstItem.anomaly_type
        } at ${timestamp.toFixed(2)}s`}
      >
        {isCluster && (
          <div style={{
            position: 'absolute',
            top: '-7px',
            right: '-7px',
            backgroundColor: '#ffffff',
            color: color,
            borderRadius: '50%',
            width: '14px',
            height: '14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '9px',
            fontWeight: '700',
            border: `1.5px solid ${color}`,
            transform: isEvent ? 'rotate(-45deg)' : 'none',
            zIndex: 1,
          }}>
            {cluster.items.length}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{
      backgroundColor: '#161b22',
      padding: '18px 22px',
      borderRadius: '8px',
      border: '1px solid #30363d',
      boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
    }}>
      {/* Header and Legend */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px',
        flexWrap: 'wrap',
        gap: '10px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '16px' }}>⏱</span>
          <h3 style={{ margin: 0, fontSize: '15px', fontWeight: '600', color: '#f0f6fc' }}>
            Investigation Timeline
          </h3>
          <span style={{ fontSize: '11px', color: '#8b949e', backgroundColor: '#0d1117', padding: '2px 8px', borderRadius: '4px' }}>
            {videoDuration.toFixed(1)}s
          </span>
        </div>

        {/* Legend with Interactive Toggle Filters */}
        <div style={{ display: 'flex', gap: '16px', fontSize: '11px', color: '#8b949e' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showAnomalies}
              onChange={(e) => setShowAnomalies(e.target.checked)}
              style={{ accentColor: '#d29922' }}
            />
            <span style={{
              width: '10px',
              height: '10px',
              backgroundColor: '#d29922',
              borderRadius: '50%',
              display: 'inline-block',
            }} />
            <span>Raw Anomalies ({anomalies.length})</span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showEvents}
              onChange={(e) => setShowEvents(e.target.checked)}
              style={{ accentColor: '#2ea043' }}
            />
            <span style={{
              width: '9px',
              height: '9px',
              backgroundColor: '#2ea043',
              transform: 'rotate(45deg)',
              display: 'inline-block',
            }} />
            <span>Correlated Events ({events.length})</span>
          </label>
        </div>
      </div>

      {/* Interactive Timeline Track */}
      <div
        onClick={handleTimelineClick}
        style={{
          position: 'relative',
          width: '100%',
          height: '64px',
          backgroundColor: '#0d1117',
          borderRadius: '6px',
          cursor: 'pointer',
          border: '1px solid #30363d',
          overflow: 'hidden',
        }}
      >
        {/* Subtle Midline divider separating anomalies (top) and events (bottom) */}
        <div style={{
          position: 'absolute',
          top: '50%',
          left: 0,
          right: 0,
          height: '1px',
          backgroundColor: '#21262d',
        }} />

        {/* Scene Boundary Dividers */}
        {scenes && scenes.length > 1 && scenes.map((sc, i) => {
          if (sc.start_timestamp === undefined || sc.start_timestamp <= 0) return null;
          const pos = getPositionPercent(sc.start_timestamp);
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: `${pos}%`,
                top: 0,
                bottom: 0,
                width: '1px',
                backgroundColor: 'rgba(88, 166, 255, 0.4)',
                borderRight: '1px dashed rgba(88, 166, 255, 0.3)',
                zIndex: 5,
              }}
              title={`Scene #${sc.scene_number || i + 1} at ${sc.start_timestamp.toFixed(1)}s`}
            />
          );
        })}

        {/* Current Playhead Cursor */}
        {currentTime !== undefined && (
          <div style={{
            position: 'absolute',
            left: `${getPositionPercent(currentTime)}%`,
            top: 0,
            bottom: 0,
            width: '2px',
            backgroundColor: '#58a6ff',
            zIndex: 50,
            boxShadow: '0 0 8px rgba(88, 166, 255, 0.9)',
            pointerEvents: 'none',
          }}>
            <div style={{
              position: 'absolute',
              top: '-4px',
              left: '50%',
              transform: 'translateX(-50%)',
              width: '0',
              height: '0',
              borderLeft: '5px solid transparent',
              borderRight: '5px solid transparent',
              borderTop: '7px solid #58a6ff',
            }} />
          </div>
        )}

        {/* Clustered Anomaly Markers */}
        {clusterMarkers.anomalies.map((cluster, index) => renderCluster(cluster, index))}

        {/* Clustered Correlated Event Markers */}
        {clusterMarkers.events.map((cluster, index) => renderCluster(cluster, index))}
      </div>

      {/* Hovered Marker Information Tooltip */}
      {hoveredItem && (
        <div style={{
          marginTop: '12px',
          backgroundColor: '#0d1117',
          padding: '10px 14px',
          borderRadius: '6px',
          fontSize: '12px',
          border: '1px solid #30363d',
          color: '#c9d1d9',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
        }}>
          <div>
            <span style={{ fontWeight: '600', color: '#f0f6fc', marginRight: '6px' }}>
              {hoveredItem.event_type
                ? `Event: ${hoveredItem.event_type.replace(/_/g, ' ')}`
                : `Anomaly: ${hoveredItem.anomaly_type.replace(/_/g, ' ')}`}
            </span>
            <span style={{ color: '#8b949e' }}>
              at {(hoveredItem.timestamp ?? hoveredItem.start_timestamp ?? 0).toFixed(2)}s
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {hoveredItem.track_id !== undefined && (
              <span style={{
                padding: '1px 6px',
                borderRadius: '3px',
                fontSize: '11px',
                fontWeight: '600',
                backgroundColor: getTrackColor(hoveredItem.track_id),
                color: '#0d1117'
              }}>
                Track #{hoveredItem.track_id}
              </span>
            )}
            <span style={{
              color: getSeverityColor(hoveredItem.severity, !!hoveredItem.event_type),
              fontWeight: '600',
              fontSize: '11px',
              textTransform: 'uppercase',
            }}>
              {hoveredItem.severity || 'Medium'} Severity
            </span>
          </div>
        </div>
      )}

      {/* Empty State */}
      {anomalies.length === 0 && events.length === 0 && (
        <div style={{
          textAlign: 'center',
          padding: '16px',
          color: '#8b949e',
          fontSize: '12px',
          marginTop: '8px',
        }}>
          ✓ No anomalies or correlated events detected — timeline indicates normal baseline activity.
        </div>
      )}
    </div>
  );
};

export default EventTimeline;
