/**
 * AI Explanation Tab
 * Professional Evidence-Driven Video Investigation Report
 * Powered by local Ollama AI with persistent state, progress tracking,
 * and 6 structured investigation sections grounded in actual telemetry.
 */
import { useState } from 'react';
import { useExplanation } from '../../context/ExplanationContext';
import { getTrackColor } from '../../utils/trackColors';

const AIExplanationTab = ({ results, onSeek }) => {
  const {
    status,
    stage,
    error,
    report,
    previousReport,
    isGenerating,
    requestExplanation,
  } = useExplanation();

  const [copied, setCopied] = useState(false);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  // Active report to display (uses active report, or previous report while regenerating)
  const displayReport = report || previousReport;

  const handleCopyReport = () => {
    if (!displayReport) return;
    const text = [
      'FLAGSHIP 107 - VIDEO INVESTIGATION REPORT',
      '=========================================',
      '',
      '1. EXECUTIVE SUMMARY',
      displayReport.executive_summary || displayReport.overview || 'N/A',
      '',
      '2. VIDEO OVERVIEW',
      `Duration: ${displayReport.video_overview?.duration_formatted || results?.video_duration + 's'}`,
      `Resolution: ${displayReport.video_overview?.resolution || `${results?.video_width}x${results?.video_height}`}`,
      `FPS: ${displayReport.video_overview?.fps || results?.video_fps}`,
      `Processed Frames: ${displayReport.video_overview?.frames_processed || results?.frames_processed}`,
      `Confirmed Tracks: ${displayReport.video_overview?.unique_confirmed_tracks || results?.m2_unique_tracks}`,
      `Raw Anomalies: ${displayReport.video_overview?.raw_anomalies || results?.m4_total_anomalies}`,
      `Correlated Events: ${displayReport.video_overview?.correlated_events || results?.m5_correlated_events}`,
      '',
      '3. FINAL ASSESSMENT',
      displayReport.final_assessment || 'N/A',
    ].join('\n');

    navigator.clipboard?.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ padding: '24px', backgroundColor: '#0d1117', color: '#e6edf3', minHeight: '500px' }}>
      {/* Header Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        paddingBottom: '16px',
        borderBottom: '1px solid #30363d',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h3 style={{ margin: 0, color: '#f0f6fc', fontSize: '18px', fontWeight: '600' }}>
              AI Investigation Report
            </h3>
            {displayReport && (
              <span style={{
                padding: '2px 8px',
                borderRadius: '12px',
                fontSize: '11px',
                fontWeight: '600',
                backgroundColor: displayReport.has_anomalies ? 'rgba(248, 81, 73, 0.15)' : 'rgba(56, 139, 253, 0.15)',
                color: displayReport.has_anomalies ? '#f85149' : '#58a6ff',
                border: `1px solid ${displayReport.has_anomalies ? 'rgba(248, 81, 73, 0.4)' : 'rgba(56, 139, 253, 0.4)'}`,
              }}>
                {displayReport.has_anomalies ? 'Anomalies Identified' : 'Baseline Activity'}
              </span>
            )}
            {displayReport?.m9_metadata?.is_fallback && (
              <span style={{
                padding: '2px 8px',
                borderRadius: '12px',
                fontSize: '11px',
                fontWeight: '500',
                backgroundColor: 'rgba(210, 153, 34, 0.15)',
                color: '#d29922',
                border: '1px solid rgba(210, 153, 34, 0.4)',
              }}>
                Deterministic Synthesis
              </span>
            )}
          </div>
          <div style={{ fontSize: '12px', color: '#8b949e', marginTop: '4px' }}>
            Evidence-grounded behavioral synthesis powered by local AI
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {displayReport && (
            <button
              onClick={handleCopyReport}
              style={{
                padding: '8px 14px',
                backgroundColor: '#21262d',
                color: '#c9d1d9',
                border: '1px solid #30363d',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#30363d'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#21262d'}
            >
              {copied ? '✓ Copied' : '📋 Copy Summary'}
            </button>
          )}

          <button
            onClick={() => requestExplanation(!!displayReport)}
            disabled={isGenerating}
            style={{
              padding: '8px 18px',
              backgroundColor: isGenerating ? '#21262d' : '#238636',
              color: isGenerating ? '#8b949e' : '#ffffff',
              border: `1px solid ${isGenerating ? '#30363d' : '#2ea043'}`,
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: '600',
              cursor: isGenerating ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.2s',
              boxShadow: isGenerating ? 'none' : '0 1px 3px rgba(0,0,0,0.3)',
            }}
            onMouseEnter={(e) => {
              if (!isGenerating) e.currentTarget.style.backgroundColor = '#2ea043';
            }}
            onMouseLeave={(e) => {
              if (!isGenerating) e.currentTarget.style.backgroundColor = '#238636';
            }}
          >
            {isGenerating ? (
              <>
                <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⟳</span>
                Generating...
              </>
            ) : displayReport ? (
              <>
                <span>🔄</span>
                Regenerate Report
              </>
            ) : (
              <>
                <span>✨</span>
                Generate Report
              </>
            )}
          </button>
        </div>
      </div>

      {/* Generation Progress Banner (shows when actively generating) */}
      {isGenerating && (
        <div style={{
          backgroundColor: '#161b22',
          border: '1px solid #388bfd',
          borderRadius: '8px',
          padding: '16px 20px',
          marginBottom: '20px',
          boxShadow: '0 0 12px rgba(56, 139, 253, 0.2)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '18px', animation: 'spin 1.2s linear infinite', display: 'inline-block' }}>⟳</span>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#58a6ff' }}>
                Generating Investigation Report
              </span>
            </div>
            <span style={{ fontSize: '12px', color: '#8b949e', backgroundColor: '#0d1117', padding: '2px 8px', borderRadius: '4px' }}>
              {status.toUpperCase()}
            </span>
          </div>
          <div style={{ fontSize: '13px', color: '#c9d1d9' }}>
            Current stage: <strong style={{ color: '#f0f6fc' }}>{stage || 'Processing telemetry...'}</strong>
          </div>
          <div style={{ fontSize: '11px', color: '#8b949e', marginTop: '6px' }}>
            Generation runs in the background. You can navigate between dashboard tabs without interrupting progress.
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && !isGenerating && (
        <div style={{
          backgroundColor: 'rgba(248, 81, 73, 0.1)',
          border: '1px solid rgba(248, 81, 73, 0.4)',
          borderRadius: '8px',
          padding: '16px 20px',
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '12px'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f85149', fontWeight: '600', fontSize: '14px' }}>
              <span>⚠️</span> Generation Issue
            </div>
            <div style={{ fontSize: '13px', color: '#ff7b72', marginTop: '4px' }}>
              {error}
            </div>
            {displayReport && (
              <div style={{ fontSize: '11px', color: '#8b949e', marginTop: '4px' }}>
                Showing previous report while retry is available.
              </div>
            )}
          </div>
          <button
            onClick={() => requestExplanation(true)}
            style={{
              padding: '6px 14px',
              backgroundColor: '#21262d',
              border: '1px solid #30363d',
              borderRadius: '6px',
              color: '#f0f6fc',
              fontSize: '12px',
              fontWeight: '500',
              cursor: 'pointer',
              whiteSpace: 'nowrap'
            }}
          >
            Retry Generation
          </button>
        </div>
      )}

      {/* Empty State: Not generated yet and not generating */}
      {!displayReport && !isGenerating && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '60px 24px',
          backgroundColor: '#161b22',
          border: '1px dashed #30363d',
          borderRadius: '12px',
          textAlign: 'center',
          marginTop: '20px'
        }}>
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '50%',
            backgroundColor: '#21262d',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '28px',
            marginBottom: '16px',
            border: '1px solid #30363d'
          }}>
            📄
          </div>
          <h4 style={{ margin: '0 0 8px 0', fontSize: '18px', color: '#f0f6fc' }}>
            No Investigation Report Generated Yet
          </h4>
          <p style={{ margin: '0 0 20px 0', fontSize: '13px', color: '#8b949e', maxWidth: '480px', lineHeight: '1.6' }}>
            Generate a human-readable investigation report synthesizing detected tracks, movement patterns,
            anomalies, and correlated events from your video telemetry.
          </p>
          <button
            onClick={() => requestExplanation(false)}
            style={{
              padding: '10px 24px',
              backgroundColor: '#238636',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 2px 6px rgba(0,0,0,0.4)'
            }}
          >
            <span>✨</span> Generate Report Now
          </button>
        </div>
      )}

      {/* Structured Report Presentation (Sections 1 through 6) */}
      {displayReport && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* SECTION 1: Executive Summary */}
          <div style={{
            backgroundColor: '#161b22',
            border: '1px solid #30363d',
            borderLeft: `4px solid ${displayReport.has_anomalies ? '#f85149' : '#238636'}`,
            borderRadius: '8px',
            padding: '20px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <span style={{ fontSize: '18px' }}>📋</span>
              <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#f0f6fc' }}>
                1. Executive Summary
              </h4>
            </div>
            <div style={{ fontSize: '14px', lineHeight: '1.7', color: '#c9d1d9' }}>
              {displayReport.executive_summary || displayReport.overview || 'Analysis completed.'}
            </div>
          </div>

          {/* SECTION 2: Video Overview Statistics */}
          <div style={{
            backgroundColor: '#161b22',
            border: '1px solid #30363d',
            borderRadius: '8px',
            padding: '20px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <span style={{ fontSize: '18px' }}>📊</span>
              <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#f0f6fc' }}>
                2. Video Overview
              </h4>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
              gap: '12px'
            }}>
              <StatMetric label="Duration" value={`${displayReport.video_overview?.duration || results?.video_duration || 0}s`} />
              <StatMetric label="Resolution" value={displayReport.video_overview?.resolution || `${results?.video_width}×${results?.video_height}`} />
              <StatMetric label="Frame Rate" value={`${displayReport.video_overview?.fps || results?.video_fps || 0} FPS`} />
              <StatMetric label="Processed Frames" value={displayReport.video_overview?.frames_processed || results?.frames_processed || 0} />
              <StatMetric label="Confirmed Tracks" value={displayReport.video_overview?.unique_confirmed_tracks || results?.m2_unique_tracks || 0} highlight="#58a6ff" />
              <StatMetric label="Raw Anomalies" value={displayReport.video_overview?.raw_anomalies ?? results?.m4_total_anomalies ?? 0} highlight={displayReport.video_overview?.raw_anomalies > 0 ? '#ff7b72' : undefined} />
              <StatMetric label="Correlated Events" value={displayReport.video_overview?.correlated_events ?? results?.m5_correlated_events ?? 0} highlight={displayReport.video_overview?.correlated_events > 0 ? '#f0883e' : undefined} />
              <StatMetric label="Analyzed Scenes" value={displayReport.video_overview?.analyzed_scenes ?? results?.m8_total_scenes ?? 0} />
            </div>

            <div style={{ marginTop: '12px', fontSize: '11px', color: '#8b949e', fontStyle: 'italic' }}>
              ℹ️ {displayReport.video_overview?.track_identity_note || 'Track IDs are temporary automated tracking identifiers, not verified unique human identities.'}
            </div>
          </div>

          {/* SECTION 3: Chronological Findings */}
          <div style={{
            backgroundColor: '#161b22',
            border: '1px solid #30363d',
            borderRadius: '8px',
            padding: '20px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '18px' }}>⏱</span>
                <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#f0f6fc' }}>
                  3. Chronological Findings
                </h4>
              </div>
              <span style={{ fontSize: '12px', color: '#8b949e' }}>
                {displayReport.chronological_events?.length || 0} recorded items
              </span>
            </div>

            {(!displayReport.chronological_events || displayReport.chronological_events.length === 0) ? (
              <div style={{
                padding: '24px',
                backgroundColor: '#0d1117',
                borderRadius: '6px',
                border: '1px solid #21262d',
                textAlign: 'center',
                color: '#8b949e',
                fontSize: '13px'
              }}>
                ✓ No anomalous events were flagged in this footage. Entity transit remained consistent with baseline observations.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {displayReport.chronological_events.map((evt, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '14px 16px',
                      backgroundColor: '#0d1117',
                      border: `1px solid ${evt.is_correlated_event ? '#388bfd' : '#30363d'}`,
                      borderLeft: `4px solid ${evt.is_correlated_event ? '#1f6feb' : '#d29922'}`,
                      borderRadius: '6px',
                      cursor: onSeek ? 'pointer' : 'default',
                      transition: 'all 0.2s',
                    }}
                    onClick={() => onSeek && onSeek(evt.timestamp)}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '6px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: '600',
                          backgroundColor: evt.is_correlated_event ? 'rgba(56, 139, 253, 0.15)' : 'rgba(210, 153, 34, 0.15)',
                          color: evt.is_correlated_event ? '#58a6ff' : '#d29922',
                        }}>
                          {evt.is_correlated_event ? 'Correlated Event' : 'Raw Anomaly'}
                        </span>
                        <span style={{ fontSize: '13px', fontWeight: '600', color: '#f0f6fc' }}>
                          {evt.category}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        {evt.track_ids && evt.track_ids.length > 0 ? (
                          <div style={{ display: 'flex', gap: '4px' }}>
                            {evt.track_ids.map(tid => (
                              <span
                                key={tid}
                                style={{
                                  padding: '1px 6px',
                                  borderRadius: '3px',
                                  fontSize: '11px',
                                  fontWeight: '600',
                                  backgroundColor: getTrackColor(tid),
                                  color: '#0d1117'
                                }}
                              >
                                #{tid}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span style={{ fontSize: '11px', color: '#8b949e', fontStyle: 'italic' }}>
                            {evt.track_id_display || 'Unassigned'}
                          </span>
                        )}
                        <span style={{ fontSize: '12px', fontFamily: 'monospace', color: '#58a6ff', backgroundColor: '#161b22', padding: '2px 6px', borderRadius: '4px' }}>
                          {evt.time_formatted || `${evt.timestamp?.toFixed(2)}s`}
                        </span>
                      </div>
                    </div>

                    <div style={{ fontSize: '13px', color: '#c9d1d9', lineHeight: '1.6' }}>
                      {evt.observable_behavior}
                    </div>

                    {evt.measurable_change && (
                      <div style={{ marginTop: '6px', fontSize: '12px', color: '#58a6ff' }}>
                        <strong>Measurable change:</strong> {evt.measurable_change}
                      </div>
                    )}

                    <div style={{ marginTop: '8px', fontSize: '11px', color: '#8b949e', borderTop: '1px dashed #21262d', paddingTop: '6px' }}>
                      <strong>Why flagged:</strong> {evt.flag_reason}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* SECTION 4: Track and Behavior Analysis */}
          <div style={{
            backgroundColor: '#161b22',
            border: '1px solid #30363d',
            borderRadius: '8px',
            padding: '20px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <span style={{ fontSize: '18px' }}>👤</span>
              <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#f0f6fc' }}>
                4. Track and Behavior Analysis
              </h4>
            </div>

            <div style={{ fontSize: '12px', color: '#8b949e', marginBottom: '16px', lineHeight: '1.5' }}>
              Kinematic tracking analyzes image-space movement (pixels/second). Velocities reflect 2D screen coordinate displacements rather than physical ground speeds.
            </div>

            {(!displayReport.track_analyses || displayReport.track_analyses.length === 0) ? (
              <div style={{ fontSize: '13px', color: '#8b949e', fontStyle: 'italic' }}>
                No active track telemetry available.
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
                {displayReport.track_analyses.map((track) => {
                  const trackColor = getTrackColor(track.track_id);
                  return (
                    <div
                      key={track.track_id}
                      style={{
                        padding: '16px',
                        backgroundColor: '#0d1117',
                        border: '1px solid #21262d',
                        borderTop: `3px solid ${trackColor}`,
                        borderRadius: '6px',
                        cursor: onSeek ? 'pointer' : 'default',
                        transition: 'border-color 0.2s',
                      }}
                      onClick={() => onSeek && onSeek(track.first_seen)}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{
                            padding: '2px 8px',
                            backgroundColor: trackColor,
                            color: '#0d1117',
                            fontWeight: '700',
                            borderRadius: '4px',
                            fontSize: '12px'
                          }}>
                            #{track.track_id}
                          </span>
                          <span style={{ fontSize: '13px', fontWeight: '600', color: '#f0f6fc', textTransform: 'capitalize' }}>
                            {track.class_name}
                          </span>
                        </div>
                        <span style={{
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          backgroundColor: track.is_flagged ? 'rgba(248, 81, 73, 0.15)' : 'rgba(46, 160, 67, 0.15)',
                          color: track.is_flagged ? '#ff7b72' : '#3fb950',
                          border: `1px solid ${track.is_flagged ? 'rgba(248, 81, 73, 0.3)' : 'rgba(46, 160, 67, 0.3)'}`
                        }}>
                          {track.is_flagged ? `${track.anomaly_count} Anomalies` : 'Normal Transit'}
                        </span>
                      </div>

                      <div style={{ fontSize: '13px', color: '#c9d1d9', lineHeight: '1.6', marginBottom: '12px' }}>
                        {track.movement_narrative}
                      </div>

                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '8px',
                        fontSize: '11px',
                        color: '#8b949e',
                        borderTop: '1px solid #21262d',
                        paddingTop: '8px'
                      }}>
                        <div>
                          <div>Duration</div>
                          <div style={{ color: '#f0f6fc', fontWeight: '600' }}>{track.duration_formatted || `${track.duration}s`}</div>
                        </div>
                        <div>
                          <div>Avg Speed</div>
                          <div style={{ color: '#f0f6fc', fontWeight: '600' }}>{track.avg_speed_px_s} px/s</div>
                        </div>
                        <div>
                          <div>Max Speed</div>
                          <div style={{ color: '#f0f6fc', fontWeight: '600' }}>{track.max_speed_px_s} px/s</div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* SECTION 5: Evidence and Limitations */}
          <div style={{
            backgroundColor: '#161b22',
            border: '1px solid #30363d',
            borderRadius: '8px',
            padding: '20px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <span style={{ fontSize: '18px' }}>🔍</span>
              <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#f0f6fc' }}>
                5. Evidence and Limitations
              </h4>
            </div>

            {/* Prominent Investigation Disclaimer */}
            <div style={{
              backgroundColor: 'rgba(210, 153, 34, 0.1)',
              border: '1px solid rgba(210, 153, 34, 0.35)',
              borderRadius: '6px',
              padding: '12px 16px',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
            }}>
              <span style={{ fontSize: '18px', lineHeight: '1.2' }}>⚠️</span>
              <div style={{ fontSize: '13px', color: '#e3b341', lineHeight: '1.5' }}>
                <strong>Investigation Signal Notice:</strong>{' '}
                {displayReport.evidence_and_limitations?.investigation_disclaimer ||
                  'A detected anomaly is an automated investigation signal flagging a statistical motion outlier. It does NOT constitute proof of criminal activity, violence, intent, or wrongdoing. Visual verification by a human investigator is required before drawing conclusions.'}
              </div>
            </div>

            {/* 6-Layer Evidence Hierarchy Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px', marginBottom: '16px' }}>
              <EvidenceTierCard
                title="1. YOLO Detections"
                badge="M1 YOLOv8"
                description="Per-frame computer vision bounding boxes"
                detail={`${displayReport.evidence_and_limitations?.yolo_detections?.count ?? displayReport.evidence_and_limitations?.directly_observed?.count ?? 0} object instances`}
              />
              <EvidenceTierCard
                title="2. Tracking Algorithm"
                badge="M2 Tracker"
                description="Persistent trajectories & displacement vectors"
                detail={`${displayReport.evidence_and_limitations?.tracker_telemetry?.confirmed_tracks_count ?? displayReport.evidence_and_limitations?.tracker_derived?.confirmed_tracks_count ?? 0} confirmed tracks`}
              />
              <EvidenceTierCard
                title="3. Inferred Behaviors"
                badge="M3 Kinematics"
                description="Image-space velocity, heading & transit states"
                detail="Geometric displacement telemetry"
              />
              <EvidenceTierCard
                title="4. Anomaly Detector"
                badge="M4 Anomaly"
                description="Threshold-based speed & direction outliers"
                detail={`${displayReport.evidence_and_limitations?.detector_anomalies?.count ?? 0} flagged outliers`}
              />
              <EvidenceTierCard
                title="5. Correlated Events"
                badge="M5 Correlation"
                description="Multi-frame spatial & temporal co-occurrences"
                detail={`${displayReport.evidence_and_limitations?.correlated_events?.count ?? 0} compound events`}
              />
              <EvidenceTierCard
                title="6. AI Explanations"
                badge={displayReport.m9_metadata?.is_fallback ? 'Rule-Based Fallback' : 'Ollama LLM'}
                description="Natural-language synthesis from verified telemetry"
                detail={displayReport.m9_metadata?.model_name || 'Evidence-grounded'}
              />
            </div>

            {/* Correlation Dynamics & Zero-Events Notice */}
            <div style={{
              backgroundColor: '#0d1117',
              border: '1px solid #21262d',
              borderRadius: '6px',
              padding: '12px 16px',
              marginBottom: '14px',
              fontSize: '12px',
              color: '#8b949e',
              lineHeight: '1.6',
            }}>
              <div style={{ color: '#58a6ff', fontWeight: '600', marginBottom: '4px' }}>
                ℹ️ Understanding Anomaly Flags vs. Correlated Events:
              </div>
              <div>
                {displayReport.evidence_and_limitations?.detector_anomalies?.why_raw_anomalies_exist_without_events ||
                  'A raw anomaly indicates that an individual frame or brief moment crossed a detection threshold. The event-correlation stage requires anomalies to persist across multiple consecutive frames before elevating them to a confirmed event.'}
              </div>
              <div style={{ marginTop: '6px' }}>
                {displayReport.evidence_and_limitations?.correlated_events?.zero_events_disclaimer ||
                  'The absence of correlated events indicates that detected movements did not cluster into an extended multi-frame pattern under configured correlation rules; it does not constitute proof that nothing significant occurred in the footage.'}
              </div>
            </div>

            {/* Detailed System Limitations */}
            <div style={{
              backgroundColor: '#0d1117',
              border: '1px solid #21262d',
              borderRadius: '6px',
              padding: '14px 16px',
              fontSize: '12px',
              color: '#8b949e',
              lineHeight: '1.6'
            }}>
              <strong style={{ color: '#d29922' }}>System Limitations & Technical Disclosures:</strong>
              <ul style={{ margin: '6px 0 0 18px', padding: 0 }}>
                {(displayReport.evidence_and_limitations?.limitations || [
                  'Pixel measurements (px/s) reflect 2D screen coordinates and do not account for camera perspective or distance.',
                  'Lighting changes, partial visual occlusions, or tracker switches may introduce localized continuity gaps.',
                  'Track IDs link consecutive detections algorithmically; personal identity continuity across re-entries is unverified.',
                  'Flagged anomalies indicate statistical deviations from baseline movement, not malicious behavior or intent.'
                ]).map((limitation, idx) => (
                  <li key={idx} style={{ marginBottom: '4px' }}>{limitation}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* SECTION 6: Final Assessment */}
          <div style={{
            backgroundColor: '#161b22',
            border: '1px solid #30363d',
            borderRadius: '8px',
            padding: '20px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
              <span style={{ fontSize: '18px' }}>⚖️</span>
              <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#f0f6fc' }}>
                6. Final Assessment
              </h4>
            </div>
            <div style={{ fontSize: '14px', color: '#c9d1d9', lineHeight: '1.7' }}>
              {displayReport.final_assessment}
            </div>
          </div>

          {/* Expandable Technical Details */}
          <div style={{
            backgroundColor: '#161b22',
            border: '1px solid #30363d',
            borderRadius: '8px',
            overflow: 'hidden',
          }}>
            <button
              onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
              style={{
                width: '100%',
                padding: '14px 20px',
                backgroundColor: 'transparent',
                border: 'none',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                color: '#8b949e',
                fontSize: '13px',
                fontWeight: '500',
                cursor: 'pointer',
              }}
            >
              <span>⚙️ Technical Engine Metadata & Model Provenance</span>
              <span>{showTechnicalDetails ? '▲ Hide' : '▼ View'}</span>
            </button>

            {showTechnicalDetails && (
              <div style={{ padding: '20px', borderTop: '1px solid #21262d', backgroundColor: '#0d1117', fontSize: '12px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '16px' }}>
                  <div>
                    <span style={{ color: '#8b949e' }}>Model Name:</span>{' '}
                    <strong style={{ color: '#f0f6fc' }}>{displayReport.m9_metadata?.model_name || 'qwen3:8b'}</strong>
                  </div>
                  <div>
                    <span style={{ color: '#8b949e' }}>Synthesis Mode:</span>{' '}
                    <strong style={{ color: displayReport.m9_metadata?.is_fallback ? '#d29922' : '#3fb950' }}>
                      {displayReport.m9_metadata?.is_fallback ? 'Deterministic Fallback' : 'Local Ollama LLM'}
                    </strong>
                  </div>
                  <div>
                    <span style={{ color: '#8b949e' }}>Confidence Level:</span>{' '}
                    <strong style={{ color: '#f0f6fc' }}>{displayReport.m9_metadata?.confidence_level || 'High'}</strong>
                  </div>
                  <div>
                    <span style={{ color: '#8b949e' }}>Inference Duration:</span>{' '}
                    <strong style={{ color: '#f0f6fc' }}>{displayReport.m9_metadata?.generation_time_ms ? `${displayReport.m9_metadata.generation_time_ms.toFixed(0)}ms` : 'Instant'}</strong>
                  </div>
                </div>

                <details>
                  <summary style={{ cursor: 'pointer', color: '#58a6ff', marginBottom: '8px' }}>
                    View Raw Structured Report JSON
                  </summary>
                  <pre style={{
                    padding: '12px',
                    backgroundColor: '#161b22',
                    borderRadius: '6px',
                    color: '#8b949e',
                    fontSize: '11px',
                    overflowX: 'auto',
                    maxHeight: '300px'
                  }}>
                    {JSON.stringify(displayReport, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

// Helper components
const StatMetric = ({ label, value, highlight }) => (
  <div style={{
    padding: '10px 12px',
    backgroundColor: '#0d1117',
    borderRadius: '6px',
    border: '1px solid #21262d'
  }}>
    <div style={{ fontSize: '11px', color: '#8b949e', marginBottom: '4px' }}>{label}</div>
    <div style={{ fontSize: '15px', fontWeight: '600', color: highlight || '#f0f6fc' }}>
      {value}
    </div>
  </div>
);

const EvidenceTierCard = ({ title, badge, description, detail }) => (
  <div style={{
    padding: '12px 14px',
    backgroundColor: '#0d1117',
    borderRadius: '6px',
    border: '1px solid #21262d'
  }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
      <div style={{ fontSize: '13px', fontWeight: '600', color: '#f0f6fc' }}>{title}</div>
      <span style={{
        fontSize: '10px',
        padding: '1px 6px',
        backgroundColor: '#21262d',
        color: '#58a6ff',
        borderRadius: '3px',
        fontWeight: '500'
      }}>
        {badge}
      </span>
    </div>
    <div style={{ fontSize: '11px', color: '#8b949e', marginBottom: '6px' }}>{description}</div>
    <div style={{ fontSize: '12px', color: '#3fb950', fontWeight: '500' }}>{detail}</div>
  </div>
);

export default AIExplanationTab;
