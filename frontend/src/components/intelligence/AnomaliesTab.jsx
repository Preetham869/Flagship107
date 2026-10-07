/**
 * Anomalies Tab - M4 anomaly detection results with selection integration
 */
import { useState } from 'react';
import { useSelection } from '../../context/SelectionContext';
import { EmptyState } from '../LoadingStates';

const AnomaliesTab = ({ results, onSeek }) => {
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const { selectedItem, selectAnomaly } = useSelection();
  
  const anomalies = results.all_anomalies || [];
  
  // Get unique types
  const anomalyTypes = ['all', ...new Set(anomalies.map(a => a.anomaly_type))];
  
  // Filter anomalies
  const filteredAnomalies = anomalies.filter(anomaly => {
    if (selectedSeverity !== 'all' && anomaly.severity !== selectedSeverity) return false;
    if (selectedType !== 'all' && anomaly.anomaly_type !== selectedType) return false;
    return true;
  });

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high': return { bg: '#f4433622', color: '#f44336', border: '#f44336' };
      case 'medium': return { bg: '#ff980022', color: '#ff9800', border: '#ff9800' };
      case 'low': return { bg: '#4caf5022', color: '#4caf50', border: '#4caf50' };
      default: return { bg: '#78909c22', color: '#78909c', border: '#78909c' };
    }
  };

  const handleAnomalyClick = (anomaly) => {
    selectAnomaly(anomaly);
    onSeek?.(anomaly.timestamp);
  };

  const isSelected = (anomaly) => {
    return selectedItem?.event_id === anomaly.event_id;
  };

  return (
    <div style={{ padding: '20px', maxHeight: 'calc(100vh - 400px)', overflowY: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3 style={{ margin: 0, color: '#eceff1', fontSize: '15px', fontWeight: '600' }}>
          Anomalies ({filteredAnomalies.length}{anomalies.length !== filteredAnomalies.length && `/${anomalies.length}`})
        </h3>
        
        {/* Filters */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid #37474f',
              backgroundColor: '#263238',
              color: '#b0bec5',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: '500'
            }}
          >
            <option value="all">All Severities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid #37474f',
              backgroundColor: '#263238',
              color: '#b0bec5',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: '500'
            }}
          >
            {anomalyTypes.map(type => (
              <option key={type} value={type}>
                {type === 'all' ? 'All Types' : type.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
        </div>
      </div>

      {filteredAnomalies.length === 0 ? (
        <EmptyState
          icon="⚠"
          title={anomalies.length === 0 ? "No Anomalies Detected" : "No Matching Anomalies"}
          message={anomalies.length === 0 ? 
            "No unusual behavior patterns were identified in this video." :
            "No anomalies match the selected filters. Try adjusting your filter criteria."
          }
          type={anomalies.length === 0 ? "success" : "info"}
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {filteredAnomalies.map((anomaly, index) => {
            const severityStyle = getSeverityColor(anomaly.severity);
            const selected = isSelected(anomaly);
            
            return (
              <div
                key={anomaly.event_id || index}
                style={{
                  backgroundColor: selected ? '#263238' : '#1e2832',
                  border: selected ? `2px solid #7e57c2` : `1px solid #37474f`,
                  borderLeft: `4px solid ${severityStyle.border}`,
                  borderRadius: '8px',
                  padding: '14px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onClick={() => handleAnomalyClick(anomaly)}
                onMouseEnter={(e) => {
                  if (!selected) {
                    e.currentTarget.style.backgroundColor = '#263238';
                    e.currentTarget.style.borderColor = '#455a64';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!selected) {
                    e.currentTarget.style.backgroundColor = '#1e2832';
                    e.currentTarget.style.borderColor = '#37474f';
                  }
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px', flexWrap: 'wrap' }}>
                      <span style={{
                        fontSize: '14px',
                        fontWeight: '600',
                        color: '#eceff1',
                        textTransform: 'capitalize'
                      }}>
                        {anomaly.anomaly_type.replace(/_/g, ' ')}
                      </span>
                      <span style={{
                        backgroundColor: severityStyle.bg,
                        color: severityStyle.color,
                        padding: '3px 10px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: '600',
                        textTransform: 'uppercase',
                        border: `1px solid ${severityStyle.border}44`
                      }}>
                        {anomaly.severity}
                      </span>
                      <span style={{
                        backgroundColor: '#263238',
                        color: '#90a4ae',
                        padding: '3px 10px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: '500'
                      }}>
                        {(anomaly.anomaly_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#90a4ae' }}>
                      Track #{anomaly.track_id} • {anomaly.timestamp.toFixed(2)}s
                    </div>
                  </div>
                </div>

                {anomaly.explanation && (
                  <div style={{
                    fontSize: '12px',
                    color: '#b0bec5',
                    lineHeight: '1.6',
                    marginTop: '10px',
                    padding: '10px',
                    backgroundColor: '#0d1117',
                    borderRadius: '6px',
                    border: '1px solid #263238'
                  }}>
                    {anomaly.explanation}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AnomaliesTab;
