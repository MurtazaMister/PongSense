"""
Simple demo script to test PongSense basic functionality.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.logger import logger
from utils.config import config
from vision.hand_tracker import HandTracker
from audio.voice_recognizer import VoiceRecognizer
from game.game_engine import GameEngine, EngineInput
from game.ai_opponent import AIOpponent
from multimodal.input_manager import InputManager


def demo_hand_tracking():
    """Demo hand tracking functionality."""
    print("\n=== Hand Tracking Demo ===")
    
    tracker = HandTracker()
    
    if not tracker.start():
        print("Failed to start hand tracker")
        return False
    
    print("Hand tracker started. Show your hand to the camera...")
    print("Press Ctrl+C to stop")
    
    try:
        for i in range(50):  # Run for ~5 seconds at 10fps
            state = tracker.get_state()
            players = state['players']
            
            if players:
                print(f"Frame {i}: Detected {len(players)} hand(s)")
                for player in players:
                    print(f"  Player {player['id']}: y={player['y_norm']:.2f}, gesture={player['gesture']}")
            else:
                print(f"Frame {i}: No hands detected")
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nStopping hand tracker...")
    
    finally:
        tracker.stop()
    
    return True


def demo_voice_recognition():
    """Demo voice recognition functionality."""
    print("\n=== Voice Recognition Demo ===")
    
    recognizer = VoiceRecognizer()
    
    if not recognizer.start():
        print("Failed to start voice recognizer")
        return False
    
    print("Voice recognizer started. Say 'faster' or 'slower'...")
    print("Press Ctrl+C to stop")
    
    try:
        for i in range(100):  # Run for ~10 seconds
            commands = recognizer.drain_commands()
            if commands:
                print(f"Voice commands detected: {commands}")
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nStopping voice recognizer...")
    
    finally:
        recognizer.stop()
    
    return True


def demo_game_engine():
    """Demo game engine functionality."""
    print("\n=== Game Engine Demo ===")
    
    engine = GameEngine()
    ai = AIOpponent()
    input_manager = InputManager()
    
    # Start game
    engine.start_game('single')
    
    print("Game engine started. Running simulation...")
    
    try:
        for i in range(100):  # Run for ~3 seconds at 30fps
            # Simulate input
            vision_state = {'players': []}
            voice_commands = []
            
            # Create engine input
            engine_input = input_manager.fuse(vision_state, voice_commands, 'single')
            
            # Add AI input
            ai_target = ai.next_y(0.5, 'medium')
            engine_input.p2_y = ai_target
            
            # Update game
            game_state = engine.tick(engine_input, voice_commands)
            
            if i % 30 == 0:  # Print every second
                print(f"Frame {i}: Ball at ({game_state.ball_x:.1f}, {game_state.ball_y:.1f}), "
                      f"Score: {game_state.score1}-{game_state.score2}")
            
            time.sleep(0.033)  # ~30fps
    
    except KeyboardInterrupt:
        print("\nStopping game engine...")
    
    finally:
        engine.stop_game()
        engine.quit()
    
    return True


def demo_integration():
    """Demo integrated functionality."""
    print("\n=== Integration Demo ===")
    
    tracker = HandTracker()
    recognizer = VoiceRecognizer()
    engine = GameEngine()
    ai = AIOpponent()
    input_manager = InputManager()
    
    # Start subsystems
    if not tracker.start():
        print("Failed to start hand tracker")
        return False
    
    if not recognizer.start():
        print("Failed to start voice recognizer")
        tracker.stop()
        return False
    
    engine.start_game('single')
    
    print("All systems started. Playing PongSense...")
    print("Move your hand to control the paddle, say 'faster' or 'slower'")
    print("Press Ctrl+C to stop")
    
    try:
        for i in range(300):  # Run for ~10 seconds at 30fps
            # Get inputs
            vision_state = tracker.get_state()
            voice_commands = recognizer.drain_commands()
            
            # Process inputs
            engine_input = input_manager.fuse(vision_state, voice_commands, 'single')
            
            # Add AI input
            ai_target = ai.next_y(0.5, 'medium')
            engine_input.p2_y = ai_target
            
            # Update game
            game_state = engine.tick(engine_input, voice_commands)
            
            # Print status every second
            if i % 30 == 0:
                players_count = len(vision_state.get('players', []))
                print(f"Time {i//30}s: Players={players_count}, "
                      f"Score={game_state.score1}-{game_state.score2}, "
                      f"Speed={game_state.ball_speed_multiplier:.1f}x")
            
            time.sleep(0.033)  # ~30fps
    
    except KeyboardInterrupt:
        print("\nStopping all systems...")
    
    finally:
        tracker.stop()
        recognizer.stop()
        engine.stop_game()
        engine.quit()
    
    return True


def main():
    """Run demos."""
    print("PongSense Demo")
    print("=" * 40)
    
    demos = [
        ("Hand Tracking", demo_hand_tracking),
        ("Voice Recognition", demo_voice_recognition),
        ("Game Engine", demo_game_engine),
        ("Integration", demo_integration)
    ]
    
    for name, demo_func in demos:
        print(f"\nRunning {name} demo...")
        try:
            success = demo_func()
            if success:
                print(f"✓ {name} demo completed successfully")
            else:
                print(f"X {name} demo failed")
        except Exception as e:
            print(f"X {name} demo error: {e}")
    
    print("\n" + "=" * 40)
    print("Demo completed!")


if __name__ == "__main__":
    main()
