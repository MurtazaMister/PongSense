"""
Multimodal input manager for PongSense.
Fuses vision and voice inputs into unified game input.
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from utils.logger import logger
from utils.config import config


@dataclass
class EngineInput:
    """Unified input for game engine."""
    p1_y: float  # Player 1 normalized y position
    p2_y: float  # Player 2 normalized y position (or AI)
    speed_delta: float  # Speed change from voice commands
    meta: Dict[str, Any]  # Additional metadata


class InputManager:
    """Manages fusion of vision and voice inputs."""
    
    def __init__(self):
        """Initialize input manager."""
        self.calibration_data = {
            'p1_min_y': 0.0,
            'p1_max_y': 1.0,
            'p2_min_y': 0.0,
            'p2_max_y': 1.0,
            'calibrated': False
        }
        
        # Voice command processing
        self.last_speed_command_time = 0
        self.speed_command_cooldown = config.get('voice_recognition.command_cooldown', 2.0)
        
        # Previous normalized positions for smoothing
        self._prev_y_norms = {}
        
        logger.info("InputManager initialized")
    
    def fuse(self, vision_state: Dict[str, Any], voice_cmds: List[str], 
             mode: str = 'single') -> EngineInput:
        """Fuse vision and voice inputs into unified game input.
        
        Args:
            vision_state: Vision tracking state
            voice_cmds: List of voice commands
            mode: Game mode ('single' or 'two_player')
            
        Returns:
            Unified engine input
        """
        try:
            # Extract player positions from vision state
            p1_y, p2_y = self._extract_player_positions(vision_state, mode)
            
            # Process voice commands for speed control
            speed_delta = self._process_voice_commands(voice_cmds)
            
            # Create metadata
            meta = {
                'timestamp': time.time(),
                'mode': mode,
                'vision_players_count': len(vision_state.get('players', [])),
                'voice_commands_count': len(voice_cmds),
                'calibrated': self.calibration_data['calibrated']
            }
            
            return EngineInput(
                p1_y=p1_y,
                p2_y=p2_y,
                speed_delta=speed_delta,
                meta=meta
            )
            
        except Exception as e:
            logger.error(f"Error fusing inputs: {e}")
            return EngineInput(
                p1_y=0.5,
                p2_y=0.5,
                speed_delta=0.0,
                meta={'error': str(e)}
            )
    
    def _extract_player_positions(self, vision_state: Dict[str, Any], 
                                 mode: str) -> Tuple[float, float]:
        """Extract player positions from vision state.
        
        Args:
            vision_state: Vision tracking state
            mode: Game mode
            
        Returns:
            Tuple of (p1_y, p2_y) normalized positions
        """
        players = vision_state.get('players', [])
        
        if mode == 'single':
            # Single player mode: Use any hand gesture for Player 1, Player 2 is AI
            p1_y = 0.5  # Default center
            p2_y = 0.5  # AI will handle this
            
            # Find any hand for Player 1 (fist or open)
            for player in players:
                gesture = player.get('gesture', 'none')
                if gesture in ['fist', 'open']:
                    p1_y = self._normalize_player_position(player, 'p1')
                    break
        
        elif mode == 'two_player':
            # Two player mode: Use any hand gestures for both players
            p1_y = 0.5
            p2_y = 0.5
            
            active_players = [p for p in players if p.get('gesture', 'none') in ['fist', 'open']]
            
            if len(active_players) >= 1:
                # Leftmost hand = Player 1
                leftmost_player = min(active_players, key=lambda p: p.get('x', 0))
                p1_y = self._normalize_player_position(leftmost_player, 'p1')
                
            if len(active_players) >= 2:
                # Rightmost hand = Player 2
                rightmost_player = max(active_players, key=lambda p: p.get('x', 0))
                p2_y = self._normalize_player_position(rightmost_player, 'p2')
        
        else:
            # Unknown mode, default positions
            p1_y = 0.5
            p2_y = 0.5
        
        return p1_y, p2_y
    
    def _normalize_player_position(self, player: Dict[str, Any], 
                                  player_id: str) -> float:
        """Normalize player position using calibration data.
        
        Args:
            player: Player data from vision
            player_id: Player identifier ('p1' or 'p2')
            
        Returns:
            Normalized position (0-1)
        """
        try:
            raw_y = player.get('y_norm', 0.5)
            
            # Apply smoothing for smoother control
            if player_id in self._prev_y_norms:
                prev_y = self._prev_y_norms[player_id]
                # Moderate smoothing (0.3 factor) for smoother movement
                smoothed_y = 0.7 * raw_y + 0.3 * prev_y
                self._prev_y_norms[player_id] = smoothed_y
                return max(0.0, min(1.0, smoothed_y))
            else:
                self._prev_y_norms[player_id] = raw_y
                return max(0.0, min(1.0, raw_y))
            
        except Exception as e:
            logger.warning(f"Error normalizing player position: {e}")
            return 0.5
    
    def _process_voice_commands(self, voice_cmds: List[str]) -> float:
        """Process voice commands for speed control.
        
        Args:
            voice_cmds: List of voice commands
            
        Returns:
            Speed delta (-1.0 to 1.0)
        """
        current_time = time.time()
        speed_delta = 0.0
        
        for cmd in voice_cmds:
            # Check cooldown
            if current_time - self.last_speed_command_time < self.speed_command_cooldown:
                continue
            
            if cmd == 'faster':
                speed_delta += 0.2
                self.last_speed_command_time = current_time
                logger.info("Voice command: faster")
            elif cmd == 'slower':
                speed_delta -= 0.2
                self.last_speed_command_time = current_time
                logger.info("Voice command: slower")
        
        # Clamp speed delta
        return max(-1.0, min(1.0, speed_delta))
    
    def calibrate_player(self, player_id: str, min_y: float, max_y: float) -> None:
        """Calibrate player position range.
        
        Args:
            player_id: Player identifier ('p1' or 'p2')
            min_y: Minimum y position (normalized)
            max_y: Maximum y position (normalized)
        """
        try:
            min_key = f'{player_id}_min_y'
            max_key = f'{player_id}_max_y'
            
            self.calibration_data[min_key] = min_y
            self.calibration_data[max_key] = max_y
            
            # Mark as calibrated if both players are calibrated
            if 'p1_min_y' in self.calibration_data and 'p1_max_y' in self.calibration_data:
                self.calibration_data['calibrated'] = True
            
            logger.info(f"Calibrated {player_id}: min={min_y:.2f}, max={max_y:.2f}")
            
        except Exception as e:
            logger.error(f"Error calibrating player {player_id}: {e}")
    
    def reset_calibration(self) -> None:
        """Reset calibration data."""
        self.calibration_data = {
            'p1_min_y': 0.0,
            'p1_max_y': 1.0,
            'p2_min_y': 0.0,
            'p2_max_y': 1.0,
            'calibrated': False
        }
        logger.info("Calibration reset")
    
    def get_calibration_status(self) -> Dict[str, Any]:
        """Get current calibration status.
        
        Returns:
            Calibration status dictionary
        """
        return self.calibration_data.copy()
    
    def quick_calibration(self, vision_state: Dict[str, Any], 
                         duration: float = 5.0) -> bool:
        """Perform quick calibration by sampling hand positions.
        
        Args:
            vision_state: Current vision state
            duration: Calibration duration in seconds
            
        Returns:
            True if calibration successful
        """
        try:
            logger.info(f"Starting quick calibration for {duration} seconds...")
            
            start_time = time.time()
            samples = {'p1': [], 'p2': []}
            
            while time.time() - start_time < duration:
                players = vision_state.get('players', [])
                
                for i, player in enumerate(players[:2]):  # Max 2 players
                    player_id = f'p{i+1}'
                    y_norm = player.get('y_norm', 0.5)
                    samples[player_id].append(y_norm)
                
                time.sleep(0.1)  # Sample every 100ms
            
            # Calculate calibration ranges
            for player_id, y_samples in samples.items():
                if y_samples:
                    min_y = min(y_samples)
                    max_y = max(y_samples)
                    
                    # Add some margin
                    margin = 0.1
                    min_y = max(0.0, min_y - margin)
                    max_y = min(1.0, max_y + margin)
                    
                    self.calibrate_player(player_id, min_y, max_y)
            
            success = self.calibration_data['calibrated']
            logger.info(f"Quick calibration {'successful' if success else 'failed'}")
            return success
            
        except Exception as e:
            logger.error(f"Error in quick calibration: {e}")
            return False
