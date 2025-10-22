"""
Test script for camera overlay functionality.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.logger import logger
from vision.hand_tracker import HandTracker
from game.game_engine import GameEngine, EngineInput
from game.ai_opponent import AIOpponent
from multimodal.input_manager import InputManager


def test_camera_overlay():
    """Test camera overlay functionality."""
    print("Testing camera overlay...")
    
    # Initialize components
    tracker = HandTracker()
    engine = GameEngine()
    ai = AIOpponent()
    input_manager = InputManager()
    
    # Start subsystems
    if not tracker.start():
        print("Failed to start hand tracker")
        return False
    
    engine.start_game('single')
    
    print("Camera overlay test started. Show your hand to the camera...")
    print("You should see:")
    print("- Game screen with paddles and ball")
    print("- Camera overlay in top-right corner")
    print("- Your hand highlighted with landmarks")
    print("- Fist detection (red circle)")
    print("- Hand tracking status at bottom")
    print("Press Ctrl+C to stop")
    
    try:
        for i in range(300):  # Run for ~10 seconds at 30fps
            # Get vision state
            vision_state = tracker.get_state()
            voice_commands = []
            
            # Process inputs
            engine_input = input_manager.fuse(vision_state, voice_commands, 'single')
            
            # Add AI input
            ai_target = ai.next_y(0.5, 'medium')
            engine_input.p2_y = ai_target
            
            # Update game
            game_state = engine.tick(engine_input, voice_commands)
            
            # Render with camera overlay
            camera_frame = vision_state.get('frame')
            engine.render_with_camera_overlay(camera_frame, vision_state)
            
            # Print status every second
            if i % 30 == 0:
                players_count = len(vision_state.get('players', []))
                print(f"Time {i//30}s: Hands detected: {players_count}")
            
            time.sleep(0.033)  # ~30fps
    
    except KeyboardInterrupt:
        print("\nStopping camera overlay test...")
    
    finally:
        tracker.stop()
        engine.stop_game()
        engine.quit()
    
    return True


if __name__ == "__main__":
    test_camera_overlay()
