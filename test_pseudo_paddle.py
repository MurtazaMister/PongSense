"""
Test script for pseudo-paddle system with AI misses.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.logger import logger
from game.ai_opponent import AIOpponent


def test_pseudo_paddle_system():
    """Test pseudo-paddle system with random hit zones and miss chances."""
    print("Testing pseudo-paddle system...")
    
    # Initialize AI
    ai = AIOpponent()
    
    print("Pseudo-paddle test started!")
    print("Testing random hit zone selection and miss chances...")
    
    # Test hit zone selection
    print("\n--- Testing Hit Zone Selection ---")
    zone_counts = {
        'center': 0,
        'top': 0,
        'bottom': 0,
        'pseudo_top': 0,
        'pseudo_bottom': 0
    }
    
    # Simulate many hit zone selections
    for i in range(100):
        ai._select_hit_zone()
        zone_counts[ai.current_hit_zone] += 1
    
    print("Hit zone distribution over 100 selections:")
    for zone, count in zone_counts.items():
        percentage = (count / 100) * 100
        print(f"  {zone}: {count} ({percentage:.1f}%)")
    
    # Test target adjustment for different zones
    print("\n--- Testing Target Adjustment ---")
    test_target = 0.5
    
    for zone in ['center', 'top', 'bottom', 'pseudo_top', 'pseudo_bottom']:
        ai.current_hit_zone = zone
        adjusted_target = ai._adjust_target_for_hit_zone(test_target)
        print(f"{zone}: {test_target:.2f} -> {adjusted_target:.2f}")
    
    # Test miss detection
    print("\n--- Testing Miss Detection ---")
    miss_count = 0
    total_tests = 50
    
    for i in range(total_tests):
        ai._select_hit_zone()
        if ai.current_hit_zone in ['pseudo_top', 'pseudo_bottom']:
            miss_count += 1
    
    miss_percentage = (miss_count / total_tests) * 100
    print(f"Miss chances: {miss_count}/{total_tests} ({miss_percentage:.1f}%)")
    print(f"Expected: ~20% (10% pseudo_top + 10% pseudo_bottom)")
    
    # Test zone change timing
    print("\n--- Testing Zone Change Timing ---")
    ai.last_zone_change_time = 0
    ai.zone_change_interval = 0.1  # Change every 0.1 seconds for testing
    
    zones_over_time = []
    for i in range(10):
        ai._select_hit_zone()
        zones_over_time.append(ai.current_hit_zone)
        time.sleep(0.05)  # 0.05 seconds between calls
    
    print("Zones over time:")
    for i, zone in enumerate(zones_over_time):
        print(f"  Step {i+1}: {zone}")
    
    print("\nPseudo-paddle system test completed!")
    print("\nExpected behavior:")
    print("- AI randomly selects hit zones based on probabilities")
    print("- Pseudo-paddle zones (pseudo_top, pseudo_bottom) cause misses")
    print("- Zone changes periodically (every 0.5 seconds)")
    print("- Target positions are adjusted based on selected zone")
    return True


if __name__ == "__main__":
    test_pseudo_paddle_system()
