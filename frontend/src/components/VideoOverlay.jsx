/**
 * Video Overlay Component
 * Displays bounding boxes and track IDs overlaid on video
 * Uses actual M1/M2 detection coordinates
 */
import { useEffect, useState, useRef } from 'react';

const VideoOverlay = ({ 
  videoRef, 
  allTracks, 
  currentTime, 
  videoMetadata,
  selectedItem,
  selectedType 
}) => {
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const overlayRef = useRef(null);

  // Calculate frame index from current time
  useEffect(() => {
    if (!videoMetadata?.video_fps || currentTime === undefined) return;
    const fps = videoMetadata.video_fps;
    const frameIndex = Math.floor(currentTime * fps);
    setCurrentFrameIndex(Math.min(frameIndex, allTracks?.length - 1 || 0));
  }, [currentTime, videoMetadata, allTracks]);

  if (!allTracks || allTracks.length === 0 || !videoRef?.current || !videoMetadata) {
    return null;
  }

  const currentFrameTracks = allTracks[currentFrameIndex] || [];
  if (currentFrameTracks.length === 0) return null;

  // Get selected track IDs
  const selectedTrackIds = new Set();
  if (selectedType === 'anomaly' && selectedItem?.track_id) {
    selectedTrackIds.add(selectedItem.track_id);
  } else if (selectedType === 'event' && selectedItem?.track_ids) {
    selectedItem.track_ids.forEach(id => selectedTrackIds.add(id));
  } else if (selectedType === 'track' && (selectedItem?.track_id || selectedItem?.id)) {
    selectedTrackIds.add(selectedItem.track_id || selectedItem.id);
  }

  // Video element dimensions
  const video = videoRef.current;
  const videoDisplayWidth = video.offsetWidth;
  const videoDisplayHeight = video.offsetHeight;

  // Original video dimensions
  const videoActualWidth = videoMetadata.video_width;
  const videoActualHeight = videoMetadata.video_height;

  // Calculate scale and offset for object-fit: contain
  const videoAspect = videoActualWidth / videoActualHeight;
  const displayAspect = videoDisplayWidth / videoDisplayHeight;

  let scale, offsetX, offsetY;
  if (videoAspect > displayAspect) {
    // Video is wider - fit to width
    scale = videoDisplayWidth / videoActualWidth;
    offsetX = 0;
    offsetY = (videoDisplayHeight - (videoActualHeight * scale)) / 2;
  } else {
    // Video is taller - fit to height
    scale = videoDisplayHeight / videoActualHeight;
    offsetX = (videoDisplayWidth - (videoActualWidth * scale)) / 2;
    offsetY = 0;
  }

  return (
    <div
      ref={overlayRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 10
      }}
    >
      {currentFrameTracks.map((track, idx) => {
        const [x1, y1, x2, y2] = track.bbox;
        const isSelected = selectedTrackIds.has(track.track_id);

        // Transform coordinates to overlay space
        const overlayX = x1 * scale + offsetX;
        const overlayY = y1 * scale + offsetY;
        const overlayWidth = (x2 - x1) * scale;
        const overlayHeight = (y2 - y1) * scale;

        const boxColor = isSelected ? '#7e57c2' : '#5a9fd4';
        const opacity = isSelected ? 1 : 0.6;

        return (
          <div
            key={`${track.track_id}-${idx}`}
            style={{
              position: 'absolute',
              left: `${overlayX}px`,
              top: `${overlayY}px`,
              width: `${overlayWidth}px`,
              height: `${overlayHeight}px`,
              border: `2px solid ${boxColor}`,
              borderRadius: '4px',
              opacity: opacity,
              transition: 'opacity 0.2s, border-color 0.2s',
              boxShadow: isSelected ? `0 0 12px ${boxColor}` : 'none'
            }}
          >
            {/* Track ID Label */}
            <div
              style={{
                position: 'absolute',
                top: '-22px',
                left: '0',
                backgroundColor: boxColor,
                color: '#fff',
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: '600',
                boxShadow: '0 2px 4px rgba(0,0,0,0.4)',
                whiteSpace: 'nowrap'
              }}
            >
              #{track.track_id} {track.class_name}
            </div>

            {/* Confidence Badge */}
            {isSelected && track.confidence && (
              <div
                style={{
                  position: 'absolute',
                  bottom: '-22px',
                  left: '0',
                  backgroundColor: 'rgba(13, 17, 23, 0.9)',
                  color: '#a0aab8',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  fontSize: '10px',
                  fontWeight: '500',
                  border: '1px solid #263238'
                }}
              >
                {(track.confidence * 100).toFixed(0)}%
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default VideoOverlay;
