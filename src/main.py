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
from ui.home_screen import HomeScreen, HowToPlayScreen
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
        
        # Set AI opponent reference in game engine for pseudo-paddle system
        self.game_engine.set_ai_opponent(self.ai_opponent)
        
        # Initialize UI components
        self.home_screen = HomeScreen(self.game_engine.window_width, self.game_engine.window_height)
        self.how_to_play_screen = HowToPlayScreen(self.game_engine.window_width, self.game_engine.window_height)
        
        self.is_running = False
        self.game_mode = 'single'  # 'single' or 'two_player'
        
        logger.info("PongSense application initialized")
    
    def run(self) -> None:
        """Run the main application loop."""
        try:
            logger.info("Starting PongSense...")
            
            # Show home screen first
            self._show_home_screen()
            
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            self._cleanup()
    
    def _show_home_screen(self) -> None:
        """Show home screen and handle user navigation."""
        logger.info("Showing home screen...")
        
        # Set up callbacks
        self.home_screen.set_callbacks(
            start_game_callback=self._start_game_from_home,
            how_to_play_callback=self._show_how_to_play
        )
        
        # Run home screen
        result = self.home_screen.run(self.game_engine.screen)
        
        if result == 'start_game':
            self._start_game_from_home()
        elif result == 'how_to_play':
            self._show_how_to_play()
        elif result == 'quit':
            logger.info("User chose to quit from home screen")
    
    def _start_game_from_home(self) -> None:
        """Start the game from home screen."""
        logger.info("Starting game from home screen...")
        
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
        result = self._main_loop()
        if result == 'home':
            # Cleanup everything and return to home
            self._cleanup_game_resources()
            self._show_home_screen()
    
    def _show_how_to_play(self) -> None:
        """Show how to play tutorial."""
        logger.info("Showing how to play tutorial...")
        
        result = self.how_to_play_screen.run(self.game_engine.screen)
        
        if result == 'back':
            # Return to home screen
            self._show_home_screen()
        elif result == 'quit':
            logger.info("User chose to quit from tutorial")
    
    def _start_subsystems(self) -> bool:
        """Start all subsystems.
        
        Returns:
            True if all subsystems started successfully
        """
        success = True
        
        # Check if subsystems are already running
        if hasattr(self.hand_tracker, 'is_running') and self.hand_tracker.is_running:
            logger.info("Hand tracker already running")
        elif not self.hand_tracker.start():
            logger.error("Failed to start hand tracker")
            success = False
        
        if hasattr(self.voice_recognizer, 'is_running') and self.voice_recognizer.is_running:
            logger.info("Voice recognizer already running")
        elif not self.voice_recognizer.start():
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
    
    def _main_loop(self):
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
                last_recognized_text = self.voice_recognizer.get_last_recognized_text()
                last_word_timestamp = self.voice_recognizer.get_last_word_timestamp()
                
                # Create dummy input for paused state
                engine_input = self.input_manager.fuse(vision_state, voice_commands, self.game_mode)
                
                # Handle AI opponent in single player mode
                if self.game_mode == 'single' and not self.game_engine.state.is_paused:
                    # Get ball position from game state
                    game_state = self.game_engine.state
                    
                    # Normalize ball positions for AI
                    ball_y_in_game_area = game_state.ball_y - self.game_engine.camera_height
                    ball_y_norm = ball_y_in_game_area / self.game_engine.game_height
                    ball_x_norm = game_state.ball_x / self.game_engine.window_width
                    
                    # Predict AI paddle position based on ball position
                    ai_target = self.ai_opponent.next_y(ball_y_norm, 'medium', ball_x_norm)
                    engine_input.p2_y = ai_target
                
                # Update game (tick will skip updates if paused)
                game_state = self.game_engine.tick(engine_input, voice_commands)
                
                # Check if exit was requested by voice command
                if game_state.exit_requested_by_voice:
                    # Reset the flag and return to home
                    game_state.exit_requested_by_voice = False
                    return 'home'
                
                # Render with integrated camera view
                camera_frame = vision_state.get('frame')
                self.game_engine.render_with_camera_view(camera_frame, vision_state, last_recognized_text, last_word_timestamp)
                
                # Check for exit conditions
                event_result = self._handle_events()
                if event_result == 'home':
                    # Exit the main loop immediately
                    return 'home'
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            
            # Frame rate control
            elapsed = time.time() - loop_start
            sleep_time = frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _handle_events(self):
        """Handle application events."""
        # Check for pygame events
        import pygame
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            elif event.type == pygame.KEYDOWN:
                # Handle pause menu if game is paused
                if self.game_engine.state.is_paused:
                    result = self.game_engine.handle_pause_menu_input(event.key)
                    if result == 'resume':
                        self.game_engine.resume_game()
                    elif result == 'end':
                        # End game and exit loop to return to home
                        return 'home'
                else:
                    # Normal game input handling
                    if event.key == pygame.K_ESCAPE:
                        # Toggle pause/resume
                        self.game_engine.pause_game()
                    elif event.key == pygame.K_SPACE:
                        # Toggle game mode (only when not paused)
                        self.game_mode = 'two_player' if self.game_mode == 'single' else 'single'
                        self.game_engine.start_game(self.game_mode)
                        logger.info(f"Switched to {self.game_mode} mode")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle mouse clicks on pause menu
                if self.game_engine.state.is_paused:
                    mouse_pos = pygame.mouse.get_pos()
                    result = self.game_engine.handle_pause_menu_input(None, mouse_pos)
                    if result == 'resume':
                        self.game_engine.resume_game()
                    elif result == 'end':
                        # End game and exit loop to return to home
                        return 'home'
        
        # Default: no special action
        return None
    
    def _cleanup_game_resources(self) -> None:
        """Cleanup all game resources and stop subsystems."""
        logger.info("Cleaning up game resources...")
        
        # Stop subsystems completely
        self.hand_tracker.stop()
        self.voice_recognizer.stop()
        
        # Stop the game
        self.game_engine.stop_game()
        
        logger.info("Game resources cleaned up - subsystems stopped")
    
    def _cleanup(self) -> None:
        """Cleanup all resources."""
        logger.info("Cleaning up...")
        
        self.is_running = False
        
        # Cleanup UI components
        self.how_to_play_screen.cleanup()
        
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
