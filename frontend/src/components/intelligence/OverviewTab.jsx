/**
 * Overview Tab - High-level summary statistics
 */

const OverviewTab = ({ results }) => {
  const stats = [
    {
      label: 'Detections',
      value: results.m1_total_detections,
      subtitle: `${results.m1_avg_detections_per_frame?.toFixed(1) || 0} per frame`,
      color: '#58a6ff',
      icon: '🎯'
    },
    {
      label: 'Unique Tracks',
      value: results.m2_unique_tracks,
      subtitle: `${results.m2_total_track_observations} observations`,
      color: '#8957e5',
      icon: '👤'
    },
    {
      label: 'Behaviors',
      value: results.m3_total_behaviors,
      subtitle: Object.keys(results.m3_states_observed || {}).length + ' states',
      color: '#3fb950',
      icon: '📈'
    },
    {
      label: 'Anomalies',
      value: results.m4_total_anomalies,
      subtitle: Object.keys(results.m4_anomalies_by_type || {}).length + ' types',
      color: '#d29922',
      icon: '⚠️'
    },
    {
      label: 'Events',
      value: results.m5_correlated_events,
      subtitle: `${results.m5_total_raw_anomalies} raw anomalies`,
      color: '#f85149',
      icon: '⚡'
    },
    {
      label: 'Interactions',
      value: results.m6_total_relationships,
      subtitle: `${results.m6_tracked_pairs} pairs tracked`,
      color: '#bc8cff',
      icon: '🔗'
    },
    {
      label: 'Scenes',
      value: results.m8_total_scenes,
      subtitle: `${results.m8_avg_scene_duration?.toFixed(1) || 0}s avg duration`,
      color: '#a371f7',
      icon: '🎬'
    },
    {
      label: 'Processing Time',
      value: `${results.processing_time?.toFixed(1) || 0}s`,
      subtitle: `${results.video_duration?.toFixed(1) || 0}s video`,
      color: '#8b949e',
      icon: '⏱️'
    }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: '#0a0e1a', minHeight: '100%' }}>
      <h3 style={{ marginTop: 0, marginBottom: '24px', color: '#e6edf3', fontSize: '18px', fontWeight: '600' }}>
        Processing Overview
      </h3>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px'
      }}>
        {stats.map((stat, index) => (
          <div
            key={index}
            style={{
              backgroundColor: '#0d1220',
              padding: '20px',
              borderRadius: '8px',
              border: '1px solid #1a2332',
              borderTop: `3px solid ${stat.color}`,
              transition: 'transform 0.2s, box-shadow 0.2s',
              cursor: 'default'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.5)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <div style={{
                fontSize: '28px',
                fontWeight: '700',
                color: '#e6edf3',
                lineHeight: '1'
              }}>
                {stat.value}
              </div>
              <div style={{ fontSize: '20px', opacity: 0.8 }}>{stat.icon}</div>
            </div>
            
            <div style={{
              fontSize: '13px',
              fontWeight: '600',
              color: stat.color,
              marginBottom: '4px'
            }}>
              {stat.label}
            </div>
            <div style={{
              fontSize: '12px',
              color: '#8b949e'
            }}>
              {stat.subtitle}
            </div>
          </div>
        ))}
      </div>

      {/* Video Metadata */}
      <div style={{
        marginTop: '24px',
        backgroundColor: '#0d1220',
        padding: '20px',
        borderRadius: '8px',
        border: '1px solid #1a2332'
      }}>
        <h4 style={{ marginTop: 0, marginBottom: '16px', color: '#c9d1d9', fontSize: '15px' }}>
          Video Information
        </h4>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '16px',
          fontSize: '13px'
        }}>
          <div>
            <div style={{ color: '#8b949e', marginBottom: '6px' }}>Resolution</div>
            <div style={{ color: '#e6edf3', fontWeight: '500' }}>{results.video_width}×{results.video_height}</div>
          </div>
          <div>
            <div style={{ color: '#8b949e', marginBottom: '6px' }}>Frame Rate</div>
            <div style={{ color: '#e6edf3', fontWeight: '500' }}>{results.video_fps?.toFixed(2)} fps</div>
          </div>
          <div>
            <div style={{ color: '#8b949e', marginBottom: '6px' }}>Total Frames</div>
            <div style={{ color: '#e6edf3', fontWeight: '500' }}>{results.video_total_frames}</div>
          </div>
          <div>
            <div style={{ color: '#8b949e', marginBottom: '6px' }}>Frames Processed</div>
            <div style={{ color: '#e6edf3', fontWeight: '500' }}>{results.frames_processed} <span style={{ color: '#8b949e' }}>({((results.frames_processed / results.video_total_frames) * 100).toFixed(0)}%)</span></div>
          </div>
        </div>
      </div>

      {/* Detection Classes */}
      {results.m1_detections_by_class && Object.keys(results.m1_detections_by_class).length > 0 && (
        <div style={{
          marginTop: '24px',
          backgroundColor: '#0d1220',
          padding: '20px',
          borderRadius: '8px',
          border: '1px solid #1a2332'
        }}>
          <h4 style={{ marginTop: 0, marginBottom: '16px', color: '#c9d1d9', fontSize: '15px' }}>
            Detected Classes
          </h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
            {Object.entries(results.m1_detections_by_class).map(([className, count]) => (
              <div
                key={className}
                style={{
                  backgroundColor: '#161b22',
                  padding: '8px 14px',
                  borderRadius: '6px',
                  border: '1px solid #30363d',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  fontSize: '13px'
                }}
              >
                <span style={{ color: '#c9d1d9', fontWeight: '500', textTransform: 'capitalize' }}>
                  {className}
                </span>
                <span style={{
                  backgroundColor: 'rgba(88, 166, 255, 0.1)',
                  color: '#58a6ff',
                  border: '1px solid rgba(88, 166, 255, 0.2)',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontSize: '11px',
                  fontWeight: '600'
                }}>
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default OverviewTab;
