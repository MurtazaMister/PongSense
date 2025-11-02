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
        
        # Parallel processing for 2-player mode
        self.parallel_mode = False
        self.hands_left = None  # MediaPipe instance for left side
        self.hands_right = None  # MediaPipe instance for right side
        self._left_results = None
        self._right_results = None
        self._result_lock = threading.Lock()
        
        # Simple instant switching - whatever hand is visible is primary
    
    def set_parallel_mode(self, enabled: bool) -> None:
        """Enable or disable parallel processing mode for 2-player mode.
        
        Args:
            enabled: True to enable parallel processing (split frame processing)
        """
        if self.parallel_mode == enabled:
            return
        
        self.parallel_mode = enabled
        
        if enabled:
            # Initialize separate MediaPipe instances for left and right sides
            self.hands_left = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,  # Only one hand per side
                min_detection_confidence=self.detection_confidence,
                min_tracking_confidence=self.tracking_confidence
            )
            self.hands_right = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,  # Only one hand per side
                min_detection_confidence=self.detection_confidence,
                min_tracking_confidence=self.tracking_confidence
            )
            logger.info("Parallel processing mode enabled for 2-player mode")
        else:
            # Clean up parallel instances if they exist
            if self.hands_left:
                self.hands_left.close()
                self.hands_left = None
            if self.hands_right:
                self.hands_right.close()
                self.hands_right = None
            logger.info("Parallel processing mode disabled")
    
    def start(self) -> bool:
        """Start hand tracking.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                logger.warning("Hand tracker already running")
                return True
            
            # Initialize MediaPipe hands (for non-parallel mode)
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
            
            # Clean up parallel mode instances
            if self.hands_left:
                self.hands_left.close()
                self.hands_left = None
            if self.hands_right:
                self.hands_right.close()
                self.hands_right = None
            
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
                
                # Process frame - use parallel mode if enabled
                if self.parallel_mode and self.hands_left and self.hands_right:
                    results = self._process_parallel(rgb_frame)
                else:
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
    
    def _process_parallel(self, rgb_frame: np.ndarray) -> Any:
        """Process frame in parallel - split left and right halves.
        
        Args:
            rgb_frame: RGB frame to process
            
        Returns:
            Combined MediaPipe results
        """
        height, width = rgb_frame.shape[:2]
        mid_x = width // 2
        
        # Split frame into left and right halves
        left_half = rgb_frame[:, :mid_x]
        right_half = rgb_frame[:, mid_x:]
        
        # Process each half in parallel using threads
        left_results = [None]
        right_results = [None]
        left_done = threading.Event()
        right_done = threading.Event()
        
        def process_left():
            try:
                left_results[0] = self.hands_left.process(left_half)
            except Exception as e:
                logger.error(f"Error processing left half: {e}")
            finally:
                left_done.set()
        
        def process_right():
            try:
                right_results[0] = self.hands_right.process(right_half)
            except Exception as e:
                logger.error(f"Error processing right half: {e}")
            finally:
                right_done.set()
        
        # Start both threads
        left_thread = threading.Thread(target=process_left, daemon=True)
        right_thread = threading.Thread(target=process_right, daemon=True)
        left_thread.start()
        right_thread.start()
        
        # Wait for both to complete
        left_done.wait()
        right_done.wait()
        
        # Merge results - adjust coordinates back to full frame
        return self._merge_hand_results(left_results[0], right_results[0], width, height, mid_x)
    
    def _merge_hand_results(self, left_results: Any, right_results: Any, 
                           full_width: int, full_height: int, mid_x: int) -> Any:
        """Merge results from left and right halves, adjusting coordinates.
        
        Args:
            left_results: MediaPipe results from left half
            right_results: MediaPipe results from right half
            full_width: Full frame width
            full_height: Full frame height
            mid_x: X coordinate of the split point
            
        Returns:
            Combined results object with same structure as MediaPipe results
        """
        # Create a simple results-like object matching MediaPipe structure
        class MergedResults:
            def __init__(self):
                self.multi_hand_landmarks = []
                self.multi_handedness = []
        
        merged = MergedResults()
        
        # Process left side results - MediaPipe returns normalized coordinates (0-1)
        # Left half: coordinates are 0-1 normalized to left half, need to scale to 0-0.5 for full frame
        if left_results and left_results.multi_hand_landmarks:
            for idx, landmarks in enumerate(left_results.multi_hand_landmarks):
                # Adjust x coordinates directly (MediaPipe landmarks are mutable protobuf objects)
                for landmark in landmarks.landmark:
                    landmark.x = landmark.x * 0.5  # Scale 0-1 to 0-0.5
                
                merged.multi_hand_landmarks.append(landmarks)
                if left_results.multi_handedness and idx < len(left_results.multi_handedness):
                    merged.multi_handedness.append(left_results.multi_handedness[idx])
        
        # Process right side results - adjust x from 0-1 (right half) to 0.5-1 (full frame)
        if right_results and right_results.multi_hand_landmarks:
            for idx, landmarks in enumerate(right_results.multi_hand_landmarks):
                # Adjust x coordinates directly
                for landmark in landmarks.landmark:
                    landmark.x = 0.5 + (landmark.x * 0.5)  # Map 0-1 to 0.5-1
                
                merged.multi_hand_landmarks.append(landmarks)
                if right_results.multi_handedness and idx < len(right_results.multi_handedness):
                    merged.multi_handedness.append(right_results.multi_handedness[idx])
        
        return merged
    
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
                if results.multi_handedness and idx < len(results.multi_handedness):
                    handedness = results.multi_handedness[idx]
                    hand_label = handedness.classification[0].label
                else:
                    hand_label = 'Unknown'
                    handedness = None
                
                # Calculate center point (using middle finger MCP)
                landmark = hand_landmarks.landmark[9]  # Middle finger MCP
                x = int(landmark.x * frame_shape[1])
                y = int(landmark.y * frame_shape[0])
                
                # Normalize y position (0 = top, 1 = bottom)
                y_norm = landmark.y
                
                # Basic gesture detection (simplified)
                gesture = self._detect_gesture(hand_landmarks)
                
                # Simple logic: if only one hand visible, it's primary
                # If multiple hands, leftmost is primary
                is_primary = len(results.multi_hand_landmarks) == 1 or idx == 0
                
                player_data = {
                    'id': 1 if is_primary else 2,  # Primary hand = Player 1, others = Player 2
                    'y_norm': y_norm,
                    'gesture': gesture,
                    'x': x,
                    'y': y,
                    'hand_label': hand_label,
                    'confidence': handedness.classification[0].score if handedness else 0.5,
                    'hand_id': hand_label,
                    'is_primary': is_primary
                }
                
                players.append(player_data)
        
        # Sort players: primary hand first, then by x position
        players.sort(key=lambda p: (not p['is_primary'], p['x']))
        
        return players
    
    def _detect_gesture(self, hand_landmarks) -> str:
        """Detect hand gesture (improved version for both hands).
        
        Args:
            hand_landmarks: MediaPipe hand landmarks
            
        Returns:
            Gesture type: 'fist', 'open', or 'none'
        """
        try:
            # Get key landmarks
            thumb_tip = hand_landmarks.landmark[4]
            thumb_ip = hand_landmarks.landmark[3]
            thumb_mcp = hand_landmarks.landmark[2]
            
            index_tip = hand_landmarks.landmark[8]
            index_pip = hand_landmarks.landmark[6]
            index_mcp = hand_landmarks.landmark[5]
            
            middle_tip = hand_landmarks.landmark[12]
            middle_pip = hand_landmarks.landmark[10]
            middle_mcp = hand_landmarks.landmark[9]
            
            ring_tip = hand_landmarks.landmark[16]
            ring_pip = hand_landmarks.landmark[14]
            
            pinky_tip = hand_landmarks.landmark[20]
            pinky_pip = hand_landmarks.landmark[18]
            
            # Count extended fingers
            extended_fingers = 0
            
            # Thumb detection - more robust for both hands
            # Check if thumb is extended by comparing distance from palm
            thumb_extended = abs(thumb_tip.x - thumb_mcp.x) > abs(thumb_ip.x - thumb_mcp.x)
            if thumb_extended:
                extended_fingers += 1
            
            # Index finger (compare y coordinates - tip above PIP when extended)
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
            
            # More lenient classification
            if extended_fingers >= 3:  # 3+ fingers = open
                return 'open'
            elif extended_fingers <= 1:  # 1 or fewer = fist
                return 'fist'
            else:  # 2 fingers = ambiguous, default to open
                return 'open'
                
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
