"""
M8 Data Schemas

Defines data structures for contextual behavioral understanding.
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
import json


@dataclass
class SourceReference:
    """
    Reference to a specific source observation from M3/M4/M5/M6
    
    Provides complete traceability for every contextual claim.
    """
    source_module: str  # "M3", "M4", "M5", "M6"
    source_type: str  # "behavior", "anomaly", "event", "relationship"
    source_id: str  # event_id, relationship_id, or index
    timestamp: float
    track_ids: List[str]
    measurement: Optional[Dict] = None  # Relevant measurements

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class PatternEvidence:
    """
    Evidence for a detected behavioral pattern
    
    Every pattern detection must include supporting evidence.
    """
    pattern_name: str
    confidence: float  # 0-1, deterministic score
    supporting_observations: List[SourceReference]
    measurements: Dict  # Pattern-specific measurements
    description: str  # Evidence-based explanation

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "pattern_name": self.pattern_name,
            "confidence": round(self.confidence, 3),
            "supporting_observations": [obs.to_dict() for obs in self.supporting_observations],
            "measurements": self.measurements,
            "description": self.description,
        }


@dataclass
class TrackEvidence:
    """
    Evidence structure for track summary
    
    Links track summary claims to source M3/M4/M6 data.
    """
    source_behaviors: List[str]  # M3 observation identifiers
    source_anomalies: List[str]  # M4 anomaly event_ids
    source_relationships: List[str]  # M6 relationship_ids
    pattern_evidence: List[PatternEvidence] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "source_behaviors": self.source_behaviors,
            "source_anomalies": self.source_anomalies,
            "source_relationships": self.source_relationships,
            "pattern_evidence": [pe.to_dict() for pe in self.pattern_evidence],
        }


@dataclass
class SceneEvidence:
    """
    Evidence structure for entire scene
    
    Aggregates all evidence for scene-level claims.
    """
    segmentation_rationale: str  # Why this is a scene
    track_evidence: Dict[str, TrackEvidence]  # track_id → evidence
    pattern_evidence: List[PatternEvidence] = field(default_factory=list)
    anomaly_summary: Dict = field(default_factory=dict)  # Aggregated M4 evidence
    event_summary: Dict = field(default_factory=dict)  # Aggregated M5 evidence
    relationship_summary: Dict = field(default_factory=dict)  # Aggregated M6 evidence

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "segmentation_rationale": self.segmentation_rationale,
            "track_evidence": {
                tid: ev.to_dict() for tid, ev in self.track_evidence.items()
            },
            "pattern_evidence": [pe.to_dict() for pe in self.pattern_evidence],
            "anomaly_summary": self.anomaly_summary,
            "event_summary": self.event_summary,
            "relationship_summary": self.relationship_summary,
        }


@dataclass
class TrackSummary:
    """
    Complete behavioral summary for one track in a scene
    
    Aggregates M3 behaviors, M4 anomalies, M6 interactions for one entity.
    """
    # === Identity ===
    track_id: str
    class_name: str

    # === Temporal ===
    first_seen: float
    last_seen: float
    duration: float
    observation_count: int

    # === Spatial ===
    entry_position: Tuple[float, float]
    exit_position: Optional[Tuple[float, float]]
    path_length: float
    avg_displacement: float

    # === Behavioral (from M3) ===
    state_distribution: Dict[str, float]  # state → percentage
    dominant_state: str
    avg_speed: float
    max_speed: float
    speed_variance: float

    # === Movement Characterization ===
    trajectory_type: str  # "linear", "circular", "erratic", "stationary"
    movement_patterns: List[str] = field(default_factory=list)

    # === Anomalies (from M4) ===
    anomaly_count: int = 0
    anomaly_types: List[str] = field(default_factory=list)
    anomaly_severity_max: str = "none"

    # === Interactions (from M6) ===
    interaction_count: int = 0
    interacted_with_tracks: List[str] = field(default_factory=list)
    interaction_types: List[str] = field(default_factory=list)

    # === Evidence ===
    evidence: Optional[TrackEvidence] = None

    # === Summary ===
    behavior_label: str = "unknown"
    summary: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        result = asdict(self)
        # Convert evidence separately to use its to_dict method
        if self.evidence:
            result["evidence"] = self.evidence.to_dict()
        return result


@dataclass
class ContextualScene:
    """
    A temporally coherent behavioral scene with complete evidence tracing
    
    Represents a segment of video activity with aggregated behavioral context.
    """
    # === Identity ===
    scene_id: str
    scene_number: int

    # === Temporal Extent ===
    start_timestamp: float
    end_timestamp: float
    duration_seconds: float
    start_frame: int
    end_frame: int

    # === Participants ===
    participating_track_ids: List[str]
    track_summaries: List[TrackSummary]

    # === Activity Summary (Aggregated from M3) ===
    total_observations: int
    dominant_states: Dict[str, int]  # state → count
    avg_scene_speed: float
    max_scene_speed: float
    total_movements: int

    # === Source Data References ===
    source_anomalies: List[str]  # Anomaly event_ids from M4
    source_events: List[str]  # Event event_ids from M5
    source_relationships: List[str]  # Relationship relationship_ids from M6

    # === Detected Patterns ===
    movement_patterns: List[str] = field(default_factory=list)
    spatial_patterns: List[str] = field(default_factory=list)
    temporal_patterns: List[str] = field(default_factory=list)

    # === Scene Classification ===
    scene_type: str = "normal_activity"
    anomaly_density: float = 0.0
    complexity_score: float = 0.0

    # === Evidence ===
    evidence: Optional[SceneEvidence] = None

    # === Narrative (Deterministic, Evidence-Based) ===
    summary: str = ""
    description: str = ""
    key_observations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        result = {
            "scene_id": self.scene_id,
            "scene_number": self.scene_number,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "duration_seconds": round(self.duration_seconds, 2),
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "participating_track_ids": self.participating_track_ids,
            "track_summaries": [ts.to_dict() for ts in self.track_summaries],
            "total_observations": self.total_observations,
            "dominant_states": self.dominant_states,
            "avg_scene_speed": round(self.avg_scene_speed, 2),
            "max_scene_speed": round(self.max_scene_speed, 2),
            "total_movements": self.total_movements,
            "source_anomalies": self.source_anomalies,
            "source_events": self.source_events,
            "source_relationships": self.source_relationships,
            "movement_patterns": self.movement_patterns,
            "spatial_patterns": self.spatial_patterns,
            "temporal_patterns": self.temporal_patterns,
            "scene_type": self.scene_type,
            "anomaly_density": round(self.anomaly_density, 3),
            "complexity_score": round(self.complexity_score, 2),
            "summary": self.summary,
            "description": self.description,
            "key_observations": self.key_observations,
        }
        
        if self.evidence:
            result["evidence"] = self.evidence.to_dict()
        
        return result

    def to_json(self, path: str):
        """Save to JSON file"""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextualScene':
        """
        Construct ContextualScene from dictionary
        
        Used by M9 API endpoint to deserialize stored M8 results.
        """
        # Parse track summaries
        track_summaries = []
        for ts_dict in data.get("track_summaries", []):
            # Handle evidence if present
            evidence = None
            if "evidence" in ts_dict and ts_dict["evidence"]:
                ev_dict = ts_dict["evidence"]
                # Parse pattern evidence
                pattern_evidence = []
                for pe_dict in ev_dict.get("pattern_evidence", []):
                    # Parse source references
                    source_refs = []
                    for sr_dict in pe_dict.get("supporting_observations", []):
                        source_refs.append(SourceReference(**sr_dict))
                    
                    pattern_evidence.append(PatternEvidence(
                        pattern_name=pe_dict["pattern_name"],
                        confidence=pe_dict["confidence"],
                        supporting_observations=source_refs,
                        measurements=pe_dict["measurements"],
                        description=pe_dict["description"]
                    ))
                
                evidence = TrackEvidence(
                    source_behaviors=ev_dict.get("source_behaviors", []),
                    source_anomalies=ev_dict.get("source_anomalies", []),
                    source_relationships=ev_dict.get("source_relationships", []),
                    pattern_evidence=pattern_evidence
                )
            
            # Build TrackSummary
            track_summaries.append(TrackSummary(
                track_id=ts_dict["track_id"],
                class_name=ts_dict["class_name"],
                first_seen=ts_dict["first_seen"],
                last_seen=ts_dict["last_seen"],
                duration=ts_dict["duration"],
                observation_count=ts_dict["observation_count"],
                entry_position=tuple(ts_dict["entry_position"]),
                exit_position=tuple(ts_dict["exit_position"]) if ts_dict.get("exit_position") else None,
                path_length=ts_dict["path_length"],
                avg_displacement=ts_dict["avg_displacement"],
                state_distribution=ts_dict["state_distribution"],
                dominant_state=ts_dict["dominant_state"],
                avg_speed=ts_dict["avg_speed"],
                max_speed=ts_dict["max_speed"],
                speed_variance=ts_dict["speed_variance"],
                trajectory_type=ts_dict["trajectory_type"],
                movement_patterns=ts_dict.get("movement_patterns", []),
                anomaly_count=ts_dict.get("anomaly_count", 0),
                anomaly_types=ts_dict.get("anomaly_types", []),
                anomaly_severity_max=ts_dict.get("anomaly_severity_max", "none"),
                interaction_count=ts_dict.get("interaction_count", 0),
                interacted_with_tracks=ts_dict.get("interacted_with_tracks", []),
                interaction_types=ts_dict.get("interaction_types", []),
                evidence=evidence,
                behavior_label=ts_dict.get("behavior_label", "unknown"),
                summary=ts_dict.get("summary", "")
            ))
        
        # Parse scene evidence if present
        scene_evidence = None
        if "evidence" in data and data["evidence"]:
            ev_dict = data["evidence"]
            # Parse pattern evidence
            pattern_evidence = []
            for pe_dict in ev_dict.get("pattern_evidence", []):
                source_refs = []
                for sr_dict in pe_dict.get("supporting_observations", []):
                    source_refs.append(SourceReference(**sr_dict))
                
                pattern_evidence.append(PatternEvidence(
                    pattern_name=pe_dict["pattern_name"],
                    confidence=pe_dict["confidence"],
                    supporting_observations=source_refs,
                    measurements=pe_dict["measurements"],
                    description=pe_dict["description"]
                ))
            
            # Parse track evidence
            track_evidence = {}
            for track_id, te_dict in ev_dict.get("track_evidence", {}).items():
                te_pattern_evidence = []
                for pe_dict in te_dict.get("pattern_evidence", []):
                    source_refs = []
                    for sr_dict in pe_dict.get("supporting_observations", []):
                        source_refs.append(SourceReference(**sr_dict))
                    
                    te_pattern_evidence.append(PatternEvidence(
                        pattern_name=pe_dict["pattern_name"],
                        confidence=pe_dict["confidence"],
                        supporting_observations=source_refs,
                        measurements=pe_dict["measurements"],
                        description=pe_dict["description"]
                    ))
                
                track_evidence[track_id] = TrackEvidence(
                    source_behaviors=te_dict.get("source_behaviors", []),
                    source_anomalies=te_dict.get("source_anomalies", []),
                    source_relationships=te_dict.get("source_relationships", []),
                    pattern_evidence=te_pattern_evidence
                )
            
            scene_evidence = SceneEvidence(
                segmentation_rationale=ev_dict.get("segmentation_rationale", ""),
                track_evidence=track_evidence,
                pattern_evidence=pattern_evidence,
                anomaly_summary=ev_dict.get("anomaly_summary", {}),
                event_summary=ev_dict.get("event_summary", {}),
                relationship_summary=ev_dict.get("relationship_summary", {})
            )
        
        # Build ContextualScene
        return cls(
            scene_id=data["scene_id"],
            scene_number=data["scene_number"],
            start_timestamp=data["start_timestamp"],
            end_timestamp=data["end_timestamp"],
            duration_seconds=data["duration_seconds"],
            start_frame=data["start_frame"],
            end_frame=data["end_frame"],
            participating_track_ids=data["participating_track_ids"],
            track_summaries=track_summaries,
            total_observations=data["total_observations"],
            dominant_states=data["dominant_states"],
            avg_scene_speed=data["avg_scene_speed"],
            max_scene_speed=data["max_scene_speed"],
            total_movements=data["total_movements"],
            source_anomalies=data.get("source_anomalies", []),
            source_events=data.get("source_events", []),
            source_relationships=data.get("source_relationships", []),
            movement_patterns=data.get("movement_patterns", []),
            spatial_patterns=data.get("spatial_patterns", []),
            temporal_patterns=data.get("temporal_patterns", []),
            scene_type=data.get("scene_type", "normal_activity"),
            anomaly_density=data.get("anomaly_density", 0.0),
            complexity_score=data.get("complexity_score", 0.0),
            evidence=scene_evidence,
            summary=data.get("summary", ""),
            description=data.get("description", ""),
            key_observations=data.get("key_observations", [])
        )
