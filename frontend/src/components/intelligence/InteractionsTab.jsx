/**
 * Interactions Tab - M6 entity relationships
 */

const InteractionsTab = ({ results, onSeek }) => {
  const relationships = results.all_relationships || [];
  const trackedPairs = results.m6_tracked_pairs || 0;

  const getRelationshipIcon = (type) => {
    const icons = {
      'proximity': '↔',
      'approach': '→',
      'departure': '←',
      'co_movement': '⇄',
      'following': '➜',
      'group_formation': '⊕',
      'group_separation': '⊖'
    };
    return icons[type] || '•';
  };

  const getRelationshipColor = (type) => {
    const colors = {
      'proximity': '#2196F3',
      'approach': '#4CAF50',
      'departure': '#FF5722',
      'co_movement': '#9C27B0',
      'following': '#FF9800',
      'group_formation': '#00BCD4',
      'group_separation': '#F44336'
    };
    return colors[type] || '#607D8B';
  };

  return (
    <div style={{ padding: '20px', height: '100%', backgroundColor: '#0a0e1a' }}>
      <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#e0e6ed', fontSize: '18px', fontWeight: '600' }}>
        Entity Interactions ({relationships.length})
      </h3>

      {relationships.length === 0 ? (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '48px 32px',
          backgroundColor: '#0d1220',
          border: '1px solid #1a2332',
          borderRadius: '12px',
          maxWidth: '800px',
          margin: '0 auto'
        }}>
          {/* Icon */}
          <div style={{
            width: '80px',
            height: '80px',
            borderRadius: '50%',
            backgroundColor: '#1a2332',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '24px',
            border: '2px solid #243447'
          }}>
            <span style={{ fontSize: '36px', opacity: 0.6 }}>↔</span>
          </div>

          {/* Title */}
          <div style={{
            fontSize: '20px',
            fontWeight: '600',
            color: '#e0e6ed',
            marginBottom: '12px',
            textAlign: 'center'
          }}>
            No Entity Relationships Detected
          </div>

          {/* Analytical Explanation */}
          <div style={{
            fontSize: '14px',
            color: '#8b95a8',
            lineHeight: '1.7',
            marginBottom: '32px',
            textAlign: 'center',
            maxWidth: '560px'
          }}>
            M6 analyzed <strong style={{ color: '#a0aab8' }}>{trackedPairs} entity pairs</strong> across all video frames, 
            but none satisfied the spatial and temporal thresholds required for relationship classification.
          </div>

          {/* Detection Criteria Panel */}
          <div style={{
            width: '100%',
            maxWidth: '640px',
            backgroundColor: '#0a0e1a',
            border: '1px solid #1a2332',
            borderRadius: '8px',
            padding: '20px'
          }}>
            <div style={{
              fontSize: '13px',
              fontWeight: '600',
              color: '#a0aab8',
              marginBottom: '16px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              Relationship Detection Thresholds
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {/* Spatial Threshold */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '10px 12px',
                backgroundColor: '#0d1220',
                borderRadius: '6px',
                border: '1px solid #1a2332'
              }}>
                <span style={{ fontSize: '13px', color: '#8b95a8' }}>
                  Proximity Radius
                </span>
                <span style={{ fontSize: '13px', color: '#5a9fd4', fontWeight: '500' }}>
                  ≤ 150px
                </span>
              </div>

              {/* Temporal Threshold */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '10px 12px',
                backgroundColor: '#0d1220',
                borderRadius: '6px',
                border: '1px solid #1a2332'
              }}>
                <span style={{ fontSize: '13px', color: '#8b95a8' }}>
                  Minimum Duration
                </span>
                <span style={{ fontSize: '13px', color: '#5a9fd4', fontWeight: '500' }}>
                  ≥ 2.0s
                </span>
              </div>

              {/* Observation Threshold */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '10px 12px',
                backgroundColor: '#0d1220',
                borderRadius: '6px',
                border: '1px solid #1a2332'
              }}>
                <span style={{ fontSize: '13px', color: '#8b95a8' }}>
                  Minimum Observations
                </span>
                <span style={{ fontSize: '13px', color: '#5a9fd4', fontWeight: '500' }}>
                  ≥ 5 frames
                </span>
              </div>
            </div>

            {/* Footer Note */}
            <div style={{
              marginTop: '16px',
              padding: '12px',
              backgroundColor: '#0a0e1a',
              borderRadius: '6px',
              border: '1px solid #1a2332'
            }}>
              <div style={{ fontSize: '12px', color: '#6b7485', lineHeight: '1.6' }}>
                <strong style={{ color: '#8b95a8' }}>Note:</strong> Relationships require sustained 
                spatial proximity between entities over multiple frames. Transient encounters 
                or brief co-occurrence are not classified as interactions.
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {relationships.map((relationship, index) => {
            const color = getRelationshipColor(relationship.relationship_type);
            const icon = getRelationshipIcon(relationship.relationship_type);
            
            return (
              <div
                key={relationship.relationship_id || index}
                style={{
                  backgroundColor: '#fff',
                  border: `1px solid ${color}40`,
                  borderLeft: `4px solid ${color}`,
                  borderRadius: '8px',
                  padding: '20px',
                  cursor: 'pointer',
                  transition: 'box-shadow 0.2s, transform 0.2s'
                }}
                onClick={() => onSeek?.(relationship.start_timestamp)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = `0 4px 12px ${color}20`;
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '5px' }}>
                      <span style={{ fontSize: '24px', color: color }}>
                        {icon}
                      </span>
                      <span style={{
                        fontSize: '18px',
                        fontWeight: 'bold',
                        color: '#333',
                        textTransform: 'capitalize'
                      }}>
                        {relationship.relationship_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <div style={{ fontSize: '13px', color: '#666' }}>
                      Tracks: {relationship.entity_1_id} ↔ {relationship.entity_2_id}
                    </div>
                  </div>
                  <div style={{
                    backgroundColor: `${color}10`,
                    color: color,
                    padding: '5px 12px',
                    borderRadius: '6px',
                    fontSize: '13px',
                    fontWeight: '500'
                  }}>
                    Confidence: {(relationship.confidence * 100).toFixed(0)}%
                  </div>
                </div>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                  gap: '12px',
                  marginBottom: '12px',
                  padding: '12px',
                  backgroundColor: '#fafafa',
                  borderRadius: '6px'
                }}>
                  <div>
                    <div style={{ fontSize: '11px', color: '#888', marginBottom: '3px' }}>Time Range</div>
                    <div style={{ fontSize: '14px', fontWeight: '500', color: '#555' }}>
                      {relationship.start_timestamp.toFixed(2)}s - {relationship.end_timestamp.toFixed(2)}s
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: '#888', marginBottom: '3px' }}>Duration</div>
                    <div style={{ fontSize: '14px', fontWeight: '500', color: '#555' }}>
                      {((relationship.end_timestamp - relationship.start_timestamp)).toFixed(2)}s
                    </div>
                  </div>
                  {relationship.distance !== undefined && (
                    <div>
                      <div style={{ fontSize: '11px', color: '#888', marginBottom: '3px' }}>Distance</div>
                      <div style={{ fontSize: '14px', fontWeight: '500', color: '#555' }}>
                        {relationship.distance.toFixed(1)} px
                      </div>
                    </div>
                  )}
                  <div>
                    <div style={{ fontSize: '11px', color: '#888', marginBottom: '3px' }}>Observations</div>
                    <div style={{ fontSize: '14px', fontWeight: '500', color: '#555' }}>
                      {relationship.observation_count || 'N/A'}
                    </div>
                  </div>
                </div>

                {relationship.explanation && (
                  <div style={{
                    fontSize: '13px',
                    color: '#555',
                    lineHeight: '1.6',
                    marginTop: '10px',
                    padding: '12px',
                    backgroundColor: '#f9f9f9',
                    borderRadius: '6px',
                    borderLeft: `3px solid ${color}`
                  }}>
                    {relationship.explanation}
                  </div>
                )}

                {relationship.evidence && (
                  <details style={{ marginTop: '10px' }}>
                    <summary style={{
                      cursor: 'pointer',
                      fontSize: '12px',
                      color: '#666',
                      padding: '5px 0'
                    }}>
                      View Evidence Details
                    </summary>
                    <pre style={{
                      fontSize: '11px',
                      backgroundColor: '#f9f9f9',
                      padding: '10px',
                      borderRadius: '4px',
                      overflow: 'auto',
                      marginTop: '5px',
                      maxHeight: '200px'
                    }}>
                      {JSON.stringify(relationship.evidence, null, 2)}
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

export default InteractionsTab;
