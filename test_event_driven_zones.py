"""
Test script for event-driven hit zone selection.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.logger import logger
from game.ai_opponent import AIOpponent


def test_event_driven_zones():
    """Test event-driven hit zone selection instead of periodic."""
    print("Testing event-driven hit zone selection...")
    
    # Initialize AI
    ai = AIOpponent()
    
    print("Event-driven zone selection test started!")
    print("Testing zone selection based on ball serve detection...")
    
    # Test serve detection
    print("\n--- Testing Serve Detection ---")
    
    # Simulate ball moving from center (serve) to edge
    ball_positions = [0.5, 0.5, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    
    print("Ball positions and zone selections:")
    for i, ball_x in enumerate(ball_positions):
        ai._detect_serve_and_select_zone(ball_x)
        print(f"Step {i+1:2d}: Ball x={ball_x:.1f}, Zone={ai.current_hit_zone}, Selected={ai.zone_selected_for_serve}")
    
    # Test multiple serves
    print("\n--- Testing Multiple Serves ---")
    
    # Reset AI state
    ai.zone_selected_for_serve = False
    ai.current_hit_zone = 'center'
    
    serve_sequences = [
        [0.5, 0.5, 0.4, 0.3, 0.2, 0.1],  # First serve
        [0.5, 0.5, 0.6, 0.7, 0.8, 0.9],  # Second serve
        [0.5, 0.5, 0.4, 0.3, 0.2, 0.1],  # Third serve
    ]
    
    for serve_num, positions in enumerate(serve_sequences):
        print(f"\nServe {serve_num + 1}:")
        for i, ball_x in enumerate(positions):
            ai._detect_serve_and_select_zone(ball_x)
            print(f"  Step {i+1}: Ball x={ball_x:.1f}, Zone={ai.current_hit_zone}")
    
    # Test zone consistency during a serve
    print("\n--- Testing Zone Consistency During Serve ---")
    
    # Reset AI state
    ai.zone_selected_for_serve = False
    ai.current_hit_zone = 'center'
    
    # Simulate a long rally with same zone
    rally_positions = [0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    print("Rally with consistent zone:")
    for i, ball_x in enumerate(rally_positions):
        ai._detect_serve_and_select_zone(ball_x)
        print(f"Step {i+1:2d}: Ball x={ball_x:.1f}, Zone={ai.current_hit_zone}")
    
    print("\nEvent-driven zone selection test completed!")
    print("\nExpected behavior:")
    print("- Zone selected only when ball is near center (serve)")
    print("- Zone remains consistent during entire rally")
    print("- New zone selected only for next serve")
    print("- No more jerky periodic zone changes")
    return True


if __name__ == "__main__":
    test_event_driven_zones()
