"""
M9 LLM Explanation Tests

Tests for local LLM explanation generation with mocked Ollama responses.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from processing.llm.config import LLMConfig
from processing.llm.client import (
    OllamaClient,
    ProviderUnavailableError,
    ModelNotFoundError,
    GenerationTimeoutError
)
from processing.llm.explanations import ExplanationGenerator
from processing.llm.constraints import HallucinationConstraints
from processing.llm.prompts import PromptBuilder
from processing.context.schemas import (
    ContextualScene,
    TrackSummary,
    TrackEvidence,
    PatternEvidence,
    SourceReference
)


# ===== Fixtures =====

@pytest.fixture
def mock_config():
    """Create test LLM configuration"""
    return LLMConfig(
        provider="ollama",
        base_url="http://localhost:11434",
        model_name="qwen3:8b",
        temperature=0.3,
        timeout_seconds=30.0,
        use_fallback_on_error=True
    )


@pytest.fixture
def mock_ollama_response():
    """Mock successful Ollama API response"""
    return {
        "model": "qwen3:8b",
        "created_at": "2024-01-01T00:00:00Z",
        "response": """**Overview:**
Three pedestrians were observed over a 3.7-second period exhibiting varied movement patterns.

**Entity Behaviors:**
Track #3 exhibited erratic movement with direction changes from 352.64° to 15.45° to 323.95°, indicating rapid directional adjustments. Average speed was 66.16 px/s with peaks reaching 194.41 px/s at t=0.75s.

Track #1 moved steadily at an average of 49.95 px/s with maximum speed of 94.32 px/s, showing consistent slow movement throughout the observation period.

Track #2 demonstrated average movement at 66.60 px/s with occasional speed variations up to 228.54 px/s.

**Notable Patterns:**
The erratic_movement pattern detected for Track #3 indicates high directional variance exceeding 80° over the observation window, consistent with rapid path adjustments.

**Anomalies:**
Two unusual_speed anomalies were detected where speeds exceeded the 150 px/s threshold, and one sudden_speed_change anomaly showing rapid acceleration.

**Context:**
The observed movement patterns may indicate pedestrians navigating through a constrained or crowded space, requiring frequent direction adjustments.""",
        "done": True,
        "total_duration": 1247300000
    }


@pytest.fixture
def mock_scene():
    """Create mock M8 scene for testing"""
    track_evidence = TrackEvidence(
        source_behaviors=["behavior_0", "behavior_1"],
        source_anomalies=[],
        source_relationships=[],
        pattern_evidence=[
            PatternEvidence(
                pattern_name="erratic_movement",
                confidence=0.5,
                supporting_observations=[
                    SourceReference(
                        source_module="M3",
                        source_type="behavior",
                        source_id="behavior_0",
                        timestamp=0.75,
                        track_ids=["3"],
                        measurement={"direction": 352.64, "speed": 106.35}
                    ),
                    SourceReference(
                        source_module="M3",
                        source_type="behavior",
                        source_id="behavior_1",
                        timestamp=1.50,
                        track_ids=["3"],
                        measurement={"direction": 15.45, "speed": 95.13}
                    )
                ],
                measurements={"variance": 85.3},
                description="High direction variance"
            )
        ]
    )
    
    return ContextualScene(
        scene_id="test_scene_001",
        scene_number=1,
        start_timestamp=0.0,
        end_timestamp=3.71,
        duration_seconds=3.71,
        start_frame=0,
        end_frame=89,
        participating_track_ids=["1", "2", "3"],
        track_summaries=[
            TrackSummary(
                track_id="3",
                class_name="person",
                first_seen=0.0,
                last_seen=3.71,
                duration=3.71,
                observation_count=90,
                entry_position=(1524.52, 1995.69),
                exit_position=(1675.95, 2025.11),
                path_length=310.15,
                avg_displacement=3.48,
                state_distribution={"moving": 0.88, "fast-moving": 0.12},
                dominant_state="moving",
                avg_speed=66.16,
                max_speed=194.41,
                speed_variance=1458.93,
                trajectory_type="erratic",
                movement_patterns=["erratic_movement"],
                anomaly_count=0,
                anomaly_types=[],
                anomaly_severity_max="none",
                interaction_count=0,
                interacted_with_tracks=[],
                interaction_types=[],
                behavior_label="erratic_mover",
                summary="Track #3 (erratic_mover) observed for 3.7s",
                evidence=track_evidence
            ),
            TrackSummary(
                track_id="1",
                class_name="person",
                first_seen=0.0,
                last_seen=3.71,
                duration=3.71,
                observation_count=90,
                entry_position=(900.0, 2000.0),
                exit_position=(950.0, 2050.0),
                path_length=185.0,
                avg_displacement=2.1,
                state_distribution={"moving": 1.0},
                dominant_state="moving",
                avg_speed=49.95,
                max_speed=94.32,
                speed_variance=120.5,
                trajectory_type="linear",
                movement_patterns=[],
                anomaly_count=0,
                anomaly_types=[],
                anomaly_severity_max="none",
                interaction_count=0,
                interacted_with_tracks=[],
                interaction_types=[],
                behavior_label="slow_mover",
                summary="Track #1 (slow_mover) observed for 3.7s",
            )
        ],
        total_observations=180,
        dominant_states={"moving": 170, "fast-moving": 10},
        avg_scene_speed=58.0,
        max_scene_speed=228.54,
        total_movements=180,
        source_anomalies=["anom_001", "anom_002"],
        source_events=["evt_001"],
        source_relationships=[],
        movement_patterns=[],
        spatial_patterns=[],
        temporal_patterns=[],
        scene_type="anomalous_activity",
        anomaly_density=0.54,
        complexity_score=3.0,
        summary="3 entities observed for 3.7s with 2 anomalies",
        description="Scene with varied movement patterns",
        key_observations=[
            "Track #3: erratic_mover (66.2px/s avg)",
            "Track #1: slow_mover (50.0px/s avg)"
        ]
    )


# ===== Core Functionality Tests =====

@pytest.mark.asyncio
async def test_explain_scene_success(mock_scene, mock_ollama_response, mock_config):
    """Test successful scene explanation generation"""
    with patch.object(OllamaClient, 'generate', new_callable=AsyncMock) as mock_generate, \
         patch.object(OllamaClient, 'check_health', new_callable=AsyncMock) as mock_health:
        
        mock_health.return_value = True
        mock_generate.return_value = mock_ollama_response
        
        generator = ExplanationGenerator(mock_config)
        explanation = await generator.explain_scene(mock_scene)
        
        assert explanation.scene_id == "test_scene_001"
        assert not explanation.is_fallback
        assert explanation.model_name == "qwen3:8b"
        # Check that explanation has content (overview may not mention specific patterns)
        assert len(explanation.overview) > 0
        assert len(explanation.entity_behaviors) > 0
        assert explanation.hallucination_checks_passed
        # Verify pattern is mentioned somewhere in the explanation
        explanation_text = str(explanation.to_dict())
        assert "erratic" in explanation_text.lower()


@pytest.mark.asyncio
async def test_ollama_unavailable_fallback(mock_scene, mock_config):
    """Test fallback when Ollama is unavailable"""
    with patch.object(OllamaClient, 'check_health', new_callable=AsyncMock) as mock_health:
        mock_health.return_value = False
        
        generator = ExplanationGenerator(mock_config)
        explanation = await generator.explain_scene(mock_scene)
        
        assert explanation.is_fallback
        assert explanation.fallback_reason is not None
        assert "unavailable" in explanation.fallback_reason.lower() or "not responding" in explanation.fallback_reason.lower()
        assert explanation.model_name == "fallback"
        assert explanation.evidence_coverage == 1.0  # Deterministic uses all M8 evidence


@pytest.mark.asyncio
async def test_generation_timeout(mock_scene, mock_config):
    """Test timeout handling"""
    with patch.object(OllamaClient, 'check_health', new_callable=AsyncMock) as mock_health, \
         patch.object(OllamaClient, 'generate', new_callable=AsyncMock) as mock_generate:
        
        mock_health.return_value = True
        mock_generate.side_effect = asyncio.TimeoutError()
        
        generator = ExplanationGenerator(mock_config)
        explanation = await generator.explain_scene(mock_scene)
        
        assert explanation.is_fallback
        assert "timeout" in explanation.fallback_reason.lower() or "exceeded" in explanation.fallback_reason.lower()


@pytest.mark.asyncio
async def test_generation_with_retries(mock_scene, mock_ollama_response, mock_config):
    """Test retry logic on timeout"""
    with patch.object(OllamaClient, 'check_health', new_callable=AsyncMock) as mock_health, \
         patch.object(OllamaClient, 'generate', new_callable=AsyncMock) as mock_generate:
        
        mock_health.return_value = True
        # Fail twice, succeed on third attempt
        mock_generate.side_effect = [
            asyncio.TimeoutError(),
            asyncio.TimeoutError(),
            mock_ollama_response
        ]
        
        mock_config.max_retries = 2
        mock_config.retry_delay_seconds = 0.01  # Fast for testing
        
        generator = ExplanationGenerator(mock_config)
        explanation = await generator.explain_scene(mock_scene)
        
        assert not explanation.is_fallback
        assert mock_generate.call_count == 3


# ===== Hallucination Detection Tests =====

@pytest.mark.asyncio
async def test_hallucination_invalid_track_id(mock_scene, mock_config):
    """Test detection of hallucinated track IDs"""
    hallucinated_response = {
        "model": "qwen3:8b",
        "response": "Track #99 exhibited unusual behavior, while Track #100 moved normally.",
        "done": True,
        "total_duration": 1000000000
    }
    
    with patch.object(OllamaClient, 'check_health', new_callable=AsyncMock) as mock_health, \
         patch.object(OllamaClient, 'generate', new_callable=AsyncMock) as mock_generate:
        
        mock_health.return_value = True
        mock_generate.return_value = hallucinated_response
        
        generator = ExplanationGenerator(mock_config)
        explanation = await generator.explain_scene(mock_scene)
        
        # Should fallback due to hallucination
        assert explanation.is_fallback
        assert "hallucination" in explanation.fallback_reason.lower()


@pytest.mark.asyncio
async def test_hallucination_invalid_timestamp(mock_scene, mock_config):
    """Test detection of out-of-range timestamps"""
    hallucinated_response = {
        "model": "qwen3:8b",
        "response": "At t=10.5s, Track #3 exhibited erratic movement.",
        "done": True,
        "total_duration": 1000000000
    }
    
    with patch.object(OllamaClient, 'check_health', new_callable=AsyncMock) as mock_health, \
         patch.object(OllamaClient, 'generate', new_callable=AsyncMock) as mock_generate:
        
        mock_health.return_value = True
        mock_generate.return_value = hallucinated_response
        
        generator = ExplanationGenerator(mock_config)
        explanation = await generator.explain_scene(mock_scene)
        
        assert explanation.is_fallback
        assert "hallucination" in explanation.fallback_reason.lower()


@pytest.mark.asyncio
async def test_hallucination_intent_language(mock_scene, mock_config):
    """Test detection of forbidden intent language"""
    hallucinated_response = {
        "model": "qwen3:8b",
        "response": "Track #3 intended to move erratically and was planning to approach Track #1.",
        "done": True,
        "total_duration": 1000000000
    }
    
    with patch.object(OllamaClient, 'check_health', new_callable=AsyncMock) as mock_health, \
         patch.object(OllamaClient, 'generate', new_callable=AsyncMock) as mock_generate:
        
        mock_health.return_value = True
        mock_generate.return_value = hallucinated_response
        
        generator = ExplanationGenerator(mock_config)
        explanation = await generator.explain_scene(mock_scene)
        
        assert explanation.is_fallback
        assert "hallucination" in explanation.fallback_reason.lower() or "forbidden" in explanation.fallback_reason.lower()


@pytest.mark.asyncio
async def test_hallucination_emotion_language(mock_scene, mock_config):
    """Test detection of forbidden emotion language"""
    hallucinated_response = {
        "model": "qwen3:8b",
        "response": "Track #3 appeared agitated and nervous while Track #1 seemed suspicious.",
        "done": True,
        "total_duration": 1000000000
    }
    
    with patch.object(OllamaClient, 'check_health', new_callable=AsyncMock) as mock_health, \
         patch.object(OllamaClient, 'generate', new_callable=AsyncMock) as mock_generate:
        
        mock_health.return_value = True
        mock_generate.return_value = hallucinated_response
        
        generator = ExplanationGenerator(mock_config)
        explanation = await generator.explain_scene(mock_scene)
        
        assert explanation.is_fallback


@pytest.mark.asyncio
async def test_hallucination_threat_language(mock_scene, mock_config):
    """Test detection of forbidden threat language"""
    hallucinated_response = {
        "model": "qwen3:8b",
        "response": "The suspicious person in Track #3 was chasing Track #1 in a threatening manner.",
        "done": True,
        "total_duration": 1000000000
    }
    
    with patch.object(OllamaClient, 'check_health', new_callable=AsyncMock) as mock_health, \
         patch.object(OllamaClient, 'generate', new_callable=AsyncMock) as mock_generate:
        
        mock_health.return_value = True
        mock_generate.return_value = hallucinated_response
        
        generator = ExplanationGenerator(mock_config)
        explanation = await generator.explain_scene(mock_scene)
        
        assert explanation.is_fallback


# ===== Prompt Building Tests =====

def test_prompt_builder_includes_all_evidence(mock_scene):
    """Test that prompt includes all M8 evidence"""
    builder = PromptBuilder()
    prompt = builder.build_scene_prompt(mock_scene)
    
    # Should include track IDs
    assert "Track #3" in prompt or "track 3" in prompt.lower()
    assert "Track #1" in prompt or "track 1" in prompt.lower()
    
    # Should include measurements
    assert "66.16" in prompt or "66.2" in prompt  # avg speed
    assert "194.41" in prompt or "194.4" in prompt  # max speed
    
    # Should include patterns
    assert "erratic_movement" in prompt or "erratic movement" in prompt
    
    # Should include time bounds
    assert "3.71" in prompt or "3.7" in prompt


def test_prompt_builder_constraints_track_ids(mock_scene):
    """Test that prompt explicitly lists valid track IDs"""
    builder = PromptBuilder()
    prompt = builder.build_scene_prompt(mock_scene)
    
    # Should have constraint section with valid track IDs
    assert "VALID DATA REFERENCES" in prompt or "Track IDs" in prompt
    assert "1" in prompt and "2" in prompt and "3" in prompt


def test_prompt_builder_forbidden_language_warning(mock_scene):
    """Test that prompt includes forbidden language warnings"""
    builder = PromptBuilder()
    prompt = builder.build_scene_prompt(mock_scene)
    
    assert "Do NOT" in prompt or "FORBIDDEN" in prompt or "CONSTRAINTS" in prompt


# ===== Evidence Coverage Tests =====

def test_evidence_coverage_calculation(mock_scene):
    """Test evidence coverage scoring"""
    constraints = HallucinationConstraints()
    
    # Good explanation citing evidence
    good_explanation = """
    Track #3 exhibited erratic_movement pattern with speeds reaching 194.41 px/s.
    Track #1 moved at 49.95 px/s showing slow_mover behavior.
    """
    
    coverage = constraints.calculate_evidence_coverage(good_explanation, mock_scene)
    assert coverage > 0.5  # Should cite >50% of evidence
    
    # Poor explanation not citing evidence
    poor_explanation = "Some entities moved around in the scene."
    coverage_poor = constraints.calculate_evidence_coverage(poor_explanation, mock_scene)
    assert coverage_poor < coverage  # Should be lower


def test_evidence_coverage_track_mentions(mock_scene):
    """Test that track mentions are counted"""
    constraints = HallucinationConstraints()
    
    explanation = "Track #3 moved erratically. Track #1 moved slowly."
    coverage = constraints.calculate_evidence_coverage(explanation, mock_scene)
    
    assert coverage > 0.0  # Both tracks mentioned


# ===== Constraints Unit Tests =====

def test_extract_track_ids():
    """Test track ID extraction"""
    constraints = HallucinationConstraints()
    
    text = "Track #3 and Track 1 moved while track #5 was stationary"
    track_ids = constraints._extract_track_ids(text)
    
    assert "3" in track_ids
    assert "1" in track_ids
    assert "5" in track_ids


def test_extract_timestamps():
    """Test timestamp extraction"""
    constraints = HallucinationConstraints()
    
    text = "At t=0.75s the speed was 106px/s, and at 1.5s it changed to 2.3 seconds"
    timestamps = constraints._extract_timestamps(text)
    
    assert 0.75 in timestamps
    assert 1.5 in timestamps
    assert 2.3 in timestamps


def test_forbidden_phrases_detection():
    """Test forbidden phrase detection"""
    constraints = HallucinationConstraints()
    mock_scene_simple = MagicMock()
    mock_scene_simple.participating_track_ids = ["1"]
    mock_scene_simple.start_timestamp = 0.0
    mock_scene_simple.end_timestamp = 5.0
    
    # Test intent
    violations = constraints.check_hallucinations(
        "The person was trying to escape",
        mock_scene_simple
    )
    assert any("trying to" in v.lower() for v in violations)
    
    # Test emotion
    violations = constraints.check_hallucinations(
        "The person appeared nervous and agitated",
        mock_scene_simple
    )
    assert any("nervous" in v.lower() or "agitated" in v.lower() for v in violations)
    
    # Test threat
    violations = constraints.check_hallucinations(
        "The suspicious person was threatening others",
        mock_scene_simple
    )
    assert any("suspicious" in v.lower() or "threatening" in v.lower() for v in violations)


# ===== Fallback Tests =====

@pytest.mark.asyncio
async def test_fallback_uses_m8_narratives(mock_scene, mock_config):
    """Test that fallback uses M8 deterministic narratives"""
    with patch.object(OllamaClient, 'check_health', new_callable=AsyncMock) as mock_health:
        mock_health.return_value = False
        
        generator = ExplanationGenerator(mock_config)
        explanation = await generator.explain_scene(mock_scene)
        
        # Should use M8 summary
        assert explanation.overview == mock_scene.summary
        assert explanation.is_fallback
        assert explanation.model_name == "fallback"
        assert explanation.evidence_coverage == 1.0


def test_config_validation():
    """Test LLM config validation"""
    # Valid config
    config = LLMConfig(temperature=0.5, max_tokens=500)
    assert config.temperature == 0.5
    
    # Invalid temperature
    with pytest.raises(ValueError, match="temperature"):
        LLMConfig(temperature=1.5)
    
    # Invalid max_tokens
    with pytest.raises(ValueError, match="max_tokens"):
        LLMConfig(max_tokens=50)
    
    # Invalid timeout
    with pytest.raises(ValueError, match="timeout"):
        LLMConfig(timeout_seconds=-1)


# ===== Integration Test =====

@pytest.mark.asyncio
async def test_end_to_end_explanation_pipeline(mock_scene, mock_ollama_response, mock_config):
    """Test complete M9 pipeline from scene to explanation"""
    with patch.object(OllamaClient, 'check_health', new_callable=AsyncMock) as mock_health, \
         patch.object(OllamaClient, 'generate', new_callable=AsyncMock) as mock_generate:
        
        mock_health.return_value = True
        mock_generate.return_value = mock_ollama_response
        
        generator = ExplanationGenerator(mock_config)
        explanation = await generator.explain_scene(mock_scene)
        
        # Verify structure
        assert explanation.scene_id == mock_scene.scene_id
        assert explanation.overview is not None
        assert len(explanation.entity_behaviors) > 0
        assert explanation.generation_time_ms > 0
        
        # Verify no hallucinations
        assert explanation.hallucination_checks_passed
        
        # Verify evidence coverage
        assert explanation.evidence_coverage >= 0.0
        assert explanation.evidence_coverage <= 1.0
        
        # Verify serialization
        explanation_dict = explanation.to_dict()
        assert "scene_id" in explanation_dict
        assert "overview" in explanation_dict
        assert "is_fallback" in explanation_dict
        assert explanation_dict["is_fallback"] == False
