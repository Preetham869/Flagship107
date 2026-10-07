/**
 * Tracks Tab - Display all tracked entities (M2/M3 data)
 */

const TracksTab = ({ results, onSeek }) => {
  // Extract track information from all_behaviors
  const trackSummaries = {};
  
  if (results.all_behaviors) {
    results.all_behaviors.forEach(frameBehaviors => {
      frameBehaviors.forEach(behavior => {
        const trackId = behavior.track_id;
        if (!trackSummaries[trackId]) {
          trackSummaries[trackId] = {
            track_id: trackId,
            class_name: behavior.class_name || 'unknown',
            observations: 0,
            first_timestamp: behavior.timestamp,
            last_timestamp: behavior.timestamp,
            speeds: [],
            states: new Set(),
            positions: []
          };
        }
        
        const summary = trackSummaries[trackId];
        summary.observations++;
        summary.last_timestamp = behavior.timestamp;
        if (behavior.speed) summary.speeds.push(behavior.speed);
        if (behavior.state) summary.states.add(behavior.state);
        if (behavior.position) summary.positions.push(behavior.position);
      });
    });
  }

  const tracks = Object.values(trackSummaries).map(track => ({
    ...track,
    duration: track.last_timestamp - track.first_timestamp,
    avg_speed: track.speeds.length > 0 
      ? track.speeds.reduce((a, b) => a + b, 0) / track.speeds.length 
      : 0,
    max_speed: track.speeds.length > 0 
      ? Math.max(...track.speeds) 
      : 0,
    states_list: Array.from(track.states)
  }));

  // Sort by track ID
  tracks.sort((a, b) => {
    const aNum = parseInt(String(a.track_id));
    const bNum = parseInt(String(b.track_id));
    return aNum - bNum;
  });

  return (
    <div style={{ padding: '20px' }}>
      <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#333' }}>
        Tracked Entities ({tracks.length})
      </h3>

      {tracks.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '40px',
          color: '#999',
          backgroundColor: '#fafafa',
          borderRadius: '8px'
        }}>
          No tracked entities found
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {tracks.map((track) => (
            <div
              key={track.track_id}
              style={{
                backgroundColor: '#fff',
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
                padding: '20px',
                transition: 'border-color 0.2s, box-shadow 0.2s',
                cursor: 'pointer'
              }}
              onClick={() => onSeek?.(track.first_timestamp)}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#9C27B0';
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(156, 39, 176, 0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#e0e0e0';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '15px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '5px' }}>
                    <span style={{
                      fontSize: '18px',
                      fontWeight: 'bold',
                      color: '#9C27B0'
                    }}>
                      Track #{track.track_id}
                    </span>
                    <span style={{
                      backgroundColor: '#f3e5f5',
                      color: '#9C27B0',
                      padding: '3px 10px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: '500',
                      textTransform: 'capitalize'
                    }}>
                      {track.class_name}
                    </span>
                  </div>
                  <div style={{ fontSize: '13px', color: '#666' }}>
                    {track.first_timestamp.toFixed(2)}s - {track.last_timestamp.toFixed(2)}s
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '14px', fontWeight: '500', color: '#555' }}>
                    {track.observations} observations
                  </div>
                  <div style={{ fontSize: '12px', color: '#888' }}>
                    {track.duration.toFixed(2)}s duration
                  </div>
                </div>
              </div>

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: '15px',
                marginTop: '15px'
              }}>
                <div>
                  <div style={{ fontSize: '12px', color: '#888', marginBottom: '3px' }}>Average Speed</div>
                  <div style={{ fontSize: '16px', fontWeight: '500', color: '#555' }}>
                    {track.avg_speed.toFixed(1)} px/s
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#888', marginBottom: '3px' }}>Maximum Speed</div>
                  <div style={{ fontSize: '16px', fontWeight: '500', color: '#555' }}>
                    {track.max_speed.toFixed(1)} px/s
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#888', marginBottom: '3px' }}>Behavior States</div>
                  <div style={{ fontSize: '14px', fontWeight: '500', color: '#555' }}>
                    {track.states_list.join(', ') || 'N/A'}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TracksTab;
