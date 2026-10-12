"""
Investigation Report Builder
Transforms raw pipeline results and M9 scene explanations into
a structured, human-readable, evidence-grounded investigation report.
"""
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Human-readable translations for algorithmic anomaly & event labels
LABEL_TRANSLATIONS: Dict[str, str] = {
    "sudden_speed_change": "Sudden change in measured movement speed",
    "unusual_speed": "Movement speed outside the configured baseline",
    "abnormal_movement_sequence": "A sequence of movement indicators that met the detector's configured criteria",
    "sudden_direction_change": "Sudden change in movement direction",
    "loitering": "Stationary presence exceeding duration threshold",
    "loitering_event": "Stationary presence exceeding duration threshold",
    "sudden_appearance": "Abrupt appearance in camera view",
    "restricted_zone_entry": "Entry into a configured restricted zone",
    "restricted_area_intrusion": "Entry into a configured restricted zone",
    "high_speed_activity": "Measured movement speed exceeding high-velocity threshold",
    "high_speed_movement": "Measured movement speed exceeding high-velocity threshold",
}


def build_investigation_report(
    pipeline_result: Dict[str, Any],
    scene_explanation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a comprehensive, human-readable investigation report from pipeline results
    and optional LLM scene explanation.

    Args:
        pipeline_result: Full PipelineResult dictionary (M1-M8 data)
        scene_explanation: SceneExplanation dictionary (M9 data, optional)

    Returns:
        Structured investigation report dictionary matching the 6-section schema
    """
    # 1. Video Overview Metrics
    duration = float(pipeline_result.get("video_duration") or 0.0)
    width = int(pipeline_result.get("video_width") or 0)
    height = int(pipeline_result.get("video_height") or 0)
    fps = float(pipeline_result.get("video_fps") or 0.0)
    frames_processed = int(pipeline_result.get("frames_processed") or 0)
    total_detections = int(pipeline_result.get("m1_total_detections") or 0)
    unique_tracks = int(pipeline_result.get("m2_unique_tracks") or 0)
    raw_anomalies_count = int(pipeline_result.get("m4_total_anomalies") or 0)
    correlated_events_count = int(pipeline_result.get("m5_correlated_events") or 0)
    scenes_count = int(pipeline_result.get("m8_total_scenes") or 0)

    video_overview = {
        "duration": round(duration, 2),
        "duration_formatted": _format_time(duration),
        "resolution": f"{width}×{height}" if width and height else "Unknown",
        "fps": round(fps, 2) if fps else 0.0,
        "frames_processed": frames_processed,
        "total_detections": total_detections,
        "unique_confirmed_tracks": unique_tracks,
        "raw_anomalies": raw_anomalies_count,
        "correlated_events": correlated_events_count,
        "analyzed_scenes": scenes_count,
        "track_identity_note": "Track IDs are temporary automated tracking identifiers, not verified unique human identities.",
    }

    # Extract anomalies, events, and behaviors
    all_anomalies = pipeline_result.get("all_anomalies") or []
    all_events = pipeline_result.get("all_events") or []
    all_behaviors = pipeline_result.get("all_behaviors") or []

    # Map tracks
    track_summaries = _extract_track_summaries(all_behaviors, all_anomalies)

    # 3. Chronological Findings Narrative
    chronological_events = _build_chronological_events(
        all_events, all_anomalies, track_summaries
    )

    # 4. Track and Movement Analysis
    track_analyses = _build_track_analyses(
        track_summaries, scene_explanation
    )

    # 1. Executive Summary
    executive_summary = _build_executive_summary(
        video_overview,
        all_events,
        all_anomalies,
        track_summaries,
        scene_explanation,
        pipeline_result,
    )

    # 5. Evidence and Limitations (Distinguishing each layer)
    avg_speed_metric = pipeline_result.get("m3_avg_speed")
    max_speed_metric = pipeline_result.get("m3_max_speed")

    evidence_and_limitations = {
        "directly_observed": {"count": total_detections},
        "tracker_derived": {"confirmed_tracks_count": unique_tracks},
        "yolo_detections": {
            "title": "Object Detections (YOLOv8)",
            "description": "Bounding box coordinates identified per frame by computer vision object detection",
            "count": total_detections,
            "classes_detected": list(pipeline_result.get("m1_detections_by_class", {}).keys()),
            "nature": "Frame-by-frame visual bounding box proposals without identity history",
        },
        "tracker_telemetry": {
            "title": "Tracking Telemetry (Multi-Object Tracker)",
            "description": "Persistent spatial trajectory linkages and displacement vectors across consecutive frames",
            "confirmed_tracks_count": unique_tracks,
            "average_speed_px_s": (
                f"{round(float(avg_speed_metric), 1)} px/s"
                if avg_speed_metric is not None
                else "Not available"
            ),
            "max_speed_px_s": (
                f"{round(float(max_speed_metric), 1)} px/s"
                if max_speed_metric is not None
                else "Not available"
            ),
            "scale_disclaimer": (
                "All velocities are measured in image-space pixels per second (px/s). "
                "They do not represent real-world physical speed (such as km/h or mph) because camera focal length, "
                "tilt angle, and real-world distance scale are uncalibrated."
            ),
        },
        "behavior_inferences": {
            "title": "Kinematic Behavior Analysis",
            "description": "Movement patterns derived from spatial displacements, frame velocities, and heading changes",
            "speed_metrics_available": avg_speed_metric is not None,
            "heading_variance_available": True,
            "limitations_note": "Behavioral labels reflect geometric trajectory properties, not human motivation or conscious intent.",
        },
        "detector_anomalies": {
            "title": "Raw Anomaly Flags (M4)",
            "description": "Statistical outliers where an individual frame exceeded velocity, acceleration, or directional variance thresholds",
            "count": raw_anomalies_count,
            "breakdown_by_type": pipeline_result.get("m4_anomalies_by_type") or {},
            "nature": "Automated warning flags identifying brief deviations from baseline movement",
            "why_raw_anomalies_exist_without_events": (
                "A raw anomaly indicates that an individual frame or brief moment crossed a detection threshold "
                "(such as a temporary speed spike, sharp turn, or detection flicker). The event-correlation stage "
                "requires anomalies to persist across multiple consecutive frames or co-occur with related indicators "
                "before elevating them to a confirmed event. Therefore, raw anomalies frequently occur in isolation "
                "without forming a correlated event."
            ),
        },
        "correlated_events": {
            "title": "Correlated Events (M5)",
            "description": "Multi-frame events synthesized from temporal and spatial co-occurrences of anomalous signals",
            "count": correlated_events_count,
            "breakdown_by_type": pipeline_result.get("m5_events_by_type") or {},
            "correlation_note": (
                "Compound events represent multiple related anomalies clustering into a sustained pattern."
                if correlated_events_count > 0
                else "Raw anomaly indicators were detected, but no correlated events were established by the event-correlation stage."
            ),
            "zero_events_disclaimer": (
                "The absence of correlated events indicates that detected movements did not cluster into an extended "
                "multi-frame pattern under configured correlation rules; it does not constitute proof that nothing "
                "significant occurred in the footage."
            ),
        },
        "ai_explanations": {
            "title": "AI Narrative Synthesis (Local Ollama LLM)",
            "description": "Natural-language contextual summary synthesized from verified pipeline observations",
            "model_name": scene_explanation.get("model_name", "local-ollama") if scene_explanation else "rule-based",
            "is_fallback": scene_explanation.get("is_fallback", False) if scene_explanation else True,
            "confidence_level": scene_explanation.get("confidence_level", "medium") if scene_explanation else "medium",
            "evidence_coverage": scene_explanation.get("evidence_coverage", 1.0) if scene_explanation else 1.0,
            "safety_boundary": "The AI model interprets observed kinematic telemetry only. It does not infer individual intent, emotional state, criminality, or identity.",
        },
        "investigation_disclaimer": (
            "A detected anomaly is an automated investigation signal flagging a statistical motion outlier. "
            "It does NOT constitute proof of criminal activity, violence, intent, or wrongdoing. "
            "Visual verification by a human investigator is required before drawing conclusions."
        ),
        "limitations": [
            "2D image-space measurements (px/s) reflect screen coordinates and do not account for camera perspective or distance.",
            "Track IDs are temporary automated tracking identifiers, not verified unique human identities.",
            "Raw anomalies may occur in isolation due to brief threshold spikes or tracking artifacts without forming correlated events.",
            "The absence of correlated events indicates movements did not form extended clusters; it is not proof that nothing unusual occurred.",
            "Flagged anomalies indicate statistical deviations from baseline movement, never human motivation or intent.",
        ],
    }

    # 6. Final Assessment
    final_assessment = _build_final_assessment(
        raw_anomalies_count,
        correlated_events_count,
        chronological_events,
        unique_tracks,
        duration,
    )

    # Status flag
    has_anomalies = raw_anomalies_count > 0 or correlated_events_count > 0

    return {
        "executive_summary": executive_summary,
        "video_overview": video_overview,
        "chronological_events": chronological_events,
        "track_analyses": track_analyses,
        "evidence_and_limitations": evidence_and_limitations,
        "final_assessment": final_assessment,
        "has_anomalies": has_anomalies,
        "m9_metadata": {
            "model_name": scene_explanation.get("model_name") if scene_explanation else "deterministic-rules",
            "model_version": scene_explanation.get("model_version") if scene_explanation else "v1.0",
            "generation_time_ms": scene_explanation.get("generation_time_ms", 0.0) if scene_explanation else 0.0,
            "is_fallback": scene_explanation.get("is_fallback", False) if scene_explanation else True,
            "fallback_reason": scene_explanation.get("fallback_reason") if scene_explanation else None,
            "confidence_level": scene_explanation.get("confidence_level", "medium") if scene_explanation else "medium",
            "evidence_coverage": scene_explanation.get("evidence_coverage", 1.0) if scene_explanation else 1.0,
        },
        # Retain original M9 fields for backward compatibility
        "overview": scene_explanation.get("overview") if scene_explanation else executive_summary,
        "entity_behaviors": scene_explanation.get("entity_behaviors", []) if scene_explanation else [],
        "pattern_significance": scene_explanation.get("pattern_significance", {}) if scene_explanation else {},
        "anomaly_significance": scene_explanation.get("anomaly_significance", []) if scene_explanation else [],
        "contextual_interpretation": scene_explanation.get("contextual_interpretation") if scene_explanation else None,
    }


def _format_time(seconds: float) -> str:
    """Format seconds into M:SS.ss string"""
    if seconds <= 0:
        return "0:00"
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins}:{secs:05.2f}"


def _format_track_id(tid: Any) -> str:
    """Format track identifier cleanly handling missing or null IDs"""
    if tid is None:
        return "Unassigned"
    s = str(tid).strip()
    if s == "" or s.lower() in ("none", "null", "undefined"):
        return "Unassigned"
    return f"Track #{s}"


def _format_track_mention(tid: Any) -> str:
    """Format track mention for conversational narratives"""
    if tid is None:
        return "an unassigned entity"
    s = str(tid).strip()
    if s == "" or s.lower() in ("none", "null", "undefined"):
        return "an unassigned entity"
    return f"Track #{s}"


def _extract_track_summaries(
    all_behaviors: List[List[Dict[str, Any]]],
    all_anomalies: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Extract and aggregate track metadata across all frames"""
    tracks: Dict[str, Dict[str, Any]] = {}

    for frame_behaviors in all_behaviors:
        for b in frame_behaviors:
            raw_tid = b.get("track_id")
            tid_key = str(raw_tid) if raw_tid is not None else "unassigned"

            if tid_key not in tracks:
                tracks[tid_key] = {
                    "track_id": raw_tid,
                    "class_name": b.get("class_name", "entity"),
                    "first_seen": float(b.get("timestamp") or 0.0),
                    "last_seen": float(b.get("timestamp") or 0.0),
                    "speeds": [],
                    "states": set(),
                    "observations": 0,
                    "anomalies": [],
                }
            item = tracks[tid_key]
            item["observations"] += 1
            t_curr = float(b.get("timestamp") or 0.0)
            item["last_seen"] = max(item["last_seen"], t_curr)
            if b.get("speed") is not None:
                try:
                    item["speeds"].append(float(b["speed"]))
                except (ValueError, TypeError):
                    pass
            if b.get("state"):
                item["states"].add(str(b["state"]))

    # Attach anomalies
    for anomaly in all_anomalies:
        raw_tid = anomaly.get("track_id")
        tid_key = str(raw_tid) if raw_tid is not None else "unassigned"
        if tid_key in tracks:
            tracks[tid_key]["anomalies"].append(anomaly)

    # Compute final metrics
    for tid_key, item in tracks.items():
        item["duration"] = max(0.0, item["last_seen"] - item["first_seen"])
        if item["speeds"]:
            item["avg_speed"] = sum(item["speeds"]) / len(item["speeds"])
            item["max_speed"] = max(item["speeds"])
        else:
            item["avg_speed"] = None
            item["max_speed"] = None
        item["states_list"] = sorted(list(item["states"]))

    return tracks


def _build_chronological_events(
    all_events: List[Dict[str, Any]],
    all_anomalies: List[Dict[str, Any]],
    track_summaries: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Build a unified, chronologically sorted list of findings (correlated events and raw anomalies)
    described in plain, understandable English suitable for non-technical investigators.
    """
    combined: List[Dict[str, Any]] = []

    # 1. Correlated Events
    for evt in all_events:
        start_t = float(evt.get("start_timestamp", 0.0))
        end_t = float(evt.get("end_timestamp", start_t))
        duration = max(0.0, end_t - start_t)
        raw_track_ids = evt.get("track_ids", [])
        evt_type = str(evt.get("event_type", "behavioral_event"))
        severity = evt.get("severity", "medium")
        confidence = evt.get("confidence")

        # Translate detector label
        readable_label = LABEL_TRANSLATIONS.get(evt_type, evt_type.replace("_", " ").title())

        # Clean track IDs
        valid_tids = [
            str(tid) for tid in raw_track_ids
            if tid is not None and str(tid).lower() not in ("none", "", "null")
        ]
        if valid_tids:
            track_mention = ", ".join(f"Track #{tid}" for tid in valid_tids)
        else:
            track_mention = "an unassigned entity"

        # Evidence dictionary
        source_count = len(evt.get("source_anomaly_ids", []))
        anomaly_types = evt.get("source_anomaly_types", [])
        evidence_dict = evt.get("evidence") or {}

        # Measurable changes
        peak_speed = evidence_dict.get("peak_speed")
        if peak_speed is not None:
            measurable_change = f"Peak measured image-space speed reached {float(peak_speed):.1f} px/s."
        else:
            measurable_change = "Measurement data: Not available."

        # Plain-English observable description
        if "high_speed" in evt_type or "speed" in evt_type:
            behavior_desc = (
                f"Between {_format_time(start_t)} and {_format_time(end_t)} ({duration:.1f}s), "
                f"the system established a confirmed event involving {track_mention}. "
                f"Measured movement speed was elevated across an extended {duration:.1f}-second interval. "
                f"{measurable_change} Review the footage around this window to visually verify the subject's movement."
            )
            flag_reason = (
                f"Sustained motion pattern: {source_count} sequential velocity indicator(s) occurred consecutively, "
                f"meeting the criteria for an extended high-speed event."
            )
        elif "loitering" in evt_type or "stationary" in evt_type:
            behavior_desc = (
                f"Between {_format_time(start_t)} and {_format_time(end_t)}, {track_mention} remained largely stationary "
                f"within a localized area for {duration:.1f} seconds. "
                f"Review the footage to confirm whether the subject was waiting, resting, or observing surroundings."
            )
            flag_reason = (
                f"Stationary presence: Entity persisted inside a confined pixel radius for {duration:.1f} seconds, "
                f"exceeding the stationary duration threshold."
            )
        elif "abnormal_movement" in evt_type or "erratic" in evt_type or "direction" in evt_type:
            behavior_desc = (
                f"Between {_format_time(start_t)} and {_format_time(end_t)} ({duration:.1f}s), {track_mention} displayed "
                f"repeated course changes and irregular heading variations across {source_count} observations. "
                f"Review the footage to determine whether the subject altered course, stepped around an obstacle, "
                f"or experienced visual occlusion."
            )
            flag_reason = (
                f"Course variance: {source_count} consecutive trajectory shifts met the criteria for an irregular movement sequence."
            )
        elif "intrusion" in evt_type or "restricted" in evt_type:
            behavior_desc = (
                f"At {_format_time(start_t)}, {track_mention} crossed into a configured monitoring zone and remained until "
                f"{_format_time(end_t)} ({duration:.1f}s). Review footage at {_format_time(start_t)} to verify boundary adherence."
            )
            flag_reason = "Boundary trigger: Object centroid crossed into a monitored spatial zone."
        else:
            behavior_desc = (
                f"Between {_format_time(start_t)} and {_format_time(end_t)} ({duration:.1f}s), {source_count} related anomaly "
                f"indicator(s) clustered together involving {track_mention}. Review the footage around {_format_time(start_t)} "
                f"to inspect visual context."
            )
            flag_reason = (
                f"Correlated pattern: {source_count} related indicator(s) clustered across a continuous observation window."
            )

        combined.append({
            "is_correlated_event": True,
            "timestamp": start_t,
            "end_timestamp": end_t,
            "time_formatted": f"{_format_time(start_t)} – {_format_time(end_t)}",
            "category": f"Event: {readable_label}",
            "raw_type": evt_type,
            "severity": severity,
            "confidence": round(float(confidence), 2) if confidence is not None else None,
            "track_ids": valid_tids,
            "track_id_display": track_mention,
            "measurable_change": measurable_change,
            "observable_behavior": behavior_desc,
            "supporting_evidence": {
                "source_anomaly_count": source_count,
                "source_anomaly_types": anomaly_types,
                **evidence_dict,
            },
            "flag_reason": flag_reason,
            "limitations": "Image-space telemetry only; does not infer subject intent, emotion, or real-world physical speed.",
        })

    # 2. Raw Anomalies (Single-frame / isolated flags)
    correlated_anomaly_ids = set()
    for evt in all_events:
        for aid in evt.get("source_anomaly_ids", []):
            correlated_anomaly_ids.add(aid)

    for anom in all_anomalies:
        aid = anom.get("anomaly_id")
        is_correlated = aid in correlated_anomaly_ids if aid else False
        t = float(anom.get("timestamp", 0.0))
        raw_tid = anom.get("track_id")
        atype = str(anom.get("anomaly_type", "unusual_behavior"))
        severity = anom.get("severity", "low")
        score = anom.get("anomaly_score")

        readable_label = LABEL_TRANSLATIONS.get(atype, atype.replace("_", " ").title())
        track_mention = _format_track_mention(raw_tid)
        tid_str = str(raw_tid) if raw_tid is not None and str(raw_tid).lower() not in ("none", "", "null") else None

        evidence = anom.get("evidence") or {}
        curr_speed = evidence.get("current_speed") or evidence.get("speed")
        thresh = evidence.get("threshold") or anom.get("threshold")
        speed_delta = evidence.get("speed_change") or evidence.get("acceleration")
        angle = evidence.get("angle_degrees") or evidence.get("angle")
        dur_val = evidence.get("duration")

        # Determine measurable change cleanly
        if curr_speed is not None and thresh is not None:
            measurable_change = f"Measured speed was {float(curr_speed):.1f} px/s against a configured threshold of {float(thresh):.1f} px/s."
        elif curr_speed is not None:
            measurable_change = f"Measured speed was {float(curr_speed):.1f} px/s (threshold: Not available)."
        elif speed_delta is not None and thresh is not None:
            measurable_change = f"Measured speed change was {float(speed_delta):.1f} px/s against a threshold of {float(thresh):.1f} px/s."
        elif speed_delta is not None:
            measurable_change = f"Measured speed change was {float(speed_delta):.1f} px/s."
        elif angle is not None and thresh is not None:
            measurable_change = f"Measured heading change was {float(angle):.1f}° against a configured threshold of {float(thresh):.1f}°."
        elif angle is not None:
            measurable_change = f"Measured heading change was {float(angle):.1f}°."
        elif dur_val is not None and thresh is not None:
            measurable_change = f"Stationary duration reached {float(dur_val):.1f}s against a threshold of {float(thresh):.1f}s."
        else:
            measurable_change = "Measurement data: Not available."

        # Plain-English observable description
        if "speed" in atype:
            behavior_desc = (
                f"At {_format_time(t)}, an isolated speed flag was logged for {track_mention}. "
                f"{measurable_change} This momentary reading occurred on an individual frame and did not persist into a confirmed event."
            )
            flag_reason = "Single-frame velocity exceeded the configured motion baseline cutoff for this scene."
        elif "direction" in atype:
            behavior_desc = (
                f"At {_format_time(t)}, a sharp course adjustment was noted for {track_mention}. "
                f"{measurable_change} The heading shift was momentary and did not cluster into an irregular sequence."
            )
            flag_reason = "Single-frame trajectory angle deviation exceeded the baseline directional threshold."
        elif "appearance" in atype:
            behavior_desc = (
                f"At {_format_time(t)}, {track_mention} first appeared abruptly inside the frame rather than entering from an edge. "
                f"This may indicate emerging from behind an obstruction or initial tracker acquisition."
            )
            flag_reason = "Tracking coordinates initialized away from the frame perimeter without a prior entry vector."
        elif "loiter" in atype:
            behavior_desc = (
                f"At {_format_time(t)}, {track_mention} triggered a stationary flag. {measurable_change}"
            )
            flag_reason = "Centroid position remained within a confined radius exceeding stationary duration criteria."
        else:
            behavior_desc = (
                f"At {_format_time(t)}, the detector logged an isolated flag ({readable_label.lower()}) for {track_mention}. "
                f"{measurable_change}"
            )
            flag_reason = "Statistical anomaly detector trigger on a single observation frame."

        if not is_correlated:
            combined.append({
                "is_correlated_event": False,
                "timestamp": t,
                "end_timestamp": t,
                "time_formatted": _format_time(t),
                "category": f"Flag: {readable_label}",
                "raw_type": atype,
                "severity": severity,
                "confidence": round(float(score), 2) if score is not None else None,
                "track_ids": [tid_str] if tid_str else [],
                "track_id_display": track_mention,
                "measurable_change": measurable_change,
                "observable_behavior": behavior_desc,
                "supporting_evidence": evidence,
                "flag_reason": flag_reason,
                "limitations": "Isolated single-frame flag; did not meet criteria for an extended multi-frame event.",
            })

    # Sort chronologically by timestamp
    combined.sort(key=lambda x: x["timestamp"])
    return combined


def _build_track_analyses(
    track_summaries: Dict[str, Dict[str, Any]],
    scene_explanation: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Build plain-English analysis for each tracked entity"""
    analyses = []

    def sort_key(item):
        tid = item.get("track_id")
        if tid is None:
            return 999999
        s = str(tid)
        return int(s) if s.lstrip("-").isdigit() else s

    sorted_tracks = sorted(track_summaries.values(), key=sort_key)

    for item in sorted_tracks:
        raw_tid = item["track_id"]
        tid_display = _format_track_mention(raw_tid)
        cname = item["class_name"]
        dur = item["duration"]
        obs_count = item["observations"]
        anoms = item["anomalies"]
        is_flagged = len(anoms) > 0
        first_t = item["first_seen"]
        last_t = item["last_seen"]

        # Speeds
        if item["speeds"]:
            avg_val = round(item["avg_speed"], 1)
            max_val = round(item["max_speed"], 1)
            avg_speed_str = f"{avg_val} px/s"
            max_speed_str = f"{max_val} px/s"
            speed_phrase = f"Recorded average image-space speed was {avg_val} px/s (peak {max_val} px/s)."
        else:
            avg_speed_str = "Not available"
            max_speed_str = "Not available"
            speed_phrase = "Speed measurement: Not available."

        # Plain-English movement narrative
        if obs_count <= 2:
            movement_narrative = (
                f"{tid_display} ({cname}) appeared momentarily at {_format_time(first_t)} for {dur:.2f}s "
                f"({obs_count} frames) before leaving view or losing tracking continuity. {speed_phrase}"
            )
        elif not is_flagged:
            movement_narrative = (
                f"{tid_display} ({cname}) entered at {_format_time(first_t)} and moved through the scene until {_format_time(last_t)} "
                f"({dur:.1f}s total duration). {speed_phrase} Trajectory remained smooth with no anomalous speed spikes or course deviations."
            )
        else:
            anom_names = ", ".join(sorted(set(
                LABEL_TRANSLATIONS.get(a.get("anomaly_type", ""), a.get("anomaly_type", "").replace("_", " ")).lower()
                for a in anoms
            )))
            movement_narrative = (
                f"{tid_display} ({cname}) was tracked from {_format_time(first_t)} to {_format_time(last_t)} ({dur:.1f}s). "
                f"{speed_phrase} The system recorded {len(anoms)} unusual motion indicator(s) ({anom_names}). "
                f"Review footage around the active timestamps to visually assess the movement context."
            )

        tid_str = str(raw_tid) if raw_tid is not None and str(raw_tid).lower() not in ("none", "", "null") else "Unassigned"

        analyses.append({
            "track_id": tid_str,
            "track_id_display": tid_display,
            "class_name": cname,
            "first_seen": round(first_t, 2),
            "last_seen": round(last_t, 2),
            "first_seen_formatted": _format_time(first_t),
            "last_seen_formatted": _format_time(last_t),
            "time_range_formatted": f"{_format_time(first_t)} – {_format_time(last_t)}",
            "duration": round(dur, 2),
            "duration_formatted": _format_time(dur),
            "observations": obs_count,
            "avg_speed_px_s": avg_speed_str,
            "max_speed_px_s": max_speed_str,
            "movement_narrative": movement_narrative,
            "is_flagged": is_flagged,
            "anomaly_count": len(anoms),
            "anomaly_types": [a.get("anomaly_type") for a in anoms],
            "states_observed": item["states_list"],
            "scale_disclaimer": "Pixel speeds (px/s) reflect screen-space movement and vary with camera perspective and distance.",
            "continuity_disclaimer": "Automated tracking assigns temporary IDs and does not verify personal identity if the subject exits and re-enters the scene.",
        })

    return analyses


def _build_executive_summary(
    video_overview: Dict[str, Any],
    all_events: List[Dict[str, Any]],
    all_anomalies: List[Dict[str, Any]],
    track_summaries: Dict[str, Dict[str, Any]],
    scene_explanation: Optional[Dict[str, Any]],
    pipeline_result: Dict[str, Any],
) -> str:
    """Build a concise, evidence-grounded executive summary in plain English"""
    duration_str = video_overview["duration_formatted"]
    tracks_count = video_overview["unique_confirmed_tracks"]
    events_count = len(all_events)
    anom_count = len(all_anomalies)
    res_str = video_overview.get("resolution", "Unknown resolution")
    fps_val = video_overview.get("fps", 0)

    class_dict = pipeline_result.get("m1_detections_by_class", {})
    if class_dict:
        classes_str = ", ".join(f"{cls} ({cnt})" for cls, cnt in class_dict.items())
    else:
        classes_str = "entities"

    # Case 1: No anomalies and no correlated events
    if events_count == 0 and anom_count == 0:
        return (
            f"Video intelligence analysis reviewed {duration_str} of footage ({res_str} at {fps_val:.1f} FPS) "
            f"containing {tracks_count} confirmed track(s) ({classes_str}) across {video_overview['frames_processed']} processed frames. "
            f"No movement anomalies or correlated events were detected. All observed trajectories conformed "
            f"to regular movement baselines without unusual accelerations, sharp turns, or loitering."
        )

    # Case 2: Raw anomalies present, but ZERO correlated events
    if events_count == 0 and anom_count > 0:
        first_anom = all_anomalies[0]
        anom_time = _format_time(float(first_anom.get("timestamp", 0.0)))
        anom_types = ", ".join(sorted(set(
            LABEL_TRANSLATIONS.get(a.get("anomaly_type", ""), a.get("anomaly_type", "").replace("_", " ")).lower()
            for a in all_anomalies
        )))
        return (
            f"Video intelligence analysis reviewed {duration_str} of footage ({res_str} at {fps_val:.1f} FPS) "
            f"containing {tracks_count} confirmed track(s) ({classes_str}). Raw anomaly indicators were detected, "
            f"but no correlated events were established by the event-correlation stage. Specifically, the detector noted "
            f"{anom_count} individual frame flag(s) ({anom_types}), first appearing at {anom_time}. In plain terms, "
            f"the system observed brief moments where movement measurements crossed configured baseline thresholds, "
            f"but these signals occurred in isolation and did not cluster into an extended multi-frame event. "
            f"Review the individual timestamped flags below to inspect each occurrence visually."
        )

    # Case 3: Correlated events exist
    first_evt = all_events[0]
    start_t = float(first_evt.get("start_timestamp", 0.0))
    end_t = float(first_evt.get("end_timestamp", start_t))
    time_span = f"{_format_time(start_t)} to {_format_time(end_t)}" if end_t > start_t else _format_time(start_t)

    evt_types = ", ".join(sorted(set(
        LABEL_TRANSLATIONS.get(e.get("event_type", ""), e.get("event_type", "").replace("_", " ").title())
        for e in all_events
    )))
    involved_tracks = set()
    for e in all_events:
        for tid in e.get("track_ids", []):
            if tid is not None and str(tid).lower() not in ("none", "", "null"):
                involved_tracks.add(f"Track #{tid}")
    tracks_mention = ", ".join(sorted(involved_tracks)) if involved_tracks else "tracked entities"

    return (
        f"Video intelligence analysis reviewed {duration_str} of footage ({res_str} at {fps_val:.1f} FPS) "
        f"with {tracks_count} confirmed track(s) ({classes_str}). The system established {events_count} "
        f"confirmed event(s) ({evt_types}) involving {tracks_mention}, highlighted between {time_span}, "
        f"supported by {anom_count} underlying anomaly flag(s). What the evidence supports: Measured image-space "
        f"movement exceeded configured baseline thresholds across an extended multi-frame window. What remains "
        f"unverified: Automated telemetry measures 2D screen motion only and cannot determine personal intent, "
        f"identity continuity, or the visual real-world cause of the movement. Investigator review is recommended "
        f"around the flagged intervals."
    )


def _build_final_assessment(
    raw_anomalies_count: int,
    correlated_events_count: int,
    chronological_events: List[Dict[str, Any]],
    unique_tracks: int,
    duration: float,
) -> str:
    """Build a cautious, evidence-grounded final assessment"""
    if raw_anomalies_count == 0 and correlated_events_count == 0:
        return (
            f"Review of {duration:.1f}s of footage across {unique_tracks} tracked entities confirms uniform baseline "
            f"movement without flagged anomalies. No intervals currently require human review."
        )

    # Collect specific timestamps that deserve review
    flagged_times = []
    for item in chronological_events:
        t_str = item.get("time_formatted")
        cat = item.get("category")
        if t_str and cat:
            flagged_times.append(f"{t_str} ({cat})")

    top_times_str = "; ".join(flagged_times[:4])
    if len(flagged_times) > 4:
        top_times_str += f"; and {len(flagged_times) - 4} additional timestamp(s)"

    if correlated_events_count > 0:
        return (
            f"The available visual evidence confirms {correlated_events_count} correlated event(s) across "
            f"{raw_anomalies_count} underlying anomaly flags. Recommended timestamps for human review: {top_times_str}. "
            f"All findings represent objective 2D screen-space kinematic measurements. Subject intent, real-world "
            f"physical velocity, and personal identity remain unverified and require visual investigator verification."
        )

    # Raw anomalies only, zero correlated events
    return (
        f"Raw anomaly indicators were detected, but no correlated events were established by the event-correlation stage. "
        f"The detector noted {raw_anomalies_count} momentary speed or direction outlier(s). "
        f"Recommended timestamps for human review: {top_times_str}. These occurrences represent brief threshold "
        f"deviations rather than sustained behavioral incidents, and should be visually reviewed to confirm whether they "
        f"reflect genuine activity or tracking/detection artifacts."
    )
