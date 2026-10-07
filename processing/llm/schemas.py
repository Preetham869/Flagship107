"""
M9 Data Schemas

Output schemas for LLM-generated explanations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class TrackExplanation:
    """Natural language explanation for one track's behavior"""
    
    track_id: str
    behavior_summary: str  # 1-2 sentences describing observed behavior
    pattern_explanations: Dict[str, str] = field(default_factory=dict)  # pattern_name → explanation
    anomaly_explanations: List[str] = field(default_factory=list)  # List of anomaly interpretations
    context: Optional[str] = None  # Broader context (with hedging)
    confidence_notes: Optional[str] = None  # Uncertainty statements if applicable
    cited_evidence: List[str] = field(default_factory=list)  # References to M8 evidence
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "track_id": self.track_id,
            "behavior_summary": self.behavior_summary,
            "pattern_explanations": self.pattern_explanations,
            "anomaly_explanations": self.anomaly_explanations,
            "context": self.context,
            "confidence_notes": self.confidence_notes,
            "cited_evidence": self.cited_evidence,
        }


@dataclass
class SceneExplanation:
    """Complete M9 explanation for a scene"""
    
    scene_id: str
    
    # LLM-generated content
    overview: str  # 1-2 sentence summary
    entity_behaviors: List[TrackExplanation] = field(default_factory=list)
    pattern_significance: Dict[str, str] = field(default_factory=dict)  # pattern → why it matters
    anomaly_significance: List[str] = field(default_factory=list)  # Why anomalies are noteworthy
    contextual_interpretation: Optional[str] = None  # Hedged interpretations
    
    # Metadata
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    model_name: str = "unknown"
    model_version: str = "unknown"
    generation_time_ms: float = 0.0
    
    # Quality indicators
    hallucination_checks_passed: bool = True
    evidence_coverage: float = 0.0  # % of M8 evidence cited
    confidence_level: str = "medium"  # "high", "medium", "low"
    
    # Fallback indicator
    is_fallback: bool = False  # True if using deterministic fallback
    fallback_reason: Optional[str] = None  # Why LLM was not used
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "scene_id": self.scene_id,
            "overview": self.overview,
            "entity_behaviors": [eb.to_dict() for eb in self.entity_behaviors],
            "pattern_significance": self.pattern_significance,
            "anomaly_significance": self.anomaly_significance,
            "contextual_interpretation": self.contextual_interpretation,
            "generated_at": self.generated_at,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "generation_time_ms": round(self.generation_time_ms, 2),
            "hallucination_checks_passed": self.hallucination_checks_passed,
            "evidence_coverage": round(self.evidence_coverage, 2),
            "confidence_level": self.confidence_level,
            "is_fallback": self.is_fallback,
            "fallback_reason": self.fallback_reason,
        }
