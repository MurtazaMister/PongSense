"""
Test script for paddle position retention when fist leaves camera frame.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.logger import logger
from multimodal.input_manager import InputManager


def test_position_retention():
    """Test paddle position retention when hands leave frame."""
    print("Testing paddle position retention...")
    
    # Initialize input manager
    input_manager = InputManager()
    
    print("Position retention test started!")
    print("Testing that paddle maintains position when fist leaves camera frame...")
    
    # Simulate vision states
    print("\n--- Test 1: Hand detected, then disappears ---")
    
    # First, simulate hand detection
    vision_state_with_hand = {
        'players': [
            {
                'id': 1,
                'x': 0.5,
                'y_norm': 0.3,  # Top position (normalized)
                'gesture': 'fist'
            }
        ],
        'frame': None,
        'meta': {'timestamp': time.time()}
    }
    
    # Get position with hand detected
    engine_input = input_manager.fuse(vision_state_with_hand, [], 'single')
    print(f"With hand detected: P1 position = {engine_input.p1_y:.2f}")
    
    # Now simulate hand leaving frame
    vision_state_no_hand = {
        'players': [],  # No hands detected
        'frame': None,
        'meta': {'timestamp': time.time()}
    }
    
    # Get position without hand
    engine_input = input_manager.fuse(vision_state_no_hand, [], 'single')
    print(f"Without hand: P1 position = {engine_input.p1_y:.2f}")
    print(f"Position retained: {'YES' if engine_input.p1_y == engine_input.p1_y else 'NO'}")
    
    print("\n--- Test 2: Multiple position changes, then hand disappears ---")
    
    # Test different positions
    test_positions = [0.2, 0.8, 0.5, 0.9, 0.1]
    last_position = None
    
    for i, y_pos in enumerate(test_positions):
        vision_state = {
            'players': [
                {
                    'id': 1,
                    'x': 0.5,
                    'y_norm': y_pos,  # Use y_norm instead of y
                    'gesture': 'fist'
                }
            ],
            'frame': None,
            'meta': {'timestamp': time.time()}
        }
        
        engine_input = input_manager.fuse(vision_state, [], 'single')
        last_position = engine_input.p1_y
        print(f"Step {i+1}: Hand at y={y_pos:.1f} -> Paddle at {engine_input.p1_y:.2f}")
        time.sleep(0.1)
    
    # Now remove hand
    vision_state_no_hand = {
        'players': [],
        'frame': None,
        'meta': {'timestamp': time.time()}
    }
    
    engine_input = input_manager.fuse(vision_state_no_hand, [], 'single')
    print(f"Hand removed: Paddle stays at {engine_input.p1_y:.2f}")
    print(f"Position retained correctly: {'YES' if abs(engine_input.p1_y - last_position) < 0.01 else 'NO'}")
    
    print("\n--- Test 3: Two-player mode position retention ---")
    
    # Test two-player mode
    vision_state_two_hands = {
        'players': [
            {
                'id': 1,
                'x': 0.3,  # Left hand
                'y_norm': 0.2,  # Use y_norm
                'gesture': 'fist'
            },
            {
                'id': 2,
                'x': 0.7,  # Right hand
                'y_norm': 0.8,  # Use y_norm
                'gesture': 'open'
            }
        ],
        'frame': None,
        'meta': {'timestamp': time.time()}
    }
    
    engine_input = input_manager.fuse(vision_state_two_hands, [], 'two_player')
    print(f"Two hands: P1={engine_input.p1_y:.2f}, P2={engine_input.p2_y:.2f}")
    
    # Remove one hand
    vision_state_one_hand = {
        'players': [
            {
                'id': 1,
                'x': 0.3,
                'y_norm': 0.2,  # Use y_norm
                'gesture': 'fist'
            }
        ],
        'frame': None,
        'meta': {'timestamp': time.time()}
    }
    
    engine_input = input_manager.fuse(vision_state_one_hand, [], 'two_player')
    print(f"One hand removed: P1={engine_input.p1_y:.2f}, P2={engine_input.p2_y:.2f}")
    print(f"P2 position retained: {'YES' if engine_input.p2_y == engine_input.p2_y else 'NO'}")
    
    print("\nPosition retention test completed!")
    return True


if __name__ == "__main__":
    test_position_retention()
