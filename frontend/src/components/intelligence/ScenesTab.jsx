/**
 * Scenes Tab - M8 contextual scenes
 */

const ScenesTab = ({ results, onSeek }) => {
  const scenes = results.all_scenes || [];

  return (
    <div style={{ padding: '20px' }}>
      <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#333' }}>
        Contextual Scenes ({scenes.length})
      </h3>

      {scenes.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '40px',
          color: '#999',
          backgroundColor: '#fafafa',
          borderRadius: '8px'
        }}>
          No contextual scenes generated
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {scenes.map((scene, index) => {
            return (
              <div
                key={scene.scene_id || index}
                style={{
                  backgroundColor: '#fff',
                  border: '1px solid #e0e0e0',
                  borderLeft: '4px solid #3182ce',
                  borderRadius: '8px',
                  padding: '20px',
                  cursor: 'pointer',
                  transition: 'box-shadow 0.2s, transform 0.2s'
                }}
                onClick={() => onSeek?.(scene.start_timestamp)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(103, 58, 183, 0.15)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '15px' }}>
                  <div>
                    <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#3182ce', marginBottom: '5px' }}>
                      Scene {scene.scene_number || index + 1}
                    </div>
                    <div style={{ fontSize: '13px', color: '#666' }}>
                      {scene.start_timestamp.toFixed(2)}s - {scene.end_timestamp.toFixed(2)}s
                      ({scene.duration_seconds.toFixed(2)}s duration)
                    </div>
                  </div>
                  <div style={{
                    backgroundColor: '#ede7f6',
                    color: '#3182ce',
                    padding: '5px 12px',
                    borderRadius: '6px',
                    fontSize: '13px',
                    fontWeight: '500'
                  }}>
                    Frames {scene.start_frame} - {scene.end_frame}
                  </div>
                </div>

                {/* Participating Tracks */}
                <div style={{
                  marginBottom: '15px',
                  padding: '12px',
                  backgroundColor: '#fafafa',
                  borderRadius: '6px'
                }}>
                  <div style={{ fontSize: '12px', color: '#888', marginBottom: '8px' }}>
                    Participating Tracks
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {(scene.participating_track_ids || []).map(trackId => (
                      <span
                        key={trackId}
                        style={{
                          backgroundColor: '#3182ce',
                          color: '#fff',
                          padding: '4px 10px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: '500'
                        }}
                      >
                        Track #{trackId}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Summary */}
                {scene.scene_summary && (
                  <div style={{
                    fontSize: '14px',
                    color: '#555',
                    lineHeight: '1.6',
                    marginBottom: '15px',
                    padding: '12px',
                    backgroundColor: '#f9f9f9',
                    borderRadius: '6px',
                    borderLeft: '3px solid #3182ce'
                  }}>
                    {scene.scene_summary}
                  </div>
                )}

                {/* Key Observations */}
                {scene.key_observations && scene.key_observations.length > 0 && (
                  <div style={{ marginBottom: '15px' }}>
                    <div style={{ fontSize: '13px', fontWeight: '500', color: '#555', marginBottom: '8px' }}>
                      Key Observations:
                    </div>
                    <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: '#666', lineHeight: '1.8' }}>
                      {scene.key_observations.map((obs, i) => (
                        <li key={i}>{obs}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Track Summaries */}
                {scene.track_summaries && scene.track_summaries.length > 0 && (
                  <details style={{ marginTop: '15px' }}>
                    <summary style={{
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: '500',
                      color: '#3182ce',
                      padding: '8px 0'
                    }}>
                      Track Details ({scene.track_summaries.length})
                    </summary>
                    <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {scene.track_summaries.map((track, i) => (
                        <div
                          key={i}
                          style={{
                            padding: '12px',
                            backgroundColor: '#fafafa',
                            borderRadius: '6px',
                            fontSize: '12px'
                          }}
                        >
                          <div style={{ fontWeight: '500', marginBottom: '5px' }}>
                            Track #{track.track_id}
                          </div>
                          <div style={{ color: '#666' }}>
                            {track.narrative}
                          </div>
                        </div>
                      ))}
                    </div>
                  </details>
                )}

                {/* Pattern Evidence */}
                {scene.patterns && scene.patterns.length > 0 && (
                  <details style={{ marginTop: '10px' }}>
                    <summary style={{
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: '500',
                      color: '#3182ce',
                      padding: '8px 0'
                    }}>
                      Detected Patterns ({scene.patterns.length})
                    </summary>
                    <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {scene.patterns.map((pattern, i) => (
                        <div
                          key={i}
                          style={{
                            padding: '10px',
                            backgroundColor: '#f9f9f9',
                            borderRadius: '4px',
                            fontSize: '12px',
                            color: '#666'
                          }}
                        >
                          <div style={{ fontWeight: '500', marginBottom: '3px' }}>
                            {pattern.pattern_type?.replace(/_/g, ' ') || 'Pattern'}
                          </div>
                          <div>{pattern.description}</div>
                        </div>
                      ))}
                    </div>
                  </details>
                )}

                {/* Evidence Provenance */}
                {scene.evidence_provenance && (
                  <details style={{ marginTop: '10px' }}>
                    <summary style={{
                      cursor: 'pointer',
                      fontSize: '12px',
                      color: '#666',
                      padding: '5px 0'
                    }}>
                      Evidence Provenance
                    </summary>
                    <pre style={{
                      fontSize: '11px',
                      backgroundColor: '#f9f9f9',
                      padding: '10px',
                      borderRadius: '4px',
                      overflow: 'auto',
                      marginTop: '5px',
                      maxHeight: '250px'
                    }}>
                      {JSON.stringify(scene.evidence_provenance, null, 2)}
                    </pre>
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

export default ScenesTab;
