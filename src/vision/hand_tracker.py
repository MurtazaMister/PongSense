"""
Hand tracking module using MediaPipe.
Implements deterministic interface: start(), stop(), get_state()
"""

import cv2
import mediapipe as mp
import numpy as np
import threading
import time
from typing import Dict, List, Any, Optional, Tuple
from queue import Queue, Empty

from utils.logger import logger
from utils.config import config


class HandTracker:
    """Hand tracking using MediaPipe with deterministic interface."""
    
    def __init__(self):
        """Initialize hand tracker."""
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = None
        self.cap = None
        self.is_running = False
        self.thread = None
        self.frame_queue = Queue(maxsize=2)
        self.current_state = {
            'players': [],
            'frame': None,
            'meta': {
                'timestamp': 0,
                'fps': 0,
                'detection_count': 0
            }
        }
        self._lock = threading.Lock()
        self._fps_counter = 0
        self._last_fps_time = time.time()
        
        # Configuration
        self.detection_confidence = config.get('hand_tracking.detection_confidence', 0.7)
        self.tracking_confidence = config.get('hand_tracking.tracking_confidence', 0.5)
        self.max_hands = config.get('hand_tracking.max_hands', 2)
        self.camera_width = config.get('camera.width', 640)
        self.camera_height = config.get('camera.height', 480)
        self.camera_fps = config.get('camera.fps', 30)
        self.device_id = config.get('camera.device_id', 0)
    
    def start(self) -> bool:
        """Start hand tracking.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                logger.warning("Hand tracker already running")
                return True
            
            # Initialize MediaPipe hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=self.max_hands,
                min_detection_confidence=self.detection_confidence,
                min_tracking_confidence=self.tracking_confidence
            )
            
            # Initialize camera
            self.cap = cv2.VideoCapture(self.device_id)
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.device_id}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.camera_fps)
            
            self.is_running = True
            self.thread = threading.Thread(target=self._tracking_loop, daemon=True)
            self.thread.start()
            
            logger.info("Hand tracker started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start hand tracker: {e}")
            return False
    
    def stop(self) -> None:
        """Stop hand tracking."""
        try:
            self.is_running = False
            
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2.0)
            
            if self.cap:
                self.cap.release()
            
            if self.hands:
                self.hands.close()
            
            # Clear frame queue
            while not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except Empty:
                    break
            
            logger.info("Hand tracker stopped")
            
        except Exception as e:
            logger.error(f"Error stopping hand tracker: {e}")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current hand tracking state.
        
        Returns:
            Dictionary with players, frame, and meta information
        """
        with self._lock:
            return self.current_state.copy()
    
    def _tracking_loop(self) -> None:
        """Main tracking loop running in separate thread."""
        logger.info("Hand tracking loop started")
        
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning("Failed to read frame from camera")
                    continue
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process frame
                results = self.hands.process(rgb_frame)
                
                # Draw hand landmarks on frame for visualization
                annotated_frame = frame.copy()
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        self.mp_drawing.draw_landmarks(
                            annotated_frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # Extract hand data
                players = self._extract_hand_data(results, frame.shape)
                
                # Update state
                with self._lock:
                    self.current_state = {
                        'players': players,
                        'frame': annotated_frame.copy(),  # Use annotated frame with landmarks
                        'meta': {
                            'timestamp': time.time(),
                            'fps': self._calculate_fps(),
                            'detection_count': len(players)
                        }
                    }
                
                # Add frame to queue (non-blocking)
                try:
                    self.frame_queue.put_nowait(frame.copy())
                except:
                    # Queue full, remove oldest frame
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame.copy())
                    except Empty:
                        pass
                
            except Exception as e:
                logger.error(f"Error in tracking loop: {e}")
                time.sleep(0.1)
        
        logger.info("Hand tracking loop ended")
    
    def _extract_hand_data(self, results, frame_shape: Tuple[int, int, int]) -> List[Dict[str, Any]]:
        """Extract hand data from MediaPipe results.
        
        Args:
            results: MediaPipe hand results
            frame_shape: Shape of the frame (height, width, channels)
            
        Returns:
            List of player dictionaries
        """
        players = []
        
        if results.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Get hand classification (left/right)
                handedness = results.multi_handedness[idx]
                hand_label = handedness.classification[0].label
                
                # Calculate center point (using middle finger MCP)
                landmark = hand_landmarks.landmark[9]  # Middle finger MCP
                x = int(landmark.x * frame_shape[1])
                y = int(landmark.y * frame_shape[0])
                
                # Normalize y position (0 = top, 1 = bottom)
                y_norm = landmark.y
                
                # Determine player ID based on position (leftmost = Player 1)
                player_id = 1 if x < frame_shape[1] // 2 else 2
                
                # Basic gesture detection (simplified)
                gesture = self._detect_gesture(hand_landmarks)
                
                player_data = {
                    'id': player_id,
                    'y_norm': y_norm,
                    'gesture': gesture,
                    'x': x,
                    'y': y,
                    'hand_label': hand_label,
                    'confidence': handedness.classification[0].score
                }
                
                players.append(player_data)
        
        # Sort players by x position (leftmost first)
        players.sort(key=lambda p: p['x'])
        
        return players
    
    def _detect_gesture(self, hand_landmarks) -> str:
        """Detect hand gesture (simplified version).
        
        Args:
            hand_landmarks: MediaPipe hand landmarks
            
        Returns:
            Gesture type: 'fist', 'open', or 'none'
        """
        try:
            # Get key landmarks
            thumb_tip = hand_landmarks.landmark[4]
            thumb_ip = hand_landmarks.landmark[3]
            index_tip = hand_landmarks.landmark[8]
            index_pip = hand_landmarks.landmark[6]
            middle_tip = hand_landmarks.landmark[12]
            middle_pip = hand_landmarks.landmark[10]
            
            # Check if fingers are extended
            fingers_extended = 0
            
            # Thumb (compare x coordinates)
            if thumb_tip.x > thumb_ip.x:
                fingers_extended += 1
            
            # Index finger
            if index_tip.y < index_pip.y:
                fingers_extended += 1
            
            # Middle finger
            if middle_tip.y < middle_pip.y:
                fingers_extended += 1
            
            # Simple classification
            if fingers_extended >= 2:
                return 'open'
            elif fingers_extended == 0:
                return 'fist'
            else:
                return 'none'
                
        except Exception as e:
            logger.warning(f"Error detecting gesture: {e}")
            return 'none'
    
    def _calculate_fps(self) -> float:
        """Calculate current FPS."""
        self._fps_counter += 1
        current_time = time.time()
        
        if current_time - self._last_fps_time >= 1.0:
            fps = self._fps_counter / (current_time - self._last_fps_time)
            self._fps_counter = 0
            self._last_fps_time = current_time
            return fps
        
        return 0.0
