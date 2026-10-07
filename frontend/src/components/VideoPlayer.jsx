/**
 * Video Player Component
 * Professional video analysis interface with dark theme
 */
import { useRef, useState, useEffect } from 'react';
import VideoOverlay from './VideoOverlay';

const VideoPlayer = ({ videoUrl, onTimeUpdate, currentTime, selectedItem, selectedType, videoMetadata, allTracks }) => {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [localTime, setLocalTime] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isHovering, setIsHovering] = useState(false);

  // Update local time when video plays
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      const time = video.currentTime;
      setLocalTime(time);
      onTimeUpdate?.(time);
    };

    const handleLoadedMetadata = () => {
      setDuration(video.duration);
    };

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleEnded = () => setIsPlaying(false);

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    video.addEventListener('ended', handleEnded);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('ended', handleEnded);
    };
  }, [onTimeUpdate]);

  // Seek to timestamp when currentTime prop changes
  useEffect(() => {
    if (currentTime !== undefined && currentTime !== null && videoRef.current) {
      videoRef.current.currentTime = currentTime;
    }
  }, [currentTime]);

  const togglePlayPause = () => {
    const video = videoRef.current;
    if (!video) return;
    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
  };

  const handleSeek = (e) => {
    const video = videoRef.current;
    if (!video) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    video.currentTime = percentage * duration;
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
    }
  };

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatTimePrecise = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00.00';
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(2);
    return `${mins}:${secs.padStart(5, '0')}`;
  };

  return (
    <div 
      style={{ 
        backgroundColor: '#0d1117', 
        borderRadius: '8px', 
        overflow: 'hidden',
        border: '1px solid #263238',
        boxShadow: '0 4px 12px rgba(0,0,0,0.6)'
      }}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      {/* Video Container */}
      <div style={{ position: 'relative', backgroundColor: '#000' }}>
        <video
          ref={videoRef}
          src={videoUrl}
          style={{ 
            width: '100%', 
            display: 'block',
            minHeight: '400px',
            maxHeight: '600px',
            objectFit: 'contain'
          }}
        />
        
        {/* Bounding Box Overlay */}
        <VideoOverlay
          videoRef={videoRef}
          allTracks={allTracks}
          currentTime={localTime}
          videoMetadata={videoMetadata}
          selectedItem={selectedItem}
          selectedType={selectedType}
        />
        
        {/* Selected Item Overlay */}
        {selectedItem && (
          <div style={{
            position: 'absolute',
            top: '12px',
            left: '12px',
            backgroundColor: 'rgba(126, 87, 194, 0.95)',
            color: '#fff',
            padding: '8px 14px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '500',
            boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
            maxWidth: '250px',
            backdropFilter: 'blur(4px)'
          }}>
            {selectedItem.anomaly_type && (
              <div>⚠ {selectedItem.anomaly_type.replace(/_/g, ' ')}</div>
            )}
            {selectedItem.event_type && (
              <div>◆ {selectedItem.event_type.replace(/_/g, ' ')}</div>
            )}
            {selectedItem.scene_number !== undefined && (
              <div>◈ Scene #{selectedItem.scene_number}</div>
            )}
          </div>
        )}

        {/* Video Metadata Overlay */}
        {videoMetadata && isHovering && (
          <div style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            backgroundColor: 'rgba(13, 17, 23, 0.85)',
            color: '#b0bec5',
            padding: '8px 12px',
            borderRadius: '6px',
            fontSize: '11px',
            backdropFilter: 'blur(4px)',
            border: '1px solid #263238'
          }}>
            <div>{videoMetadata.video_width}×{videoMetadata.video_height}</div>
            <div>{videoMetadata.video_fps?.toFixed(2)} FPS</div>
          </div>
        )}
      </div>
      
      {/* Controls */}
      <div style={{ 
        padding: '14px 18px', 
        backgroundColor: '#161b22',
        borderTop: '1px solid #263238'
      }}>
        {/* Progress Bar */}
        <div
          onClick={handleSeek}
          style={{
            width: '100%',
            height: '8px',
            backgroundColor: '#263238',
            borderRadius: '4px',
            cursor: 'pointer',
            marginBottom: '14px',
            position: 'relative',
            overflow: 'hidden'
          }}
        >
          <div style={{
            width: `${(localTime / duration) * 100}%`,
            height: '100%',
            backgroundColor: '#58a6ff',
            borderRadius: '4px',
            transition: 'width 0.1s',
            boxShadow: '0 0 8px rgba(126, 87, 194, 0.6)'
          }} />
        </div>

        {/* Control Buttons and Time */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          gap: '15px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              onClick={togglePlayPause}
              style={{
                padding: '8px 18px',
                backgroundColor: '#58a6ff',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: '500',
                transition: 'background-color 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#3182ce'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#58a6ff'}
            >
              {isPlaying ? '⏸' : '▶'} {isPlaying ? 'Pause' : 'Play'}
            </button>
            
            {/* Volume Control */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '14px', color: '#b0bec5' }}>
                {volume === 0 ? '🔇' : '🔊'}
              </span>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={volume}
                onChange={handleVolumeChange}
                style={{
                  width: '70px',
                  accentColor: '#58a6ff'
                }}
              />
            </div>
          </div>
          
          <div style={{ 
            fontSize: '14px', 
            color: '#eceff1',
            fontFamily: 'monospace',
            fontWeight: '500'
          }}>
            {formatTimePrecise(localTime)} <span style={{ color: '#546e7a' }}>/</span> {formatTime(duration)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoPlayer;
