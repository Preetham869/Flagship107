"""
M9 Prompt Builder

Constructs structured prompts from M8 contextual scenes.
"""

import logging
from typing import List, Dict
from processing.context.schemas import ContextualScene

logger = logging.getLogger(__name__)

# System prompt defining LLM behavior and constraints
SYSTEM_PROMPT = """You are an AI assistant explaining video intelligence analysis results.

Your role:
- Interpret structured behavioral evidence from computer vision systems
- Provide natural language explanations of OBSERVED patterns only
- Distinguish facts from interpretation
- Preserve uncertainty when evidence is limited

STRICT CONSTRAINTS:
- Base explanations ONLY on provided evidence
- Do NOT invent objects, tracks, timestamps, or measurements
- Do NOT claim intent, motivation, emotion, or mental states
- Do NOT claim pursuit, threat, causality, or significance without evidence
- Do NOT compare to "normal" behavior without baseline data
- Use hedging language for interpretations: "may indicate", "consistent with", "suggests"
- If evidence is insufficient, explicitly state uncertainty

Evidence format:
- Measurements are from computer vision (speeds in pixels/second, not mph/kph)
- Patterns are detected algorithmically (e.g., erratic_movement = high direction variance)
- Anomalies are statistical outliers (e.g., unusual_speed = >150px/s threshold)
- All timestamps and track IDs reference the provided scene data

Forbidden language:
- Intent: "intending to", "planning", "trying to", "attempting to", "goal", "purpose"
- Motivation: "wants to", "desires", "motivated by"
- Emotion: "angry", "suspicious", "nervous", "agitated"
- Threat: "threatening", "dangerous", "malicious", "suspicious person"
- Causality: "because", "in order to", "so that" (unless evidence-based)
- Pursuit: "chasing", "following with intent", "stalking"

Acceptable language:
- "exhibited erratic movement (direction variance 352°→15°→324°)"
- "speed increased from 66 px/s to 194 px/s at t=0.75s"
- "movement pattern consistent with rapid direction changes"
- "may indicate navigating obstacles" (hedged interpretation)
- "insufficient evidence to determine" (honest uncertainty)"""


class PromptBuilder:
    """Builds LLM prompts from M8 contextual scenes"""
    
    def build_scene_prompt(self, scene: ContextualScene) -> str:
        """
        Build complete prompt for scene explanation
        
        Args:
            scene: M8 ContextualScene
        
        Returns:
            Formatted prompt string
        """
        
        # Extract valid references for constraints
        valid_track_ids = scene.participating_track_ids
        time_range = (scene.start_timestamp, scene.end_timestamp)
        
        # Build prompt sections
        sections = []
        
        # Header with constraints
        sections.append(self._build_header(valid_track_ids, time_range))
        
        # Scene overview
        sections.append(self._build_scene_overview(scene))
        
        # Observed entities
        sections.append(self._build_track_summaries(scene))
        
        # Detected anomalies
        sections.append(self._build_anomalies_section(scene))
        
        # Detected patterns
        sections.append(self._build_patterns_section(scene))
        
        # M8 baseline analysis
        sections.append(self._build_baseline_section(scene))
        
        # Key observations
        sections.append(self._build_key_observations(scene))
        
        # Response format instructions
        sections.append(self._build_format_instructions())
        
        return "\n\n".join(sections)
    
    def _build_header(self, valid_track_ids: List[str], time_range: tuple) -> str:
        """Build constraint header"""
        return f"""VALID DATA REFERENCES:
- Track IDs in this scene: {', '.join(valid_track_ids)}
- Timestamp range: {time_range[0]:.2f}s to {time_range[1]:.2f}s
- Only reference measurements from the evidence sections below
- Do NOT invent data outside these constraints"""
    
    def _build_scene_overview(self, scene: ContextualScene) -> str:
        """Build scene overview section"""
        entity_types = {}
        for ts in scene.track_summaries:
            class_name = ts.class_name
            entity_types[class_name] = entity_types.get(class_name, 0) + 1
        
        entity_desc = ", ".join([f"{count} {name}(s)" for name, count in entity_types.items()])
        
        return f"""## Scene Overview
- Duration: {scene.duration_seconds:.1f} seconds (frame {scene.start_frame} to {scene.end_frame})
- Entities: {len(scene.track_summaries)} ({entity_desc})
- Scene Type: {scene.scene_type}
- Complexity: {scene.complexity_score:.1f}/10
- Anomaly Density: {scene.anomaly_density:.2f} per second"""
    
    def _build_track_summaries(self, scene: ContextualScene) -> str:
        """Build observed entities section"""
        lines = ["## Observed Entities"]
        
        for ts in scene.track_summaries:
            lines.append(f"\nTrack #{ts.track_id} ({ts.class_name}):")
            lines.append(f"- Observation period: {ts.duration:.2f} seconds ({ts.observation_count} frames)")
            lines.append(f"- Behavior label: {ts.behavior_label}")
            lines.append(f"- Trajectory type: {ts.trajectory_type}")
            lines.append(f"- Average speed: {ts.avg_speed:.2f} px/s")
            lines.append(f"- Maximum speed: {ts.max_speed:.2f} px/s")
            lines.append(f"- Speed variance: {ts.speed_variance:.2f}")
            
            if ts.movement_patterns:
                lines.append(f"- Detected patterns: {', '.join(ts.movement_patterns)}")
                
                # Include pattern evidence if available
                if ts.evidence and hasattr(ts.evidence, 'pattern_evidence'):
                    for pattern_ev in ts.evidence.pattern_evidence:
                        if hasattr(pattern_ev, 'supporting_observations'):
                            lines.append(f"  Evidence for {pattern_ev.pattern_name}:")
                            for obs in pattern_ev.supporting_observations[:3]:  # Show first 3
                                if hasattr(obs, 'timestamp') and hasattr(obs, 'measurement'):
                                    meas = obs.measurement or {}
                                    meas_str = ", ".join([f"{k}={v:.2f}" for k, v in meas.items()])
                                    lines.append(f"    t={obs.timestamp:.2f}s: {meas_str}")
            
            if ts.anomaly_count > 0:
                lines.append(f"- Anomalies: {ts.anomaly_count} ({', '.join(ts.anomaly_types)})")
            
            if ts.interaction_count > 0:
                lines.append(f"- Interactions: {ts.interaction_count} with tracks {', '.join(ts.interacted_with_tracks)}")
        
        return "\n".join(lines)
    
    def _build_anomalies_section(self, scene: ContextualScene) -> str:
        """Build anomalies section"""
        lines = ["## Detected Anomalies"]
        
        if not scene.source_anomalies:
            lines.append("- No anomalies detected in this scene")
        else:
            lines.append(f"- Total anomalies: {len(scene.source_anomalies)}")
            lines.append(f"- Anomaly density: {scene.anomaly_density:.2f} per second")
            
            # Aggregate anomaly types from tracks
            all_anomaly_types = []
            for ts in scene.track_summaries:
                all_anomaly_types.extend(ts.anomaly_types)
            
            if all_anomaly_types:
                anomaly_counts = {}
                for atype in all_anomaly_types:
                    anomaly_counts[atype] = anomaly_counts.get(atype, 0) + 1
                
                for atype, count in anomaly_counts.items():
                    lines.append(f"- {count}× {atype}")
        
        return "\n".join(lines)
    
    def _build_patterns_section(self, scene: ContextualScene) -> str:
        """Build patterns section"""
        lines = ["## Detected Patterns"]
        
        all_patterns = (
            scene.movement_patterns +
            scene.spatial_patterns +
            scene.temporal_patterns
        )
        
        # Also collect track-level patterns
        track_patterns = []
        for ts in scene.track_summaries:
            for pattern in ts.movement_patterns:
                if pattern not in track_patterns:
                    track_patterns.append(pattern)
        
        all_patterns = list(set(all_patterns + track_patterns))
        
        if not all_patterns:
            lines.append("- No specific patterns detected")
        else:
            lines.append("Track-level patterns:")
            for ts in scene.track_summaries:
                if ts.movement_patterns:
                    lines.append(f"- Track #{ts.track_id}: {', '.join(ts.movement_patterns)}")
        
        return "\n".join(lines)
    
    def _build_baseline_section(self, scene: ContextualScene) -> str:
        """Build M8 baseline section"""
        lines = ["## Baseline Analysis (Computer Generated)"]
        lines.append(f"Summary: {scene.summary}")
        lines.append(f"\nDescription: {scene.description}")
        return "\n".join(lines)
    
    def _build_key_observations(self, scene: ContextualScene) -> str:
        """Build key observations section"""
        lines = ["## Key Observations"]
        
        if scene.key_observations:
            for obs in scene.key_observations:
                lines.append(f"- {obs}")
        else:
            lines.append("- (See description above)")
        
        return "\n".join(lines)
    
    def _build_format_instructions(self) -> str:
        """Build response format instructions"""
        return """---

Provide a natural language explanation in this format:

**Overview:**
[1-2 sentences summarizing what was OBSERVED - no speculation]

**Entity Behaviors:**
[For each entity, explain observed behavior with specific measurements]

**Notable Patterns:**
[Explain detected patterns using evidence - what do they mean technically?]

**Anomalies:**
[Explain anomalies using thresholds and measurements]

**Context:**
[OPTIONAL: Hedged interpretations only if supported by evidence. Use "may indicate", "consistent with", "suggests"]

Use clear, professional language. Cite specific track IDs, timestamps, and measurements."""
