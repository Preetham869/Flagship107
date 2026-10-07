/**
 * Loading and Empty State Components
 */

export const LoadingSpinner = ({ message = 'Processing...' }) => (
  <div style={{
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '60px 20px',
    color: '#90a4ae'
  }}>
    <div style={{
      width: '48px',
      height: '48px',
      border: '4px solid #37474f',
      borderTop: '4px solid #58a6ff',
      borderRadius: '50%',
      animation: 'spin 1s linear infinite',
      marginBottom: '20px'
    }} />
    <div style={{ fontSize: '14px', fontWeight: '500' }}>{message}</div>
    <style>{`
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `}</style>
  </div>
);

export const UploadingState = ({ progress }) => (
  <div style={{
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '60px 20px',
    color: '#eceff1'
  }}>
    <div style={{
      width: '64px',
      height: '64px',
      marginBottom: '24px',
      position: 'relative'
    }}>
      <svg viewBox="0 0 64 64" style={{ width: '100%', height: '100%' }}>
        <circle cx="32" cy="32" r="28" fill="none" stroke="#37474f" strokeWidth="4" />
        <circle 
          cx="32" 
          cy="32" 
          r="28" 
          fill="none" 
          stroke="#58a6ff" 
          strokeWidth="4"
          strokeDasharray="175.84"
          strokeDashoffset={175.84 * (1 - (progress || 0) / 100)}
          strokeLinecap="round"
          transform="rotate(-90 32 32)"
          style={{ transition: 'stroke-dashoffset 0.3s' }}
        />
      </svg>
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        fontSize: '16px',
        fontWeight: '600',
        color: '#58a6ff'
      }}>
        {progress || 0}%
      </div>
    </div>
    <div style={{ fontSize: '16px', fontWeight: '500', marginBottom: '8px' }}>
      Uploading Video
    </div>
    <div style={{ fontSize: '13px', color: '#90a4ae' }}>
      Please wait...
    </div>
  </div>
);

export const ProcessingState = ({ status, progress }) => (
  <div style={{
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '60px 20px',
    color: '#eceff1'
  }}>
    <LoadingSpinner message="" />
    <div style={{ fontSize: '16px', fontWeight: '500', marginBottom: '8px' }}>
      Processing Video Intelligence
    </div>
    {status && (
      <div style={{ fontSize: '13px', color: '#90a4ae', marginBottom: '12px' }}>
        {status}
      </div>
    )}
    {progress !== undefined && progress !== null && (
      <div style={{
        width: '300px',
        height: '6px',
        backgroundColor: '#37474f',
        borderRadius: '3px',
        overflow: 'hidden',
        marginTop: '8px'
      }}>
        <div style={{
          width: `${progress}%`,
          height: '100%',
          backgroundColor: '#58a6ff',
          transition: 'width 0.3s',
          borderRadius: '3px'
        }} />
      </div>
    )}
  </div>
);

export const EmptyState = ({ 
  icon = '◯', 
  title = 'No Data', 
  message = 'No data available',
  type = 'info' // 'info' | 'success' | 'warning'
}) => {
  const getColor = () => {
    switch (type) {
      case 'success': return '#4caf50';
      case 'warning': return '#ff9800';
      default: return '#90a4ae';
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '60px 20px',
      color: '#90a4ae',
      textAlign: 'center'
    }}>
      <div style={{
        fontSize: '48px',
        marginBottom: '16px',
        color: getColor(),
        opacity: 0.6
      }}>
        {icon}
      </div>
      <div style={{ fontSize: '16px', fontWeight: '500', color: '#b0bec5', marginBottom: '8px' }}>
        {title}
      </div>
      <div style={{ fontSize: '13px', color: '#78909c', maxWidth: '400px' }}>
        {message}
      </div>
    </div>
  );
};

export const ErrorState = ({ error, onRetry }) => (
  <div style={{
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '60px 20px',
    color: '#eceff1',
    textAlign: 'center'
  }}>
    <div style={{
      fontSize: '48px',
      marginBottom: '16px',
      color: '#f44336',
      opacity: 0.8
    }}>
      ⚠
    </div>
    <div style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px', color: '#f44336' }}>
      Processing Error
    </div>
    <div style={{ fontSize: '14px', color: '#b0bec5', marginBottom: '24px', maxWidth: '500px' }}>
      {error || 'An error occurred during video processing. Please try again.'}
    </div>
    {onRetry && (
      <button
        onClick={onRetry}
        style={{
          padding: '10px 24px',
          backgroundColor: '#58a6ff',
          color: '#fff',
          border: 'none',
          borderRadius: '6px',
          fontSize: '14px',
          fontWeight: '500',
          cursor: 'pointer',
          transition: 'background-color 0.2s'
        }}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#3182ce'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#58a6ff'}
      >
        Try Again
      </button>
    )}
  </div>
);

export const M9UnavailableState = () => (
  <div style={{
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '40px 20px',
    color: '#90a4ae',
    textAlign: 'center',
    backgroundColor: '#263238',
    borderRadius: '8px',
    border: '1px solid #37474f'
  }}>
    <div style={{
      fontSize: '36px',
      marginBottom: '16px',
      color: '#58a6ff',
      opacity: 0.6
    }}>
      ◈
    </div>
    <div style={{ fontSize: '15px', fontWeight: '500', color: '#b0bec5', marginBottom: '8px' }}>
      AI Explanation Unavailable
    </div>
    <div style={{ fontSize: '13px', color: '#78909c', maxWidth: '450px', lineHeight: '1.6' }}>
      Local AI explanation (M9/Qwen) is currently unavailable.
      All deterministic analysis results (M1-M8) remain available in other tabs.
    </div>
  </div>
);
