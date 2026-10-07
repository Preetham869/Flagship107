/**
 * Overview Tab - High-level summary statistics
 */

const OverviewTab = ({ results }) => {
  const stats = [
    {
      label: 'Detections',
      value: results.m1_total_detections,
      subtitle: `${results.m1_avg_detections_per_frame?.toFixed(1) || 0} per frame`,
      color: '#2196F3',
      bg: '#e3f2fd'
    },
    {
      label: 'Unique Tracks',
      value: results.m2_unique_tracks,
      subtitle: `${results.m2_total_track_observations} observations`,
      color: '#9C27B0',
      bg: '#f3e5f5'
    },
    {
      label: 'Behaviors',
      value: results.m3_total_behaviors,
      subtitle: Object.keys(results.m3_states_observed || {}).length + ' states',
      color: '#00BCD4',
      bg: '#e0f7fa'
    },
    {
      label: 'Anomalies',
      value: results.m4_total_anomalies,
      subtitle: Object.keys(results.m4_anomalies_by_type || {}).length + ' types',
      color: '#FF9800',
      bg: '#fff3e0'
    },
    {
      label: 'Events',
      value: results.m5_correlated_events,
      subtitle: `${results.m5_total_raw_anomalies} raw anomalies`,
      color: '#4CAF50',
      bg: '#e8f5e9'
    },
    {
      label: 'Interactions',
      value: results.m6_total_relationships,
      subtitle: `${results.m6_tracked_pairs} pairs tracked`,
      color: '#E91E63',
      bg: '#fce4ec'
    },
    {
      label: 'Scenes',
      value: results.m8_total_scenes,
      subtitle: `${results.m8_avg_scene_duration?.toFixed(1) || 0}s avg duration`,
      color: '#673AB7',
      bg: '#ede7f6'
    },
    {
      label: 'Processing Time',
      value: `${results.processing_time?.toFixed(1) || 0}s`,
      subtitle: `${results.video_duration?.toFixed(1) || 0}s video`,
      color: '#607D8B',
      bg: '#eceff1'
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#333' }}>
        Processing Overview
      </h3>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '15px'
      }}>
        {stats.map((stat, index) => (
          <div
            key={index}
            style={{
              backgroundColor: stat.bg,
              padding: '20px',
              borderRadius: '8px',
              border: `1px solid ${stat.color}20`,
              transition: 'transform 0.2s',
              cursor: 'default'
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <div style={{
              fontSize: '32px',
              fontWeight: 'bold',
              color: stat.color,
              marginBottom: '5px'
            }}>
              {stat.value}
            </div>
            <div style={{
              fontSize: '14px',
              fontWeight: '500',
              color: '#555',
              marginBottom: '3px'
            }}>
              {stat.label}
            </div>
            <div style={{
              fontSize: '12px',
              color: '#888'
            }}>
              {stat.subtitle}
            </div>
          </div>
        ))}
      </div>

      {/* Video Metadata */}
      <div style={{
        marginTop: '30px',
        backgroundColor: '#fafafa',
        padding: '20px',
        borderRadius: '8px',
        border: '1px solid #e0e0e0'
      }}>
        <h4 style={{ marginTop: 0, marginBottom: '15px', color: '#555' }}>
          Video Information
        </h4>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '15px',
          fontSize: '14px'
        }}>
          <div>
            <div style={{ color: '#888', marginBottom: '5px' }}>Resolution</div>
            <div style={{ fontWeight: '500' }}>{results.video_width}×{results.video_height}</div>
          </div>
          <div>
            <div style={{ color: '#888', marginBottom: '5px' }}>Frame Rate</div>
            <div style={{ fontWeight: '500' }}>{results.video_fps?.toFixed(2)} fps</div>
          </div>
          <div>
            <div style={{ color: '#888', marginBottom: '5px' }}>Total Frames</div>
            <div style={{ fontWeight: '500' }}>{results.video_total_frames}</div>
          </div>
          <div>
            <div style={{ color: '#888', marginBottom: '5px' }}>Frames Processed</div>
            <div style={{ fontWeight: '500' }}>{results.frames_processed} ({((results.frames_processed / results.video_total_frames) * 100).toFixed(0)}%)</div>
          </div>
        </div>
      </div>

      {/* Detection Classes */}
      {results.m1_detections_by_class && Object.keys(results.m1_detections_by_class).length > 0 && (
        <div style={{
          marginTop: '20px',
          backgroundColor: '#fafafa',
          padding: '20px',
          borderRadius: '8px',
          border: '1px solid #e0e0e0'
        }}>
          <h4 style={{ marginTop: 0, marginBottom: '15px', color: '#555' }}>
            Detected Classes
          </h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
            {Object.entries(results.m1_detections_by_class).map(([className, count]) => (
              <div
                key={className}
                style={{
                  backgroundColor: '#fff',
                  padding: '10px 15px',
                  borderRadius: '6px',
                  border: '1px solid #e0e0e0',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}
              >
                <span style={{ fontWeight: '500', textTransform: 'capitalize' }}>
                  {className}
                </span>
                <span style={{
                  backgroundColor: '#2196F3',
                  color: '#fff',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: 'bold'
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
