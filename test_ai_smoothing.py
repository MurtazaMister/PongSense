"""
Test script for AI opponent smoothing functionality.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.logger import logger
from game.ai_opponent import AIOpponent


def test_ai_smoothing():
    """Test AI opponent smoothing behavior."""
    print("Testing AI opponent smoothing...")
    
    # Initialize AI
    ai = AIOpponent()
    
    print("AI smoothing test started!")
    print("Testing smooth movement with rapid position changes...")
    
    # Test rapid position changes to see smoothing effect
    positions = [0.0, 1.0, 0.5, 0.8, 0.2, 0.9, 0.1, 0.7, 0.3, 0.6]
    
    print("\n--- Testing AI Smoothing ---")
    print("Position changes -> AI response (should be smooth)")
    print("-" * 50)
    
    for i, pos in enumerate(positions):
        ai_target = ai.next_y(pos, 'medium')
        print(f"Step {i+1:2d}: Ball at {pos:.2f} -> AI target: {ai_target:.2f}")
        time.sleep(0.1)  # Small delay to see progression
    
    print("\n--- Testing Different Difficulties ---")
    difficulties = ['easy', 'medium', 'hard']
    test_pos = 0.7
    
    for difficulty in difficulties:
        print(f"\n{difficulty.upper()} difficulty:")
        for i in range(5):
            ai_target = ai.next_y(test_pos, difficulty)
            print(f"  Step {i+1}: AI target: {ai_target:.2f}")
            time.sleep(0.05)
    
    print("\nAI smoothing test completed!")
    return True


if __name__ == "__main__":
    test_ai_smoothing()
