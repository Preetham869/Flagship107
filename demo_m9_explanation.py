#!/usr/bin/env python3
"""
M9 Demonstration Script

Shows M9 Local LLM Explanation Layer in action with sample.mp4
"""

import asyncio
import json
import logging
from pathlib import Path

from processing.pipeline.e2e_pipeline import EndToEndPipeline, PipelineConfig
from processing.llm.config import LLMConfig
from processing.llm.explanations import ExplanationGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demonstrate_m9():
    """Demonstrate M9 explanation generation"""
    
    print("=" * 80)
    print("M9: Local LLM Explanation Layer Demonstration")
    print("=" * 80)
    print()
    
    # Step 1: Run M1-M8 pipeline
    print("Step 1: Processing video through M1-M8 pipeline...")
    print("-" * 80)
    
    video_path = "data/sample.mp4"
    
    if not Path(video_path).exists():
        print(f"ERROR: Video not found: {video_path}")
        return
    
    # Process with M1-M8 only (M9 disabled by default)
    config = PipelineConfig(max_frames=90)
    pipeline = EndToEndPipeline(config)
    result = pipeline.process_video(video_path)
    
    print(f"✓ Processed {result.frames_processed} frames")
    print(f"  M1: {result.m1_total_detections} detections")
    print(f"  M2: {result.m2_unique_tracks} tracks")
    print(f"  M8: {result.m8_total_scenes} contextual scenes")
    print()
    
    if not result.all_scenes:
        print("No scenes generated. Exiting.")
        return
    
    # Step 2: Load first scene
    scene_dict = result.all_scenes[0]
    print("Step 2: Loading first contextual scene...")
    print("-" * 80)
    print(f"Scene ID: {scene_dict['scene_id']}")
    print(f"Duration: {scene_dict['duration_seconds']:.2f}s")
    print(f"Tracks: {len(scene_dict['track_summaries'])}")
    print()
    
    # Show M8 baseline narrative
    print("M8 Baseline Narrative (Deterministic):")
    print("-" * 80)
    print(f"Summary: {scene_dict['summary']}")
    print(f"Description: {scene_dict['description'][:200]}...")
    print()
    
    # Step 3: Generate M9 LLM explanation
    print("Step 3: Generating M9 LLM Explanation...")
    print("-" * 80)
    
    # Reconstruct scene object (simplified)
    from processing.context.schemas import ContextualScene, TrackSummary
    
    track_summaries = []
    for ts_dict in scene_dict['track_summaries']:
        track_summaries.append(
            TrackSummary(
                track_id=ts_dict['track_id'],
                class_name=ts_dict['class_name'],
                first_seen=ts_dict['first_seen'],
                last_seen=ts_dict['last_seen'],
                duration=ts_dict['duration'],
                observation_count=ts_dict['observation_count'],
                entry_position=tuple(ts_dict['entry_position']),
                exit_position=tuple(ts_dict['exit_position']) if ts_dict['exit_position'] else None,
                path_length=ts_dict['path_length'],
                avg_displacement=ts_dict['avg_displacement'],
                state_distribution=ts_dict['state_distribution'],
                dominant_state=ts_dict['dominant_state'],
                avg_speed=ts_dict['avg_speed'],
                max_speed=ts_dict['max_speed'],
                speed_variance=ts_dict['speed_variance'],
                trajectory_type=ts_dict['trajectory_type'],
                movement_patterns=ts_dict['movement_patterns'],
                anomaly_count=ts_dict['anomaly_count'],
                anomaly_types=ts_dict['anomaly_types'],
                anomaly_severity_max=ts_dict['anomaly_severity_max'],
                interaction_count=ts_dict['interaction_count'],
                interacted_with_tracks=ts_dict['interacted_with_tracks'],
                interaction_types=ts_dict['interaction_types'],
                behavior_label=ts_dict['behavior_label'],
                summary=ts_dict['summary'],
            )
        )
    
    scene = ContextualScene(
        scene_id=scene_dict['scene_id'],
        scene_number=scene_dict['scene_number'],
        start_timestamp=scene_dict['start_timestamp'],
        end_timestamp=scene_dict['end_timestamp'],
        duration_seconds=scene_dict['duration_seconds'],
        start_frame=scene_dict['start_frame'],
        end_frame=scene_dict['end_frame'],
        participating_track_ids=scene_dict['participating_track_ids'],
        track_summaries=track_summaries,
        total_observations=scene_dict['total_observations'],
        dominant_states=scene_dict['dominant_states'],
        avg_scene_speed=scene_dict['avg_scene_speed'],
        max_scene_speed=scene_dict['max_scene_speed'],
        total_movements=scene_dict['total_movements'],
        source_anomalies=scene_dict['source_anomalies'],
        source_events=scene_dict['source_events'],
        source_relationships=scene_dict['source_relationships'],
        movement_patterns=scene_dict['movement_patterns'],
        spatial_patterns=scene_dict['spatial_patterns'],
        temporal_patterns=scene_dict['temporal_patterns'],
        scene_type=scene_dict['scene_type'],
        anomaly_density=scene_dict['anomaly_density'],
        complexity_score=scene_dict['complexity_score'],
        summary=scene_dict['summary'],
        description=scene_dict['description'],
        key_observations=scene_dict['key_observations'],
    )
    
    # Generate explanation with M9
    llm_config = LLMConfig(
        provider="ollama",
        model_name="qwen3:8b",
        temperature=0.3,
        timeout_seconds=30.0
    )
    
    generator = ExplanationGenerator(llm_config)
    
    try:
        explanation = await generator.explain_scene(scene)
        
        if explanation.is_fallback:
            print(f"⚠️  Using fallback (LLM unavailable): {explanation.fallback_reason}")
            print()
        else:
            print(f"✓ Generated by {explanation.model_name} in {explanation.generation_time_ms:.0f}ms")
            print(f"  Evidence coverage: {explanation.evidence_coverage:.1%}")
            print(f"  Confidence: {explanation.confidence_level}")
            print()
        
        # Display M9 explanation
        print("M9 LLM Explanation (Natural Language):")
        print("=" * 80)
        print()
        
        print("Overview:")
        print("-" * 80)
        print(explanation.overview)
        print()
        
        if explanation.entity_behaviors:
            print("Entity Behaviors:")
            print("-" * 80)
            for eb in explanation.entity_behaviors:
                print(f"\nTrack #{eb.track_id}:")
                print(f"  {eb.behavior_summary}")
                
                if eb.pattern_explanations:
                    print(f"  Patterns:")
                    for pattern, expl in eb.pattern_explanations.items():
                        print(f"    - {pattern}: {expl[:100]}...")
                
                if eb.context:
                    print(f"  Context: {eb.context[:150]}...")
        
        if explanation.anomaly_significance:
            print("\nAnomalies:")
            print("-" * 80)
            for sig in explanation.anomaly_significance:
                print(f"  {sig}")
        
        if explanation.contextual_interpretation:
            print("\nContextual Interpretation:")
            print("-" * 80)
            print(f"  {explanation.contextual_interpretation}")
        
        print()
        print("=" * 80)
        
        # Save explanation
        output_file = "data/m9_explanation_demo.json"
        with open(output_file, 'w') as f:
            json.dump(explanation.to_dict(), f, indent=2)
        
        print(f"\n✓ Explanation saved to: {output_file}")
        
    except Exception as e:
        print(f"ERROR: Failed to generate explanation: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    try:
        asyncio.run(demonstrate_m9())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
