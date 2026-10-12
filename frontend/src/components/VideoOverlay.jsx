/**
 * Video Overlay Component
 * Renders color-coded bounding boxes, track labels, trajectory motion trails,
 * and anomaly indicator badges synchronized with video playback.
 */
import { useEffect, useState, useRef, useMemo } from 'react';
import { getTrackColor, getContrastTextColor, isUnconfirmedTrack } from '../utils/trackColors';

const VideoOverlay = ({
  videoRef,
  allTracks = [],
  allAnomalies = [],
  currentTime = 0,
  videoMetadata,
  selectedItem,
  selectedType,
  showOverlays = true,
  showLabels = true,
  showTrajectories = true,
  onSelectTrack,
  fitMode = 'contain',
}) => {
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const overlayRef = useRef(null);

  // Update overlay dimensions from video element
  useEffect(() => {
    const video = videoRef?.current;
    if (!video) return;

    const updateDims = () => {
      setDimensions({
        width: video.offsetWidth,
        height: video.offsetHeight,
      });
    };

    updateDims();
    const resizeObserver = new ResizeObserver(updateDims);
    resizeObserver.observe(video);

    return () => resizeObserver.disconnect();
  }, [videoRef]);

  // Calculate frame index from current time and FPS
  useEffect(() => {
    const fps = videoMetadata?.video_fps || 30.0;
    if (currentTime === undefined) return;
    const frameIndex = Math.floor(currentTime * fps);
    setCurrentFrameIndex(Math.max(0, Math.min(frameIndex, (allTracks?.length || 1) - 1)));
  }, [currentTime, videoMetadata, allTracks]);

  // Transform coordinates from video native resolution to video display box
  const transformCoords = useMemo(() => {
    const video = videoRef?.current;
    const nativeWidth = videoMetadata?.video_width || video?.videoWidth || 0;
    const nativeHeight = videoMetadata?.video_height || video?.videoHeight || 0;

    if (!nativeWidth || !nativeHeight || dimensions.width === 0 || dimensions.height === 0) {
      return null;
    }

    const videoAspect = nativeWidth / nativeHeight;
    const displayAspect = dimensions.width / dimensions.height;

    let scale, offsetX, offsetY;
    if (fitMode === 'cover') {
      if (videoAspect > displayAspect) {
        // Cropped horizontally
        scale = dimensions.height / nativeHeight;
        offsetX = (dimensions.width - (nativeWidth * scale)) / 2;
        offsetY = 0;
      } else {
        // Cropped vertically
        scale = dimensions.width / nativeWidth;
        offsetX = 0;
        offsetY = (dimensions.height - (nativeHeight * scale)) / 2;
      }
    } else {
      if (videoAspect > displayAspect) {
        // Letterboxed top and bottom
        scale = dimensions.width / nativeWidth;
        offsetX = 0;
        offsetY = (dimensions.height - (nativeHeight * scale)) / 2;
      } else {
        // Pillarboxed left and right
        scale = dimensions.height / nativeHeight;
        offsetX = (dimensions.width - (nativeWidth * scale)) / 2;
        offsetY = 0;
      }
    }

    return { scale, offsetX, offsetY };
  }, [videoMetadata, dimensions, fitMode, videoRef]);

  if (!showOverlays || !allTracks || allTracks.length === 0 || !transformCoords) {
    return null;
  }

  const { scale, offsetX, offsetY } = transformCoords;
  const currentFrameTracks = allTracks[currentFrameIndex] || [];

  // Determine selected track IDs
  const selectedTrackIds = new Set();
  if (selectedType === 'anomaly' && selectedItem?.track_id !== undefined) {
    selectedTrackIds.add(String(selectedItem.track_id));
  } else if (selectedType === 'event' && selectedItem?.track_ids) {
    selectedItem.track_ids.forEach(id => selectedTrackIds.add(String(id)));
  } else if (selectedType === 'track' && (selectedItem?.track_id !== undefined || selectedItem?.id !== undefined)) {
    selectedTrackIds.add(String(selectedItem.track_id || selectedItem.id));
  }

  // Active anomalies occurring near current timestamp (+/- 0.8s)
  const activeAnomaliesByTrack = {};
  if (allAnomalies && allAnomalies.length > 0) {
    allAnomalies.forEach(anom => {
      if (anom.timestamp !== undefined && Math.abs(anom.timestamp - currentTime) <= 0.8) {
        const tid = String(anom.track_id);
        if (!activeAnomaliesByTrack[tid]) {
          activeAnomaliesByTrack[tid] = [];
        }
        activeAnomaliesByTrack[tid].push(anom);
      }
    });
  }

  // Calculate trajectories for visible tracks across previous frames (up to 30 frames)
  const trajectoryPaths = [];
  if (showTrajectories && currentFrameTracks.length > 0) {
    const activeTrackIdsInFrame = new Set(currentFrameTracks.map(t => String(t.track_id)));
    const lookbackStart = Math.max(0, currentFrameIndex - 30);

    activeTrackIdsInFrame.forEach(trackIdStr => {
      const points = [];
      for (let f = lookbackStart; f <= currentFrameIndex; f++) {
        const frameDetections = allTracks[f];
        if (!frameDetections) continue;
        const det = frameDetections.find(d => String(d.track_id) === trackIdStr);
        if (det && det.bbox) {
          const [x1, y1, x2, y2] = det.bbox;
          const cx = ((x1 + x2) / 2) * scale + offsetX;
          const cy = ((y1 + y2) / 2) * scale + offsetY;
          points.push({ x: cx, y: cy });
        }
      }

      if (points.length >= 2) {
        const trackColor = getTrackColor(trackIdStr, !isUnconfirmedTrack(trackIdStr));
        const pathData = points.reduce((acc, pt, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`, '');
        trajectoryPaths.push({
          trackId: trackIdStr,
          color: trackColor,
          pathData,
          lastPoint: points[points.length - 1],
        });
      }
    });
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
        zIndex: 10,
        overflow: 'hidden',
      }}
    >
      {/* SVG Trajectory Layer */}
      {showTrajectories && trajectoryPaths.length > 0 && (
        <svg
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            pointerEvents: 'none',
          }}
        >
          {trajectoryPaths.map(traj => (
            <g key={traj.trackId}>
              <path
                d={traj.pathData}
                fill="none"
                stroke={traj.color}
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeDasharray="4 2"
                opacity="0.8"
              />
              <circle
                cx={traj.lastPoint.x}
                cy={traj.lastPoint.y}
                r="3.5"
                fill={traj.color}
                opacity="0.9"
              />
            </g>
          ))}
        </svg>
      )}

      {/* Bounding Box Overlays */}
      {currentFrameTracks.map((track, idx) => {
        const [x1, y1, x2, y2] = track.bbox;
        const trackIdStr = String(track.track_id);
        const isSelected = selectedTrackIds.has(trackIdStr);
        const isUnconfirmed = isUnconfirmedTrack(track.track_id, track.confirmed);
        const trackAnomalies = activeAnomaliesByTrack[trackIdStr] || [];
        const hasActiveAnomaly = trackAnomalies.length > 0;

        // Overlay pixel coordinates
        const overlayX = x1 * scale + offsetX;
        const overlayY = y1 * scale + offsetY;
        const overlayWidth = Math.max(4, (x2 - x1) * scale);
        const overlayHeight = Math.max(4, (y2 - y1) * scale);

        const baseColor = getTrackColor(track.track_id, !isUnconfirmed);
        const textColor = getContrastTextColor(baseColor);

        // Styling based on selection, unconfirmed status, and anomalies
        const borderStyle = isUnconfirmed ? '2px dashed #8b949e' : `2px solid ${baseColor}`;
        const opacity = isSelected ? 1 : isUnconfirmed ? 0.45 : 0.85;

        let shadow = 'none';
        if (hasActiveAnomaly) {
          shadow = `0 0 14px rgba(255, 68, 68, 0.9), inset 0 0 10px rgba(255, 68, 68, 0.3)`;
        } else if (isSelected) {
          shadow = `0 0 12px ${baseColor}, 0 0 4px #ffffff`;
        }

        return (
          <div
            key={`${trackIdStr}-${idx}`}
            onClick={(e) => {
              e.stopPropagation();
              onSelectTrack?.({
                track_id: track.track_id,
                class_name: track.class_name,
                confidence: track.confidence,
              });
            }}
            style={{
              position: 'absolute',
              left: `${overlayX}px`,
              top: `${overlayY}px`,
              width: `${overlayWidth}px`,
              height: `${overlayHeight}px`,
              border: borderStyle,
              borderRadius: '4px',
              opacity: opacity,
              boxShadow: shadow,
              pointerEvents: 'auto',
              cursor: 'pointer',
              transition: 'opacity 0.15s, box-shadow 0.15s',
              backgroundColor: isSelected ? `${baseColor}15` : hasActiveAnomaly ? 'rgba(255, 68, 68, 0.1)' : 'transparent',
            }}
          >
            {/* Top Label Badge */}
            {showLabels && (
              <div
                style={{
                  position: 'absolute',
                  top: '-24px',
                  left: '0',
                  backgroundColor: baseColor,
                  color: textColor,
                  padding: '2px 7px',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: '700',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.5)',
                  whiteSpace: 'nowrap',
                  letterSpacing: '0.2px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  zIndex: 2,
                }}
              >
                {isUnconfirmed ? `[temp] #${track.track_id}` : `#${track.track_id}`}
                {track.class_name && (
                  <span style={{ fontWeight: '500', opacity: 0.9 }}>
                    {track.class_name}
                  </span>
                )}
              </div>
            )}

            {/* Active Anomaly Indicator Badge */}
            {hasActiveAnomaly && (
              <div
                style={{
                  position: 'absolute',
                  top: '-46px',
                  left: '0',
                  backgroundColor: '#d32f2f',
                  color: '#ffffff',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontSize: '10px',
                  fontWeight: '700',
                  boxShadow: '0 0 8px rgba(255, 68, 68, 0.8)',
                  whiteSpace: 'nowrap',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  zIndex: 3,
                  animation: 'pulse 1.5s infinite',
                }}
              >
                <span>⚠ ANOMALY:</span>
                <span>{trackAnomalies[0].anomaly_type?.replace(/_/g, ' ') || 'Flagged'}</span>
              </div>
            )}

            {/* Bottom Confidence Badge (when selected) */}
            {isSelected && track.confidence !== undefined && (
              <div
                style={{
                  position: 'absolute',
                  bottom: '-20px',
                  left: '0',
                  backgroundColor: 'rgba(13, 17, 23, 0.9)',
                  color: '#c9d1d9',
                  padding: '1px 6px',
                  borderRadius: '3px',
                  fontSize: '10px',
                  fontWeight: '600',
                  border: '1px solid #30363d',
                }}
              >
                {(track.confidence * 100).toFixed(0)}% conf
              </div>
            )}
          </div>
        );
      })}

      <style>{`
        @keyframes pulse {
          0% { transform: scale(1); }
          50% { transform: scale(1.05); }
          100% { transform: scale(1); }
        }
      `}</style>
    </div>
  );
};

export default VideoOverlay;
