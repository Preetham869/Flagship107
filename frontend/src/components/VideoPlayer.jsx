/**
 * Video Player Component
 * Professional video intelligence interface with precise frame-stepping,
 * color-coded track overlays, event navigation, bookmarking, and keyboard shortcuts.
 */
import { useRef, useState, useEffect, useCallback, useMemo } from 'react';
import VideoOverlay from './VideoOverlay';
import { getTrackColor } from '../utils/trackColors';

const PLAYBACK_SPEEDS = [0.25, 0.5, 1, 1.5, 2];

const VideoPlayer = ({
  videoUrl,
  onTimeUpdate,
  currentTime: seekTime,
  selectedItem,
  selectedType,
  videoMetadata,
  allTracks = [],
  allEvents = [],
  allAnomalies = [],
  onSeek,
  onSelectTrack,
  jobId,
}) => {
  const videoRef = useRef(null);
  const containerRef = useRef(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(() => Number(videoMetadata?.video_duration) || 0);
  const [localTime, setLocalTime] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [isHovering, setIsHovering] = useState(false);
  const [fitMode, setFitMode] = useState('contain'); // 'contain' | 'cover'
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [isSeeking, setIsSeeking] = useState(false);

  // Visibility toggles
  const [showOverlays, setShowOverlays] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [showTrajectories, setShowTrajectories] = useState(true);
  const [showLegend, setShowLegend] = useState(false);
  const [showBookmarks, setShowBookmarks] = useState(false);

  // Bookmarks state (persisted to localStorage per job)
  const [bookmarks, setBookmarks] = useState(() => {
    try {
      const saved = localStorage.getItem(`flagship107_bm_${jobId || 'default'}`);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Save bookmarks on change
  useEffect(() => {
    try {
      localStorage.setItem(`flagship107_bm_${jobId || 'default'}`, JSON.stringify(bookmarks));
    } catch (e) {
      console.warn('Failed to save bookmarks:', e);
    }
  }, [bookmarks, jobId]);

  // Actual FPS from metadata or default to 30.0
  const fps = useMemo(() => {
    const metaFps = videoMetadata?.video_fps;
    return metaFps && metaFps > 0 ? metaFps : 30.0;
  }, [videoMetadata]);

  // Unique confirmed tracks for legend
  const uniqueTracks = useMemo(() => {
    const map = new Map();
    allTracks.forEach((frameTracks) => {
      frameTracks.forEach((t) => {
        const tid = String(t.track_id);
        if (!map.has(tid)) {
          map.set(tid, {
            track_id: t.track_id,
            class_name: t.class_name || 'object',
            observations: 1,
            color: getTrackColor(t.track_id, t.confirmed !== false),
            isConfirmed: t.confirmed !== false,
          });
        } else {
          map.get(tid).observations += 1;
        }
      });
    });
    return Array.from(map.values()).sort((a, b) => {
      const numA = parseInt(String(a.track_id), 10);
      const numB = parseInt(String(b.track_id), 10);
      if (!isNaN(numA) && !isNaN(numB)) return numA - numB;
      return String(a.track_id).localeCompare(String(b.track_id));
    });
  }, [allTracks]);

  // Unified event navigation points
  const navPoints = useMemo(() => {
    const points = [];
    allEvents.forEach((evt) => {
      if (evt.start_timestamp !== undefined) {
        points.push({
          time: evt.start_timestamp,
          label: evt.event_type?.replace(/_/g, ' ') || 'Event',
          type: 'event',
          item: evt,
        });
      }
    });
    allAnomalies.forEach((anom) => {
      if (anom.timestamp !== undefined) {
        points.push({
          time: anom.timestamp,
          label: anom.anomaly_type?.replace(/_/g, ' ') || 'Anomaly',
          type: 'anomaly',
          item: anom,
        });
      }
    });
    return points.sort((a, b) => a.time - b.time);
  }, [allEvents, allAnomalies]);

  // Sync fallback duration from videoMetadata
  useEffect(() => {
    if (videoMetadata?.video_duration && (!duration || duration <= 0)) {
      setDuration(Number(videoMetadata.video_duration));
    }
  }, [videoMetadata, duration]);

  // Sync video event listeners
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // Check if video is already ready or has metadata
    if (video.readyState >= 1 && video.duration && !isNaN(video.duration) && isFinite(video.duration)) {
      setDuration(video.duration);
      setIsLoading(false);
    }

    const handleTimeUpdate = () => {
      const time = video.currentTime;
      setLocalTime(time);
      onTimeUpdate?.(time);
    };

    const handleLoadedMetadata = () => {
      const d = video.duration;
      if (d && !isNaN(d) && isFinite(d) && d > 0) {
        setDuration(d);
      } else if (videoMetadata?.video_duration) {
        setDuration(Number(videoMetadata.video_duration));
      }
      setIsLoading(false);
      setLoadError(null);
    };

    const handleDurationChange = () => {
      const d = video.duration;
      if (d && !isNaN(d) && isFinite(d) && d > 0) {
        setDuration(d);
      }
    };

    const handleCanPlay = () => {
      setIsLoading(false);
      setLoadError(null);
    };

    const handleWaiting = () => {
      setIsLoading(true);
    };

    const handleSeeking = () => {
      setIsSeeking(true);
    };

    const handleSeeked = () => {
      setIsSeeking(false);
      setIsLoading(false);
    };

    const handlePlay = () => {
      setIsPlaying(true);
      setIsLoading(false);
    };

    const handlePause = () => {
      setIsPlaying(false);
    };

    const handleEnded = () => {
      setIsPlaying(false);
    };

    const handleError = () => {
      setIsLoading(false);
      const err = video.error;
      let msg = "Video stream could not be loaded.";
      if (err) {
        switch (err.code) {
          case 1:
            msg = "Playback aborted by user or browser.";
            break;
          case 2:
            msg = "Network error occurred while fetching video stream.";
            break;
          case 3:
            msg = "Video decoding error or corrupted format.";
            break;
          case 4:
            msg = "Video stream unavailable or format not supported by browser.";
            break;
          default:
            msg = err.message || "Failed to load video stream.";
        }
      }
      console.warn("Video element error event:", err, msg);
      setLoadError(msg);
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('durationchange', handleDurationChange);
    video.addEventListener('canplay', handleCanPlay);
    video.addEventListener('canplaythrough', handleCanPlay);
    video.addEventListener('waiting', handleWaiting);
    video.addEventListener('seeking', handleSeeking);
    video.addEventListener('seeked', handleSeeked);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    video.addEventListener('ended', handleEnded);
    video.addEventListener('error', handleError);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('durationchange', handleDurationChange);
      video.removeEventListener('canplay', handleCanPlay);
      video.removeEventListener('canplaythrough', handleCanPlay);
      video.removeEventListener('waiting', handleWaiting);
      video.removeEventListener('seeking', handleSeeking);
      video.removeEventListener('seeked', handleSeeked);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('ended', handleEnded);
      video.removeEventListener('error', handleError);
    };
  }, [videoUrl, onTimeUpdate, videoMetadata]);

  // External seek trigger
  useEffect(() => {
    if (seekTime !== undefined && seekTime !== null && videoRef.current) {
      videoRef.current.currentTime = seekTime;
    }
  }, [seekTime]);

  // Play / Pause toggle
  const togglePlayPause = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    if (isPlaying) {
      video.pause();
    } else {
      video.play().catch(console.warn);
    }
  }, [isPlaying]);

  // Time jump helper
  const jumpTime = useCallback((deltaSeconds) => {
    const video = videoRef.current;
    if (!video) return;
    const newTime = Math.max(0, Math.min(video.currentTime + deltaSeconds, duration || video.duration));
    video.currentTime = newTime;
  }, [duration]);

  // Frame stepping
  const stepFrame = useCallback((direction) => {
    const video = videoRef.current;
    if (!video) return;
    video.pause();
    const frameDuration = 1 / fps;
    const newTime = Math.max(0, Math.min(video.currentTime + direction * frameDuration, duration || video.duration));
    video.currentTime = newTime;
  }, [fps, duration]);

  // Playback speed change
  const handleSpeedChange = useCallback((speed) => {
    setPlaybackSpeed(speed);
    if (videoRef.current) {
      videoRef.current.playbackRate = speed;
    }
  }, []);

  // Volume change
  const handleVolumeChange = (e) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    setIsMuted(val === 0);
    if (videoRef.current) {
      videoRef.current.volume = val;
      videoRef.current.muted = val === 0;
    }
  };

  // Mute toggle
  const toggleMute = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    const nextMuted = !isMuted;
    setIsMuted(nextMuted);
    video.muted = nextMuted;
    if (!nextMuted && volume === 0) {
      setVolume(0.5);
      video.volume = 0.5;
    }
  }, [isMuted, volume]);

  // Fullscreen toggle
  const toggleFullscreen = () => {
    const container = containerRef.current;
    if (!container) return;
    if (!document.fullscreenElement) {
      container.requestFullscreen?.().catch(console.warn);
    } else {
      document.exitFullscreen?.().catch(console.warn);
    }
  };

  // Next / Previous Event Seek
  const jumpNextEvent = () => {
    const next = navPoints.find((p) => p.time > localTime + 0.1);
    if (next) {
      if (videoRef.current) videoRef.current.currentTime = next.time;
      onSeek?.(next.time);
    }
  };

  const jumpPrevEvent = () => {
    const prev = [...navPoints].reverse().find((p) => p.time < localTime - 0.2);
    if (prev) {
      if (videoRef.current) videoRef.current.currentTime = prev.time;
      onSeek?.(prev.time);
    }
  };

  // Bookmark current position
  const addBookmark = () => {
    const newBm = {
      id: Date.now(),
      time: localTime,
      label: `Marker at ${formatTimePrecise(localTime)}`,
    };
    setBookmarks((prev) => [...prev, newBm].sort((a, b) => a.time - b.time));
  };

  const removeBookmark = (id, e) => {
    e.stopPropagation();
    setBookmarks((prev) => prev.filter((b) => b.id !== id));
  };

  // Keyboard shortcuts listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ignore if user is currently typing in an input, textarea, or editable element
      const activeTag = document.activeElement?.tagName?.toLowerCase();
      if (
        activeTag === 'input' ||
        activeTag === 'textarea' ||
        document.activeElement?.isContentEditable
      ) {
        return;
      }

      switch (e.key) {
        case ' ':
        case 'k':
        case 'K':
          e.preventDefault();
          togglePlayPause();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          if (e.shiftKey) {
            stepFrame(-1);
          } else {
            jumpTime(-5);
          }
          break;
        case 'ArrowRight':
          e.preventDefault();
          if (e.shiftKey) {
            stepFrame(1);
          } else {
            jumpTime(5);
          }
          break;
        case 'j':
        case 'J':
          e.preventDefault();
          jumpTime(-5);
          break;
        case 'l':
        case 'L':
          e.preventDefault();
          jumpTime(5);
          break;
        case ',':
        case '<':
          e.preventDefault();
          stepFrame(-1);
          break;
        case '.':
        case '>':
          e.preventDefault();
          stepFrame(1);
          break;
        case 'm':
        case 'M':
          e.preventDefault();
          toggleMute();
          break;
        case 'f':
        case 'F':
          e.preventDefault();
          toggleFullscreen();
          break;
        case '[': {
          const idx = PLAYBACK_SPEEDS.indexOf(playbackSpeed);
          if (idx > 0) handleSpeedChange(PLAYBACK_SPEEDS[idx - 1]);
          break;
        }
        case ']': {
          const idx = PLAYBACK_SPEEDS.indexOf(playbackSpeed);
          if (idx < PLAYBACK_SPEEDS.length - 1) handleSpeedChange(PLAYBACK_SPEEDS[idx + 1]);
          break;
        }
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [togglePlayPause, jumpTime, stepFrame, toggleMute, playbackSpeed, handleSpeedChange]);

  // Scrub timeline click
  const handleSeekClick = (e) => {
    const video = videoRef.current;
    if (!video || !duration) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    const target = percentage * duration;
    video.currentTime = target;
  };

  const formatTimePrecise = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00.00';
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(2);
    return `${mins}:${secs.padStart(5, '0')}`;
  };

  const formatDuration = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const retryLoad = () => {
    setLoadError(null);
    setIsLoading(true);
    if (videoRef.current) {
      videoRef.current.load();
    }
  };

  return (
    <div
      ref={containerRef}
      style={{
        backgroundColor: '#0d1117',
        borderRadius: '8px',
        overflow: 'hidden',
        border: '1px solid #30363d',
        boxShadow: '0 4px 16px rgba(0,0,0,0.6)',
        display: 'flex',
        flexDirection: 'column',
      }}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      {/* Video Viewport Area */}
      <div style={{ position: 'relative', backgroundColor: '#000000', minHeight: '400px', maxHeight: '580px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <video
          ref={videoRef}
          src={videoUrl}
          playsInline
          preload="auto"
          crossOrigin="anonymous"
          style={{
            width: '100%',
            height: '100%',
            maxHeight: '580px',
            objectFit: fitMode,
            display: 'block',
          }}
          onClick={togglePlayPause}
        />

        {/* Loading / Buffering Overlay */}
        {isLoading && !loadError && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(13, 17, 23, 0.6)',
            backdropFilter: 'blur(3px)',
            zIndex: 12,
            gap: '12px',
          }}>
            <div style={{
              width: '36px',
              height: '36px',
              border: '3px solid rgba(88, 166, 255, 0.25)',
              borderTop: '3px solid #58a6ff',
              borderRadius: '50%',
              animation: 'spin 0.8s linear infinite',
            }} />
            <span style={{ fontSize: '12px', color: '#8b949e', fontWeight: '500', letterSpacing: '0.3px' }}>
              {isSeeking ? 'Seeking stream position...' : 'Buffering original footage...'}
            </span>
          </div>
        )}

        {/* Playback Error Overlay */}
        {loadError && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(13, 17, 23, 0.92)',
            zIndex: 14,
            padding: '24px',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '32px', marginBottom: '8px' }}>⚠️</div>
            <div style={{ fontSize: '15px', fontWeight: '600', color: '#f85149', marginBottom: '6px' }}>
              Video Stream Unavailable
            </div>
            <div style={{ fontSize: '12px', color: '#8b949e', maxWidth: '420px', marginBottom: '16px', lineHeight: '1.5' }}>
              {loadError}
            </div>
            <button
              onClick={retryLoad}
              style={{
                padding: '8px 18px',
                backgroundColor: '#238636',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'background-color 0.15s ease',
              }}
            >
              Retry Video Stream
            </button>
          </div>
        )}

        {/* Bounding Box & Trajectory Overlay */}
        <VideoOverlay
          videoRef={videoRef}
          allTracks={allTracks}
          allAnomalies={allAnomalies}
          currentTime={localTime}
          videoMetadata={videoMetadata}
          selectedItem={selectedItem}
          selectedType={selectedType}
          showOverlays={showOverlays}
          showLabels={showLabels}
          showTrajectories={showTrajectories}
          onSelectTrack={onSelectTrack}
          fitMode={fitMode}
        />

        {/* Selected Item Notification Badge */}
        {selectedItem && (
          <div style={{
            position: 'absolute',
            top: '12px',
            left: '12px',
            backgroundColor: 'rgba(22, 27, 34, 0.95)',
            border: '1px solid #388bfd',
            color: '#f0f6fc',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            boxShadow: '0 2px 10px rgba(0,0,0,0.5)',
            backdropFilter: 'blur(6px)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            zIndex: 15,
          }}>
            <span style={{ color: '#58a6ff' }}>TARGET:</span>
            {selectedItem.event_type && `Correlated Event: ${selectedItem.event_type.replace(/_/g, ' ')}`}
            {selectedItem.anomaly_type && `Anomaly: ${selectedItem.anomaly_type.replace(/_/g, ' ')}`}
            {selectedItem.track_id !== undefined && `Track #${selectedItem.track_id}`}
          </div>
        )}

        {/* Resolution & FPS Badge (on hover) */}
        {videoMetadata && isHovering && (
          <div style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            backgroundColor: 'rgba(13, 17, 23, 0.85)',
            color: '#8b949e',
            padding: '6px 10px',
            borderRadius: '4px',
            fontSize: '11px',
            fontFamily: 'monospace',
            border: '1px solid #30363d',
            zIndex: 15,
          }}>
            <div>{videoMetadata.video_width}×{videoMetadata.video_height}</div>
            <div>{fps.toFixed(2)} FPS</div>
          </div>
        )}

        {/* Interactive Track Legend Drawer */}
        {showLegend && uniqueTracks.length > 0 && (
          <div style={{
            position: 'absolute',
            bottom: '12px',
            left: '12px',
            backgroundColor: 'rgba(13, 17, 23, 0.92)',
            border: '1px solid #30363d',
            borderRadius: '6px',
            padding: '10px 14px',
            maxWidth: '280px',
            maxHeight: '180px',
            overflowY: 'auto',
            zIndex: 20,
            backdropFilter: 'blur(8px)',
            boxShadow: '0 4px 12px rgba(0,0,0,0.6)',
          }}>
            <div style={{ fontSize: '11px', fontWeight: '700', color: '#8b949e', marginBottom: '8px', textTransform: 'uppercase' }}>
              Track Color Registry ({uniqueTracks.length})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {uniqueTracks.map((t) => (
                <div
                  key={t.track_id}
                  onClick={() => onSelectTrack?.(t)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    padding: '2px 4px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    backgroundColor: 'rgba(255,255,255,0.03)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: t.color,
                      boxShadow: `0 0 4px ${t.color}`,
                    }} />
                    <span style={{ color: '#f0f6fc', fontWeight: '600' }}>
                      #{t.track_id}
                    </span>
                    <span style={{ color: '#8b949e', fontSize: '11px' }}>
                      {t.class_name}
                    </span>
                  </div>
                  <span style={{ color: '#6e7681', fontSize: '10px' }}>
                    {t.observations} obs
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Bookmarks Drawer */}
        {showBookmarks && (
          <div style={{
            position: 'absolute',
            bottom: '12px',
            right: '12px',
            backgroundColor: 'rgba(13, 17, 23, 0.94)',
            border: '1px solid #30363d',
            borderRadius: '6px',
            padding: '12px 14px',
            minWidth: '220px',
            maxHeight: '200px',
            overflowY: 'auto',
            zIndex: 20,
            backdropFilter: 'blur(8px)',
            boxShadow: '0 4px 12px rgba(0,0,0,0.6)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: '700', color: '#8b949e', textTransform: 'uppercase' }}>
                Bookmarks ({bookmarks.length})
              </span>
              <button
                onClick={addBookmark}
                style={{
                  padding: '2px 6px',
                  backgroundColor: '#238636',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '3px',
                  fontSize: '10px',
                  cursor: 'pointer',
                }}
              >
                + Add Current
              </button>
            </div>

            {bookmarks.length === 0 ? (
              <div style={{ fontSize: '11px', color: '#6e7681', fontStyle: 'italic', padding: '8px 0' }}>
                No bookmarks saved for this investigation.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {bookmarks.map((bm) => (
                  <div
                    key={bm.id}
                    onClick={() => {
                      if (videoRef.current) videoRef.current.currentTime = bm.time;
                      onSeek?.(bm.time);
                    }}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '4px 6px',
                      backgroundColor: 'rgba(255,255,255,0.04)',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '11px',
                    }}
                  >
                    <span style={{ color: '#58a6ff', fontFamily: 'monospace' }}>
                      {formatTimePrecise(bm.time)}
                    </span>
                    <button
                      onClick={(e) => removeBookmark(bm.id, e)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#f85149',
                        cursor: 'pointer',
                        fontSize: '12px',
                        padding: '0 4px',
                      }}
                      title="Delete bookmark"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Primary Video Controls Bar */}
      <div style={{
        padding: '12px 18px',
        backgroundColor: '#161b22',
        borderTop: '1px solid #30363d',
      }}>
        {/* Scrubbable Timeline Progress Bar */}
        <div
          onClick={handleSeekClick}
          style={{
            width: '100%',
            height: '8px',
            backgroundColor: '#21262d',
            borderRadius: '4px',
            cursor: 'pointer',
            marginBottom: '12px',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <div style={{
            width: `${duration > 0 ? (localTime / duration) * 100 : 0}%`,
            height: '100%',
            backgroundColor: '#58a6ff',
            borderRadius: '4px',
            transition: 'width 0.05s linear',
            boxShadow: '0 0 8px rgba(88, 166, 255, 0.7)',
          }} />
        </div>

        {/* Playback Controls Row */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}>
          {/* Left Buttons: Play/Pause, Steps, Jumps */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={togglePlayPause}
              style={{
                padding: '6px 14px',
                backgroundColor: '#238636',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                transition: 'background-color 0.2s',
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2ea043'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#238636'}
              title="Play/Pause (Space)"
            >
              {isPlaying ? '⏸ Pause' : '▶ Play'}
            </button>

            {/* Jump -5s / +5s */}
            <button
              onClick={() => jumpTime(-5)}
              style={iconBtnStyle}
              title="Jump Backward 5s (J / Left Arrow)"
            >
              ⏪ -5s
            </button>
            <button
              onClick={() => jumpTime(5)}
              style={iconBtnStyle}
              title="Jump Forward 5s (L / Right Arrow)"
            >
              +5s ⏩
            </button>

            {/* Frame Stepping */}
            <button
              onClick={() => stepFrame(-1)}
              style={iconBtnStyle}
              title="Previous Frame (< or ,)"
            >
              ⏮ Frame
            </button>
            <button
              onClick={() => stepFrame(1)}
              style={iconBtnStyle}
              title="Next Frame (> or .)"
            >
              Frame ⏭
            </button>

            {/* Speed Selector */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginLeft: '4px' }}>
              <span style={{ fontSize: '11px', color: '#8b949e' }}>Speed:</span>
              <select
                value={playbackSpeed}
                onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
                style={{
                  backgroundColor: '#21262d',
                  color: '#f0f6fc',
                  border: '1px solid #30363d',
                  borderRadius: '4px',
                  padding: '3px 6px',
                  fontSize: '12px',
                  cursor: 'pointer',
                }}
              >
                {PLAYBACK_SPEEDS.map((s) => (
                  <option key={s} value={s}>{s}×</option>
                ))}
              </select>
            </div>
          </div>

          {/* Center: Timestamp Display */}
          <div style={{
            fontFamily: 'monospace',
            fontSize: '13px',
            color: '#f0f6fc',
            fontWeight: '600',
            backgroundColor: '#0d1117',
            padding: '4px 10px',
            borderRadius: '4px',
            border: '1px solid #21262d',
          }}>
            {formatTimePrecise(localTime)} <span style={{ color: '#6e7681' }}>/</span> {formatDuration(duration)}
          </div>

          {/* Right Controls: Volume, Fit, Fullscreen */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Volume */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <button
                onClick={toggleMute}
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '14px', color: '#c9d1d9' }}
                title="Mute / Unmute (M)"
              >
                {isMuted || volume === 0 ? '🔇' : '🔊'}
              </button>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={isMuted ? 0 : volume}
                onChange={handleVolumeChange}
                style={{ width: '60px', accentColor: '#58a6ff', cursor: 'pointer' }}
                title="Volume"
              />
            </div>

            {/* Fit mode toggle */}
            <button
              onClick={() => setFitMode(fitMode === 'contain' ? 'cover' : 'contain')}
              style={iconBtnStyle}
              title={fitMode === 'contain' ? 'Fit Video: Contain (Click for Cover)' : 'Fit Video: Cover (Click for Contain)'}
            >
              {fitMode === 'contain' ? 'Fit: Contain' : 'Fit: Fill'}
            </button>

            {/* Fullscreen */}
            <button
              onClick={toggleFullscreen}
              style={iconBtnStyle}
              title="Fullscreen (F)"
            >
              ⛶ Fullscreen
            </button>
          </div>
        </div>

        {/* Secondary Investigation Toolstrip */}
        <div style={{
          marginTop: '10px',
          paddingTop: '10px',
          borderTop: '1px solid #21262d',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
          fontSize: '12px',
        }}>
          {/* Event Navigation & Bookmarking */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={jumpPrevEvent}
              disabled={navPoints.length === 0}
              style={{
                ...iconBtnStyle,
                color: navPoints.length > 0 ? '#58a6ff' : '#484f58',
                borderColor: navPoints.length > 0 ? '#388bfd44' : '#21262d',
              }}
              title="Jump to Previous Event/Anomaly"
            >
              ◀ Prev Event
            </button>
            <button
              onClick={jumpNextEvent}
              disabled={navPoints.length === 0}
              style={{
                ...iconBtnStyle,
                color: navPoints.length > 0 ? '#58a6ff' : '#484f58',
                borderColor: navPoints.length > 0 ? '#388bfd44' : '#21262d',
              }}
              title="Jump to Next Event/Anomaly"
            >
              Next Event ▶
            </button>

            {/* Bookmark button */}
            <button
              onClick={addBookmark}
              style={iconBtnStyle}
              title="Bookmark Current Time"
            >
              🔖 Bookmark
            </button>
            <button
              onClick={() => setShowBookmarks(!showBookmarks)}
              style={{
                ...iconBtnStyle,
                backgroundColor: showBookmarks ? '#30363d' : '#21262d',
              }}
              title="View Bookmarks List"
            >
              Bookmarks ({bookmarks.length})
            </button>
          </div>

          {/* Overlay Feature Toggles */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#8b949e' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={showOverlays}
                onChange={(e) => setShowOverlays(e.target.checked)}
                style={{ accentColor: '#58a6ff' }}
              />
              Boxes
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={showLabels}
                onChange={(e) => setShowLabels(e.target.checked)}
                style={{ accentColor: '#58a6ff' }}
              />
              Labels
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={showTrajectories}
                onChange={(e) => setShowTrajectories(e.target.checked)}
                style={{ accentColor: '#58a6ff' }}
              />
              Trajectories
            </label>

            <button
              onClick={() => setShowLegend(!showLegend)}
              style={{
                ...iconBtnStyle,
                backgroundColor: showLegend ? '#30363d' : '#21262d',
                color: showLegend ? '#58a6ff' : '#c9d1d9',
              }}
              title="Toggle Track Color Legend"
            >
              Legend
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const iconBtnStyle = {
  padding: '5px 10px',
  backgroundColor: '#21262d',
  color: '#c9d1d9',
  border: '1px solid #30363d',
  borderRadius: '4px',
  fontSize: '12px',
  fontWeight: '500',
  cursor: 'pointer',
  transition: 'all 0.15s',
  whiteSpace: 'nowrap',
};

export default VideoPlayer;
