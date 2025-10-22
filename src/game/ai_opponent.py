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
        
        logger.info("AIOpponent initialized")
    
    def next_y(self, target_y: float, difficulty: str = 'medium') -> float:
        """Calculate next paddle position based on target and difficulty.
        
        Args:
            target_y: Target y position (normalized 0-1)
            difficulty: AI difficulty level ('easy', 'medium', 'hard')
            
        Returns:
            Normalized y position for paddle (0-1)
        """
        try:
            # Update difficulty
            self.current_difficulty = difficulty
            
            # Get difficulty factor
            difficulty_factor = self._get_difficulty_factor(difficulty)
            
            # For more responsive AI, reduce imperfections
            imperfect_target = self._add_imperfections(target_y, difficulty_factor)
            
            # Minimal reaction delay for better gameplay
            delayed_target = self._apply_reaction_delay(imperfect_target)
            
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
    
    def _add_imperfections(self, target_y: float, difficulty_factor: float) -> float:
        """Add human-like imperfections to AI behavior.
        
        Args:
            target_y: Target y position
            difficulty_factor: Difficulty factor (0-1)
            
        Returns:
            Imperfect target y position
        """
        # Reduced imperfection amount for better AI performance
        imperfection_amount = (1.0 - difficulty_factor) * 0.05  # Reduced from 0.2
        
        # Add minimal random noise
        noise = np.random.normal(0, imperfection_amount)
        imperfect_y = target_y + noise
        
        # Minimal systematic bias
        bias = np.random.normal(0, imperfection_amount * 0.3)  # Reduced from 0.5
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
        
        # Simple delay simulation (in real implementation, this would be more sophisticated)
        if current_time - self.last_prediction_time < actual_delay:
            # Return previous prediction if within delay period
            if self.prediction_history:
                return self.prediction_history[-1]['imperfect_target']
        
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
