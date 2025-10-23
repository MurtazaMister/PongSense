"""
AI opponent for PongSense.
Implements deterministic interface: next_y(target_y, difficulty) -> y_norm
"""

import numpy as np
import time
from typing import Tuple, Optional
from dataclasses import dataclass

from utils.logger import logger
from utils.config import config


@dataclass
class BallPrediction:
    """Ball trajectory prediction."""
    target_y: float
    time_to_reach: float
    confidence: float


class AIOpponent:
    """AI opponent with deterministic interface."""
    
    def __init__(self):
        """Initialize AI opponent."""
        # Configuration
        self.difficulty_easy = config.get('ai.difficulty_easy', 0.3)
        self.difficulty_medium = config.get('ai.difficulty_medium', 0.6)
        self.difficulty_hard = config.get('ai.difficulty_hard', 0.9)
        self.prediction_frames = config.get('ai.prediction_frames', 5)
        self.reaction_delay_ms = config.get('ai.reaction_delay_ms', 50)
        
        # AI state
        self.current_difficulty = 'medium'
        self.last_prediction_time = 0
        self.prediction_history = []
        self.current_position = 0.5  # Current AI paddle position for smoothing
        self.smoothing_factor = 0.4  # Increased for more agile movement (higher = more responsive)

        # Simple miss system: miss 2 out of every 10 shots
        self.shot_count = 0  # Track total shots
        self.miss_count = 0   # Track misses in current 10-shot cycle
        self.should_miss_this_shot = False  # Whether to miss current shot
        self.last_ball_x = 0.5  # Track ball position to detect actual shots
        self.miss_offset = 0.0  # Store the miss offset for current shot
        self.shot_decided = False  # Track if decision made for current shot
        
        logger.info("AIOpponent initialized")
    
    def next_y(self, target_y: float, difficulty: str = 'medium', ball_x: float = None) -> float:
        """Calculate next paddle position based on target and difficulty.
        
        Args:
            target_y: Target y position (normalized 0-1)
            difficulty: AI difficulty level ('easy', 'medium', 'hard')
            ball_x: Current ball x position (normalized 0-1) for shot counting
            
        Returns:
            Normalized y position for paddle (0-1)
        """
        try:
            # Update difficulty
            self.current_difficulty = difficulty
            
            # Count shots and determine if should miss
            if ball_x is not None:
                self._update_shot_count(ball_x)
            
            # Get difficulty factor
            difficulty_factor = self._get_difficulty_factor(difficulty)
            
            # Adjust target if AI should miss (make it look unintentional)
            if self.should_miss_this_shot:
                # AI tries to hit but aims slightly off-target (use stored offset)
                target_y = max(0.0, min(1.0, target_y + self.miss_offset))
                # Don't log every frame - only log once per shot
            
            # For more responsive AI, reduce imperfections
            imperfect_target = self._add_imperfections(target_y, difficulty_factor)
            
            # Apply smoothing to make movement less jerky
            smoothed_target = self._apply_smoothing(imperfect_target)
            
            # Minimal reaction delay for better gameplay
            delayed_target = self._apply_reaction_delay(smoothed_target)
            
            # Record prediction
            self._record_prediction(target_y, imperfect_target)
            
            return delayed_target
            
        except Exception as e:
            logger.error(f"Error in AI next_y: {e}")
            return 0.5  # Default center position
    
    def _get_difficulty_factor(self, difficulty: str) -> float:
        """Get difficulty factor for AI behavior.
        
        Args:
            difficulty: Difficulty level
            
        Returns:
            Difficulty factor (0-1)
        """
        difficulty_map = {
            'easy': self.difficulty_easy,
            'medium': self.difficulty_medium,
            'hard': self.difficulty_hard
        }
        
        return difficulty_map.get(difficulty, self.difficulty_medium)
    
    def _update_shot_count(self, ball_x: float) -> None:
        """Update shot count and determine if AI should miss this shot."""
        # Only count when ball crosses from player's side to AI's side (actual shot)
        if self.last_ball_x <= 0.5 and ball_x > 0.5 and not self.shot_decided:
            # Ball crossed center - this is a new shot
            self.shot_count += 1
            self.shot_decided = True
            
            # Determine if this shot should be a miss (decide once per shot)
            # Miss shots 1-2 of each 10-shot cycle
            cycle_position = (self.shot_count - 1) % 10  # 0-9
            if cycle_position < 2:  # First 2 shots of cycle
                self.should_miss_this_shot = True
                self.miss_count += 1
                # Generate miss offset once per shot
                self.miss_offset = np.random.uniform(-0.15, 0.15)
                logger.info(f"AI will miss shot {self.shot_count} (miss {self.miss_count}/2, offset: {self.miss_offset:.3f}, cycle_pos: {cycle_position})")
            else:
                self.should_miss_this_shot = False
                self.miss_offset = 0.0
                logger.info(f"AI will hit shot {self.shot_count} (cycle_pos: {cycle_position})")
            
            # Reset miss count every 10 shots
            if self.shot_count % 10 == 0:
                self.miss_count = 0
                logger.info(f"Reset miss count after {self.shot_count} shots")
        
        # Reset decision flag when ball goes back to player's side
        if ball_x <= 0.5:
            self.shot_decided = False
        
        # Update last ball position
        self.last_ball_x = ball_x
    
    def should_miss(self) -> bool:
        """Check if AI should miss the current shot.
        
        Returns:
            True if AI should miss, False otherwise
        """
        return self.should_miss_this_shot
    
    def _apply_smoothing(self, target_y: float) -> float:
        """Apply smoothing to AI movement to reduce jerkiness.
        
        Args:
            target_y: Target y position
            
        Returns:
            Smoothed y position
        """
        # Smooth movement by blending current position with target
        smoothed_y = (self.smoothing_factor * target_y + 
                     (1.0 - self.smoothing_factor) * self.current_position)
        
        # Update current position
        self.current_position = smoothed_y
        
        # Clamp to valid range
        smoothed_y = max(0.0, min(1.0, smoothed_y))
        
        return smoothed_y
    
    def _add_imperfections(self, target_y: float, difficulty_factor: float) -> float:
        """Add human-like imperfections to AI behavior.
        
        Args:
            target_y: Target y position
            difficulty_factor: Difficulty factor (0-1)
            
        Returns:
            Imperfect target y position
        """
        # Minimal imperfection for very responsive AI
        imperfection_amount = (1.0 - difficulty_factor) * 0.01  # Further reduced for agility
        
        # Add minimal random noise
        noise = np.random.normal(0, imperfection_amount)
        imperfect_y = target_y + noise
        
        # Minimal systematic bias
        bias = np.random.normal(0, imperfection_amount * 0.1)  # Further reduced for precision
        imperfect_y += bias
        
        # Clamp to valid range
        imperfect_y = max(0.0, min(1.0, imperfect_y))
        
        return imperfect_y
    
    def _apply_reaction_delay(self, target_y: float) -> float:
        """Apply reaction delay to AI response.
        
        Args:
            target_y: Target y position
            
        Returns:
            Delayed target y position
        """
        current_time = time.time()
        
        # Calculate delay based on difficulty
        delay_factor = self._get_difficulty_factor(self.current_difficulty)
        actual_delay = self.reaction_delay_ms * (1.0 - delay_factor) / 1000.0
        
        # Always update prediction time and return current target
        # This ensures AI moves smoothly instead of getting stuck
        self.last_prediction_time = current_time
        return target_y
    
    def _record_prediction(self, target_y: float, imperfect_target: float) -> None:
        """Record prediction for analysis and debugging.
        
        Args:
            target_y: Original target
            imperfect_target: Imperfect target
        """
        prediction = {
            'timestamp': time.time(),
            'target_y': target_y,
            'imperfect_target': imperfect_target,
            'difficulty': self.current_difficulty
        }
        
        self.prediction_history.append(prediction)
        
        # Keep only recent predictions
        if len(self.prediction_history) > 100:
            self.prediction_history = self.prediction_history[-100:]
    
    def predict_ball_trajectory(self, ball_x: float, ball_y: float, 
                              ball_vx: float, ball_vy: float, 
                              paddle_x: float) -> BallPrediction:
        """Predict where the ball will be when it reaches the paddle.
        
        Args:
            ball_x: Current ball x position
            ball_y: Current ball y position
            ball_vx: Ball x velocity
            ball_vy: Ball y velocity
            paddle_x: Paddle x position
            
        Returns:
            Ball prediction with target y and confidence
        """
        try:
            if ball_vx == 0:
                return BallPrediction(target_y=0.5, time_to_reach=0, confidence=0)
            
            # Calculate time to reach paddle
            distance_to_paddle = abs(paddle_x - ball_x)
            time_to_reach = distance_to_paddle / abs(ball_vx)
            
            # Predict y position at paddle
            predicted_y = ball_y + ball_vy * time_to_reach
            
            # Account for wall bounces
            predicted_y = self._simulate_wall_bounces(predicted_y, ball_vy, time_to_reach)
            
            # Normalize to 0-1 range (assuming paddle is at screen edge)
            # This is a simplified calculation
            normalized_y = max(0.0, min(1.0, predicted_y / 720.0))  # Assuming 720px height
            
            # Calculate confidence based on prediction distance
            confidence = max(0.1, 1.0 - (time_to_reach / 5.0))  # Lower confidence for longer predictions
            
            return BallPrediction(
                target_y=normalized_y,
                time_to_reach=time_to_reach,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error predicting ball trajectory: {e}")
            return BallPrediction(target_y=0.5, time_to_reach=0, confidence=0)
    
    def _simulate_wall_bounces(self, y: float, vy: float, time: float) -> float:
        """Simulate wall bounces for ball prediction.
        
        Args:
            y: Current y position
            vy: Current y velocity
            time: Time to simulate
            
        Returns:
            Predicted y position after bounces
        """
        # Simplified wall bounce simulation
        # In a real implementation, this would be more sophisticated
        
        # Simulate multiple small time steps
        dt = 0.1
        steps = int(time / dt)
        
        current_y = y
        current_vy = vy
        
        for _ in range(steps):
            current_y += current_vy * dt
            
            # Wall bounce (assuming walls at y=0 and y=720)
            if current_y <= 0:
                current_y = 0
                current_vy = abs(current_vy)
            elif current_y >= 720:
                current_y = 720
                current_vy = -abs(current_vy)
        
        return current_y
    
    def get_prediction_stats(self) -> dict:
        """Get AI prediction statistics for debugging.
        
        Returns:
            Dictionary with prediction statistics
        """
        if not self.prediction_history:
            return {'total_predictions': 0}
        
        recent_predictions = self.prediction_history[-10:]  # Last 10 predictions
        
        avg_error = np.mean([abs(p['target_y'] - p['imperfect_target']) 
                            for p in recent_predictions])
        
        return {
            'total_predictions': len(self.prediction_history),
            'recent_predictions': len(recent_predictions),
            'average_error': avg_error,
            'current_difficulty': self.current_difficulty,
            'last_prediction_time': self.last_prediction_time
        }
    
    def reset_stats(self) -> None:
        """Reset AI statistics."""
        self.prediction_history.clear()
        self.last_prediction_time = 0
        logger.info("AI opponent stats reset")
