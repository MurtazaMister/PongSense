"""
Basic unit tests for PongSense components.
"""

import unittest
import numpy as np
from unittest.mock import Mock, patch

from src.vision.gesture_recognizer import GestureRecognizer
from src.game.ai_opponent import AIOpponent
from src.multimodal.input_manager import InputManager


class TestGestureRecognizer(unittest.TestCase):
    """Test gesture recognition functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.recognizer = GestureRecognizer()
    
    def test_infer_empty_input(self):
        """Test inference with empty input."""
        result = self.recognizer.infer([])
        self.assertEqual(result['gesture'], 'none')
        self.assertEqual(result['y_norm'], 0.5)
    
    def test_infer_none_input(self):
        """Test inference with None input."""
        result = self.recognizer.infer(None)
        self.assertEqual(result['gesture'], 'none')
        self.assertEqual(result['y_norm'], 0.5)
    
    def test_smoothing(self):
        """Test gesture smoothing."""
        # Mock landmarks
        mock_landmarks = Mock()
        mock_landmarks.landmark = [Mock() for _ in range(21)]
        
        # Set up mock landmark positions
        for i, landmark in enumerate(mock_landmarks.landmark):
            landmark.x = 0.5
            landmark.y = 0.5
        
        # Test smoothing
        result1 = self.recognizer.infer([mock_landmarks])
        result2 = self.recognizer.infer([mock_landmarks])
        
        self.assertIsInstance(result1['gesture'], str)
        self.assertIsInstance(result1['y_norm'], float)
        self.assertGreaterEqual(result1['y_norm'], 0.0)
        self.assertLessEqual(result1['y_norm'], 1.0)


class TestAIOpponent(unittest.TestCase):
    """Test AI opponent functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ai = AIOpponent()
    
    def test_next_y_basic(self):
        """Test basic next_y functionality."""
        result = self.ai.next_y(0.5, 'medium')
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)
    
    def test_difficulty_levels(self):
        """Test different difficulty levels."""
        for difficulty in ['easy', 'medium', 'hard']:
            result = self.ai.next_y(0.5, difficulty)
            self.assertIsInstance(result, float)
            self.assertGreaterEqual(result, 0.0)
            self.assertLessEqual(result, 1.0)
    
    def test_ball_prediction(self):
        """Test ball trajectory prediction."""
        prediction = self.ai.predict_ball_trajectory(
            ball_x=100, ball_y=200, ball_vx=5, ball_vy=2, paddle_x=600
        )
        
        self.assertIsInstance(prediction.target_y, float)
        self.assertIsInstance(prediction.time_to_reach, float)
        self.assertIsInstance(prediction.confidence, float)
        
        self.assertGreaterEqual(prediction.target_y, 0.0)
        self.assertLessEqual(prediction.target_y, 1.0)
        self.assertGreaterEqual(prediction.confidence, 0.0)
        self.assertLessEqual(prediction.confidence, 1.0)


class TestInputManager(unittest.TestCase):
    """Test input manager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.input_manager = InputManager()
    
    def test_fuse_empty_inputs(self):
        """Test fusing empty inputs."""
        vision_state = {'players': []}
        voice_cmds = []
        
        result = self.input_manager.fuse(vision_state, voice_cmds, 'single')
        
        self.assertEqual(result.p1_y, 0.5)
        self.assertEqual(result.p2_y, 0.5)
        self.assertEqual(result.speed_delta, 0.0)
        self.assertEqual(result.meta['mode'], 'single')
    
    def test_fuse_with_players(self):
        """Test fusing with player data."""
        vision_state = {
            'players': [
                {'id': 1, 'y_norm': 0.3, 'gesture': 'fist'},
                {'id': 2, 'y_norm': 0.7, 'gesture': 'open'}
            ]
        }
        voice_cmds = ['faster']
        
        result = self.input_manager.fuse(vision_state, voice_cmds, 'two_player')
        
        self.assertIsInstance(result.p1_y, float)
        self.assertIsInstance(result.p2_y, float)
        self.assertGreaterEqual(result.p1_y, 0.0)
        self.assertLessEqual(result.p1_y, 1.0)
        self.assertGreaterEqual(result.p2_y, 0.0)
        self.assertLessEqual(result.p2_y, 1.0)
    
    def test_calibration(self):
        """Test calibration functionality."""
        self.input_manager.calibrate_player('p1', 0.2, 0.8)
        
        status = self.input_manager.get_calibration_status()
        self.assertEqual(status['p1_min_y'], 0.2)
        self.assertEqual(status['p1_max_y'], 0.8)
    
    def test_reset_calibration(self):
        """Test calibration reset."""
        self.input_manager.calibrate_player('p1', 0.2, 0.8)
        self.input_manager.reset_calibration()
        
        status = self.input_manager.get_calibration_status()
        self.assertFalse(status['calibrated'])


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_hand_mapping(self):
        """Test hand position mapping."""
        # Simulate hand tracking data
        vision_state = {
            'players': [
                {'id': 1, 'y_norm': 0.2, 'gesture': 'fist', 'x': 200, 'y': 100},
                {'id': 2, 'y_norm': 0.8, 'gesture': 'open', 'x': 500, 'y': 400}
            ],
            'meta': {'timestamp': 1234567890, 'fps': 30}
        }
        
        input_manager = InputManager()
        result = input_manager.fuse(vision_state, [], 'two_player')
        
        # Verify mapping
        self.assertIsInstance(result.p1_y, float)
        self.assertIsInstance(result.p2_y, float)
        self.assertGreaterEqual(result.p1_y, 0.0)
        self.assertLessEqual(result.p1_y, 1.0)
    
    def test_voice_parsing(self):
        """Test voice command parsing."""
        input_manager = InputManager()
        
        # Test speed commands
        result1 = input_manager.fuse({'players': []}, ['faster'], 'single')
        self.assertGreater(result1.speed_delta, 0)
        
        result2 = input_manager.fuse({'players': []}, ['slower'], 'single')
        self.assertLess(result2.speed_delta, 0)
    
    def test_physics_simulation(self):
        """Test basic physics simulation."""
        from src.game.game_engine import GameEngine, EngineInput
        
        game = GameEngine()
        
        # Test basic game tick
        input_state = EngineInput(p1_y=0.5, p2_y=0.5, speed_delta=0.0, meta={})
        game_state = game.tick(input_state, [])
        
        # Verify game state
        self.assertIsInstance(game_state.ball_x, float)
        self.assertIsInstance(game_state.ball_y, float)
        self.assertIsInstance(game_state.score1, int)
        self.assertIsInstance(game_state.score2, int)


if __name__ == '__main__':
    unittest.main()
