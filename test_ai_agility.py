"""
Test script for AI agility improvements.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.logger import logger
from game.ai_opponent import AIOpponent


def test_ai_agility():
    """Test AI agility and responsiveness."""
    print("Testing AI agility improvements...")
    
    # Initialize AI
    ai = AIOpponent()
    
    print("AI agility test started!")
    print("Testing responsiveness with rapid position changes...")
    
    # Test rapid position changes to measure agility
    print("\n--- Testing AI Responsiveness ---")
    positions = [0.0, 1.0, 0.5, 0.8, 0.2, 0.9, 0.1, 0.7, 0.3, 0.6]
    
    print("Position changes -> AI response (should be more responsive now)")
    print("-" * 60)
    
    for i, pos in enumerate(positions):
        ai_target = ai.next_y(pos, 'medium')
        print(f"Step {i+1:2d}: Ball at {pos:.2f} -> AI target: {ai_target:.2f}")
        time.sleep(0.05)  # Faster test
    
    print("\n--- Testing Different Difficulties ---")
    difficulties = ['easy', 'medium', 'hard']
    test_pos = 0.7
    
    for difficulty in difficulties:
        print(f"\n{difficulty.upper()} difficulty:")
        for i in range(3):
            ai_target = ai.next_y(test_pos, difficulty)
            print(f"  Step {i+1}: AI target: {ai_target:.2f}")
            time.sleep(0.03)
    
    print("\n--- Testing Smoothness vs Responsiveness ---")
    # Test how quickly AI reaches target
    target_positions = [0.2, 0.8, 0.5]
    
    for target in target_positions:
        print(f"\nMoving to target {target:.1f}:")
        for i in range(5):
            ai_target = ai.next_y(target, 'medium')
            distance = abs(ai_target - target)
            print(f"  Step {i+1}: AI={ai_target:.2f}, Distance={distance:.3f}")
            time.sleep(0.05)
    
    print("\nAI agility test completed!")
    print("\nExpected improvements:")
    print("- Higher smoothing factor (0.4) = more responsive")
    print("- Lower imperfections = more precise")
    print("- Faster paddle speed = more agile movement")
    return True


if __name__ == "__main__":
    test_ai_agility()
