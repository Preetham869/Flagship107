/**
 * System Status Component
 * Displays processing metadata and system information
 */

const SystemStatus = ({ results }) => {
  if (!results) return null;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '25px',
      padding: '12px 20px',
      backgroundColor: '#263238',
      borderRadius: '6px',
      fontSize: '12px',
      color: '#b0bec5'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <span style={{ color: '#4caf50' }}>●</span>
        <span style={{ fontWeight: '500' }}>Local Processing</span>
      </div>
      
      <div style={{ height: '16px', width: '1px', backgroundColor: '#37474f' }} />
      
      <div>
        <span style={{ color: '#78909c' }}>Resolution:</span>{' '}
        <span style={{ color: '#eceff1', fontWeight: '500' }}>
          {results.video_width}×{results.video_height}
        </span>
      </div>
      
      <div>
        <span style={{ color: '#78909c' }}>FPS:</span>{' '}
        <span style={{ color: '#eceff1', fontWeight: '500' }}>
          {results.video_fps?.toFixed(2)}
        </span>
      </div>
      
      <div>
        <span style={{ color: '#78909c' }}>Duration:</span>{' '}
        <span style={{ color: '#eceff1', fontWeight: '500' }}>
          {results.video_duration?.toFixed(2)}s
        </span>
      </div>
      
      <div>
        <span style={{ color: '#78909c' }}>Frames:</span>{' '}
        <span style={{ color: '#eceff1', fontWeight: '500' }}>
          {results.frames_processed} / {results.video_total_frames}
        </span>
      </div>
      
      <div>
        <span style={{ color: '#78909c' }}>Processing Time:</span>{' '}
        <span style={{ color: '#eceff1', fontWeight: '500' }}>
          {results.processing_time?.toFixed(2)}s
        </span>
      </div>

      <div style={{ height: '16px', width: '1px', backgroundColor: '#37474f' }} />
      
      <div>
        <span style={{ color: '#78909c' }}>Detection:</span>{' '}
        <span style={{ color: '#eceff1', fontWeight: '500' }}>
          YOLOv8
        </span>
      </div>
    </div>
  );
};

export default SystemStatus;
