/**
 * Investigation Header
 * Shows current investigation status and selection details
 */
import { useSelection } from '../context/SelectionContext';

const InvestigationHeader = () => {
  const { selectedItem, selectedType, clearSelection } = useSelection();

  if (!selectedItem) {
    return (
      <div style={{
        backgroundColor: '#161b22',
        border: '1px solid #263238',
        borderRadius: '8px',
        padding: '16px 20px',
        marginBottom: '20px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      }}>
        <span style={{ fontSize: '20px', opacity: 0.6 }}>🔍</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '14px', color: '#8b95a8', fontWeight: '500' }}>
            Investigation Mode
          </div>
          <div style={{ fontSize: '12px', color: '#6b7485', marginTop: '2px' }}>
            Select an event, anomaly, track, or scene to investigate
          </div>
        </div>
      </div>
    );
  }

  // Format selection details based on type
  const getInvestigationDetails = () => {
    switch (selectedType) {
      case 'event':
        return {
          icon: '◆',
          title: selectedItem.event_type?.replace(/_/g, ' ') || 'Event',
          details: [
            selectedItem.track_ids?.length > 0 && `Tracks: ${selectedItem.track_ids.map(id => `#${id}`).join(', ')}`,
            selectedItem.start_timestamp !== undefined && selectedItem.end_timestamp !== undefined && 
              `Time: ${selectedItem.start_timestamp.toFixed(2)}s → ${selectedItem.end_timestamp.toFixed(2)}s`,
            selectedItem.severity && `Severity: ${selectedItem.severity}`,
            selectedItem.confidence !== undefined && `Confidence: ${(selectedItem.confidence * 100).toFixed(0)}%`
          ].filter(Boolean),
          color: '#5a9fd4'
        };
      
      case 'anomaly':
        return {
          icon: '⚠',
          title: selectedItem.anomaly_type?.replace(/_/g, ' ') || 'Anomaly',
          details: [
            selectedItem.track_id && `Track: #${selectedItem.track_id}`,
            selectedItem.timestamp !== undefined && `Time: ${selectedItem.timestamp.toFixed(2)}s`,
            selectedItem.severity && `Severity: ${selectedItem.severity}`,
            selectedItem.anomaly_score !== undefined && `Score: ${(selectedItem.anomaly_score * 100).toFixed(0)}%`
          ].filter(Boolean),
          color: '#ff9800'
        };
      
      case 'track':
        return {
          icon: '👤',
          title: `Track #${selectedItem.track_id || selectedItem.id || '?'}`,
          details: [
            selectedItem.class_name && `Type: ${selectedItem.class_name}`,
            selectedItem.first_seen !== undefined && selectedItem.last_seen !== undefined && 
              `Duration: ${selectedItem.first_seen.toFixed(2)}s → ${selectedItem.last_seen.toFixed(2)}s`,
            selectedItem.avg_speed !== undefined && `Avg Speed: ${selectedItem.avg_speed.toFixed(1)} px/s`,
            selectedItem.anomaly_count !== undefined && `Anomalies: ${selectedItem.anomaly_count}`
          ].filter(Boolean),
          color: '#4caf50'
        };
      
      case 'scene':
        return {
          icon: '◈',
          title: `Scene #${selectedItem.scene_number || '?'}`,
          details: [
            selectedItem.start_timestamp !== undefined && selectedItem.end_timestamp !== undefined && 
              `Time: ${selectedItem.start_timestamp.toFixed(2)}s → ${selectedItem.end_timestamp.toFixed(2)}s`,
            selectedItem.participating_track_ids?.length > 0 && 
              `Tracks: ${selectedItem.participating_track_ids.map(id => `#${id}`).join(', ')}`,
            selectedItem.scene_type && `Type: ${selectedItem.scene_type.replace(/_/g, ' ')}`,
            selectedItem.complexity_score !== undefined && `Complexity: ${selectedItem.complexity_score.toFixed(1)}`
          ].filter(Boolean),
          color: '#9c27b0'
        };
      
      case 'relationship':
        return {
          icon: '↔',
          title: selectedItem.relationship_type?.replace(/_/g, ' ') || 'Relationship',
          details: [
            selectedItem.entity_1_id && selectedItem.entity_2_id && 
              `Entities: #${selectedItem.entity_1_id} ↔ #${selectedItem.entity_2_id}`,
            selectedItem.start_timestamp !== undefined && selectedItem.end_timestamp !== undefined && 
              `Time: ${selectedItem.start_timestamp.toFixed(2)}s → ${selectedItem.end_timestamp.toFixed(2)}s`,
            selectedItem.confidence !== undefined && `Confidence: ${(selectedItem.confidence * 100).toFixed(0)}%`
          ].filter(Boolean),
          color: '#2196f3'
        };
      
      default:
        return {
          icon: '•',
          title: 'Item Selected',
          details: [],
          color: '#78909c'
        };
    }
  };

  const { icon, title, details, color } = getInvestigationDetails();

  return (
    <div style={{
      backgroundColor: '#161b22',
      border: `1px solid ${color}44`,
      borderLeft: `4px solid ${color}`,
      borderRadius: '8px',
      padding: '16px 20px',
      marginBottom: '20px',
      boxShadow: `0 0 12px ${color}22`
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
        <div style={{
          fontSize: '24px',
          lineHeight: 1,
          opacity: 0.9
        }}>
          {icon}
        </div>
        
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <div style={{
              fontSize: '11px',
              color: color,
              fontWeight: '600',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              Investigating
            </div>
          </div>
          
          <div style={{ 
            fontSize: '16px', 
            fontWeight: '600', 
            color: '#e0e6ed',
            marginBottom: '10px',
            textTransform: 'capitalize'
          }}>
            {title}
          </div>
          
          {details.length > 0 && (
            <div style={{ 
              display: 'flex', 
              flexWrap: 'wrap', 
              gap: '12px',
              fontSize: '12px',
              color: '#a0aab8'
            }}>
              {details.map((detail, idx) => (
                <div key={idx} style={{ 
                  display: 'flex', 
                  alignItems: 'center',
                  padding: '4px 10px',
                  backgroundColor: '#0d1220',
                  borderRadius: '4px',
                  border: '1px solid #1a2332'
                }}>
                  {detail}
                </div>
              ))}
            </div>
          )}
        </div>
        
        <button
          onClick={clearSelection}
          style={{
            padding: '8px 14px',
            backgroundColor: '#263238',
            color: '#b0bec5',
            border: '1px solid #37474f',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '12px',
            fontWeight: '500',
            transition: 'all 0.2s',
            whiteSpace: 'nowrap'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#2d3a42';
            e.currentTarget.style.color = '#eceff1';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#263238';
            e.currentTarget.style.color = '#b0bec5';
          }}
        >
          Clear Selection
        </button>
      </div>
    </div>
  );
};

export default InvestigationHeader;
