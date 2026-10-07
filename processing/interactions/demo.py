"""
Milestone 6 Demo: Multi-Entity Interaction Detection

Demonstrates spatial reasoning and interaction detection capabilities.
"""

from processing.interactions.detector import InteractionDetector, InteractionConfig
from processing.interactions.spatial import SpatialReasoning


def print_section(title: str):
    """Print section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def scenario_a_approach():
    """Scenario A: Two entities approaching each other"""
    print_section("Scenario A: Approach Detection")
    
    detector = InteractionDetector()
    
    # Simulate two entities moving toward each other
    print("Simulating two pedestrians (Tracks #1 and #2) walking toward each other...")
    
    for i in range(10):
        # Track 1 moves right (100 -> 190)
        # Track 2 moves left (300 -> 210)
        # Distance decreases from 200px to 20px
        behaviors = [
            {
                "track_id": "1",
                "timestamp": 1.0 + i * 0.5,
                "position": [100 + i * 10, 200],
                "speed": 20.0,
                "direction": 0.0,  # Moving right
            },
            {
                "track_id": "2",
                "timestamp": 1.0 + i * 0.5,
                "position": [300 - i * 10, 200],
                "speed": 20.0,
                "direction": 180.0,  # Moving left
            },
        ]
        rels = detector.detect(behaviors)
        
        if i == 0 or i == 9:
            dist = SpatialReasoning.euclidean_distance(
                behaviors[0]["position"], behaviors[1]["position"]
            )
            print(f"  Frame {i}: Distance = {dist:.1f}px")
        
        if rels and i == 9:
            print(f"\n✓ Relationships detected at t={behaviors[0]['timestamp']:.1f}s:")
            for r in rels:
                print(f"  • {r.relationship_type.value}")
                print(f"    Tracks: #{', #'.join(r.participating_track_ids)}")
                print(f"    Duration: {r.duration_seconds:.1f}s")
                print(f"    Avg distance: {r.avg_distance:.1f}px")
                print(f"    Confidence: {r.confidence:.2f}")
                print()


def scenario_b_co_movement():
    """Scenario B: Co-movement (walking together)"""
    print_section("Scenario B: Co-Movement Detection")
    
    detector = InteractionDetector()
    
    # Simulate two entities moving together in same direction
    print("Simulating two pedestrians (Tracks #3 and #4) walking together...")
    
    for i in range(10):
        # Both move right at same speed, maintaining 80px distance
        behaviors = [
            {
                "track_id": "3",
                "timestamp": 1.0 + i * 0.5,
                "position": [100 + i * 20, 200],
                "speed": 40.0,
                "direction": 0.0,  # Moving right
            },
            {
                "track_id": "4",
                "timestamp": 1.0 + i * 0.5,
                "position": [180 + i * 20, 200],  # 80px away
                "speed": 40.0,
                "direction": 0.0,  # Same direction
            },
        ]
        rels = detector.detect(behaviors)
        
        if i == 9 and rels:
            print(f"✓ Relationships detected at t={behaviors[0]['timestamp']:.1f}s:")
            for r in rels:
                print(f"  • {r.relationship_type.value}")
                print(f"    Tracks: #{', #'.join(r.participating_track_ids)}")
                print(f"    Explanation: {r.explanation}")
                print()


def scenario_c_following():
    """Scenario C: Following pattern"""
    print_section("Scenario C: Following Pattern Detection")
    
    detector = InteractionDetector()
    
    # Simulate Track 6 following Track 5
    print("Simulating Track #6 following Track #5...")
    
    for i in range(10):
        # Track 5 leads, Track 6 follows 60px behind
        behaviors = [
            {
                "track_id": "5",  # Leader
                "timestamp": 1.0 + i * 0.5,
                "position": [150 + i * 15, 200],
                "speed": 30.0,
                "direction": 0.0,  # Moving right
            },
            {
                "track_id": "6",  # Follower
                "timestamp": 1.0 + i * 0.5,
                "position": [90 + i * 15, 200],  # 60px behind
                "speed": 30.0,
                "direction": 0.0,  # Same direction
            },
        ]
        rels = detector.detect(behaviors)
        
        if i == 9 and rels:
            print(f"✓ Relationships detected at t={behaviors[0]['timestamp']:.1f}s:")
            for r in rels:
                print(f"  • {r.relationship_type.value}")
                print(f"    Tracks: #{', #'.join(r.participating_track_ids)}")
                if r.relationship_type.value == "following_pattern":
                    print(f"    Explanation: {r.explanation}")
                print()


def scenario_d_group_formation():
    """Scenario D: Group formation"""
    print_section("Scenario D: Group Formation")
    
    detector = InteractionDetector()
    
    # Three entities come together to form a group
    print("Simulating 3 pedestrians (Tracks #7, #8, #9) forming a group...")
    
    behaviors = [
        {
            "track_id": "7",
            "timestamp": 5.0,
            "position": [300, 300],
            "speed": 5.0,
            "direction": 0.0,
        },
        {
            "track_id": "8",
            "timestamp": 5.0,
            "position": [380, 300],  # 80px from #7
            "speed": 5.0,
            "direction": 0.0,
        },
        {
            "track_id": "9",
            "timestamp": 5.0,
            "position": [380, 380],  # 80px from #8
            "speed": 5.0,
            "direction": 0.0,
        },
    ]
    
    rels = detector.detect(behaviors)
    
    if rels:
        print(f"✓ Relationships detected:")
        for r in rels:
            print(f"  • {r.relationship_type.value}")
            print(f"    Group members: #{', #'.join(r.participating_track_ids)}")
            print(f"    Explanation: {r.explanation}")
            print()


def scenario_e_group_separation():
    """Scenario E: Departure (entities separating)"""
    print_section("Scenario E: Departure Detection")
    
    detector = InteractionDetector()
    
    # Two entities moving apart
    print("Simulating two pedestrians (Tracks #10 and #11) separating...")
    
    for i in range(10):
        # Track 10 stays, Track 11 moves away
        behaviors = [
            {
                "track_id": "10",
                "timestamp": 1.0 + i * 0.5,
                "position": [200, 300],
                "speed": 0.0,
                "direction": 0.0,
            },
            {
                "track_id": "11",
                "timestamp": 1.0 + i * 0.5,
                "position": [220 + i * 15, 300],  # Moving away
                "speed": 30.0,
                "direction": 0.0,
            },
        ]
        rels = detector.detect(behaviors)
        
        if i == 9 and rels:
            dist = SpatialReasoning.euclidean_distance(
                behaviors[0]["position"], behaviors[1]["position"]
            )
            print(f"  Final distance: {dist:.1f}px")
            print(f"\n✓ Relationships detected at t={behaviors[0]['timestamp']:.1f}s:")
            for r in rels:
                print(f"  • {r.relationship_type.value}")
                print(f"    Tracks: #{', #'.join(r.participating_track_ids)}")
                print(f"    Duration: {r.duration_seconds:.1f}s")
                print()


def demo_statistics():
    """Show detector statistics"""
    print_section("Detector Statistics Example")
    
    detector = InteractionDetector()
    
    # Process some data
    for i in range(5):
        behaviors = [
            {"track_id": "A", "timestamp": i * 0.5, "position": [100 + i * 10, 200], "speed": 20.0, "direction": 0.0},
            {"track_id": "B", "timestamp": i * 0.5, "position": [150 + i * 10, 200], "speed": 20.0, "direction": 0.0},
            {"track_id": "C", "timestamp": i * 0.5, "position": [100, 250], "speed": 5.0, "direction": 90.0},
        ]
        detector.detect(behaviors)
    
    stats = detector.get_statistics()
    
    print("Detector Statistics:")
    print(f"  Tracked pairs: {stats['tracked_pairs']}")
    print(f"  Proximity radius: {stats['proximity_radius']}px")
    print(f"  Interaction radius: {stats['interaction_radius']}px")
    print(f"  Min observations required: {stats['min_observations']}")
    print()


def main():
    """Run all demo scenarios"""
    print("\n" + "=" * 70)
    print("  MILESTONE 6: Multi-Entity Interaction Detection Demo")
    print("  Flagship 107 - HackNEX 2026")
    print("=" * 70)
    
    print("\nThis demo showcases spatial reasoning and relationship detection")
    print("between multiple tracked entities in video footage.\n")
    
    print("NOTE: All distance calculations use PIXEL coordinates.")
    print("Relationships are detected based on spatial/temporal patterns,")
    print("not on intent recognition.\n")
    
    # Run scenarios
    scenario_a_approach()
    scenario_b_co_movement()
    scenario_c_following()
    scenario_d_group_formation()
    scenario_e_group_separation()
    demo_statistics()
    
    print_section("Demo Complete!")
    print("All M6 interaction detection capabilities demonstrated.")
    print("✓ Proximity detection")
    print("✓ Approach/Departure detection")
    print("✓ Co-movement detection")
    print("✓ Following pattern detection")
    print("✓ Group formation detection")
    print("\nThese interactions can be combined with M5 events to provide")
    print("richer context for behavioral anomaly detection.\n")


if __name__ == "__main__":
    main()
