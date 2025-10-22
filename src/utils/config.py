"""
Configuration management for PongSense.
Handles loading and validation of config.yaml settings.
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for PongSense."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as file:
                    self._config = yaml.safe_load(file) or {}
            else:
                self._config = self._get_default_config()
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self._config = self._get_default_config()
    
    def save_config(self) -> None:
        """Save current configuration to YAML file."""
        try:
            with open(self.config_path, 'w') as file:
                yaml.dump(self._config, file, default_flow_style=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'game.fps')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'game.fps')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'game': {
                'window_width': 1280,
                'window_height': 720,
                'fps': 60,
                'target_fps': 30,
                'difficulty_levels': ['easy', 'medium', 'hard'],
                'ball_speed_base': 5.0,
                'ball_speed_multiplier': 1.0,
                'paddle_speed': 8.0
            },
            'hand_tracking': {
                'detection_confidence': 0.7,
                'tracking_confidence': 0.5,
                'min_hand_landmarks': 21,
                'gesture_threshold': 0.1,
                'smoothing_factor': 0.8,
                'max_hands': 2,
                'calibration_samples': 10
            },
            'voice_recognition': {
                'language': 'en-US',
                'timeout': 1.0,
                'phrase_timeout': 0.3,
                'energy_threshold': 300,
                'dynamic_energy_threshold': True,
                'command_cooldown': 2.0,
                'supported_commands': ['faster', 'slower']
            },
            'camera': {
                'device_id': 0,
                'width': 640,
                'height': 480,
                'fps': 30,
                'auto_exposure': True
            },
            'audio': {
                'sample_rate': 44100,
                'chunk_size': 1024,
                'channels': 1,
                'format': 'pyaudio.paInt16'
            },
            'performance': {
                'max_latency_ms': 100,
                'enable_multithreading': True,
                'debug_mode': False,
                'enable_performance_monitoring': True
            },
            'ai': {
                'difficulty_easy': 0.3,
                'difficulty_medium': 0.6,
                'difficulty_hard': 0.9,
                'prediction_frames': 5,
                'reaction_delay_ms': 50
            }
        }


# Global configuration instance
config = Config()
