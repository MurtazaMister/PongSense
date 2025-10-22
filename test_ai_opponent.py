"""
Test script for AI opponent functionality.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.logger import logger
from game.ai_opponent import AIOpponent


def test_ai_opponent():
    """Test AI opponent behavior."""
    print("Testing AI opponent...")
    
    # Initialize AI
    ai = AIOpponent()
    
    print("AI opponent test started!")
    print("Testing different ball positions and difficulties...")
    
    # Test different ball positions
    test_positions = [0.0, 0.25, 0.5, 0.75, 1.0]
    difficulties = ['easy', 'medium', 'hard']
    
    for difficulty in difficulties:
        print(f"\n--- Testing {difficulty.upper()} difficulty ---")
        for pos in test_positions:
            ai_target = ai.next_y(pos, difficulty)
            print(f"Ball at {pos:.2f} -> AI target: {ai_target:.2f}")
            time.sleep(0.1)  # Small delay to see progression
    
    print("\n--- Testing AI responsiveness ---")
    # Test rapid position changes
    positions = [0.0, 1.0, 0.5, 0.8, 0.2, 0.9, 0.1]
    for i, pos in enumerate(positions):
        ai_target = ai.next_y(pos, 'medium')
        print(f"Step {i+1}: Ball at {pos:.2f} -> AI target: {ai_target:.2f}")
        time.sleep(0.05)
    
    print("\nAI opponent test completed!")
    return True


if __name__ == "__main__":
    test_ai_opponent()
