"""
Separate camera window for hand tracking visualization.
"""

import cv2
import numpy as np
import threading
import time
from typing import Optional, Dict, Any

from utils.logger import logger


class CameraWindow:
    """Separate window for camera feed with hand tracking."""
    
    def __init__(self, window_name: str = "PongSense Camera"):
        """Initialize camera window."""
        self.window_name = window_name
        self.is_running = False
        self.current_frame = None
        self.hand_data = None
        self._lock = threading.Lock()
        
        # Create window
        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
        
        logger.info(f"Camera window '{window_name}' initialized")
    
    def update_frame(self, frame: np.ndarray, hand_data: Dict[str, Any]) -> None:
        """Update the camera frame and hand data.
        
        Args:
            frame: Camera frame with hand landmarks
            hand_data: Hand tracking data
        """
        with self._lock:
            self.current_frame = frame.copy() if frame is not None else None
            self.hand_data = hand_data.copy() if hand_data else None
    
    def show(self) -> None:
        """Show the camera window."""
        self.is_running = True
        
        while self.is_running:
            try:
                with self._lock:
                    if self.current_frame is not None:
                        # Draw hand highlights on frame
                        display_frame = self._draw_hand_highlights(
                            self.current_frame.copy(), self.hand_data)
                        
                        # Show frame
                        cv2.imshow(self.window_name, display_frame)
                    
                # Check for window close
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                    self.is_running = False
                    break
                
                time.sleep(0.033)  # ~30fps
                
            except Exception as e:
                logger.error(f"Error in camera window: {e}")
                break
        
        cv2.destroyWindow(self.window_name)
        logger.info("Camera window closed")
    
    def _draw_hand_highlights(self, frame: np.ndarray, hand_data: Optional[Dict[str, Any]]) -> np.ndarray:
        """Draw hand highlights on the frame.
        
        Args:
            frame: Camera frame
            hand_data: Hand tracking data
            
        Returns:
            Frame with hand highlights
        """
        if hand_data and 'players' in hand_data:
            for player in hand_data['players']:
                if 'x' in player and 'y' in player:
                    x = player['x']
                    y = player['y']
                    gesture = player.get('gesture', 'none')
                    
                    # Draw hand highlight based on gesture
                    if gesture == 'fist':
                        # Draw red circle for fist
                        cv2.circle(frame, (x, y), 40, (0, 0, 255), 4)
                        cv2.putText(frame, f"FIST P{player['id']}", 
                                  (x - 50, y - 50), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    elif gesture == 'open':
                        # Draw green circle for open hand
                        cv2.circle(frame, (x, y), 40, (0, 255, 0), 4)
                        cv2.putText(frame, f"OPEN P{player['id']}", 
                                  (x - 50, y - 50), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    else:
                        # Draw yellow circle for other gestures
                        cv2.circle(frame, (x, y), 40, (0, 255, 255), 4)
                        cv2.putText(frame, f"NONE P{player['id']}", 
                                  (x - 50, y - 50), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    
                    # Draw hand position info
                    y_norm = player.get('y_norm', 0.5)
                    cv2.putText(frame, f"Y: {y_norm:.2f}", 
                              (x - 30, y + 60), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add instructions
        cv2.putText(frame, "Press 'q' to close", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Red=Fist, Green=Open, Yellow=None", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame
    
    def stop(self) -> None:
        """Stop the camera window."""
        self.is_running = False
        cv2.destroyAllWindows()
        logger.info("Camera window stopped")
