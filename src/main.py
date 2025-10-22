"""
Main application entry point for PongSense.
"""

import sys
import time
import threading
from typing import Optional

from vision.hand_tracker import HandTracker
from audio.voice_recognizer import VoiceRecognizer
from game.game_engine import GameEngine, EngineInput
from game.ai_opponent import AIOpponent
from multimodal.input_manager import InputManager
from utils.logger import logger
from utils.config import config


class PongSenseApp:
    """Main PongSense application."""
    
    def __init__(self):
        """Initialize PongSense application."""
        self.hand_tracker = HandTracker()
        self.voice_recognizer = VoiceRecognizer()
        self.game_engine = GameEngine()
        self.ai_opponent = AIOpponent()
        self.input_manager = InputManager()
        
        self.is_running = False
        self.game_mode = 'single'  # 'single' or 'two_player'
        
        logger.info("PongSense application initialized")
    
    def run(self) -> None:
        """Run the main application loop."""
        try:
            logger.info("Starting PongSense...")
            
            # Start subsystems
            if not self._start_subsystems():
                logger.error("Failed to start subsystems")
                return
            
            # Perform calibration
            self._perform_calibration()
            
            # Start game
            self.game_engine.start_game(self.game_mode)
            self.is_running = True
            
            # Main game loop
            self._main_loop()
            
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            self._cleanup()
    
    def _start_subsystems(self) -> bool:
        """Start all subsystems.
        
        Returns:
            True if all subsystems started successfully
        """
        success = True
        
        # Start hand tracking
        if not self.hand_tracker.start():
            logger.error("Failed to start hand tracker")
            success = False
        
        # Start voice recognition
        if not self.voice_recognizer.start():
            logger.error("Failed to start voice recognizer")
            success = False
        
        return success
    
    def _perform_calibration(self) -> None:
        """Perform quick calibration."""
        logger.info("Performing quick calibration...")
        
        # Sample hand positions for 3 seconds
        start_time = time.time()
        calibration_samples = []
        
        while time.time() - start_time < 3.0:
            vision_state = self.hand_tracker.get_state()
            calibration_samples.append(vision_state)
            time.sleep(0.1)
        
        # Perform calibration
        if calibration_samples:
            # Use the last sample for calibration
            last_state = calibration_samples[-1]
            self.input_manager.quick_calibration(last_state, duration=1.0)
        
        logger.info("Calibration completed")
    
    def _main_loop(self) -> None:
        """Main game loop."""
        logger.info("Starting main game loop...")
        
        target_fps = config.get('game.target_fps', 30)
        frame_time = 1.0 / target_fps
        
        while self.is_running:
            loop_start = time.time()
            
            try:
                # Get current states
                vision_state = self.hand_tracker.get_state()
                voice_commands = self.voice_recognizer.drain_commands()
                
                # Fuse inputs
                engine_input = self.input_manager.fuse(vision_state, voice_commands, self.game_mode)
                
                # Handle AI opponent in single player mode
                if self.game_mode == 'single':
                    # Get ball position from game state
                    game_state = self.game_engine.state
                    
                    # Predict AI paddle position based on ball position
                    # Normalize ball position within the game area (not including camera view)
                    ball_y_in_game_area = game_state.ball_y - self.game_engine.camera_height
                    ball_y_norm = ball_y_in_game_area / self.game_engine.game_height
                    ai_target = self.ai_opponent.next_y(ball_y_norm, 'medium')
                    engine_input.p2_y = ai_target
                
                # Update game
                game_state = self.game_engine.tick(engine_input, voice_commands)
                
                # Render with integrated camera view
                camera_frame = vision_state.get('frame')
                self.game_engine.render_with_camera_view(camera_frame, vision_state)
                
                # Check for exit conditions
                self._handle_events()
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            
            # Frame rate control
            elapsed = time.time() - loop_start
            sleep_time = frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _handle_events(self) -> None:
        """Handle application events."""
        # Check for pygame events
        import pygame
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_running = False
                elif event.key == pygame.K_SPACE:
                    # Toggle game mode
                    self.game_mode = 'two_player' if self.game_mode == 'single' else 'single'
                    self.game_engine.start_game(self.game_mode)
                    logger.info(f"Switched to {self.game_mode} mode")
    
    def _cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up...")
        
        self.is_running = False
        
        # Stop subsystems
        self.hand_tracker.stop()
        self.voice_recognizer.stop()
        self.game_engine.quit()
        
        logger.info("Cleanup completed")


def main():
    """Main entry point."""
    try:
        app = PongSenseApp()
        app.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
