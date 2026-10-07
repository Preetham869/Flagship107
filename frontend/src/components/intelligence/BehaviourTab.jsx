/**
 * Behaviour Tab - M3 behavior analysis visualization
 */

const BehaviourTab = ({ results }) => {
  const statesObserved = results.m3_states_observed || {};
  const totalBehaviors = results.m3_total_behaviors || 0;
  
  const stateColors = {
    'stationary': '#607D8B',
    'moving': '#2196F3',
    'fast-moving': '#FF9800'
  };

  return (
    <div style={{ padding: '20px' }}>
      <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#333' }}>
        Behavior Analysis
      </h3>

      {/* Summary Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '15px',
        marginBottom: '30px'
      }}>
        <div style={{
          backgroundColor: '#e0f7fa',
          padding: '20px',
          borderRadius: '8px',
          border: '1px solid #00BCD420'
        }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#00BCD4', marginBottom: '5px' }}>
            {totalBehaviors}
          </div>
          <div style={{ fontSize: '14px', fontWeight: '500', color: '#555' }}>
            Total Behaviors
          </div>
        </div>
        <div style={{
          backgroundColor: '#e0f2f1',
          padding: '20px',
          borderRadius: '8px',
          border: '1px solid #00968820'
        }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#009688', marginBottom: '5px' }}>
            {results.m3_avg_speed?.toFixed(1) || 0}
          </div>
          <div style={{ fontSize: '14px', fontWeight: '500', color: '#555' }}>
            Avg Speed (px/s)
          </div>
        </div>
        <div style={{
          backgroundColor: '#fff3e0',
          padding: '20px',
          borderRadius: '8px',
          border: '1px solid #FF980020'
        }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#FF9800', marginBottom: '5px' }}>
            {results.m3_max_speed?.toFixed(1) || 0}
          </div>
          <div style={{ fontSize: '14px', fontWeight: '500', color: '#555' }}>
            Max Speed (px/s)
          </div>
        </div>
      </div>

      {/* Behavior State Distribution */}
      <div style={{
        backgroundColor: '#fafafa',
        padding: '20px',
        borderRadius: '8px',
        border: '1px solid #e0e0e0'
      }}>
        <h4 style={{ marginTop: 0, marginBottom: '15px', color: '#555' }}>
          Behavior State Distribution
        </h4>
        
        {Object.keys(statesObserved).length === 0 ? (
          <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
            No behavior states observed
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            {Object.entries(statesObserved).map(([state, count]) => {
              const percentage = totalBehaviors > 0 ? (count / totalBehaviors) * 100 : 0;
              const color = stateColors[state] || '#607D8B';
              
              return (
                <div key={state}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '8px',
                    fontSize: '14px'
                  }}>
                    <span style={{ fontWeight: '500', textTransform: 'capitalize' }}>
                      {state.replace(/-/g, ' ')}
                    </span>
                    <span style={{ color: '#666' }}>
                      {count} ({percentage.toFixed(1)}%)
                    </span>
                  </div>
                  <div style={{
                    width: '100%',
                    height: '24px',
                    backgroundColor: '#e0e0e0',
                    borderRadius: '12px',
                    overflow: 'hidden',
                    position: 'relative'
                  }}>
                    <div style={{
                      width: `${percentage}%`,
                      height: '100%',
                      backgroundColor: color,
                      transition: 'width 0.3s ease',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-end',
                      paddingRight: percentage > 10 ? '10px' : '0'
                    }}>
                      {percentage > 10 && (
                        <span style={{ color: '#fff', fontSize: '12px', fontWeight: 'bold' }}>
                          {percentage.toFixed(0)}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Behavior Timeline Visualization */}
      <div style={{
        marginTop: '20px',
        backgroundColor: '#fafafa',
        padding: '20px',
        borderRadius: '8px',
        border: '1px solid #e0e0e0'
      }}>
        <h4 style={{ marginTop: 0, marginBottom: '15px', color: '#555' }}>
          Speed Distribution
        </h4>
        <div style={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: '10px',
          height: '150px',
          padding: '10px',
          backgroundColor: '#fff',
          borderRadius: '4px'
        }}>
          {Object.entries(statesObserved).map(([state, count]) => {
            const maxCount = Math.max(...Object.values(statesObserved));
            const height = (count / maxCount) * 100;
            const color = stateColors[state] || '#607D8B';
            
            return (
              <div
                key={state}
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '10px'
                }}
              >
                <div style={{
                  width: '100%',
                  height: `${height}%`,
                  backgroundColor: color,
                  borderRadius: '4px 4px 0 0',
                  transition: 'height 0.3s ease',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'flex-start',
                  alignItems: 'center',
                  paddingTop: '5px',
                  position: 'relative'
                }}>
                  <span style={{
                    fontSize: '12px',
                    fontWeight: 'bold',
                    color: '#fff'
                  }}>
                    {count}
                  </span>
                </div>
                <div style={{
                  fontSize: '11px',
                  textAlign: 'center',
                  textTransform: 'capitalize',
                  color: '#666'
                }}>
                  {state.replace(/-/g, ' ')}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default BehaviourTab;
