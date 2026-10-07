"""
End-to-end pipeline for video intelligence processing

Integrates M1-M6:
- M1: Object Detection
- M2: Multi-Object Tracking
- M3: Behavior Analysis
- M4: Anomaly Detection
- M5: Event Correlation
- M6: Multi-Entity Interaction Detection
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Callable
import cv2
import numpy as np

from processing.tracking.object_tracker import ObjectTracker
from processing.behavior.analyzer import BehaviorAnalyzer, BehaviorConfig
from processing.anomaly.detector import AnomalyDetector, AnomalyConfig
from processing.events.correlator import EventCorrelator, EventConfig
from processing.interactions.detector import InteractionDetector, InteractionConfig

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for end-to-end pipeline"""
    
    # M1/M2: Detection and Tracking
    model_name: str = "yolov8n.pt"
    confidence_threshold: float = 0.5
    device: Optional[str] = None
    tracker_config: str = "bytetrack.yaml"
    person_only: bool = False
    
    # M3: Behavior Analysis
    behavior_config: Optional[BehaviorConfig] = None
    
    # M4: Anomaly Detection
    anomaly_config: Optional[AnomalyConfig] = None
    
    # M5: Event Correlation
    event_config: Optional[EventConfig] = None
    
    # M6: Interaction Detection
    interaction_config: Optional[InteractionConfig] = None
    
    # Processing options
    frame_skip: int = 1
    max_frames: Optional[int] = None
    
    def __post_init__(self):
        """Initialize default configs"""
        if self.behavior_config is None:
            self.behavior_config = BehaviorConfig()
        if self.anomaly_config is None:
            self.anomaly_config = AnomalyConfig()
        if self.event_config is None:
            self.event_config = EventConfig()
        if self.interaction_config is None:
            self.interaction_config = InteractionConfig()


@dataclass
class PipelineResult:
    """Results from end-to-end pipeline processing"""
    
    # Video metadata (required)
    video_path: str
    video_width: int
    video_height: int
    video_fps: float
    video_total_frames: int
    video_duration: float
    
    # Processing metadata (required)
    frames_processed: int
    frames_skipped: int
    processing_time: float
    
    # M1: Detection statistics (required)
    m1_total_detections: int
    
    # M2: Tracking statistics (required)
    m2_unique_tracks: int
    m2_active_tracks: int
    m2_total_track_observations: int
    
    # M3: Behavior statistics (required)
    m3_total_behaviors: int
    
    # M4: Anomaly statistics (required)
    m4_total_anomalies: int
    
    # M5: Event statistics (required)
    m5_total_raw_anomalies: int
    m5_correlated_events: int
    
    # M6: Interaction statistics (required)
    m6_total_relationships: int
    m6_tracked_pairs: int
    
    # M8: Context statistics (required)
    m8_total_scenes: int = 0
    m8_avg_scene_duration: float = 0.0
    
    # All optional fields with defaults
    m1_detections_by_class: Dict[str, int] = field(default_factory=dict)
    m1_avg_detections_per_frame: float = 0.0
    m2_avg_tracks_per_frame: float = 0.0
    m2_track_duration_stats: Dict[str, float] = field(default_factory=dict)
    m3_states_observed: Dict[str, int] = field(default_factory=dict)
    m3_avg_speed: float = 0.0
    m3_max_speed: float = 0.0
    m4_anomalies_by_type: Dict[str, int] = field(default_factory=dict)
    m4_severity_distribution: Dict[str, int] = field(default_factory=dict)
    m5_events_by_type: Dict[str, int] = field(default_factory=dict)
    m5_event_severity_distribution: Dict[str, int] = field(default_factory=dict)
    m5_compression_ratio: float = 0.0
    m6_relationships_by_type: Dict[str, int] = field(default_factory=dict)
    m6_groups_formed: int = 0
    all_tracks: List[List[Dict]] = field(default_factory=list)
    all_behaviors: List[List[Dict]] = field(default_factory=list)
    all_anomalies: List[Dict] = field(default_factory=list)
    all_events: List[Dict] = field(default_factory=list)
    all_relationships: List[Dict] = field(default_factory=list)
    all_scenes: List[Dict] = field(default_factory=list)  # M8 contextual scenes
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        result = asdict(self)
        return result
    
    def to_json(self, path: str):
        """Save to JSON file"""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


class EndToEndPipeline:
    """
    End-to-end video intelligence pipeline
    
    Processes video through M1-M8:
    1. Detection & Tracking (M1/M2)
    2. Behavior Analysis (M3)
    3. Anomaly Detection (M4)
    4. Event Correlation (M5)
    5. Interaction Detection (M6)
    6. Contextual Understanding (M8)
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize pipeline
        
        Args:
            config: Pipeline configuration
        """
        self.config = config or PipelineConfig()
        
        # Initialize M1/M2: Object Tracker
        logger.info(f"Initializing object tracker with model {self.config.model_name}")
        self.tracker = ObjectTracker(
            model_name=self.config.model_name,
            confidence_threshold=self.config.confidence_threshold,
            device=self.config.device,
            tracker_config=self.config.tracker_config,
        )
        
        # Determine track classes
        self.track_classes = None
        if self.config.person_only:
            person_id = self.tracker.get_person_class_id()
            self.track_classes = [person_id]
            logger.info(f"Tracking only people (class {person_id})")
        
        # Initialize M3: Behavior Analyzer
        logger.info("Initializing behavior analyzer")
        self.behavior_analyzer = BehaviorAnalyzer(self.config.behavior_config)
        
        # Initialize M4: Anomaly Detector
        logger.info("Initializing anomaly detector")
        self.anomaly_detector = AnomalyDetector(self.config.anomaly_config)
        
        # Initialize M5: Event Correlator
        logger.info("Initializing event correlator")
        self.event_correlator = EventCorrelator(self.config.event_config)
        
        # Initialize M6: Interaction Detector
        logger.info("Initializing interaction detector")
        self.interaction_detector = InteractionDetector(self.config.interaction_config)
        
        # Initialize M8: Context Synthesizer
        logger.info("Initializing context synthesizer")
        from processing.context import ContextSynthesizer, ContextConfig
        self.context_synthesizer = ContextSynthesizer(ContextConfig())
    
    def process_video(
        self,
        video_path: str,
        output_video_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> PipelineResult:
        """
        Process video through complete pipeline
        
        Args:
            video_path: Path to input video
            output_video_path: Optional path for annotated output video
            progress_callback: Optional callback(current_frame, total_frames)
            
        Returns:
            PipelineResult with statistics and outputs
        """
        import time
        start_time = time.time()
        
        # Get video info
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"Video: {width}x{height} @ {fps:.2f}fps, {total_frames} frames ({duration:.2f}s)")
        
        # Initialize output video writer if requested
        video_writer = None
        if output_video_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        
        # Initialize result
        result = PipelineResult(
            video_path=video_path,
            video_width=width,
            video_height=height,
            video_fps=fps,
            video_total_frames=total_frames,
            video_duration=duration,
            frames_processed=0,
            frames_skipped=0,
            processing_time=0.0,
            m1_total_detections=0,
            m2_unique_tracks=0,
            m2_active_tracks=0,
            m2_total_track_observations=0,
            m3_total_behaviors=0,
            m4_total_anomalies=0,
            m5_total_raw_anomalies=0,
            m5_correlated_events=0,
            m6_total_relationships=0,
            m6_tracked_pairs=0,
        )
        
        # Track unique IDs
        unique_track_ids = set()
        track_durations = {}  # track_id -> (first_frame, last_frame)
        
        # Accumulated data for M5 (event correlation)
        all_anomalies = []
        
        frame_idx = 0
        frames_processed = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Apply frame skip
                if frame_idx % self.config.frame_skip != 0:
                    frame_idx += 1
                    result.frames_skipped += 1
                    continue
                
                # Check max frames limit
                if self.config.max_frames and frames_processed >= self.config.max_frames:
                    logger.info(f"Reached max_frames limit: {self.config.max_frames}")
                    break
                
                timestamp = frame_idx / fps if fps > 0 else frame_idx
                
                # M1/M2: Detection and Tracking
                tracks = self.tracker.track(
                    frame,
                    persist=True,
                    classes=self.track_classes,
                )
                
                # Update statistics
                result.m1_total_detections += len(tracks)
                for track in tracks:
                    class_name = track.get("class_name", "unknown")
                    result.m1_detections_by_class[class_name] = \
                        result.m1_detections_by_class.get(class_name, 0) + 1
                    
                    track_id = track["track_id"]
                    unique_track_ids.add(track_id)
                    
                    # Track duration
                    if track_id not in track_durations:
                        track_durations[track_id] = (frame_idx, frame_idx)
                    else:
                        track_durations[track_id] = (track_durations[track_id][0], frame_idx)
                
                result.all_tracks.append(tracks)
                result.m2_total_track_observations += len(tracks)
                
                # M3: Behavior Analysis
                behaviors = self.behavior_analyzer.update(tracks, timestamp)
                result.all_behaviors.append(behaviors)
                result.m3_total_behaviors += len(behaviors)
                
                # Update behavior statistics
                for behavior in behaviors:
                    state = behavior.get("state", "unknown")
                    result.m3_states_observed[state] = \
                        result.m3_states_observed.get(state, 0) + 1
                    
                    speed = behavior.get("speed", 0.0)
                    result.m3_avg_speed += speed
                    result.m3_max_speed = max(result.m3_max_speed, speed)
                
                # M4: Anomaly Detection
                anomalies = self.anomaly_detector.detect(behaviors)
                all_anomalies.extend(anomalies)
                result.m4_total_anomalies += len(anomalies)
                
                # Update anomaly statistics
                for anomaly in anomalies:
                    anom_type = anomaly.get("anomaly_type", "unknown")
                    result.m4_anomalies_by_type[anom_type] = \
                        result.m4_anomalies_by_type.get(anom_type, 0) + 1
                    
                    severity = anomaly.get("severity", "UNKNOWN")
                    result.m4_severity_distribution[severity] = \
                        result.m4_severity_distribution.get(severity, 0) + 1
                
                # M6: Interaction Detection (needs multiple entities)
                if len(behaviors) >= 2:
                    relationships = self.interaction_detector.detect(behaviors)
                    result.m6_total_relationships += len(relationships)
                    
                    # Update relationship statistics
                    for rel in relationships:
                        rel_type = rel.relationship_type.value
                        result.m6_relationships_by_type[rel_type] = \
                            result.m6_relationships_by_type.get(rel_type, 0) + 1
                        
                        # Track group formations
                        if rel_type == "group_formation":
                            result.m6_groups_formed += 1
                        
                        # Store relationship as dict
                        result.all_relationships.append(rel.to_dict())
                
                # Draw annotations if output video requested
                if video_writer:
                    annotated_frame = self._draw_annotations(
                        frame.copy(), tracks, behaviors, anomalies
                    )
                    video_writer.write(annotated_frame)
                
                # Progress callback
                if progress_callback:
                    progress_callback(frames_processed + 1, total_frames)
                
                frames_processed += 1
                frame_idx += 1
            
        finally:
            cap.release()
            if video_writer:
                video_writer.release()
        
        # M5: Event Correlation (process all accumulated anomalies)
        logger.info(f"Correlating {len(all_anomalies)} anomalies into events...")
        events = self.event_correlator.correlate(all_anomalies)
        
        result.m5_total_raw_anomalies = len(all_anomalies)
        result.m5_correlated_events = len(events)
        result.all_anomalies = all_anomalies
        
        # Calculate compression ratio
        if len(all_anomalies) > 0:
            result.m5_compression_ratio = len(events) / len(all_anomalies)
        
        # Update event statistics
        for event in events:
            event_dict = event.to_dict()
            result.all_events.append(event_dict)
            
            event_type = event_dict.get("event_type", "unknown")
            result.m5_events_by_type[event_type] = \
                result.m5_events_by_type.get(event_type, 0) + 1
            
            severity = event_dict.get("severity", "UNKNOWN")
            result.m5_event_severity_distribution[severity] = \
                result.m5_event_severity_distribution.get(severity, 0) + 1
        
        # M8: Context Synthesis (process all accumulated data)
        logger.info("Synthesizing contextual scenes...")
        video_metadata = {
            "video_fps": fps,
            "video_width": width,
            "video_height": height,
        }
        scenes = self.context_synthesizer.synthesize(
            all_behaviors=result.all_behaviors,
            all_anomalies=result.all_anomalies,
            all_events=result.all_events,
            all_relationships=result.all_relationships,
            video_metadata=video_metadata,
        )
        
        result.m8_total_scenes = len(scenes)
        
        # Store scenes
        for scene in scenes:
            result.all_scenes.append(scene.to_dict())
        
        # Calculate M8 statistics
        if scenes:
            scene_durations = [s.duration_seconds for s in scenes]
            result.m8_avg_scene_duration = sum(scene_durations) / len(scene_durations)
        
        # Finalize statistics
        result.frames_processed = frames_processed
        result.processing_time = time.time() - start_time
        result.m2_unique_tracks = len(unique_track_ids)
        result.m2_active_tracks = len(unique_track_ids)  # Simplified: all are "active"
        
        if frames_processed > 0:
            result.m1_avg_detections_per_frame = result.m1_total_detections / frames_processed
            result.m2_avg_tracks_per_frame = result.m2_total_track_observations / frames_processed
            result.m3_avg_speed = result.m3_avg_speed / result.m3_total_behaviors if result.m3_total_behaviors > 0 else 0
        
        # Calculate track duration statistics
        durations = []
        for track_id, (first, last) in track_durations.items():
            duration_frames = last - first + 1
            duration_seconds = duration_frames / fps if fps > 0 else duration_frames
            durations.append(duration_seconds)
        
        if durations:
            result.m2_track_duration_stats = {
                "min": min(durations),
                "max": max(durations),
                "avg": sum(durations) / len(durations),
                "total_tracks": len(durations),
            }
        
        # M6 statistics
        result.m6_tracked_pairs = self.interaction_detector.get_statistics()["tracked_pairs"]
        
        logger.info(f"Pipeline complete: processed {frames_processed} frames in {result.processing_time:.2f}s")
        logger.info(f"  M1: {result.m1_total_detections} detections")
        logger.info(f"  M2: {result.m2_unique_tracks} unique tracks")
        logger.info(f"  M3: {result.m3_total_behaviors} behaviors")
        logger.info(f"  M4: {result.m4_total_anomalies} anomalies")
        logger.info(f"  M5: {result.m5_correlated_events} events (from {result.m5_total_raw_anomalies} anomalies)")
        logger.info(f"  M6: {result.m6_total_relationships} relationships")
        logger.info(f"  M8: {result.m8_total_scenes} contextual scenes")
        
        return result
    
    def _draw_annotations(
        self,
        frame: np.ndarray,
        tracks: List[Dict],
        behaviors: List[Dict],
        anomalies: List[Dict],
    ) -> np.ndarray:
        """
        Draw annotations on frame
        
        Args:
            frame: Input frame
            tracks: Tracking results
            behaviors: Behavior analysis results
            anomalies: Detected anomalies
            
        Returns:
            Annotated frame
        """
        # Create a mapping of track_id to anomalies
        anomaly_tracks = {a["track_id"] for a in anomalies}
        
        # Draw tracks with behavior information
        for track in tracks:
            track_id = track["track_id"]
            bbox = track["bbox"]
            class_name = track.get("class_name", "unknown")
            
            # Find corresponding behavior
            behavior = next((b for b in behaviors if b["track_id"] == track_id), None)
            
            # Color: red if anomaly, green otherwise
            color = (0, 0, 255) if track_id in anomaly_tracks else (0, 255, 0)
            
            # Draw bounding box
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"#{track_id} {class_name}"
            if behavior:
                state = behavior.get("state", "")
                speed = behavior.get("speed", 0)
                label += f" {state} {speed:.1f}px/s"
            
            cv2.putText(
                frame, label, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
            )
        
        # Draw anomaly count
        if anomalies:
            cv2.putText(
                frame, f"Anomalies: {len(anomalies)}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2
            )
        
        return frame
