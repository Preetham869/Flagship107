"""
M9 Explanation Generator

Main orchestrator for LLM-based scene explanations.
"""

import logging
import time
import asyncio
from typing import Optional
from datetime import datetime

from processing.context.schemas import ContextualScene
from .config import LLMConfig
from .client import (
    create_llm_client,
    LLMClient,
    LLMClientError,
    ProviderUnavailableError,
    ModelNotFoundError,
    GenerationTimeoutError
)
from .prompts import PromptBuilder, SYSTEM_PROMPT
from .constraints import HallucinationConstraints
from .schemas import SceneExplanation, TrackExplanation

logger = logging.getLogger(__name__)


class ExplanationGenerator:
    """
    Generates natural language explanations for M8 contextual scenes
    
    Uses local LLM (Ollama/Qwen3:8b) with hallucination prevention.
    Falls back to deterministic M8 narratives if LLM unavailable.
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize explanation generator
        
        Args:
            config: LLM configuration (uses defaults if None)
        """
        self.config = config or LLMConfig()
        self.client = create_llm_client(self.config)
        self.prompt_builder = PromptBuilder()
        self.constraints = HallucinationConstraints()
        
        logger.info(f"ExplanationGenerator initialized with {self.config.provider}:{self.config.model_name}")
    
    async def explain_scene(self, scene: ContextualScene) -> SceneExplanation:
        """
        Generate explanation for a scene
        
        Args:
            scene: M8 ContextualScene to explain
        
        Returns:
            SceneExplanation (may be fallback if LLM fails)
        """
        start_time = time.time()
        
        try:
            # 1. Check provider availability
            logger.debug(f"Checking {self.config.provider} health...")
            if not await self.client.check_health():
                raise ProviderUnavailableError(
                    f"{self.config.provider} not responding at {self.config.base_url}"
                )
            
            # 2. Build prompt from M8 evidence
            logger.debug(f"Building prompt for scene {scene.scene_id}...")
            prompt = self.prompt_builder.build_scene_prompt(scene)
            
            # 3. Generate with timeout and retries
            response_text = None
            last_error = None
            
            for attempt in range(self.config.max_retries + 1):
                try:
                    logger.debug(
                        f"Generating explanation (attempt {attempt + 1}/{self.config.max_retries + 1})..."
                    )
                    
                    response = await asyncio.wait_for(
                        self.client.generate(prompt, system=SYSTEM_PROMPT),
                        timeout=self.config.timeout_seconds
                    )
                    
                    response_text = response["response"]
                    model_id = response.get("model", self.config.model_name)
                    break
                    
                except asyncio.TimeoutError as e:
                    last_error = GenerationTimeoutError(
                        f"Generation exceeded {self.config.timeout_seconds}s"
                    )
                    if attempt < self.config.max_retries:
                        logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                        await asyncio.sleep(self.config.retry_delay_seconds)
                    else:
                        raise last_error from e
                
                except LLMClientError as e:
                    # Don't retry on client errors (model not found, etc.)
                    raise
            
            if response_text is None:
                raise last_error or LLMClientError("No response received")
            
            # 4. Validate against hallucinations
            if self.config.enable_hallucination_checks:
                logger.debug("Checking for hallucinations...")
                violations = self.constraints.check_hallucinations(response_text, scene)
                
                if violations:
                    logger.warning(
                        f"Hallucination detected in scene {scene.scene_id}: "
                        f"{len(violations)} violations"
                    )
                    for violation in violations[:3]:  # Log first 3
                        logger.warning(f"  - {violation}")
                    
                    # Use fallback instead of hallucinated response
                    raise LLMClientError(f"Hallucination detected: {violations[0]}")
            
            # 5. Calculate evidence coverage
            evidence_coverage = self.constraints.calculate_evidence_coverage(
                response_text, scene
            )
            
            if evidence_coverage < self.config.min_evidence_coverage:
                logger.warning(
                    f"Low evidence coverage: {evidence_coverage:.2%} "
                    f"(min: {self.config.min_evidence_coverage:.2%})"
                )
            
            # 6. Parse response into structured explanation
            explanation = self._parse_explanation(response_text, scene, model_id)
            explanation.generation_time_ms = (time.time() - start_time) * 1000
            explanation.evidence_coverage = evidence_coverage
            explanation.hallucination_checks_passed = True
            
            # Determine confidence level based on evidence coverage
            if evidence_coverage >= 0.8:
                explanation.confidence_level = "high"
            elif evidence_coverage >= 0.5:
                explanation.confidence_level = "medium"
            else:
                explanation.confidence_level = "low"
            
            logger.info(
                f"Generated explanation for scene {scene.scene_id} "
                f"({explanation.generation_time_ms:.0f}ms, "
                f"coverage: {evidence_coverage:.2%})"
            )
            
            return explanation
        
        except Exception as e:
            # Log error and fall back to M8 deterministic narrative
            logger.warning(f"M9 explanation failed for scene {scene.scene_id}: {e}")
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if self.config.use_fallback_on_error:
                return self._create_fallback_explanation(scene, str(e), elapsed_ms)
            else:
                raise
    
    def _parse_explanation(
        self,
        response_text: str,
        scene: ContextualScene,
        model_id: str
    ) -> SceneExplanation:
        """
        Parse LLM response into structured explanation
        
        Args:
            response_text: Raw LLM response
            scene: Source scene
            model_id: Model identifier
        
        Returns:
            Structured SceneExplanation
        """
        # Simple parsing - extract sections by headers
        sections = self._split_into_sections(response_text)
        
        # Build track explanations
        entity_behaviors = []
        for track_summary in scene.track_summaries:
            # Extract mentions of this track from response
            track_mentions = self._extract_track_mentions(
                response_text, track_summary.track_id
            )
            
            entity_behaviors.append(
                TrackExplanation(
                    track_id=track_summary.track_id,
                    behavior_summary=track_mentions or f"Track #{track_summary.track_id} ({track_summary.behavior_label})",
                    pattern_explanations={
                        p: sections.get("Notable Patterns", "") 
                        for p in track_summary.movement_patterns
                    },
                    anomaly_explanations=track_summary.anomaly_types,
                    context=sections.get("Context"),
                    confidence_notes=None,
                    cited_evidence=[],  # TODO: Extract citations if formatted
                )
            )
        
        # Build pattern significance
        pattern_significance = {}
        all_patterns = []
        for ts in scene.track_summaries:
            all_patterns.extend(ts.movement_patterns)
        
        for pattern in set(all_patterns):
            if pattern in response_text or pattern.replace('_', ' ') in response_text:
                pattern_significance[pattern] = sections.get("Notable Patterns", "")
        
        return SceneExplanation(
            scene_id=scene.scene_id,
            overview=sections.get("Overview", scene.summary),
            entity_behaviors=entity_behaviors,
            pattern_significance=pattern_significance,
            anomaly_significance=[sections.get("Anomalies", "")],
            contextual_interpretation=sections.get("Context"),
            generated_at=datetime.utcnow().isoformat(),
            model_name=self.config.model_name,
            model_version=model_id,
            generation_time_ms=0.0,  # Will be set by caller
            hallucination_checks_passed=True,
            evidence_coverage=0.0,  # Will be set by caller
            confidence_level="medium",  # Will be set by caller
            is_fallback=False,
            fallback_reason=None,
        )
    
    def _split_into_sections(self, text: str) -> dict:
        """Split response into sections by headers"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in text.split('\n'):
            # Check if line is a header (starts with **)
            if line.strip().startswith('**') and line.strip().endswith('**'):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = line.strip().strip('*').strip(':').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _extract_track_mentions(self, text: str, track_id: str) -> Optional[str]:
        """Extract sentences mentioning a specific track"""
        import re
        
        # Find sentences containing this track ID
        sentences = re.split(r'[.!?]+', text)
        mentions = []
        
        for sentence in sentences:
            if f"Track #{track_id}" in sentence or f"Track {track_id}" in sentence:
                mentions.append(sentence.strip())
        
        return ' '.join(mentions) if mentions else None
    
    def _create_fallback_explanation(
        self,
        scene: ContextualScene,
        error_reason: str,
        elapsed_ms: float
    ) -> SceneExplanation:
        """
        Create deterministic fallback using M8 narratives
        
        No LLM involved - pure M8 template expansion
        
        Args:
            scene: M8 scene
            error_reason: Why fallback was used
            elapsed_ms: Time elapsed before fallback
        
        Returns:
            Deterministic SceneExplanation
        """
        logger.info(f"Using deterministic fallback for scene {scene.scene_id}")
        
        # Use M8 baseline narratives
        overview = scene.summary
        
        # Build track explanations from M8 data
        entity_behaviors = []
        for track_summary in scene.track_summaries:
            # Deterministic pattern explanations
            pattern_explanations = {
                "erratic_movement": "Direction variance exceeds 80° over 2+ seconds",
                "rapid_movement": "Speed sustained above 150 px/s for 3+ seconds",
                "stationary_extended": "Movement less than 20 pixels over 10+ seconds",
                "linear_traversal": "Direction variance less than 30° with >50px travel",
            }
            
            entity_behaviors.append(
                TrackExplanation(
                    track_id=track_summary.track_id,
                    behavior_summary=track_summary.summary,
                    pattern_explanations={
                        p: pattern_explanations.get(p, f"Pattern: {p}")
                        for p in track_summary.movement_patterns
                    },
                    anomaly_explanations=[
                        f"{atype} anomaly"
                        for atype in track_summary.anomaly_types
                    ],
                    context=None,  # No interpretation without LLM
                    confidence_notes="Deterministic analysis only (LLM unavailable)",
                    cited_evidence=[],
                )
            )
        
        # Pattern significance (deterministic definitions)
        pattern_significance = {
            p: "Direction variance exceeds 80° over 2+ seconds"
            if p == "erratic_movement"
            else f"Detected pattern: {p}"
            for p in scene.movement_patterns + scene.spatial_patterns
        }
        
        return SceneExplanation(
            scene_id=scene.scene_id,
            overview=overview,
            entity_behaviors=entity_behaviors,
            pattern_significance=pattern_significance,
            anomaly_significance=[
                f"{len(scene.source_anomalies)} anomalies detected"
            ] if scene.source_anomalies else [],
            contextual_interpretation=None,  # No interpretation without LLM
            generated_at=datetime.utcnow().isoformat(),
            model_name="fallback",
            model_version="deterministic_m8_v1",
            generation_time_ms=elapsed_ms,
            hallucination_checks_passed=True,  # Deterministic = no hallucinations
            evidence_coverage=1.0,  # 100% (using M8 directly)
            confidence_level="high",  # Deterministic
            is_fallback=True,
            fallback_reason=error_reason,
        )
