"""
M9 Hallucination Constraints

Validates LLM outputs against M8 evidence to prevent hallucinations.
"""

import re
import logging
from typing import List, Set, Dict, Any
from processing.context.schemas import ContextualScene

logger = logging.getLogger(__name__)


class HallucinationConstraints:
    """Validates LLM outputs against M8 evidence"""
    
    # Forbidden phrases indicating unobservable states
    FORBIDDEN_PHRASES = [
        # Intent
        "intend", "intending", "plan", "planning", "want", "wanting",
        "trying to", "attempting to", "goal", "purpose", "motivated",
        
        # Emotion
        "angry", "suspicious", "nervous", "agitated", "scared", "afraid",
        "confident", "hesitant", "aggressive",
        
        # Threat assessment
        "threatening", "dangerous", "malicious", "suspicious person",
        "criminal", "perpetrator", "assailant",
        
        # Pursuit
        "chasing", "pursuing", "stalking", "following with intent",
        "hunting",
    ]
    
    def check_hallucinations(
        self,
        explanation_text: str,
        scene: ContextualScene
    ) -> List[str]:
        """
        Check for hallucinated content
        
        Args:
            explanation_text: Generated explanation text
            scene: Source M8 scene
        
        Returns:
            List of violation descriptions (empty if valid)
        """
        violations = []
        
        # Extract valid references from M8
        valid_track_ids = set(scene.participating_track_ids)
        time_range = (scene.start_timestamp, scene.end_timestamp)
        
        # Check 1: Track ID references
        mentioned_tracks = self._extract_track_ids(explanation_text)
        for track_id in mentioned_tracks:
            if track_id not in valid_track_ids:
                violations.append(
                    f"Mentioned non-existent track: Track #{track_id} "
                    f"(valid: {', '.join(valid_track_ids)})"
                )
        
        # Check 2: Timestamp references
        mentioned_times = self._extract_timestamps(explanation_text)
        for timestamp in mentioned_times:
            if not (time_range[0] - 0.1 <= timestamp <= time_range[1] + 0.1):  # Small tolerance
                violations.append(
                    f"Mentioned out-of-range timestamp: {timestamp:.2f}s "
                    f"(valid: {time_range[0]:.2f}s - {time_range[1]:.2f}s)"
                )
        
        # Check 3: Forbidden language (intent/motivation/emotion)
        for phrase in self.FORBIDDEN_PHRASES:
            # Case-insensitive search with word boundaries
            pattern = r'\b' + re.escape(phrase) + r'\b'
            if re.search(pattern, explanation_text, re.IGNORECASE):
                violations.append(
                    f"Used forbidden phrase indicating unobservable state: '{phrase}'"
                )
        
        # Check 4: Causality without evidence
        # Look for causal claims without hedging
        causal_patterns = [
            r'\bbecause\s+\w+\s+(wanted|intended|planned)',
            r'\bin order to\s+\w+',
            r'\bso that\s+\w+\s+(could|would)',
        ]
        for pattern in causal_patterns:
            if re.search(pattern, explanation_text, re.IGNORECASE):
                violations.append(
                    f"Made causal claim about unobservable intent"
                )
        
        return violations
    
    def _extract_track_ids(self, text: str) -> Set[str]:
        """
        Extract track ID mentions like 'Track #3' or 'Track 3'
        
        Args:
            text: Text to search
        
        Returns:
            Set of track IDs (as strings)
        """
        pattern = r'[Tt]rack\s*#?(\d+)'
        matches = re.findall(pattern, text)
        return set(matches)
    
    def _extract_timestamps(self, text: str) -> List[float]:
        """
        Extract timestamp mentions like '2.5s', 't=3.1s', or 'at 1.2 seconds'
        
        Args:
            text: Text to search
        
        Returns:
            List of timestamps (as floats)
        """
        # Pattern: t=X.Xs, X.Xs, X.X seconds
        patterns = [
            r't\s*=\s*(\d+\.?\d*)\s*s',
            r'(\d+\.?\d*)\s*s(?:econds)?',
            r'at\s+(\d+\.?\d*)\s*s',
        ]
        
        timestamps = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            timestamps.extend([float(m) for m in matches if m])
        
        return timestamps
    
    def calculate_evidence_coverage(
        self,
        explanation_text: str,
        scene: ContextualScene
    ) -> float:
        """
        Calculate what % of M8 evidence was cited
        
        Higher coverage indicates explanation is grounded in evidence
        
        Args:
            explanation_text: Generated explanation
            scene: Source M8 scene
        
        Returns:
            Coverage ratio (0.0 to 1.0)
        """
        total_evidence_items = 0
        cited_evidence_items = 0
        
        # Count M8 evidence items
        for track_summary in scene.track_summaries:
            # Track itself
            total_evidence_items += 1
            
            # Patterns
            total_evidence_items += len(track_summary.movement_patterns)
            
            # Anomalies
            total_evidence_items += track_summary.anomaly_count
        
        # Count citations in explanation
        for track_summary in scene.track_summaries:
            # Check if track is mentioned
            if f"Track #{track_summary.track_id}" in explanation_text or \
               f"Track {track_summary.track_id}" in explanation_text:
                cited_evidence_items += 1
            
            # Check if patterns are mentioned
            for pattern in track_summary.movement_patterns:
                if pattern in explanation_text or \
                   pattern.replace('_', ' ') in explanation_text.lower():
                    cited_evidence_items += 1
            
            # Check if anomalies are mentioned
            for anomaly_type in track_summary.anomaly_types:
                if anomaly_type in explanation_text or \
                   anomaly_type.replace('_', ' ') in explanation_text.lower():
                    cited_evidence_items += 1
        
        if total_evidence_items == 0:
            return 1.0  # No evidence to cite (vacuously true)
        
        return min(1.0, cited_evidence_items / total_evidence_items)
