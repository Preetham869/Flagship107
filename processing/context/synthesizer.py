"""
Context Synthesizer

Orchestrates contextual scene creation from M3/M4/M5/M6 outputs.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
import uuid
import math

from .schemas import (
    ContextualScene,
    TrackSummary,
    SceneEvidence,
    TrackEvidence,
)
from .evidence import EvidenceBuilder
from .patterns import PatternRecognizer, PatternConfig

logger = logging.getLogger(__name__)


@dataclass
class ContextConfig:
    """Configuration for context synthesis"""

    # Scene segmentation
    scene_idle_threshold: float = 3.0  # Seconds without activity = scene boundary
    scene_min_duration: float = 1.0  # Minimum scene duration

    # Pattern recognition config
    pattern_config: Optional[PatternConfig] = None


class ContextSynthesizer:
    """
    Synthesizes M3/M4/M5/M6 outputs into contextual behavioral scenes
    
    Does NOT reprocess data - only aggregates and annotates.
    """

    def __init__(self, config: Optional[ContextConfig] = None):
        """
        Initialize context synthesizer
        
        Args:
            config: Configuration for synthesis
        """
        self.config = config or ContextConfig()
        self.pattern_recognizer = PatternRecognizer(
            self.config.pattern_config or PatternConfig()
        )
        logger.info("ContextSynthesizer initialized")

    def synthesize(
        self,
        all_behaviors: List[List[Dict]],
        all_anomalies: List[Dict],
        all_events: List[Dict],
        all_relationships: List[Dict],
        video_metadata: Dict,
    ) -> List[ContextualScene]:
        """
        Synthesize contextual scenes from M3/M4/M5/M6 data
        
        Args:
            all_behaviors: Frame-by-frame M3 behavior observations
            all_anomalies: M4 anomaly detections
            all_events: M5 correlated events
            all_relationships: M6 entity relationships
            video_metadata: Video metadata (fps, dimensions, etc.)
            
        Returns:
            List of ContextualScene objects
        """
        logger.info("Synthesizing contextual scenes...")

        # Flatten behaviors for easier processing
        flat_behaviors = []
        for frame_behaviors in all_behaviors:
            flat_behaviors.extend(frame_behaviors)

        if not flat_behaviors:
            logger.warning("No behaviors to synthesize")
            return []

        # Segment into scenes
        scene_boundaries = self._segment_scenes(flat_behaviors, all_events)
        logger.info(f"Identified {len(scene_boundaries)} scene boundaries")

        # Build contextual scenes
        scenes = []
        fps = video_metadata.get("video_fps", 30.0)

        for scene_num, (start_time, end_time, boundary_type) in enumerate(scene_boundaries, 1):
            scene = self._build_scene(
                scene_num=scene_num,
                start_time=start_time,
                end_time=end_time,
                boundary_type=boundary_type,
                flat_behaviors=flat_behaviors,
                all_anomalies=all_anomalies,
                all_events=all_events,
                all_relationships=all_relationships,
                fps=fps,
            )
            
            if scene:
                scenes.append(scene)

        logger.info(f"Synthesized {len(scenes)} contextual scenes")
        return scenes

    def _segment_scenes(
        self, flat_behaviors: List[Dict], all_events: List[Dict]
    ) -> List[Tuple[float, float, str]]:
        """
        Segment video into temporal scenes
        
        Boundaries occur at:
        - Activity gaps > threshold
        - Video start/end
        
        Args:
            flat_behaviors: Flattened behavior observations
            all_events: M5 events
            
        Returns:
            List of (start_time, end_time, boundary_type)
        """
        if not flat_behaviors:
            return []

        scenes = []
        current_scene_start = flat_behaviors[0]["timestamp"]
        last_activity = current_scene_start

        for behavior in flat_behaviors:
            timestamp = behavior["timestamp"]

            # Check for activity gap
            gap = timestamp - last_activity
            if gap > self.config.scene_idle_threshold:
                # Close previous scene
                if last_activity - current_scene_start >= self.config.scene_min_duration:
                    scenes.append((current_scene_start, last_activity, "gap"))
                
                # Start new scene
                current_scene_start = timestamp

            last_activity = timestamp

        # Close final scene
        if last_activity - current_scene_start >= self.config.scene_min_duration:
            scenes.append((current_scene_start, last_activity, "end"))

        return scenes

    def _build_scene(
        self,
        scene_num: int,
        start_time: float,
        end_time: float,
        boundary_type: str,
        flat_behaviors: List[Dict],
        all_anomalies: List[Dict],
        all_events: List[Dict],
        all_relationships: List[Dict],
        fps: float,
    ) -> Optional[ContextualScene]:
        """
        Build a contextual scene from data
        
        Args:
            scene_num: Scene number
            start_time: Start timestamp
            end_time: End timestamp
            boundary_type: Reason for boundary
            flat_behaviors: All behaviors
            all_anomalies: All anomalies
            all_events: All events
            all_relationships: All relationships
            fps: Video frame rate
            
        Returns:
            ContextualScene or None
        """
        # Filter data for this scene
        scene_behaviors = EvidenceBuilder.filter_by_timerange(
            flat_behaviors, start_time, end_time
        )
        scene_anomalies = EvidenceBuilder.filter_by_timerange(
            all_anomalies, start_time, end_time
        )
        scene_events = EvidenceBuilder.filter_by_timerange(
            all_events, start_time, end_time
        )
        scene_relationships = EvidenceBuilder.filter_by_timerange(
            all_relationships, start_time, end_time
        )

        if not scene_behaviors:
            return None

        # Identify participating tracks
        track_ids = list(set(str(b["track_id"]) for b in scene_behaviors))

        # Build track summaries
        track_summaries = []
        track_evidence_dict = {}

        for track_id in track_ids:
            track_behaviors = [b for b in scene_behaviors if str(b["track_id"]) == track_id]
            track_anomalies = EvidenceBuilder.filter_by_track_id(scene_anomalies, track_id)
            track_relationships = EvidenceBuilder.filter_by_track_id(scene_relationships, track_id)

            summary = self._build_track_summary(
                track_id,
                track_behaviors,
                track_anomalies,
                track_relationships,
            )
            
            if summary:
                track_summaries.append(summary)
                if summary.evidence:
                    track_evidence_dict[track_id] = summary.evidence

        # Aggregate scene statistics
        total_observations = len(scene_behaviors)
        dominant_states = {}
        speeds = []
        movements = 0

        for behavior in scene_behaviors:
            state = behavior.get("state", "unknown")
            dominant_states[state] = dominant_states.get(state, 0) + 1
            
            speed = behavior.get("speed", 0)
            speeds.append(speed)
            
            if state != "stationary":
                movements += 1

        avg_scene_speed = sum(speeds) / len(speeds) if speeds else 0
        max_scene_speed = max(speeds) if speeds else 0

        # Classify scene type
        anomaly_density = len(scene_anomalies) / (end_time - start_time) if (end_time - start_time) > 0 else 0
        scene_type = "anomalous_activity" if anomaly_density > 0.5 else "normal_activity"

        # Calculate complexity
        complexity_score = len(track_ids) + (len(scene_relationships) * 0.5)

        # Detect scene-level patterns
        scene_patterns = []
        if len(track_ids) > 1:
            # Check for spatial patterns from relationships
            if any(r.get("relationship_type") == "co_movement_event" for r in scene_relationships):
                if pattern := self.pattern_recognizer.detect_parallel_movement(scene_relationships):
                    scene_patterns.append(pattern)

        # Build evidence
        segmentation_rationale = f"Scene boundaries: {boundary_type} (t={start_time:.1f}s to t={end_time:.1f}s)"
        evidence = EvidenceBuilder.create_scene_evidence(
            segmentation_rationale=segmentation_rationale,
            track_evidence=track_evidence_dict,
            pattern_evidence=scene_patterns,
            anomalies=scene_anomalies,
            events=scene_events,
            relationships=scene_relationships,
        )

        # Generate narrative
        summary = self._generate_scene_summary(
            len(track_ids),
            end_time - start_time,
            len(scene_anomalies),
            len(scene_relationships),
        )

        description = self._generate_scene_description(
            track_summaries,
            scene_anomalies,
            scene_relationships,
            start_time,
            end_time,
        )

        key_observations = self._generate_key_observations(
            track_summaries,
            scene_anomalies,
            scene_relationships,
            scene_patterns,
        )

        # Create scene
        scene = ContextualScene(
            scene_id=str(uuid.uuid4()),
            scene_number=scene_num,
            start_timestamp=start_time,
            end_timestamp=end_time,
            duration_seconds=end_time - start_time,
            start_frame=int(start_time * fps),
            end_frame=int(end_time * fps),
            participating_track_ids=track_ids,
            track_summaries=track_summaries,
            total_observations=total_observations,
            dominant_states=dominant_states,
            avg_scene_speed=avg_scene_speed,
            max_scene_speed=max_scene_speed,
            total_movements=movements,
            source_anomalies=[a.get("event_id", "") for a in scene_anomalies],
            source_events=[e.get("event_id", "") for e in scene_events],
            source_relationships=[r.get("relationship_id", "") for r in scene_relationships],
            movement_patterns=[p.pattern_name for p in scene_patterns if "movement" in p.pattern_name.lower()],
            spatial_patterns=[p.pattern_name for p in scene_patterns if any(x in p.pattern_name.lower() for x in ["proximity", "parallel", "approach"])],
            temporal_patterns=[p.pattern_name for p in scene_patterns if "presence" in p.pattern_name.lower()],
            scene_type=scene_type,
            anomaly_density=anomaly_density,
            complexity_score=complexity_score,
            evidence=evidence,
            summary=summary,
            description=description,
            key_observations=key_observations,
        )

        return scene

    def _build_track_summary(
        self,
        track_id: str,
        track_behaviors: List[Dict],
        track_anomalies: List[Dict],
        track_relationships: List[Dict],
    ) -> Optional[TrackSummary]:
        """
        Build summary for a single track
        
        Args:
            track_id: Track ID
            track_behaviors: M3 behaviors for track
            track_anomalies: M4 anomalies for track
            track_relationships: M6 relationships for track
            
        Returns:
            TrackSummary or None
        """
        if not track_behaviors:
            return None

        # Temporal extent
        first_seen = track_behaviors[0]["timestamp"]
        last_seen = track_behaviors[-1]["timestamp"]
        duration = last_seen - first_seen
        observation_count = len(track_behaviors)

        # Spatial analysis
        positions = [b["position"] for b in track_behaviors]
        entry_position = tuple(positions[0])
        exit_position = tuple(positions[-1]) if len(positions) > 1 else None

        # Calculate path length
        path_length = 0.0
        for i in range(1, len(positions)):
            dx = positions[i][0] - positions[i-1][0]
            dy = positions[i][1] - positions[i-1][1]
            path_length += math.sqrt(dx**2 + dy**2)

        avg_displacement = path_length / (len(positions) - 1) if len(positions) > 1 else 0

        # Behavioral statistics
        states = [b.get("state", "unknown") for b in track_behaviors]
        state_counts = {}
        for state in states:
            state_counts[state] = state_counts.get(state, 0) + 1

        total_states = len(states)
        state_distribution = {
            state: count / total_states for state, count in state_counts.items()
        }
        dominant_state = max(state_counts, key=state_counts.get) if state_counts else "unknown"

        speeds = [b.get("speed", 0) for b in track_behaviors]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        max_speed = max(speeds) if speeds else 0
        
        # Speed variance
        speed_variance = (
            sum((s - avg_speed) ** 2 for s in speeds) / len(speeds)
            if len(speeds) > 1 else 0
        )

        # Trajectory classification
        trajectory_type = self._classify_trajectory(track_behaviors, path_length, avg_displacement)

        # Detect patterns
        patterns = self.pattern_recognizer.detect_all_patterns(
            track_behaviors,
            track_relationships,
            speed_threshold=150.0,
        )

        # Anomaly summary
        anomaly_types = list(set(a.get("anomaly_type", "unknown") for a in track_anomalies))
        severities = [a.get("severity", "unknown") for a in track_anomalies]
        anomaly_severity_max = "high" if "high" in severities else (
            "medium" if "medium" in severities else (
                "low" if "low" in severities else "none"
            )
        )

        # Interaction summary
        interacted_with = []
        interaction_types = []
        for rel in track_relationships:
            other_tracks = [
                tid for tid in rel.get("participating_track_ids", [])
                if tid != track_id
            ]
            interacted_with.extend(other_tracks)
            interaction_types.append(rel.get("relationship_type", "unknown"))

        interacted_with = list(set(interacted_with))

        # Build evidence
        evidence = EvidenceBuilder.create_track_evidence(
            behaviors=track_behaviors,
            anomalies=track_anomalies,
            relationships=track_relationships,
            patterns=patterns,
        )

        # Classify behavior
        behavior_label = self._classify_behavior(
            dominant_state,
            avg_speed,
            patterns,
        )

        # Generate summary
        summary = self._generate_track_summary(
            track_id,
            behavior_label,
            duration,
            avg_speed,
            len(track_anomalies),
        )

        return TrackSummary(
            track_id=track_id,
            class_name=track_behaviors[0].get("class_name", "unknown"),
            first_seen=first_seen,
            last_seen=last_seen,
            duration=duration,
            observation_count=observation_count,
            entry_position=entry_position,
            exit_position=exit_position,
            path_length=path_length,
            avg_displacement=avg_displacement,
            state_distribution=state_distribution,
            dominant_state=dominant_state,
            avg_speed=avg_speed,
            max_speed=max_speed,
            speed_variance=speed_variance,
            trajectory_type=trajectory_type,
            movement_patterns=[p.pattern_name for p in patterns],
            anomaly_count=len(track_anomalies),
            anomaly_types=anomaly_types,
            anomaly_severity_max=anomaly_severity_max,
            interaction_count=len(track_relationships),
            interacted_with_tracks=interacted_with,
            interaction_types=interaction_types,
            evidence=evidence,
            behavior_label=behavior_label,
            summary=summary,
        )

    def _classify_trajectory(
        self, track_behaviors: List[Dict], path_length: float, avg_displacement: float
    ) -> str:
        """Classify trajectory type based on movement"""
        if avg_displacement < 5.0:
            return "stationary"
        
        # Check for linear movement
        directions = [b.get("direction") for b in track_behaviors if b.get("direction") is not None]
        if len(directions) >= 5:
            avg_dir = sum(directions) / len(directions)
            variance = sum((d - avg_dir) ** 2 for d in directions) / len(directions)
            std_dev = math.sqrt(variance)
            
            if std_dev < 30.0:
                return "linear"
            elif std_dev > 80.0:
                return "erratic"
        
        return "curved"

    def _classify_behavior(
        self, dominant_state: str, avg_speed: float, patterns: List
    ) -> str:
        """Classify overall behavior"""
        if dominant_state == "stationary":
            return "stationary_entity"
        
        # Check patterns
        pattern_names = [p.pattern_name for p in patterns]
        
        if "rapid_movement" in pattern_names:
            return "rapid_mover"
        elif "stationary_extended" in pattern_names:
            return "stationary_entity"
        elif "linear_traversal" in pattern_names:
            return "pedestrian"
        elif "erratic_movement" in pattern_names:
            return "erratic_mover"
        elif avg_speed < 50:
            return "slow_mover"
        else:
            return "normal_mover"

    # ========================================================================
    # Narrative Generation (Deterministic, Evidence-Based)
    # ========================================================================

    def _generate_scene_summary(
        self,
        entity_count: int,
        duration: float,
        anomaly_count: int,
        relationship_count: int,
    ) -> str:
        """Generate one-sentence scene summary"""
        entities_text = f"{entity_count} {'entity' if entity_count == 1 else 'entities'}"
        
        summary = f"{entities_text} observed for {duration:.1f}s"
        
        if anomaly_count > 0:
            summary += f" with {anomaly_count} {'anomaly' if anomaly_count == 1 else 'anomalies'}"
        
        if relationship_count > 0:
            summary += f" and {relationship_count} {'interaction' if relationship_count == 1 else 'interactions'}"
        
        return summary

    def _generate_scene_description(
        self,
        track_summaries: List[TrackSummary],
        scene_anomalies: List[Dict],
        scene_relationships: List[Dict],
        start_time: float,
        end_time: float,
    ) -> str:
        """Generate multi-sentence scene description"""
        lines = []
        
        # Scene extent
        lines.append(
            f"Scene spans {end_time - start_time:.1f}s (t={start_time:.1f}s to t={end_time:.1f}s) "
            f"with {len(track_summaries)} participating {'entity' if len(track_summaries) == 1 else 'entities'}."
        )
        
        # Track summaries
        for ts in track_summaries:
            if ts.movement_patterns:
                patterns_text = ", ".join(ts.movement_patterns)
                lines.append(
                    f"Track #{ts.track_id}: {ts.behavior_label} "
                    f"(avg {ts.avg_speed:.1f}px/s, patterns: {patterns_text})."
                )
            else:
                lines.append(
                    f"Track #{ts.track_id}: {ts.behavior_label} (avg {ts.avg_speed:.1f}px/s)."
                )
        
        # Anomalies
        if scene_anomalies:
            anomaly_types = list(set(a.get("anomaly_type", "unknown") for a in scene_anomalies))
            lines.append(
                f"{len(scene_anomalies)} anomalies detected ({', '.join(anomaly_types)})."
            )
        else:
            lines.append("No anomalies detected.")
        
        # Relationships
        if scene_relationships:
            rel_types = list(set(r.get("relationship_type", "unknown") for r in scene_relationships))
            lines.append(
                f"{len(scene_relationships)} entity interactions observed ({', '.join(rel_types)})."
            )
        else:
            lines.append("No entity interactions observed.")
        
        return " ".join(lines)

    def _generate_key_observations(
        self,
        track_summaries: List[TrackSummary],
        scene_anomalies: List[Dict],
        scene_relationships: List[Dict],
        scene_patterns: List,
    ) -> List[str]:
        """Generate bullet-point key observations"""
        observations = []
        
        # Track observations
        for ts in track_summaries:
            obs = f"Track #{ts.track_id}: {ts.behavior_label}"
            if ts.avg_speed > 0:
                obs += f" ({ts.avg_speed:.1f}px/s avg, max {ts.max_speed:.1f}px/s)"
            observations.append(obs)
        
        # Pattern observations
        for pattern in scene_patterns:
            observations.append(f"Pattern: {pattern.description}")
        
        # Anomaly observations
        if scene_anomalies:
            anomaly_by_type = {}
            for a in scene_anomalies:
                atype = a.get("anomaly_type", "unknown")
                anomaly_by_type[atype] = anomaly_by_type.get(atype, 0) + 1
            
            for atype, count in anomaly_by_type.items():
                observations.append(f"Anomaly: {count} {atype} {'detection' if count == 1 else 'detections'}")
        else:
            observations.append("No anomalies detected")
        
        # Relationship observations
        if scene_relationships:
            rel_by_type = {}
            for r in scene_relationships:
                rtype = r.get("relationship_type", "unknown")
                rel_by_type[rtype] = rel_by_type.get(rtype, 0) + 1
            
            for rtype, count in rel_by_type.items():
                observations.append(f"Interaction: {count} {rtype} {'observation' if count == 1 else 'observations'}")
        else:
            observations.append("No entity interactions observed")
        
        return observations

    def _generate_track_summary(
        self,
        track_id: str,
        behavior_label: str,
        duration: float,
        avg_speed: float,
        anomaly_count: int,
    ) -> str:
        """Generate evidence-based track summary"""
        summary = f"Track #{track_id} ({behavior_label})"
        
        if duration > 0:
            summary += f" observed for {duration:.1f}s"
        
        if avg_speed > 0:
            summary += f" with average speed {avg_speed:.1f}px/s"
        
        if anomaly_count > 0:
            summary += f" and {anomaly_count} {'anomaly' if anomaly_count == 1 else 'anomalies'}"
        
        return summary
