"""
Tests for Final Investigation Report Readability and Robustness

Regression protection for:
1. 11 raw anomalies with zero correlated events
2. Missing speed measurements
3. Missing track IDs
4. Zero anomalies (baseline footage)
5. Accurate timestamp preservation and formatting
6. Strict prevention of invented human actions, emotions, or intent
"""
import pytest
from processing.llm.investigation_report import build_investigation_report, LABEL_TRANSLATIONS


def test_eleven_raw_anomalies_zero_correlated_events():
    """
    Test scenario: 11 raw anomalies occur, but 0 correlated events are established.
    The report must explicitly state:
    'Raw anomaly indicators were detected, but no correlated events were established by the event-correlation stage.'
    and must not use robotic boilerplate.
    """
    anomalies = [
        {
            "anomaly_id": f"anom_{i:02d}",
            "track_id": 1,
            "timestamp": 2.0 + (i * 0.5),
            "anomaly_type": "unusual_speed",
            "severity": "medium",
            "anomaly_score": 0.75,
            "evidence": {"current_speed": 120.0 + i, "threshold": 80.0},
        }
        for i in range(11)
    ]

    pipeline_result = {
        "video_duration": 30.0,
        "video_width": 1920,
        "video_height": 1080,
        "video_fps": 30.0,
        "frames_processed": 900,
        "m1_total_detections": 450,
        "m1_detections_by_class": {"person": 450},
        "m2_unique_tracks": 1,
        "m3_avg_speed": 65.0,
        "m3_max_speed": 130.0,
        "m4_total_anomalies": 11,
        "m4_anomalies_by_type": {"unusual_speed": 11},
        "m5_correlated_events": 0,
        "m8_total_scenes": 1,
        "all_tracks": [],
        "all_behaviors": [
            [
                {"track_id": 1, "class_name": "person", "timestamp": 2.0 + (i * 0.5), "speed": 120.0 + i, "state": "walking"}
                for i in range(11)
            ]
        ],
        "all_anomalies": anomalies,
        "all_events": [],
        "all_scenes": [],
    }

    report = build_investigation_report(pipeline_result, scene_explanation=None)

    exec_summary = report["executive_summary"]
    final_assessment = report["final_assessment"]

    # 1. Must explicitly include required sentence
    expected_statement = "Raw anomaly indicators were detected, but no correlated events were established by the event-correlation stage."
    assert expected_statement in exec_summary, f"Expected statement missing from executive summary: {exec_summary}"
    assert expected_statement in final_assessment, f"Expected statement missing from final assessment: {final_assessment}"

    # 2. Must NOT contain robotic boilerplate
    robotic_phrases = [
        "11 isolated motion anomaly observation(s)",
        "The detector recorded",
        "Overall activity in the scene remained largely standard",
        "These observations did not persist long enough to establish a correlated multi-frame event.",
        "Unknown entity exhibited",
        "correlated High Speed Activity pattern",
    ]
    for phrase in robotic_phrases:
        assert phrase not in exec_summary, f"Robotic phrase found in executive summary: '{phrase}'"

    # 3. Evidence and limitations must explain why raw anomalies exist without correlated events
    evidence = report["evidence_and_limitations"]
    assert "why_raw_anomalies_exist_without_events" in evidence["detector_anomalies"]
    assert "zero_events_disclaimer" in evidence["correlated_events"]
    assert "it does not constitute proof that nothing significant occurred" in evidence["correlated_events"]["zero_events_disclaimer"]


def test_missing_speed_measurements():
    """
    Test scenario: Missing speed measurements should display 'Not available'
    instead of inventing a value or showing 0.0 px/s.
    """
    pipeline_result = {
        "video_duration": 10.0,
        "video_width": 1280,
        "video_height": 720,
        "video_fps": 25.0,
        "frames_processed": 250,
        "m1_total_detections": 50,
        "m1_detections_by_class": {"person": 50},
        "m2_unique_tracks": 1,
        "m3_avg_speed": None,
        "m3_max_speed": None,
        "m4_total_anomalies": 1,
        "m4_anomalies_by_type": {"loitering": 1},
        "m5_correlated_events": 0,
        "m8_total_scenes": 1,
        "all_tracks": [],
        "all_behaviors": [
            [
                {"track_id": 1, "class_name": "person", "timestamp": 1.0, "speed": None, "state": "standing"}
            ]
        ],
        "all_anomalies": [
            {
                "anomaly_id": "anom_01",
                "track_id": 1,
                "timestamp": 3.0,
                "anomaly_type": "loitering",
                "severity": "low",
                "anomaly_score": 0.6,
                "evidence": {},  # No speed or duration measurements
            }
        ],
        "all_events": [],
        "all_scenes": [],
    }

    report = build_investigation_report(pipeline_result, scene_explanation=None)

    # Track analysis should show "Not available" for speeds
    track0 = report["track_analyses"][0]
    assert track0["avg_speed_px_s"] == "Not available"
    assert track0["max_speed_px_s"] == "Not available"
    assert "Speed measurement: Not available" in track0["movement_narrative"]

    # Finding should show "Measurement data: Not available"
    finding0 = report["chronological_events"][0]
    assert "Not available" in finding0["measurable_change"]


def test_missing_track_ids():
    """
    Test scenario: Missing or null track IDs must be handled gracefully as 'Unassigned'
    without printing 'None' or crashing.
    """
    pipeline_result = {
        "video_duration": 10.0,
        "video_width": 1920,
        "video_height": 1080,
        "video_fps": 30.0,
        "frames_processed": 300,
        "m1_total_detections": 30,
        "m1_detections_by_class": {},
        "m2_unique_tracks": 0,
        "m3_avg_speed": None,
        "m3_max_speed": None,
        "m4_total_anomalies": 1,
        "m4_anomalies_by_type": {"sudden_appearance": 1},
        "m5_correlated_events": 0,
        "m8_total_scenes": 1,
        "all_tracks": [],
        "all_behaviors": [
            [
                {"track_id": None, "class_name": "unknown", "timestamp": 2.5, "speed": None, "state": None}
            ]
        ],
        "all_anomalies": [
            {
                "anomaly_id": "anom_no_id",
                "track_id": None,
                "timestamp": 2.5,
                "anomaly_type": "sudden_appearance",
                "severity": "low",
                "anomaly_score": 0.5,
                "evidence": {},
            }
        ],
        "all_events": [],
        "all_scenes": [],
    }

    report = build_investigation_report(pipeline_result, scene_explanation=None)

    finding = report["chronological_events"][0]
    assert "Track #None" not in finding["observable_behavior"]
    assert "an unassigned entity" in finding["observable_behavior"]
    assert finding["track_id_display"] == "an unassigned entity"


def test_no_anomalies_baseline():
    """
    Test scenario: Video with 0 anomalies and 0 events.
    Must not manufacture suspicious activity or threat.
    """
    pipeline_result = {
        "video_duration": 15.0,
        "video_width": 1920,
        "video_height": 1080,
        "video_fps": 30.0,
        "frames_processed": 450,
        "m1_total_detections": 150,
        "m1_detections_by_class": {"person": 150},
        "m2_unique_tracks": 1,
        "m3_avg_speed": 40.0,
        "m3_max_speed": 55.0,
        "m4_total_anomalies": 0,
        "m4_anomalies_by_type": {},
        "m5_correlated_events": 0,
        "m8_total_scenes": 1,
        "all_tracks": [],
        "all_behaviors": [
            [
                {"track_id": 1, "class_name": "person", "timestamp": 1.0, "speed": 40.0, "state": "walking"}
            ]
        ],
        "all_anomalies": [],
        "all_events": [],
        "all_scenes": [],
    }

    report = build_investigation_report(pipeline_result, scene_explanation=None)

    assert report["has_anomalies"] is False
    assert len(report["chronological_events"]) == 0
    assert "No movement anomalies or correlated events were detected" in report["executive_summary"]
    assert "No intervals currently require human review" in report["final_assessment"]


def test_report_contains_actual_timestamps_and_navigation():
    """
    Test scenario: Exact timestamps must be preserved for clickable seeking navigation.
    """
    pipeline_result = {
        "video_duration": 20.0,
        "video_width": 1920,
        "video_height": 1080,
        "video_fps": 30.0,
        "frames_processed": 600,
        "m1_total_detections": 200,
        "m1_detections_by_class": {"person": 200},
        "m2_unique_tracks": 1,
        "m3_avg_speed": 50.0,
        "m3_max_speed": 110.0,
        "m4_total_anomalies": 1,
        "m4_anomalies_by_type": {"unusual_speed": 1},
        "m5_correlated_events": 1,
        "m5_events_by_type": {"high_speed_movement": 1},
        "m8_total_scenes": 1,
        "all_tracks": [],
        "all_behaviors": [],
        "all_anomalies": [
            {
                "anomaly_id": "anom_01",
                "track_id": 1,
                "timestamp": 4.25,
                "anomaly_type": "unusual_speed",
                "severity": "medium",
                "evidence": {"current_speed": 110.0, "threshold": 80.0},
            }
        ],
        "all_events": [
            {
                "event_id": "evt_01",
                "event_type": "high_speed_movement",
                "track_ids": [1],
                "start_timestamp": 4.25,
                "end_timestamp": 6.80,
                "severity": "medium",
                "confidence": 0.9,
                "source_anomaly_ids": ["anom_01"],
                "evidence": {"peak_speed": 110.0},
            }
        ],
        "all_scenes": [],
    }

    report = build_investigation_report(pipeline_result, scene_explanation=None)

    evt = report["chronological_events"][0]
    assert evt["timestamp"] == 4.25
    assert evt["end_timestamp"] == 6.80
    assert evt["time_formatted"] == "0:04.25 – 0:06.80"
    assert "Peak measured image-space speed reached 110.0 px/s" in evt["measurable_change"]


def test_report_does_not_invent_human_actions_or_intent():
    """
    Test scenario: The report must translate algorithmic labels cleanly
    and never claim someone 'ran', 'fought', 'attacked', 'stole', 'panicked',
    or acted with criminal intent.
    """
    pipeline_result = {
        "video_duration": 15.0,
        "video_width": 1920,
        "video_height": 1080,
        "video_fps": 30.0,
        "frames_processed": 450,
        "m1_total_detections": 100,
        "m1_detections_by_class": {"person": 100},
        "m2_unique_tracks": 1,
        "m3_avg_speed": 85.0,
        "m3_max_speed": 160.0,
        "m4_total_anomalies": 3,
        "m4_anomalies_by_type": {
            "sudden_speed_change": 1,
            "sudden_direction_change": 1,
            "abnormal_movement_sequence": 1,
        },
        "m5_correlated_events": 0,
        "m8_total_scenes": 1,
        "all_tracks": [],
        "all_behaviors": [],
        "all_anomalies": [
            {
                "anomaly_id": "a1",
                "track_id": 1,
                "timestamp": 1.5,
                "anomaly_type": "sudden_speed_change",
                "evidence": {"speed_change": 45.0, "threshold": 30.0},
            },
            {
                "anomaly_id": "a2",
                "track_id": 1,
                "timestamp": 3.0,
                "anomaly_type": "sudden_direction_change",
                "evidence": {"angle_degrees": 95.0, "threshold": 60.0},
            },
            {
                "anomaly_id": "a3",
                "track_id": 1,
                "timestamp": 5.0,
                "anomaly_type": "abnormal_movement_sequence",
                "evidence": {},
            },
        ],
        "all_events": [],
        "all_scenes": [],
    }

    report = build_investigation_report(pipeline_result, scene_explanation=None)

    # 1. Check translated labels in categories
    categories = [e["category"] for e in report["chronological_events"]]
    assert any("Sudden change in measured movement speed" in c for c in categories)
    assert any("Sudden change in movement direction" in c for c in categories)
    assert any("A sequence of movement indicators that met the detector's configured criteria" in c for c in categories)

    # 2. Check absence of invented actions / emotions / criminal claims across all text
    all_text = " ".join([
        report["executive_summary"],
        report["final_assessment"],
        " ".join(e["observable_behavior"] for e in report["chronological_events"]),
        " ".join(e["flag_reason"] for e in report["chronological_events"]),
    ]).lower()

    forbidden_action_words = [
        "ran away", "running away", "fled", "fleeing",
        "fought", "fighting", "attacked", "attacking",
        "stole", "stealing", "theft",
        "panicked", "panicking",
        "suspicious person", "malicious", "guilt", "criminal",
    ]
    for bad_word in forbidden_action_words:
        assert bad_word not in all_text, f"Forbidden action/intent word '{bad_word}' found in report text: {all_text}"
