"""
Gesture recognition module for hand landmarks.
Implements deterministic interface: infer(hand_landmarks) -> {gesture, y_norm}
"""

import numpy as np
from typing import Dict, Any, List, Optional
import mediapipe as mp

from utils.logger import logger
from utils.config import config


class GestureRecognizer:
    """Gesture recognition for hand landmarks."""
    
    def __init__(self):
        """Initialize gesture recognizer."""
        self.gesture_threshold = config.get('hand_tracking.gesture_threshold', 0.1)
        self.smoothing_factor = config.get('hand_tracking.smoothing_factor', 0.8)
        
        # Previous states for smoothing
        self._prev_gestures = {}
        self._prev_y_norms = {}
        
        logger.info("GestureRecognizer initialized")
    
    def infer(self, hand_landmarks: List[Any]) -> Dict[str, Any]:
        """Infer gesture and normalized y position from hand landmarks.
        
        Args:
            hand_landmarks: List of MediaPipe hand landmarks
            
        Returns:
            Dictionary with gesture and y_norm
        """
        try:
            if not hand_landmarks:
                return {'gesture': 'none', 'y_norm': 0.5}
            
            # Process each hand
            results = []
            for idx, landmarks in enumerate(hand_landmarks):
                gesture = self._classify_gesture(landmarks)
                y_norm = self._calculate_y_norm(landmarks)
                
                # Apply smoothing
                hand_id = f"hand_{idx}"
                gesture = self._smooth_gesture(hand_id, gesture)
                y_norm = self._smooth_y_norm(hand_id, y_norm)
                
                results.append({
                    'gesture': gesture,
                    'y_norm': y_norm
                })
            
            # Return primary hand result (first hand)
            if results:
                return results[0]
            else:
                return {'gesture': 'none', 'y_norm': 0.5}
                
        except Exception as e:
            logger.error(f"Error in gesture inference: {e}")
            return {'gesture': 'none', 'y_norm': 0.5}
    
    def _classify_gesture(self, landmarks) -> str:
        """Classify hand gesture from landmarks.
        
        Args:
            landmarks: MediaPipe hand landmarks
            
        Returns:
            Gesture type: 'fist', 'open', or 'none'
        """
        try:
            # Get key landmarks
            thumb_tip = landmarks.landmark[4]
            thumb_ip = landmarks.landmark[3]
            thumb_mcp = landmarks.landmark[2]
            
            index_tip = landmarks.landmark[8]
            index_pip = landmarks.landmark[6]
            index_mcp = landmarks.landmark[5]
            
            middle_tip = landmarks.landmark[12]
            middle_pip = landmarks.landmark[10]
            middle_mcp = landmarks.landmark[9]
            
            ring_tip = landmarks.landmark[16]
            ring_pip = landmarks.landmark[14]
            
            pinky_tip = landmarks.landmark[20]
            pinky_pip = landmarks.landmark[18]
            
            # Count extended fingers
            extended_fingers = 0
            
            # Thumb (compare x coordinates for right hand, opposite for left)
            thumb_extended = thumb_tip.x > thumb_ip.x
            if thumb_extended:
                extended_fingers += 1
            
            # Index finger (compare y coordinates)
            if index_tip.y < index_pip.y:
                extended_fingers += 1
            
            # Middle finger
            if middle_tip.y < middle_pip.y:
                extended_fingers += 1
            
            # Ring finger
            if ring_tip.y < ring_pip.y:
                extended_fingers += 1
            
            # Pinky finger
            if pinky_tip.y < pinky_pip.y:
                extended_fingers += 1
            
            # Classify gesture based on extended fingers
            if extended_fingers >= 3:  # More lenient - 3+ fingers = open
                return 'open'
            elif extended_fingers <= 2:  # More lenient - 2 or fewer = fist
                return 'fist'
            else:
                return 'open'  # Default to open instead of none
                
        except Exception as e:
            logger.warning(f"Error classifying gesture: {e}")
            return 'none'
    
    def _calculate_y_norm(self, landmarks) -> float:
        """Calculate normalized y position from landmarks.
        
        Args:
            landmarks: MediaPipe hand landmarks
            
        Returns:
            Normalized y position (0.0 = top, 1.0 = bottom)
        """
        try:
            # Use middle finger MCP as reference point
            middle_mcp = landmarks.landmark[9]
            return float(middle_mcp.y)
            
        except Exception as e:
            logger.warning(f"Error calculating y_norm: {e}")
            return 0.5
    
    def _smooth_gesture(self, hand_id: str, current_gesture: str) -> str:
        """Apply smoothing to gesture classification.
        
        Args:
            hand_id: Unique identifier for the hand
            current_gesture: Current gesture classification
            
        Returns:
            Smoothed gesture
        """
        if hand_id not in self._prev_gestures:
            self._prev_gestures[hand_id] = current_gesture
            return current_gesture
        
        prev_gesture = self._prev_gestures[hand_id]
        
        # Simple smoothing: keep previous gesture if current is 'none'
        if current_gesture == 'none' and prev_gesture != 'none':
            return prev_gesture
        
        # Update previous gesture
        self._prev_gestures[hand_id] = current_gesture
        return current_gesture
    
    def _smooth_y_norm(self, hand_id: str, current_y_norm: float) -> float:
        """Apply smoothing to y_norm values.
        
        Args:
            hand_id: Unique identifier for the hand
            current_y_norm: Current normalized y position
            
        Returns:
            Smoothed y_norm
        """
        if hand_id not in self._prev_y_norms:
            self._prev_y_norms[hand_id] = current_y_norm
            return current_y_norm
        
        prev_y_norm = self._prev_y_norms[hand_id]
        
        # Apply exponential smoothing
        smoothed_y_norm = (self.smoothing_factor * prev_y_norm + 
                          (1 - self.smoothing_factor) * current_y_norm)
        
        # Update previous value
        self._prev_y_norms[hand_id] = smoothed_y_norm
        
        return smoothed_y_norm
    
    def reset_smoothing(self, hand_id: Optional[str] = None) -> None:
        """Reset smoothing state for a specific hand or all hands.
        
        Args:
            hand_id: Specific hand ID to reset, or None for all hands
        """
        if hand_id is None:
            self._prev_gestures.clear()
            self._prev_y_norms.clear()
        else:
            self._prev_gestures.pop(hand_id, None)
            self._prev_y_norms.pop(hand_id, None)
        
        logger.info(f"Reset smoothing for {hand_id or 'all hands'}")
