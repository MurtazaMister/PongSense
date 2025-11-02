"""
Loading screen with animated progress bar.
"""

import pygame
import time
from typing import Callable, Optional
from utils.logger import logger


class LoadingScreen:
    """Loading screen with animated progress bar."""
    
    def __init__(self, window_width: int = 1280, window_height: int = 720):
        """Initialize loading screen.
        
        Args:
            window_width: Window width
            window_height: Window height
        """
        self.window_width = window_width
        self.window_height = window_height
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BLUE = (0, 100, 200)
        self.LIGHT_BLUE = (100, 150, 255)
        self.GREEN = (0, 200, 0)
        self.DARK_GREEN = (0, 150, 0)
        
        # Fonts
        pygame.font.init()
        self.title_font = pygame.font.Font(None, 72)
        self.text_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Progress bar dimensions
        self.progress_bar_width = 600
        self.progress_bar_height = 30
        self.progress_bar_border = 3
        
        # Animation
        self.animation_start_time = time.time()
        
        logger.info("LoadingScreen initialized")
    
    def render(self, screen: pygame.Surface, progress: float, message: str = "Loading...") -> None:
        """Render the loading screen.
        
        Args:
            screen: Pygame surface to render on
            progress: Progress from 0.0 to 1.0 (0 to 100%)
            message: Current loading message
        """
        # Clamp progress between 0 and 1
        progress = max(0.0, min(1.0, progress))
        
        # Clear screen
        screen.fill(self.BLACK)
        
        # Draw title
        title_text = self.title_font.render("PongSense", True, self.WHITE)
        title_rect = title_text.get_rect(center=(self.window_width // 2, 250))
        screen.blit(title_text, title_rect)
        
        # Draw loading message
        message_text = self.text_font.render(message, True, self.LIGHT_BLUE)
        message_rect = message_text.get_rect(center=(self.window_width // 2, 320))
        screen.blit(message_text, message_rect)
        
        # Calculate progress bar position (centered)
        progress_bar_x = (self.window_width - self.progress_bar_width) // 2
        progress_bar_y = 400
        
        # Draw progress bar background
        progress_bar_bg_rect = pygame.Rect(
            progress_bar_x - self.progress_bar_border,
            progress_bar_y - self.progress_bar_border,
            self.progress_bar_width + 2 * self.progress_bar_border,
            self.progress_bar_height + 2 * self.progress_bar_border
        )
        pygame.draw.rect(screen, self.WHITE, progress_bar_bg_rect)
        
        # Draw progress bar fill
        fill_width = int(self.progress_bar_width * progress)
        if fill_width > 0:
            fill_rect = pygame.Rect(progress_bar_x, progress_bar_y, fill_width, self.progress_bar_height)
            
            # Animated shimmer effect
            current_time = time.time()
            anim_offset = int((current_time - self.animation_start_time) * 200) % 300
            
            # Draw solid background
            pygame.draw.rect(screen, self.DARK_GREEN, fill_rect)
            
            # Draw animated shimmer highlight
            if fill_width > 50:  # Only show shimmer if bar is wide enough
                shimmer_width = min(60, fill_width // 3)
                shimmer_x = progress_bar_x + anim_offset - shimmer_width
                if shimmer_x < progress_bar_x + fill_width and shimmer_x + shimmer_width > progress_bar_x:
                    # Clamp shimmer to fill area
                    shimmer_start = max(progress_bar_x, shimmer_x)
                    shimmer_end = min(progress_bar_x + fill_width, shimmer_x + shimmer_width)
                    if shimmer_end > shimmer_start:
                        shimmer_rect = pygame.Rect(shimmer_start, progress_bar_y, shimmer_end - shimmer_start, self.progress_bar_height)
                        # Create a semi-transparent highlight surface
                        shimmer = pygame.Surface((shimmer_end - shimmer_start, self.progress_bar_height))
                        shimmer.set_alpha(180)
                        shimmer.fill(self.GREEN)
                        screen.blit(shimmer, (shimmer_start, progress_bar_y))
            
            # Draw bright edge on the leading edge
            edge_rect = pygame.Rect(
                progress_bar_x + fill_width - 3,
                progress_bar_y,
                3,
                self.progress_bar_height
            )
            pygame.draw.rect(screen, self.GREEN, edge_rect)
        
        # Draw progress percentage text
        progress_percent = int(progress * 100)
        percent_text = self.text_font.render(f"{progress_percent}%", True, self.WHITE)
        percent_rect = percent_text.get_rect(center=(
            self.window_width // 2,
            progress_bar_y + self.progress_bar_height + 40
        ))
        screen.blit(percent_text, percent_rect)
        
        # Draw tip/hint text
        tip_text = self.small_font.render("Preparing your game experience...", True, self.WHITE)
        tip_rect = tip_text.get_rect(center=(self.window_width // 2, self.window_height - 80))
        screen.blit(tip_text, tip_rect)
    
    def show_loading_with_progress(
        self,
        screen: pygame.Surface,
        progress_callback: Callable[[Callable[[float, str], None]], bool],
        fps: int = 60
    ) -> bool:
        """Show loading screen and run initialization with progress updates.
        
        Args:
            screen: Pygame surface to render on
            progress_callback: Function that takes an update function and performs initialization.
                               The update function signature is update_progress(progress: float, message: str)
                               Returns True if successful, False otherwise
            fps: Frames per second for the loading animation
        
        Returns:
            True if initialization was successful, False otherwise
        """
        clock = pygame.time.Clock()
        
        # Progress state
        current_progress = 0.0
        current_message = "Initializing..."
        
        # Define progress update function
        should_continue = True
        
        def update_progress(progress: float, message: str = ""):
            nonlocal current_progress, current_message, should_continue
            current_progress = progress
            if message:
                current_message = message
            
            # Handle events to prevent window freezing
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    should_continue = False
                    return False
            
            # Render loading screen
            self.render(screen, current_progress, current_message)
            pygame.display.flip()
            clock.tick(fps)
            
            return should_continue
        
        # Run initialization in a thread-safe manner
        # We'll call the callback which will call update_progress
        try:
            success = progress_callback(update_progress)
            return success
        except Exception as e:
            logger.error(f"Error during loading: {e}")
            return False

