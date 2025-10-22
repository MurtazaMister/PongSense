"""
Test script for improved PongSense functionality.
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
from ui.camera_window import CameraWindow


def test_improvements():
    """Test the improved functionality."""
    print("Testing improved PongSense...")
    
    # Initialize components
    tracker = HandTracker()
    engine = GameEngine()
    ai = AIOpponent()
    input_manager = InputManager()
    camera_window = CameraWindow()
    
    # Start subsystems
    if not tracker.start():
        print("Failed to start hand tracker")
        return False
    
    # Start camera window in separate thread
    import threading
    camera_thread = threading.Thread(target=camera_window.show, daemon=True)
    camera_thread.start()
    
    engine.start_game('single')
    
    print("Improved PongSense test started!")
    print("You should see:")
    print("- Main game window with paddles and ball")
    print("- Separate camera window showing your hand")
    print("- AI paddle should move to follow the ball")
    print("- Your paddle should follow your hand exactly (no gliding)")
    print("- Hand at top edge = paddle at top edge")
    print("- Hand at bottom edge = paddle at bottom edge")
    print("Press Ctrl+C to stop")
    
    try:
        for i in range(300):  # Run for ~10 seconds at 30fps
            # Get vision state
            vision_state = tracker.get_state()
            voice_commands = []
            
            # Process inputs
            engine_input = input_manager.fuse(vision_state, voice_commands, 'single')
            
            # Add AI input based on ball position
            game_state = engine.state
            ball_y_norm = game_state.ball_y / engine.window_height
            ai_target = ai.next_y(ball_y_norm, 'medium')
            engine_input.p2_y = ai_target
            
            # Update camera window
            camera_frame = vision_state.get('frame')
            camera_window.update_frame(camera_frame, vision_state)
            
            # Update game
            game_state = engine.tick(engine_input, voice_commands)
            
            # Render game
            engine._render()
            
            # Print status every second
            if i % 30 == 0:
                players_count = len(vision_state.get('players', []))
                print(f"Time {i//30}s: Hands={players_count}, "
                      f"Ball Y={ball_y_norm:.2f}, AI Target={ai_target:.2f}, "
                      f"Score={game_state.score1}-{game_state.score2}")
            
            time.sleep(0.033)  # ~30fps
    
    except KeyboardInterrupt:
        print("\nStopping improved test...")
    
    finally:
        tracker.stop()
        camera_window.stop()
        engine.stop_game()
        engine.quit()
    
    return True


if __name__ == "__main__":
    test_improvements()
