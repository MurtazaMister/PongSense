"""
Test script for fist-only paddle control.
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


def test_fist_control():
    """Test fist-only paddle control."""
    print("Testing fist-only paddle control...")
    
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
    
    print("Fist-only control test started!")
    print("You should see:")
    print("- Camera view at top (maintaining aspect ratio)")
    print("- Game area below")
    print("- Only FIST gestures control Player 1 paddle")
    print("- Open hand and other gestures are ignored")
    print("- AI controls Player 2 paddle")
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
            ball_y_norm = (game_state.ball_y - engine.camera_height) / engine.game_height
            ai_target = ai.next_y(ball_y_norm, 'medium')
            engine_input.p2_y = ai_target
            
            # Update game
            game_state = engine.tick(engine_input, voice_commands)
            
            # Render with integrated camera view
            camera_frame = vision_state.get('frame')
            engine.render_with_camera_view(camera_frame, vision_state)
            
            # Print status every second
            if i % 30 == 0:
                players_count = len(vision_state.get('players', []))
                fist_count = len([p for p in vision_state.get('players', []) if p.get('gesture') == 'fist'])
                print(f"Time {i//30}s: Hands={players_count}, Fists={fist_count}, "
                      f"P1_Y={engine_input.p1_y:.2f}, AI_Y={ai_target:.2f}, "
                      f"Score={game_state.score1}-{game_state.score2}")
            
            time.sleep(0.033)  # ~30fps
    
    except KeyboardInterrupt:
        print("\nStopping fist control test...")
    
    finally:
        tracker.stop()
        engine.stop_game()
        engine.quit()
    
    return True


if __name__ == "__main__":
    test_fist_control()
