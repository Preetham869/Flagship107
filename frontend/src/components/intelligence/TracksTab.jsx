/**
 * Tracks Tab - Display all tracked entities (M2/M3 data)
 * Uses deterministic track colors, dark investigation theme,
 * pixel speed disclosures, anomaly associations, and navigation shortcuts.
 */
import { useSelection } from '../../context/SelectionContext';
import { getTrackColor } from '../../utils/trackColors';

const TracksTab = ({ results = {}, onSeek }) => {
  const { selectTrack, selectedItem } = useSelection();

  // Extract track summaries from behaviors and tracks
  const trackSummaries = {};

  if (results.all_behaviors && results.all_behaviors.length > 0) {
    results.all_behaviors.forEach((frameBehaviors) => {
      frameBehaviors.forEach((behavior) => {
        const trackId = String(behavior.track_id);
        if (!trackSummaries[trackId]) {
          trackSummaries[trackId] = {
            track_id: behavior.track_id,
            class_name: behavior.class_name || 'person',
            observations: 0,
            first_timestamp: behavior.timestamp ?? 0,
            last_timestamp: behavior.timestamp ?? 0,
            speeds: [],
            states: new Set(),
            anomalies: [],
          };
        }

        const summary = trackSummaries[trackId];
        summary.observations++;
        if (behavior.timestamp !== undefined) {
          summary.last_timestamp = Math.max(summary.last_timestamp, behavior.timestamp);
        }
        if (behavior.speed !== undefined && behavior.speed !== null) {
          summary.speeds.push(behavior.speed);
        }
        if (behavior.state) summary.states.add(behavior.state);
      });
    });
  } else if (results.all_tracks && results.all_tracks.length > 0) {
    // Fallback directly to all_tracks if behaviors array is empty
    const fps = results.video_fps || 30.0;
    results.all_tracks.forEach((frameTracks, frameIdx) => {
      const timestamp = frameIdx / fps;
      frameTracks.forEach((t) => {
        const trackId = String(t.track_id);
        if (!trackSummaries[trackId]) {
          trackSummaries[trackId] = {
            track_id: t.track_id,
            class_name: t.class_name || 'object',
            observations: 0,
            first_timestamp: timestamp,
            last_timestamp: timestamp,
            speeds: [],
            states: new Set(),
            anomalies: [],
          };
        }
        const summary = trackSummaries[trackId];
        summary.observations++;
        summary.last_timestamp = Math.max(summary.last_timestamp, timestamp);
      });
    });
  }

  // Associate anomalies
  if (results.all_anomalies) {
    results.all_anomalies.forEach((anom) => {
      const tid = String(anom.track_id);
      if (trackSummaries[tid]) {
        trackSummaries[tid].anomalies.push(anom);
      }
    });
  }

  const tracks = Object.values(trackSummaries).map((track) => ({
    ...track,
    duration: Math.max(0, track.last_timestamp - track.first_timestamp),
    avg_speed: track.speeds.length > 0
      ? track.speeds.reduce((a, b) => a + b, 0) / track.speeds.length
      : 0,
    max_speed: track.speeds.length > 0
      ? Math.max(...track.speeds)
      : 0,
    states_list: Array.from(track.states),
  }));

  // Sort by track ID numeric
  tracks.sort((a, b) => {
    const aNum = parseInt(String(a.track_id), 10);
    const bNum = parseInt(String(b.track_id), 10);
    if (!isNaN(aNum) && !isNaN(bNum)) return aNum - bNum;
    return String(a.track_id).localeCompare(String(b.track_id));
  });

  return (
    <div style={{ padding: '20px', backgroundColor: '#0d1117', color: '#e6edf3' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px',
        paddingBottom: '12px',
        borderBottom: '1px solid #30363d',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '18px' }}>👤</span>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#f0f6fc' }}>
            Confirmed Entity Tracks ({tracks.length})
          </h3>
        </div>
        <div style={{ fontSize: '12px', color: '#8b949e' }}>
          Image-space movement analysis (px/s)
        </div>
      </div>

      {tracks.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '40px 20px',
          color: '#8b949e',
          backgroundColor: '#161b22',
          borderRadius: '8px',
          border: '1px dashed #30363d',
          fontSize: '13px',
        }}>
          No tracked entities identified in this footage
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {tracks.map((track) => {
            const trackColor = getTrackColor(track.track_id);
            const isSelected = selectedItem && String(selectedItem.track_id || selectedItem.id) === String(track.track_id);
            const hasAnomalies = track.anomalies.length > 0;

            return (
              <div
                key={track.track_id}
                onClick={() => {
                  selectTrack(track);
                  onSeek?.(track.first_timestamp);
                }}
                style={{
                  backgroundColor: '#161b22',
                  border: `1px solid ${isSelected ? '#388bfd' : '#30363d'}`,
                  borderLeft: `4px solid ${trackColor}`,
                  borderRadius: '8px',
                  padding: '18px 20px',
                  transition: 'all 0.2s',
                  cursor: 'pointer',
                  boxShadow: isSelected ? '0 0 12px rgba(56, 139, 253, 0.25)' : 'none',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{
                        backgroundColor: trackColor,
                        color: '#0d1117',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '13px',
                        fontWeight: '700',
                      }}>
                        #{track.track_id}
                      </span>
                      <span style={{
                        backgroundColor: '#21262d',
                        color: '#f0f6fc',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: '500',
                        textTransform: 'capitalize',
                      }}>
                        {track.class_name}
                      </span>
                      {hasAnomalies && (
                        <span style={{
                          backgroundColor: 'rgba(248, 81, 73, 0.15)',
                          color: '#ff7b72',
                          border: '1px solid rgba(248, 81, 73, 0.3)',
                          padding: '1px 6px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: '600',
                        }}>
                          ⚠ {track.anomalies.length} Flagged
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: '12px', color: '#8b949e' }}>
                      Active: {track.first_timestamp.toFixed(2)}s → {track.last_timestamp.toFixed(2)}s ({track.duration.toFixed(2)}s observed duration)
                    </div>
                  </div>

                  {/* Navigation Quick Actions */}
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSeek?.(track.first_timestamp);
                      }}
                      style={{
                        padding: '4px 10px',
                        backgroundColor: '#21262d',
                        border: '1px solid #30363d',
                        color: '#c9d1d9',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: '500',
                        cursor: 'pointer',
                      }}
                    >
                      ⏮ First Seen
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSeek?.(track.last_timestamp);
                      }}
                      style={{
                        padding: '4px 10px',
                        backgroundColor: '#21262d',
                        border: '1px solid #30363d',
                        color: '#c9d1d9',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: '500',
                        cursor: 'pointer',
                      }}
                    >
                      Last Seen ⏭
                    </button>
                  </div>
                </div>

                {/* Metrics Grid */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                  gap: '10px',
                  backgroundColor: '#0d1117',
                  padding: '10px 14px',
                  borderRadius: '6px',
                  border: '1px solid #21262d',
                  fontSize: '12px',
                }}>
                  <div>
                    <div style={{ color: '#8b949e', fontSize: '11px', marginBottom: '2px' }}>Observations</div>
                    <div style={{ fontWeight: '600', color: '#f0f6fc' }}>{track.observations} frames</div>
                  </div>
                  <div>
                    <div style={{ color: '#8b949e', fontSize: '11px', marginBottom: '2px' }}>Avg Image Speed</div>
                    <div style={{ fontWeight: '600', color: '#f0f6fc' }}>{track.avg_speed.toFixed(1)} px/s</div>
                  </div>
                  <div>
                    <div style={{ color: '#8b949e', fontSize: '11px', marginBottom: '2px' }}>Peak Image Speed</div>
                    <div style={{ fontWeight: '600', color: '#f0f6fc' }}>{track.max_speed.toFixed(1)} px/s</div>
                  </div>
                  <div>
                    <div style={{ color: '#8b949e', fontSize: '11px', marginBottom: '2px' }}>Behavior States</div>
                    <div style={{ fontWeight: '600', color: '#f0f6fc' }}>
                      {track.states_list.length > 0 ? track.states_list.join(', ') : 'In transit'}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default TracksTab;
