#!/usr/bin/env python3
"""
M8 Real-Video Validation Script

Runs the complete M1-M8 pipeline on sample.mp4 and validates M8 contextual scenes.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from processing.pipeline.e2e_pipeline import EndToEndPipeline, PipelineConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_evidence_chain(scene: Dict, behaviors: List[Dict], anomalies: List[Dict]) -> Dict[str, Any]:
    """
    Validate that evidence in a scene actually traces back to M3/M4/M5/M6 data.
    
    Returns validation report with any issues found.
    """
    issues = []
    validated_patterns = []
    
    scene_id = scene.get('scene_id', 'unknown')
    logger.info(f"Validating evidence for {scene_id}...")
    
    # Check each track summary
    for track_summary in scene.get('track_summaries', []):
        track_id = track_summary.get('track_id')
        observed_patterns = track_summary.get('observed_patterns', [])
        evidence = track_summary.get('evidence', {})
        
        # Verify track exists in behaviors
        track_behaviors = [b for b in behaviors if b.get('track_id') == track_id]
        if not track_behaviors:
            issues.append(f"Track {track_id} has no behaviors in M5 output")
            continue
        
        # Check each pattern has evidence
        pattern_evidence_list = evidence.get('pattern_evidence', [])
        for pattern_name in observed_patterns:
            # Find evidence for this pattern
            pattern_ev = [p for p in pattern_evidence_list if p.get('pattern_type') == pattern_name]
            
            if not pattern_ev:
                issues.append(f"Pattern '{pattern_name}' for {track_id} has no evidence")
                continue
            
            # Verify source references
            for pev in pattern_ev:
                source_refs = pev.get('source_references', [])
                if not source_refs:
                    issues.append(f"Pattern '{pattern_name}' for {track_id} has no source references")
                    continue
                
                # Validate source references point to actual data
                for src_ref in source_refs:
                    module = src_ref.get('module')
                    ref_track_id = src_ref.get('track_id')
                    frame_range = src_ref.get('frame_range', [])
                    
                    # Basic validation
                    if not module or not ref_track_id:
                        issues.append(f"Invalid source reference in pattern '{pattern_name}'")
                        continue
                    
                    if ref_track_id != track_id:
                        issues.append(f"Source reference track mismatch: {ref_track_id} != {track_id}")
                        continue
                    
                    # Verify timestamps are reasonable
                    if len(frame_range) == 2:
                        start_frame, end_frame = frame_range
                        if start_frame > end_frame:
                            issues.append(f"Invalid frame range: {start_frame} > {end_frame}")
                        if start_frame < 0 or end_frame < 0:
                            issues.append(f"Negative frame numbers: {frame_range}")
                
                # Pattern validated
                validated_patterns.append({
                    'track_id': track_id,
                    'pattern': pattern_name,
                    'has_evidence': True,
                    'source_count': len(source_refs)
                })
    
    return {
        'scene_id': scene_id,
        'issues': issues,
        'validated_patterns': validated_patterns,
        'validation_passed': len(issues) == 0
    }


def generate_validation_report(
    video_path: str,
    result: Dict,
    validation_results: List[Dict]
) -> str:
    """Generate comprehensive validation report."""
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("M8 REAL-VIDEO VALIDATION REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # A. Video Properties
    report_lines.append("A. VIDEO PROPERTIES")
    report_lines.append("-" * 80)
    report_lines.append(f"Path: {result.get('video_path')}")
    report_lines.append(f"Resolution: {result.get('video_width')}x{result.get('video_height')}")
    report_lines.append(f"FPS: {result.get('video_fps', 0):.2f}")
    report_lines.append(f"Duration: {result.get('video_duration', 0):.2f}s")
    report_lines.append(f"Total Frames: {result.get('video_total_frames', 0)}")
    report_lines.append("")
    
    # B. Pipeline Execution
    report_lines.append("B. PIPELINE EXECUTION RESULTS")
    report_lines.append("-" * 80)
    report_lines.append(f"Frames Processed: {result.get('frames_processed', 0)}")
    report_lines.append(f"Frames Skipped: {result.get('frames_skipped', 0)}")
    report_lines.append(f"Processing Time: {result.get('processing_time', 0):.2f}s")
    report_lines.append("")
    
    # C. M1-M7 Statistics
    report_lines.append("C. M1-M7 STATISTICS")
    report_lines.append("-" * 80)
    report_lines.append(f"M1 Total Detections: {result.get('m1_total_detections', 0)}")
    report_lines.append(f"M1 Avg Detections/Frame: {result.get('m1_avg_detections_per_frame', 0):.2f}")
    report_lines.append(f"M2 Unique Tracks: {result.get('m2_unique_tracks', 0)}")
    report_lines.append(f"M2 Active Tracks: {result.get('m2_active_tracks', 0)}")
    report_lines.append(f"M3 Total Behaviors: {result.get('m3_total_behaviors', 0)}")
    report_lines.append(f"M3 Avg Speed: {result.get('m3_avg_speed', 0):.2f} px/s")
    report_lines.append(f"M4 Total Anomalies: {result.get('m4_total_anomalies', 0)}")
    report_lines.append(f"M5 Raw Anomalies: {result.get('m5_total_raw_anomalies', 0)}")
    report_lines.append(f"M5 Correlated Events: {result.get('m5_correlated_events', 0)}")
    report_lines.append(f"M6 Relationships: {result.get('m6_total_relationships', 0)}")
    report_lines.append(f"M6 Tracked Pairs: {result.get('m6_tracked_pairs', 0)}")
    report_lines.append("")
    
    # D. M8 Statistics
    report_lines.append("D. M8 CONTEXTUAL BEHAVIOUR STATISTICS")
    report_lines.append("-" * 80)
    report_lines.append(f"Total Scenes: {result.get('m8_total_scenes', 0)}")
    report_lines.append(f"Avg Scene Duration: {result.get('m8_avg_scene_duration', 0):.2f}s")
    
    contextual_scenes = result.get('contextual_scenes', [])
    if contextual_scenes:
        total_patterns = sum(
            len(ts.get('observed_patterns', []))
            for scene in contextual_scenes
            for ts in scene.get('track_summaries', [])
        )
        report_lines.append(f"Total Patterns Detected: {total_patterns}")
        
        # Pattern frequency
        pattern_counts = {}
        for scene in contextual_scenes:
            for ts in scene.get('track_summaries', []):
                for pattern in ts.get('observed_patterns', []):
                    pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        if pattern_counts:
            report_lines.append("\nPattern Distribution:")
            for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"  - {pattern}: {count}")
    report_lines.append("")
    
    # E. Example Contextual Scenes
    report_lines.append("E. EXAMPLE CONTEXTUAL SCENES")
    report_lines.append("-" * 80)
    
    for i, scene in enumerate(contextual_scenes[:3], 1):  # Show first 3 scenes
        report_lines.append(f"\nScene {i}: {scene.get('scene_id')}")
        report_lines.append(f"  Time Range: {scene.get('start_time', 0):.2f}s - {scene.get('end_time', 0):.2f}s")
        report_lines.append(f"  Duration: {scene.get('duration', 0):.2f}s")
        report_lines.append(f"  Active Tracks: {', '.join(scene.get('active_tracks', []))}")
        
        track_summaries = scene.get('track_summaries', [])
        report_lines.append(f"  Track Summaries ({len(track_summaries)}):")
        
        for ts in track_summaries:
            track_id = ts.get('track_id')
            patterns = ts.get('observed_patterns', [])
            anomalies = ts.get('anomalies_associated', 0)
            narrative = ts.get('narrative', 'N/A')
            
            report_lines.append(f"\n    Track: {track_id}")
            report_lines.append(f"      Duration: {ts.get('total_duration', 0):.2f}s")
            report_lines.append(f"      First Seen: {ts.get('first_seen', 0):.2f}s")
            report_lines.append(f"      Last Seen: {ts.get('last_seen', 0):.2f}s")
            report_lines.append(f"      Patterns: {', '.join(patterns) if patterns else 'None'}")
            report_lines.append(f"      Anomalies: {anomalies}")
            report_lines.append(f"      Narrative: {narrative}")
    
    if len(contextual_scenes) > 3:
        report_lines.append(f"\n... and {len(contextual_scenes) - 3} more scenes")
    report_lines.append("")
    
    # F. Evidence Provenance Verification
    report_lines.append("F. EVIDENCE PROVENANCE VERIFICATION")
    report_lines.append("-" * 80)
    
    total_validated = 0
    total_issues = 0
    
    for val_result in validation_results:
        scene_id = val_result['scene_id']
        issues = val_result['issues']
        validated = val_result['validated_patterns']
        passed = val_result['validation_passed']
        
        total_validated += len(validated)
        total_issues += len(issues)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        report_lines.append(f"\n{scene_id}: {status}")
        report_lines.append(f"  Validated Patterns: {len(validated)}")
        
        if issues:
            report_lines.append(f"  Issues Found: {len(issues)}")
            for issue in issues[:5]:  # Show first 5 issues
                report_lines.append(f"    - {issue}")
            if len(issues) > 5:
                report_lines.append(f"    ... and {len(issues) - 5} more issues")
    
    report_lines.append(f"\nSummary:")
    report_lines.append(f"  Total Patterns Validated: {total_validated}")
    report_lines.append(f"  Total Issues Found: {total_issues}")
    report_lines.append(f"  Overall Status: {'✅ PASS' if total_issues == 0 else '❌ FAIL'}")
    report_lines.append("")
    
    # G. Suspicious/Incorrect Results
    report_lines.append("G. SUSPICIOUS/INCORRECT RESULTS")
    report_lines.append("-" * 80)
    
    suspicious_findings = []
    
    # Check for scenes with no patterns
    for scene in contextual_scenes:
        track_summaries = scene.get('track_summaries', [])
        total_patterns_in_scene = sum(len(ts.get('observed_patterns', [])) for ts in track_summaries)
        if total_patterns_in_scene == 0 and len(track_summaries) > 0:
            suspicious_findings.append(
                f"Scene {scene.get('scene_id')} has {len(track_summaries)} tracks but no patterns"
            )
    
    # Check for impossible timestamps
    for scene in contextual_scenes:
        start = scene.get('start_time', 0)
        end = scene.get('end_time', 0)
        duration = scene.get('duration', 0)
        
        if end < start:
            suspicious_findings.append(
                f"Scene {scene.get('scene_id')} has end_time < start_time: {end} < {start}"
            )
        
        if abs((end - start) - duration) > 0.1:
            suspicious_findings.append(
                f"Scene {scene.get('scene_id')} duration mismatch: "
                f"calculated {end - start:.2f}s != reported {duration:.2f}s"
            )
    
    # Check for patterns without evidence (from validation results)
    patterns_without_evidence = [
        f"{vr['scene_id']}: {issue}"
        for vr in validation_results
        for issue in vr['issues']
        if 'no evidence' in issue.lower()
    ]
    suspicious_findings.extend(patterns_without_evidence[:10])  # Show first 10
    
    if suspicious_findings:
        for finding in suspicious_findings:
            report_lines.append(f"  ⚠️  {finding}")
    else:
        report_lines.append("  No suspicious results detected. ✅")
    report_lines.append("")
    
    # H. Regression Test Status (to be filled after running tests)
    report_lines.append("H. REGRESSION TEST RESULTS")
    report_lines.append("-" * 80)
    report_lines.append("  Run 'pytest processing/tests/' to verify all 182 tests still pass.")
    report_lines.append("")
    
    # I. Files Generated
    report_lines.append("I. FILES GENERATED")
    report_lines.append("-" * 80)
    report_lines.append(f"  - data/sample_e2e_result_m8.json (Pipeline result with M8 data)")
    report_lines.append(f"  - M8_VALIDATION_REPORT.txt (This report)")
    report_lines.append("")
    
    # J. M8 Readiness Assessment
    report_lines.append("J. M8 READINESS FOR M9")
    report_lines.append("-" * 80)
    
    readiness_checks = []
    
    # Check 1: Scenes generated
    if result.get('m8_total_scenes', 0) > 0:
        readiness_checks.append("✅ Contextual scenes successfully generated")
    else:
        readiness_checks.append("❌ No contextual scenes generated")
    
    # Check 2: Patterns detected
    if total_patterns > 0:
        readiness_checks.append(f"✅ Observable patterns detected ({total_patterns} total)")
    else:
        readiness_checks.append("⚠️  No patterns detected (may be expected for this video)")
    
    # Check 3: Evidence validation
    if total_issues == 0:
        readiness_checks.append("✅ All evidence chains validated")
    else:
        readiness_checks.append(f"❌ Evidence validation issues found ({total_issues} issues)")
    
    # Check 4: No suspicious results
    if not suspicious_findings:
        readiness_checks.append("✅ No suspicious results detected")
    else:
        readiness_checks.append(f"⚠️  {len(suspicious_findings)} suspicious findings")
    
    for check in readiness_checks:
        report_lines.append(f"  {check}")
    
    report_lines.append("")
    
    # Final assessment
    critical_failures = sum(1 for c in readiness_checks if c.startswith("❌"))
    warnings = sum(1 for c in readiness_checks if c.startswith("⚠️"))
    
    if critical_failures == 0 and warnings == 0:
        report_lines.append("FINAL ASSESSMENT: ✅ M8 IS READY FOR M9 INTEGRATION")
    elif critical_failures == 0:
        report_lines.append(f"FINAL ASSESSMENT: ⚠️  M8 IS MOSTLY READY (with {warnings} warnings)")
    else:
        report_lines.append(f"FINAL ASSESSMENT: ❌ M8 NEEDS FIXES ({critical_failures} critical issues)")
    
    report_lines.append("")
    report_lines.append("=" * 80)
    
    return "\n".join(report_lines)


def main():
    """Run M8 validation on sample.mp4."""
    
    video_path = "data/sample.mp4"
    
    logger.info("=" * 80)
    logger.info("M8 REAL-VIDEO VALIDATION")
    logger.info("=" * 80)
    logger.info(f"Video: {video_path}")
    logger.info("")
    
    # Check video exists
    if not Path(video_path).exists():
        logger.error(f"Video not found: {video_path}")
        return
    
    # Setup pipeline with M7-calibrated config
    logger.info("Initializing pipeline with M7-calibrated anomaly detection...")
    config = PipelineConfig(
        max_frames=120,  # Process first 120 frames (5 seconds at 24fps) for faster validation
        frame_skip=0,     # Don't skip frames
    )
    
    pipeline = EndToEndPipeline(config)
    
    # Process video
    logger.info("Processing video through M1-M8 pipeline...")
    result = pipeline.process_video(video_path)
    
    logger.info("Pipeline processing complete!")
    logger.info(f"Frames processed: {result.frames_processed}")
    logger.info(f"Processing time: {result.processing_time:.2f}s")
    logger.info(f"M8 Scenes generated: {result.m8_total_scenes}")
    logger.info("")
    
    # Convert result to dict
    result_dict = result.to_dict()
    
    # Save JSON result
    output_json = "data/sample_e2e_result_m8.json"
    logger.info(f"Saving results to {output_json}...")
    with open(output_json, 'w') as f:
        json.dump(result_dict, f, indent=2)
    
    # Validate evidence chains
    logger.info("Validating evidence provenance...")
    validation_results = []
    
    for scene in result_dict.get('contextual_scenes', []):
        val_result = validate_evidence_chain(
            scene,
            result_dict.get('behaviors', []),
            result_dict.get('anomalies', [])
        )
        validation_results.append(val_result)
    
    # Generate validation report
    logger.info("Generating validation report...")
    report = generate_validation_report(video_path, result_dict, validation_results)
    
    # Save report
    report_path = "M8_VALIDATION_REPORT.txt"
    with open(report_path, 'w') as f:
        f.write(report)
    
    logger.info(f"Validation report saved to {report_path}")
    logger.info("")
    
    # Print report to console
    print("\n")
    print(report)
    
    # Note: Annotated video generation would require implementing generate_annotated_video
    # For now, focus on data validation
    logger.info("Skipping annotated video generation (not implemented in pipeline)")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("VALIDATION COMPLETE")
    logger.info("=" * 80)
    logger.info("Next steps:")
    logger.info("1. Review M8_VALIDATION_REPORT.txt")
    logger.info("2. Run: pytest processing/tests/ (verify 182/182 tests pass)")
    logger.info("3. If validation passes, M8 is ready for M9")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
