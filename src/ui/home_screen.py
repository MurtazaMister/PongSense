"""
Home screen UI for PongSense.
Provides start game button and how to play tutorial.
"""

import pygame
import cv2
import os
from typing import Optional, Callable
from utils.logger import logger


class HomeScreen:
    """Home screen with start game and how to play functionality."""
    
    def __init__(self, window_width: int = 1280, window_height: int = 720):
        """Initialize home screen.
        
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
        self.RED = (200, 0, 0)
        self.GRAY = (100, 100, 100)
        
        # Fonts
        pygame.font.init()
        self.title_font = pygame.font.Font(None, 72)
        self.button_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Button dimensions
        self.button_width = 300
        self.button_height = 80
        self.button_spacing = 100  # Equal spacing between button centers
        
        # Calculate button positions
        center_x = self.window_width // 2
        center_y = self.window_height // 2
        
        # Position buttons with equal spacing - centered around screen center
        self.start_button_rect = pygame.Rect(
            center_x - self.button_width // 2,
            center_y - self.button_spacing - self.button_height // 2,
            self.button_width,
            self.button_height
        )
        
        self.how_to_play_button_rect = pygame.Rect(
            center_x - self.button_width // 2,
            center_y - self.button_height // 2,
            self.button_width,
            self.button_height
        )
        
        self.quit_button_rect = pygame.Rect(
            center_x - self.button_width // 2,
            center_y + self.button_spacing - self.button_height // 2,
            self.button_width,
            self.button_height
        )
        
        # Callbacks
        self.on_start_game: Optional[Callable] = None
        self.on_how_to_play: Optional[Callable] = None
        self.on_toggle_fullscreen: Optional[Callable] = None
        
        # State
        self.is_running = True
        
        logger.info("HomeScreen initialized")
    
    def set_callbacks(self, start_game_callback: Callable, how_to_play_callback: Callable, 
                     toggle_fullscreen_callback: Optional[Callable] = None):
        """Set callback functions for button clicks.
        
        Args:
            start_game_callback: Function to call when start game is clicked
            how_to_play_callback: Function to call when how to play is clicked
            toggle_fullscreen_callback: Function to call when F11 is pressed (optional)
        """
        self.on_start_game = start_game_callback
        self.on_how_to_play = how_to_play_callback
        self.on_toggle_fullscreen = toggle_fullscreen_callback
    
    def run(self, screen: pygame.Surface) -> str:
        """Run the home screen.
        
        Args:
            screen: Pygame surface to render on
            
        Returns:
            'start_game', 'how_to_play', or 'mode_selected:{mode}' based on user selection
        """
        clock = pygame.time.Clock()
        
        while self.is_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit'
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return 'quit'
                    elif event.key == pygame.K_F11:
                        # Toggle fullscreen
                        if self.on_toggle_fullscreen:
                            self.on_toggle_fullscreen()
                            # Update window dimensions after toggle
                            self.window_width, self.window_height = screen.get_size()
                            # Recalculate button positions with new dimensions
                            center_x = self.window_width // 2
                            center_y = self.window_height // 2
                            self.start_button_rect = pygame.Rect(
                                center_x - self.button_width // 2,
                                center_y - self.button_spacing - self.button_height // 2,
                                self.button_width,
                                self.button_height
                            )
                            self.how_to_play_button_rect = pygame.Rect(
                                center_x - self.button_width // 2,
                                center_y - self.button_height // 2,
                                self.button_width,
                                self.button_height
                            )
                            self.quit_button_rect = pygame.Rect(
                                center_x - self.button_width // 2,
                                center_y + self.button_spacing - self.button_height // 2,
                                self.button_width,
                                self.button_height
                            )
                        else:
                            # Fallback if no callback provided
                            try:
                                pygame.display.toggle_fullscreen()
                                # Update window dimensions
                                self.window_width, self.window_height = screen.get_size()
                            except Exception:
                                pass  # Silently fail if fullscreen toggle not supported
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mouse_pos = pygame.mouse.get_pos()
                        if self.start_button_rect.collidepoint(mouse_pos):
                            # Show mode selection overlay
                            selected_mode = self._show_mode_selection(screen)
                            if selected_mode:
                                return f'mode_selected:{selected_mode}'
                            # If user cancelled, continue showing home screen
                        elif self.how_to_play_button_rect.collidepoint(mouse_pos):
                            return 'how_to_play'
                        elif self.quit_button_rect.collidepoint(mouse_pos):
                            return 'quit'
            
            # Render home screen
            self._render(screen)
            pygame.display.flip()
            clock.tick(60)
        
        return 'quit'
    
    def _render(self, screen: pygame.Surface):
        """Render the home screen."""
        # Clear screen
        screen.fill(self.BLACK)
        
        # Draw title
        title_text = self.title_font.render("PongSense", True, self.WHITE)
        title_rect = title_text.get_rect(center=(self.window_width // 2, 150))
        screen.blit(title_text, title_rect)
        
        # Draw subtitle
        subtitle_text = self.text_font.render("Gesture-Controlled Pong Game", True, self.LIGHT_BLUE)
        subtitle_rect = subtitle_text.get_rect(center=(self.window_width // 2, 200))
        screen.blit(subtitle_text, subtitle_rect)
        
        # Draw start game button
        self._draw_button(screen, self.start_button_rect, "Start Game", self.GREEN)
        
        # Draw how to play button
        self._draw_button(screen, self.how_to_play_button_rect, "How to Play", self.BLUE)
        
        # Draw quit button
        self._draw_button(screen, self.quit_button_rect, "Quit Game", self.RED)
        
        # Draw instructions
        instructions = [
            "Press ESC to quit",
            "Click buttons to navigate"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, self.GRAY)
            screen.blit(text, (20, self.window_height - 60 + i * 20))
    
    def _draw_button(self, screen: pygame.Surface, rect: pygame.Rect, text: str, color: tuple):
        """Draw a button with text."""
        # Check if mouse is hovering
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = rect.collidepoint(mouse_pos)
        
        # Button color
        button_color = self.LIGHT_BLUE if is_hovered else color
        
        # Draw button background
        pygame.draw.rect(screen, button_color, rect)
        pygame.draw.rect(screen, self.WHITE, rect, 3)
        
        # Draw button text
        text_surface = self.button_font.render(text, True, self.WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)
    
    def _show_mode_selection(self, screen: pygame.Surface) -> Optional[str]:
        """Show mode selection overlay.
        
        Args:
            screen: Pygame surface to render on
            
        Returns:
            Selected mode ('single' or 'two_player'), or None if cancelled
        """
        clock = pygame.time.Clock()
        
        # Mode selection button dimensions
        mode_button_width = 350
        mode_button_height = 100
        mode_button_spacing = 30
        
        # Calculate button positions (centered vertically)
        center_x = self.window_width // 2
        center_y = self.window_height // 2
        
        ai_button_rect = pygame.Rect(
            center_x - mode_button_width // 2,
            center_y - mode_button_height - mode_button_spacing // 2,
            mode_button_width,
            mode_button_height
        )
        
        two_player_button_rect = pygame.Rect(
            center_x - mode_button_width // 2,
            center_y + mode_button_spacing // 2,
            mode_button_width,
            mode_button_height
        )
        
        # Close button (X) in top right
        close_button_size = 40
        close_button_rect = pygame.Rect(
            self.window_width - close_button_size - 20,
            20,
            close_button_size,
            close_button_size
        )
        
        # Fade animation state
        fade_alpha = 0
        fade_speed = 15
        max_fade_alpha = 230  # Increased for better readability
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_F11:
                        # Toggle fullscreen
                        if self.on_toggle_fullscreen:
                            self.on_toggle_fullscreen()
                        else:
                            # Fallback if no callback provided
                            try:
                                pygame.display.toggle_fullscreen()
                            except Exception:
                                pass  # Silently fail if fullscreen toggle not supported
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mouse_pos = pygame.mouse.get_pos()
                        if close_button_rect.collidepoint(mouse_pos):
                            return None
                        elif ai_button_rect.collidepoint(mouse_pos):
                            return 'single'
                        elif two_player_button_rect.collidepoint(mouse_pos):
                            return 'two_player'
            
            # Update fade animation
            if fade_alpha < max_fade_alpha:
                fade_alpha = min(max_fade_alpha, fade_alpha + fade_speed)
            
            # Render
            self._render_mode_selection(
                screen, fade_alpha,
                ai_button_rect, two_player_button_rect, close_button_rect
            )
            pygame.display.flip()
            clock.tick(60)
    
    def _render_mode_selection(self, screen: pygame.Surface, fade_alpha: int,
                              ai_button_rect: pygame.Rect, two_player_button_rect: pygame.Rect,
                              close_button_rect: pygame.Rect):
        """Render mode selection overlay.
        
        Args:
            screen: Pygame surface to render on
            fade_alpha: Alpha value for background fade (0-255)
            ai_button_rect: Rectangle for AI mode button
            two_player_button_rect: Rectangle for 2-player mode button
            close_button_rect: Rectangle for close button
        """
        # First render the background home screen
        self._render(screen)
        
        # Draw background overlay (faded)
        overlay = pygame.Surface((self.window_width, self.window_height))
        overlay.set_alpha(fade_alpha)
        overlay.fill(self.BLACK)
        screen.blit(overlay, (0, 0))
        
        # Draw title
        title_text = self.title_font.render("Select Game Mode", True, self.WHITE)
        title_rect = title_text.get_rect(center=(self.window_width // 2, 150))
        screen.blit(title_text, title_rect)
        
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        self._draw_mode_button(screen, ai_button_rect, "Play with AI", self.GREEN, 
                              mouse_pos)
        self._draw_mode_button(screen, two_player_button_rect, "2-Player Mode", self.BLUE, 
                              mouse_pos)
        
        # Draw close button (X)
        is_hovered = close_button_rect.collidepoint(mouse_pos)
        close_color = self.RED if is_hovered else self.GRAY
        pygame.draw.rect(screen, close_color, close_button_rect)
        pygame.draw.rect(screen, self.WHITE, close_button_rect, 2)
        
        # Draw X symbol
        x_font = pygame.font.Font(None, 32)
        x_text = x_font.render("×", True, self.WHITE)
        x_rect = x_text.get_rect(center=close_button_rect.center)
        screen.blit(x_text, x_rect)
    
    def _draw_mode_button(self, screen: pygame.Surface, rect: pygame.Rect, 
                         text: str, color: tuple, mouse_pos: tuple):
        """Draw a mode selection button.
        
        Args:
            screen: Pygame surface to render on
            rect: Button rectangle
            text: Button text
            color: Base button color
            mouse_pos: Current mouse position
        """
        # Check if mouse is hovering
        is_hovered = rect.collidepoint(mouse_pos)
        
        # Button color
        button_color = self.LIGHT_BLUE if is_hovered else color
        
        # Draw button background
        pygame.draw.rect(screen, button_color, rect)
        pygame.draw.rect(screen, self.WHITE, rect, 3)
        
        # Draw button text
        text_surface = self.button_font.render(text, True, self.WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)


class HowToPlayScreen:
    """How to play tutorial screen with slides."""
    
    def __init__(self, window_width: int = 1280, window_height: int = 720):
        """Initialize how to play screen.
        
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
        self.RED = (200, 0, 0)
        self.GRAY = (100, 100, 100)
        
        # Fonts
        pygame.font.init()
        self.title_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Slides data
        self.slides = [
            {
                'title': 'Slide 1: Hand Control',
                'video_path': os.path.join('assets', 'videos', 'game_control.mp4'),
                'text': 'Close your fist and move your arm up and down to control the paddle',
                'description': 'Use your hand gestures to control the paddle position. Make a fist and move your arm vertically to move the paddle up and down.'
            },
            {
                'title': 'Slide 2: Speed Control',
                'video_path': None,
                'text': 'Voice: "faster"/"slower" | Keyboard: W/↑ increase, S/↓ decrease',
                'description': 'Control game speed with voice ("faster"/"slower") or keyboard (W/S or Up/Down arrows) to increase/decrease ball speed.'
            },
            {
                'title': 'Slide 3: Pause & Resume',
                'video_path': None,
                'text': 'Say "pause" or "stop" to pause, "resume" or "play" to continue',
                'description': 'Voice commands work in-game: "pause"/"stop" pauses the game with menu, "resume"/"play" unpauses. Say "exit"/"quit"/"leave" when paused to return to home.'
            }
        ]
        
        self.current_slide = 0
        
        # Video player
        self.video_capture = None
        self.video_frame = None
        self.video_playing = False
        self.video_ended = False
        self.video_total_frames = 0
        self.video_current_frame = 0
        
        # Button dimensions
        self.button_width = 120
        self.button_height = 50
        
        # Calculate button positions
        self.back_button_rect = pygame.Rect(50, self.window_height - 80, self.button_width, self.button_height)
        self.next_button_rect = pygame.Rect(self.window_width - 170, self.window_height - 80, self.button_width, self.button_height)
        
        # Video area for click detection
        self.video_area_rect = None
        
        logger.info("HowToPlayScreen initialized")
    
    def run(self, screen: pygame.Surface) -> str:
        """Run the how to play screen.
        
        Args:
            screen: Pygame surface to render on
            
        Returns:
            'back' to return to home screen
        """
        # Reset to first slide when entering tutorial
        self.current_slide = 0
        self._load_video()
        if self.slides[self.current_slide]['video_path'] and self.video_capture is not None:
            self._start_video()
        
        clock = pygame.time.Clock()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit'
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return 'back'
                    elif event.key == pygame.K_LEFT:
                        self._previous_slide()
                    elif event.key == pygame.K_RIGHT:
                        self._next_slide()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mouse_pos = pygame.mouse.get_pos()
                        logger.debug(f"Mouse clicked at {mouse_pos}")
                        if self.back_button_rect.collidepoint(mouse_pos):
                            return 'back'
                        elif self.next_button_rect.collidepoint(mouse_pos):
                            self._next_slide()
                        elif self.video_area_rect and self.video_area_rect.collidepoint(mouse_pos):
                            self._toggle_video()
                        else:
                            logger.debug("No button clicked")
            
            # Update video if playing
            if self.video_playing and self.video_capture is not None:
                try:
                    ret, frame = self.video_capture.read()
                    if ret:
                        self.video_frame = frame
                        self.video_current_frame += 1
                        # Log progress every 30 frames
                        if self.video_current_frame % 30 == 0:
                            logger.debug(f"Video progress: {self.video_current_frame}/{self.video_total_frames} frames")
                    else:
                        # Video ended - loop it automatically
                        logger.info(f"Video ended - looping (played {self.video_current_frame} frames)")
                        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        self.video_current_frame = 0
                except Exception as e:
                    logger.error(f"Error reading video frame: {e}")
                    self.video_playing = False
                    self.video_ended = True
            
            # Render current slide
            self._render(screen)
            pygame.display.flip()
            clock.tick(30)
        
        return 'back'
    
    def _render(self, screen: pygame.Surface):
        """Render the current slide."""
        # Clear screen
        screen.fill(self.BLACK)
        
        slide = self.slides[self.current_slide]
        
        # Draw title
        title_text = self.title_font.render(slide['title'], True, self.WHITE)
        title_rect = title_text.get_rect(center=(self.window_width // 2, 50))
        screen.blit(title_text, title_rect)
        
        # Draw video or placeholder
        if slide['video_path'] is not None and os.path.exists(slide['video_path']):
            self._draw_video_area(screen)
        else:
            self._draw_placeholder(screen)
        
        # Draw text content
        self._draw_text_content(screen, slide)
        
        # Draw navigation buttons
        self._draw_navigation_buttons(screen)
        
        # Draw slide indicator
        slide_text = self.small_font.render(f"Slide {self.current_slide + 1} of {len(self.slides)}", True, self.GRAY)
        screen.blit(slide_text, (self.window_width // 2 - 50, self.window_height - 30))
    
    def _draw_video_area(self, screen: pygame.Surface):
        """Draw video area."""
        video_width = 640
        video_height = 360
        video_x = (self.window_width - video_width) // 2
        video_y = 120
        
        # Set video area rect for click detection
        self.video_area_rect = pygame.Rect(video_x, video_y, video_width, video_height)
        
        # Check if mouse is hovering over video
        mouse_pos = pygame.mouse.get_pos()
        is_hovering = self.video_area_rect.collidepoint(mouse_pos)
        
        # Draw video frame if available
        if self.video_frame is not None:
            try:
                # Resize video frame
                resized_frame = cv2.resize(self.video_frame, (video_width, video_height))
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                
                # Convert to pygame surface
                frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                
                # Draw video frame
                screen.blit(frame_surface, (video_x, video_y))
                
            except Exception as e:
                logger.warning(f"Error drawing video frame: {e}")
                self._draw_video_placeholder(screen, video_x, video_y, video_width, video_height)
        else:
            self._draw_video_placeholder(screen, video_x, video_y, video_width, video_height)
        
        # Draw video border
        pygame.draw.rect(screen, self.WHITE, (video_x - 2, video_y - 2, video_width + 4, video_height + 4), 2)
        
        # Draw hover overlay with pause/play button
        if is_hovering and not self.video_ended:
            # Semi-transparent overlay
            overlay = pygame.Surface((video_width, video_height))
            overlay.set_alpha(128)
            overlay.fill(self.BLACK)
            screen.blit(overlay, (video_x, video_y))
            
            # Draw pause/play icon
            icon_size = 60
            icon_x = video_x + video_width // 2 - icon_size // 2
            icon_y = video_y + video_height // 2 - icon_size // 2
            
            if self.video_playing:
                # Draw pause icon (two vertical bars)
                bar_width = 8
                bar_height = 40
                pygame.draw.rect(screen, self.WHITE, (icon_x + 10, icon_y + 10, bar_width, bar_height))
                pygame.draw.rect(screen, self.WHITE, (icon_x + 30, icon_y + 10, bar_width, bar_height))
            else:
                # Draw play icon (triangle)
                points = [
                    (icon_x + 15, icon_y + 10),
                    (icon_x + 15, icon_y + 50),
                    (icon_x + 45, icon_y + 30)
                ]
                pygame.draw.polygon(screen, self.WHITE, points)
        
        
    
    def _draw_video_placeholder(self, screen: pygame.Surface, x: int, y: int, width: int, height: int):
        """Draw video placeholder."""
        pygame.draw.rect(screen, self.GRAY, (x, y, width, height))
        
        # Draw play button icon
        play_text = self.text_font.render("Click Play to Start Video", True, self.WHITE)
        play_rect = play_text.get_rect(center=(x + width // 2, y + height // 2))
        screen.blit(play_text, play_rect)
    
    def _draw_placeholder(self, screen: pygame.Surface):
        """Draw placeholder for slides without video."""
        placeholder_width = 640
        placeholder_height = 360
        placeholder_x = (self.window_width - placeholder_width) // 2
        placeholder_y = 120
        
        pygame.draw.rect(screen, self.GRAY, (placeholder_x, placeholder_y, placeholder_width, placeholder_height))
        
        # Draw icon or text based on current slide
        slide = self.slides[self.current_slide]
        if slide['title'] == 'Slide 2: Speed Control':
            icon_text = self.text_font.render("🎤 Speed Commands", True, self.WHITE)
        elif slide['title'] == 'Slide 3: Pause & Resume':
            icon_text = self.text_font.render("🎤 Game Control", True, self.WHITE)
        else:
            icon_text = self.text_font.render("Voice Commands", True, self.WHITE)
        
        icon_rect = icon_text.get_rect(center=(placeholder_x + placeholder_width // 2, placeholder_y + placeholder_height // 2))
        screen.blit(icon_text, icon_rect)
    
    def _draw_text_content(self, screen: pygame.Surface, slide: dict):
        """Draw text content for the slide."""
        text_y = 500
        
        # Main instruction text
        main_text = self.text_font.render(slide['text'], True, self.WHITE)
        main_rect = main_text.get_rect(center=(self.window_width // 2, text_y))
        screen.blit(main_text, main_rect)
        
        # Description text
        if 'description' in slide:
            desc_text = self.small_font.render(slide['description'], True, self.GRAY)
            desc_rect = desc_text.get_rect(center=(self.window_width // 2, text_y + 50))
            screen.blit(desc_text, desc_rect)
    
    def _draw_navigation_buttons(self, screen: pygame.Surface):
        """Draw navigation buttons."""
        # Back button
        self._draw_button(screen, self.back_button_rect, "Back", self.RED)
        
        # Next button
        if self.current_slide < len(self.slides) - 1:
            self._draw_button(screen, self.next_button_rect, "Next", self.BLUE)
    
    def _draw_button(self, screen: pygame.Surface, rect: pygame.Rect, text: str, color: tuple):
        """Draw a button with text."""
        # Check if mouse is hovering
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = rect.collidepoint(mouse_pos)
        
        # Button color
        button_color = (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50)) if is_hovered else color
        
        # Draw button background
        pygame.draw.rect(screen, button_color, rect)
        pygame.draw.rect(screen, self.WHITE, rect, 2)
        
        # Draw button text
        text_surface = self.small_font.render(text, True, self.WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)
    
    def _next_slide(self):
        """Go to next slide."""
        if self.current_slide < len(self.slides) - 1:
            self._stop_video()
            self.current_slide += 1
            self._load_video()
            if self.slides[self.current_slide]['video_path'] and self.video_capture is not None:
                self._start_video()  # Auto-start video
    
    def _previous_slide(self):
        """Go to previous slide."""
        if self.current_slide > 0:
            self._stop_video()
            self.current_slide -= 1
            self._load_video()
            if self.slides[self.current_slide]['video_path'] and self.video_capture is not None:
                self._start_video()  # Auto-start video
    
    def _toggle_video(self):
        """Toggle video play/pause."""
        if self.slides[self.current_slide]['video_path'] and self.video_capture is not None:
            if self.video_playing:
                self._stop_video()
            else:
                self._start_video()
    
    def _load_video(self):
        """Load video for current slide."""
        slide = self.slides[self.current_slide]
        if slide['video_path'] is not None and os.path.exists(slide['video_path']):
            try:
                # Release previous video capture if exists
                if self.video_capture is not None:
                    self.video_capture.release()
                
                self.video_capture = cv2.VideoCapture(slide['video_path'])
                
                # Check if video capture is working
                if not self.video_capture.isOpened():
                    logger.error(f"Failed to open video: {slide['video_path']}")
                    self.video_capture = None
                    return
                
                self.video_frame = None
                self.video_playing = False
                self.video_ended = False
                self.video_current_frame = 0
                # Get total frames for progress tracking
                self.video_total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
                video_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
                video_duration = self.video_total_frames / video_fps if video_fps > 0 else 0
                logger.info(f"Loaded video: {slide['video_path']} ({self.video_total_frames} frames, {video_fps:.1f} FPS, {video_duration:.1f}s duration)")
            except Exception as e:
                logger.error(f"Error loading video: {e}")
                self.video_capture = None
        else:
            if slide['video_path'] is None:
                logger.debug("No video for this slide")
            else:
                logger.warning(f"Video file not found: {slide['video_path']}")
            self.video_capture = None
    
    def _start_video(self):
        """Start video playback."""
        if self.video_capture is not None:
            self.video_playing = True
            logger.info("Video started")
    
    def _stop_video(self):
        """Stop video playback."""
        self.video_playing = False
        logger.info("Video stopped")
    
    
    def cleanup(self):
        """Cleanup resources."""
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        logger.info("HowToPlayScreen cleaned up")
