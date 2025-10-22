"""
Game engine for PongSense with deterministic interface.
Implements tick(input_state, voice_cmds) -> GameState
"""

import pygame
import numpy as np
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from utils.logger import logger
from utils.config import config


@dataclass
class GameState:
    """Game state data structure."""
    ball_x: float
    ball_y: float
    ball_vx: float
    ball_vy: float
    paddle1_y: float
    paddle2_y: float
    score1: int
    score2: int
    game_running: bool
    game_mode: str  # 'single' or 'two_player'
    ball_speed_multiplier: float
    frame_count: int
    timestamp: float


@dataclass
class EngineInput:
    """Input state for game engine."""
    p1_y: float  # Player 1 normalized y position
    p2_y: float  # Player 2 normalized y position (or AI)
    speed_delta: float  # Speed change from voice commands
    meta: Dict[str, Any]


class GameEngine:
    """Main game engine with deterministic interface."""
    
    def __init__(self):
        """Initialize game engine."""
        # Configuration
        self.window_width = config.get('game.window_width', 1280)
        self.window_height = config.get('game.window_height', 720)
        self.target_fps = config.get('game.target_fps', 30)
        self.ball_speed_base = config.get('game.ball_speed_base', 5.0)
        self.paddle_speed = config.get('game.paddle_speed', 8.0)
        
        # Camera view configuration
        self.camera_height = 200  # Height for camera view at top
        self.game_height = self.window_height - self.camera_height  # Remaining height for game
        
        # Game state
        self.state = GameState(
            ball_x=self.window_width // 2,
            ball_y=self.camera_height + self.game_height // 2,  # Center in game area
            ball_vx=self.ball_speed_base,
            ball_vy=0,
            paddle1_y=self.camera_height + self.game_height // 2,
            paddle2_y=self.camera_height + self.game_height // 2,
            score1=0,
            score2=0,
            game_running=False,
            game_mode='single',
            ball_speed_multiplier=1.0,
            frame_count=0,
            timestamp=time.time()
        )
        
        # Game constants
        self.paddle_width = 20
        self.paddle_height = 100
        self.ball_radius = 10
        self.paddle_margin = 50
        
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("PongSense")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        
        # Clock for FPS control
        self.clock = pygame.time.Clock()
        
        # AI opponent reference for pseudo-paddle system
        self.ai_opponent = None
        
        logger.info("GameEngine initialized")
    
    def set_ai_opponent(self, ai_opponent) -> None:
        """Set AI opponent reference for pseudo-paddle system.
        
        Args:
            ai_opponent: AIOpponent instance
        """
        self.ai_opponent = ai_opponent
    
    def tick(self, input_state: EngineInput, voice_cmds: List[str]) -> GameState:
        """Update game state based on input and voice commands.
        
        Args:
            input_state: Current input state
            voice_cmds: List of voice commands
            
        Returns:
            Updated game state
        """
        try:
            # Update timestamp
            self.state.timestamp = time.time()
            self.state.frame_count += 1
            
            # Process voice commands
            self._process_voice_commands(voice_cmds)
            
            # Update paddles based on input
            self._update_paddles(input_state)
            
            # Update ball physics
            self._update_ball()
            
            # Check collisions
            self._check_collisions()
            
            # Check scoring
            self._check_scoring()
            
            # Control FPS
            self.clock.tick(self.target_fps)
            
            return self.state
            
        except Exception as e:
            logger.error(f"Error in game tick: {e}")
            return self.state
    
    def _process_voice_commands(self, voice_cmds: List[str]) -> None:
        """Process voice commands for ball speed control.
        
        Args:
            voice_cmds: List of voice commands
        """
        for cmd in voice_cmds:
            if cmd == 'faster':
                self.state.ball_speed_multiplier = min(2.0, self.state.ball_speed_multiplier + 0.2)
                logger.info(f"Ball speed increased to {self.state.ball_speed_multiplier}")
            elif cmd == 'slower':
                self.state.ball_speed_multiplier = max(0.5, self.state.ball_speed_multiplier - 0.2)
                logger.info(f"Ball speed decreased to {self.state.ball_speed_multiplier}")
    
    def _update_paddles(self, input_state: EngineInput) -> None:
        """Update paddle positions based on input."""
        # Convert normalized positions to screen coordinates within game area
        paddle1_target = self.camera_height + input_state.p1_y * self.game_height
        paddle2_target = self.camera_height + input_state.p2_y * self.game_height
        
        # Direct paddle movement - no smoothing/gliding
        # Player 1 paddle - direct control
        self.state.paddle1_y = paddle1_target
        
        # Player 2 paddle (or AI) - direct control
        self.state.paddle2_y = paddle2_target
        
        # Keep paddles in bounds (within game area)
        min_y = self.camera_height
        max_y = self.window_height - self.paddle_height
        self.state.paddle1_y = max(min_y, min(max_y, self.state.paddle1_y))
        self.state.paddle2_y = max(min_y, min(max_y, self.state.paddle2_y))
    
    def _update_ball(self) -> None:
        """Update ball position and velocity."""
        # Apply speed multiplier
        current_speed = self.ball_speed_base * self.state.ball_speed_multiplier
        
        # Update position
        self.state.ball_x += self.state.ball_vx
        self.state.ball_y += self.state.ball_vy
        
        # Normalize velocity to maintain consistent speed
        speed = np.sqrt(self.state.ball_vx**2 + self.state.ball_vy**2)
        if speed > 0:
            self.state.ball_vx = (self.state.ball_vx / speed) * current_speed
            self.state.ball_vy = (self.state.ball_vy / speed) * current_speed
    
    def _check_collisions(self) -> None:
        """Check ball collisions with paddles and walls."""
        # Wall collisions (top and bottom of game area)
        if self.state.ball_y <= self.camera_height + self.ball_radius:
            self.state.ball_y = self.camera_height + self.ball_radius
            self.state.ball_vy = abs(self.state.ball_vy)
        elif self.state.ball_y >= self.window_height - self.ball_radius:
            self.state.ball_y = self.window_height - self.ball_radius
            self.state.ball_vy = -abs(self.state.ball_vy)
        
        # Paddle collisions
        # Left paddle (Player 1)
        if (self.state.ball_x <= self.paddle_margin + self.paddle_width + self.ball_radius and
            self.state.ball_x >= self.paddle_margin - self.ball_radius and
            self.state.ball_y >= self.state.paddle1_y - self.ball_radius and
            self.state.ball_y <= self.state.paddle1_y + self.paddle_height + self.ball_radius and
            self.state.ball_vx < 0):
            
            self.state.ball_x = self.paddle_margin + self.paddle_width + self.ball_radius
            self.state.ball_vx = abs(self.state.ball_vx)
            
            # Add spin based on hit position
            hit_pos = (self.state.ball_y - self.state.paddle1_y) / self.paddle_height
            self.state.ball_vy += (hit_pos - 0.5) * 3
        
        # Right paddle (Player 2 or AI)
        elif (self.state.ball_x >= self.window_width - self.paddle_margin - self.paddle_width - self.ball_radius and
              self.state.ball_x <= self.window_width - self.paddle_margin + self.ball_radius and
              self.state.ball_y >= self.state.paddle2_y - self.ball_radius and
              self.state.ball_y <= self.state.paddle2_y + self.paddle_height + self.ball_radius and
              self.state.ball_vx > 0):
            
            # Check if AI is trying to hit from pseudo-paddle zone (miss)
            if self._should_ai_miss():
                # AI misses - ball passes through
                logger.info("AI missed the ball! (pseudo-paddle zone)")
                pass
            else:
                # Normal collision
                self.state.ball_x = self.window_width - self.paddle_margin - self.paddle_width - self.ball_radius
                self.state.ball_vx = -abs(self.state.ball_vx)
                
                # Add spin based on hit position
                hit_pos = (self.state.ball_y - self.state.paddle2_y) / self.paddle_height
                self.state.ball_vy += (hit_pos - 0.5) * 3
    
    def _should_ai_miss(self) -> bool:
        """Check if AI should miss based on pseudo-paddle hit zone.
        
        Returns:
            True if AI should miss, False otherwise
        """
        if self.ai_opponent is None:
            return False
        
        # Check if AI is trying to hit from pseudo-paddle zones
        current_zone = getattr(self.ai_opponent, 'current_hit_zone', 'center')
        
        # AI misses if trying to hit from pseudo-paddle zones
        return current_zone in ['pseudo_top', 'pseudo_bottom']
    
    def _check_scoring(self) -> None:
        """Check for scoring."""
        # Left side scoring (Player 2 scores)
        if self.state.ball_x < 0:
            self.state.score2 += 1
            self._reset_ball()
            logger.info(f"Player 2 scores! Score: {self.state.score1}-{self.state.score2}")
        
        # Right side scoring (Player 1 scores)
        elif self.state.ball_x > self.window_width:
            self.state.score1 += 1
            self._reset_ball()
            logger.info(f"Player 1 scores! Score: {self.state.score1}-{self.state.score2}")
    
    def _reset_ball(self) -> None:
        """Reset ball to center with random direction."""
        self.state.ball_x = self.window_width // 2
        self.state.ball_y = self.window_height // 2
        
        # Random direction
        angle = np.random.uniform(-np.pi/4, np.pi/4)
        speed = self.ball_speed_base * self.state.ball_speed_multiplier
        
        self.state.ball_vx = speed * np.cos(angle) * np.random.choice([-1, 1])
        self.state.ball_vy = speed * np.sin(angle)
    
    def _render(self) -> None:
        """Render the game frame."""
        # Clear screen
        self.screen.fill(self.BLACK)
        
        # Draw paddles
        pygame.draw.rect(self.screen, self.WHITE, 
                        (self.paddle_margin, self.state.paddle1_y, 
                         self.paddle_width, self.paddle_height))
        
        pygame.draw.rect(self.screen, self.WHITE,
                        (self.window_width - self.paddle_margin - self.paddle_width, 
                         self.state.paddle2_y, self.paddle_width, self.paddle_height))
        
        # Draw ball
        pygame.draw.circle(self.screen, self.WHITE,
                          (int(self.state.ball_x), int(self.state.ball_y)), 
                          self.ball_radius)
        
        # Draw center line
        pygame.draw.line(self.screen, self.WHITE,
                        (self.window_width // 2, 0),
                        (self.window_width // 2, self.window_height), 2)
        
        # Draw scores
        font = pygame.font.Font(None, 74)
        score1_text = font.render(str(self.state.score1), True, self.WHITE)
        score2_text = font.render(str(self.state.score2), True, self.WHITE)
        
        self.screen.blit(score1_text, (self.window_width // 4, 50))
        self.screen.blit(score2_text, (3 * self.window_width // 4, 50))
        
        # Draw speed indicator
        speed_text = font.render(f"Speed: {self.state.ball_speed_multiplier:.1f}x", True, self.WHITE)
        self.screen.blit(speed_text, (10, self.window_height - 50))
        
        # Update display
        pygame.display.flip()
    
    def render_with_camera_overlay(self, camera_frame, hand_data) -> None:
        """Render the game frame with camera overlay showing hand tracking."""
        # Clear screen
        self.screen.fill(self.BLACK)
        
        # Draw paddles
        pygame.draw.rect(self.screen, self.WHITE, 
                        (self.paddle_margin, self.state.paddle1_y, 
                         self.paddle_width, self.paddle_height))
        
        pygame.draw.rect(self.screen, self.WHITE,
                        (self.window_width - self.paddle_margin - self.paddle_width, 
                         self.state.paddle2_y, self.paddle_width, self.paddle_height))
        
        # Draw ball
        pygame.draw.circle(self.screen, self.WHITE,
                          (int(self.state.ball_x), int(self.state.ball_y)), 
                          self.ball_radius)
        
        # Draw center line
        pygame.draw.line(self.screen, self.WHITE,
                        (self.window_width // 2, 0),
                        (self.window_width // 2, self.window_height), 2)
        
        # Draw camera overlay on the side of controlled paddle
        if self.show_camera_overlay and camera_frame is not None:
            self._draw_camera_overlay(camera_frame, hand_data)
        
        # Draw scores
        font = pygame.font.Font(None, 74)
        score1_text = font.render(str(self.state.score1), True, self.WHITE)
        score2_text = font.render(str(self.state.score2), True, self.WHITE)
        
        self.screen.blit(score1_text, (self.window_width // 4, 50))
        self.screen.blit(score2_text, (3 * self.window_width // 4, 50))
        
        # Draw speed indicator
        speed_text = font.render(f"Speed: {self.state.ball_speed_multiplier:.1f}x", True, self.WHITE)
        self.screen.blit(speed_text, (10, self.window_height - 50))
        
        # Draw hand tracking status
        self._draw_hand_status(hand_data)
        
        # Update display
        pygame.display.flip()
    
    def render_with_camera_view(self, camera_frame, hand_data) -> None:
        """Render the game frame with integrated camera view at top."""
        # Clear screen
        self.screen.fill(self.BLACK)
        
        # Draw camera view at top
        if camera_frame is not None:
            self._draw_camera_view(camera_frame, hand_data)
        
        # Draw separator line
        pygame.draw.line(self.screen, self.WHITE,
                        (0, self.camera_height),
                        (self.window_width, self.camera_height), 2)
        
        # Draw paddles in game area
        pygame.draw.rect(self.screen, self.WHITE, 
                        (self.paddle_margin, self.state.paddle1_y, 
                         self.paddle_width, self.paddle_height))
        
        pygame.draw.rect(self.screen, self.WHITE,
                        (self.window_width - self.paddle_margin - self.paddle_width, 
                         self.state.paddle2_y, self.paddle_width, self.paddle_height))
        
        # Draw ball
        pygame.draw.circle(self.screen, self.WHITE,
                          (int(self.state.ball_x), int(self.state.ball_y)), 
                          self.ball_radius)
        
        # Draw center line in game area
        pygame.draw.line(self.screen, self.WHITE,
                        (self.window_width // 2, self.camera_height),
                        (self.window_width // 2, self.window_height), 2)
        
        # Draw scores
        font = pygame.font.Font(None, 74)
        score1_text = font.render(str(self.state.score1), True, self.WHITE)
        score2_text = font.render(str(self.state.score2), True, self.WHITE)
        
        self.screen.blit(score1_text, (self.window_width // 4, self.camera_height + 50))
        self.screen.blit(score2_text, (3 * self.window_width // 4, self.camera_height + 50))
        
        # Draw speed indicator
        speed_text = font.render(f"Speed: {self.state.ball_speed_multiplier:.1f}x", True, self.WHITE)
        self.screen.blit(speed_text, (10, self.window_height - 50))
        
        # Draw hand tracking status
        self._draw_hand_status(hand_data)
        
        # Update display
        pygame.display.flip()
    
    def _draw_camera_view(self, camera_frame, hand_data) -> None:
        """Draw camera view at the top of the screen."""
        try:
            import cv2
            import numpy as np
            
            # Calculate camera view size maintaining aspect ratio
            original_height, original_width = camera_frame.shape[:2]
            aspect_ratio = original_width / original_height
            
            # Use fixed height and calculate width to maintain aspect ratio
            camera_height = self.camera_height
            camera_width = int(camera_height * aspect_ratio)
            
            # Center the camera view horizontally
            camera_x = (self.window_width - camera_width) // 2
            
            # Resize camera frame maintaining aspect ratio
            resized_frame = cv2.resize(camera_frame, (camera_width, camera_height))
            
            # Draw hand highlights
            if hand_data and 'players' in hand_data:
                for player in hand_data['players']:
                    if 'x' in player and 'y' in player:
                        # Scale coordinates to camera view size
                        scale_x = camera_width / original_width
                        scale_y = camera_height / original_height
                        
                        hand_x = int(player['x'] * scale_x)
                        hand_y = int(player['y'] * scale_y)
                        
                        gesture = player.get('gesture', 'none')
                        if gesture == 'fist':
                            cv2.circle(resized_frame, (hand_x, hand_y), 30, (0, 0, 255), 3)  # Red
                            cv2.putText(resized_frame, f"FIST P{player['id']}", 
                                      (hand_x - 30, hand_y - 40), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        elif gesture == 'open':
                            cv2.circle(resized_frame, (hand_x, hand_y), 30, (0, 255, 0), 3)  # Green
                            cv2.putText(resized_frame, f"OPEN P{player['id']}", 
                                      (hand_x - 30, hand_y - 40), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        else:
                            cv2.circle(resized_frame, (hand_x, hand_y), 30, (0, 255, 255), 3)  # Yellow
                            cv2.putText(resized_frame, f"NONE P{player['id']}", 
                                      (hand_x - 30, hand_y - 40), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Add instructions
            cv2.putText(resized_frame, "Camera View - Use FIST or OPEN hand to control paddle", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Convert to pygame surface
            frame_rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(np.transpose(frame_rgb, (1, 0, 2)))
            
            # Draw camera view centered at top
            self.screen.blit(frame_surface, (camera_x, 0))
            
            # Draw border around camera view
            pygame.draw.rect(self.screen, self.WHITE, 
                           (camera_x - 2, 0, camera_width + 4, camera_height + 4), 2)
            
        except Exception as e:
            logger.warning(f"Error drawing camera view: {e}")
            # Draw placeholder if camera fails
            pygame.draw.rect(self.screen, (50, 50, 50), (0, 0, self.window_width, self.camera_height))
            font = pygame.font.Font(None, 36)
            error_text = font.render("Camera Error", True, self.WHITE)
            self.screen.blit(error_text, (self.window_width // 2 - 50, self.camera_height // 2))
    
    # Old camera overlay method removed - now using integrated camera view
    
    def _draw_hand_status(self, hand_data) -> None:
        """Draw hand tracking status information."""
        font = pygame.font.Font(None, 36)
        
        if hand_data and 'players' in hand_data:
            players = hand_data['players']
            status_text = f"Hands: {len(players)}"
            
            if players:
                for i, player in enumerate(players):
                    gesture = player.get('gesture', 'none')
                    y_norm = player.get('y_norm', 0.5)
                    status_text += f" | P{player['id']}: {gesture} ({y_norm:.2f})"
            
            text_surface = font.render(status_text, True, self.WHITE)
            self.screen.blit(text_surface, (10, self.window_height - 100))
        else:
            status_text = "No hands detected"
            text_surface = font.render(status_text, True, (255, 100, 100))
            self.screen.blit(text_surface, (10, self.window_height - 100))
    
    def start_game(self, mode: str = 'single') -> None:
        """Start a new game.
        
        Args:
            mode: Game mode ('single' or 'two_player')
        """
        self.state.game_mode = mode
        self.state.game_running = True
        self.state.score1 = 0
        self.state.score2 = 0
        self.state.ball_speed_multiplier = 1.0
        self._reset_ball()
        
        logger.info(f"Game started in {mode} mode")
    
    def stop_game(self) -> None:
        """Stop the current game."""
        self.state.game_running = False
        logger.info("Game stopped")
    
    def quit(self) -> None:
        """Quit the game engine."""
        pygame.quit()
        logger.info("Game engine quit")
