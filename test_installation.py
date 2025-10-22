"""
Simple test script to verify PongSense installation.
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import cv2
        print("OK OpenCV imported successfully")
    except ImportError as e:
        print(f"X OpenCV import failed: {e}")
        return False
    
    try:
        import mediapipe
        print("OK MediaPipe imported successfully")
    except ImportError as e:
        print(f"X MediaPipe import failed: {e}")
        return False
    
    try:
        import pygame
        print("OK Pygame imported successfully")
    except ImportError as e:
        print(f"X Pygame import failed: {e}")
        return False
    
    try:
        import speech_recognition
        print("OK SpeechRecognition imported successfully")
    except ImportError as e:
        print(f"X SpeechRecognition import failed: {e}")
        return False
    
    try:
        import pyaudio
        print("OK PyAudio imported successfully")
    except ImportError as e:
        print(f"X PyAudio import failed: {e}")
        return False
    
    try:
        import numpy
        print("OK NumPy imported successfully")
    except ImportError as e:
        print(f"X NumPy import failed: {e}")
        return False
    
    try:
        import yaml
        print("OK PyYAML imported successfully")
    except ImportError as e:
        print(f"X PyYAML import failed: {e}")
        return False
    
    return True

def test_camera():
    """Test camera access."""
    print("\nTesting camera access...")
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print("OK Camera access successful")
                cap.release()
                return True
            else:
                print("X Camera read failed")
                cap.release()
                return False
        else:
            print("X Camera not accessible")
            return False
    except Exception as e:
        print(f"X Camera test failed: {e}")
        return False

def test_microphone():
    """Test microphone access."""
    print("\nTesting microphone access...")
    
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        mic = sr.Microphone()
        
        with mic as source:
            print("OK Microphone access successful")
            return True
    except Exception as e:
        print(f"X Microphone test failed: {e}")
        return False

def test_pongsense_modules():
    """Test PongSense modules."""
    print("\nTesting PongSense modules...")
    
    try:
        # Add src to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        # Test imports without relative imports
        import utils.config
        print("OK Config module imported")
        
        import utils.logger
        print("OK Logger module imported")
        
        import vision.hand_tracker
        print("OK HandTracker module imported")
        
        import vision.gesture_recognizer
        print("OK GestureRecognizer module imported")
        
        import audio.voice_recognizer
        print("OK VoiceRecognizer module imported")
        
        import game.game_engine
        print("OK GameEngine module imported")
        
        import game.ai_opponent
        print("OK AIOpponent module imported")
        
        import multimodal.input_manager
        print("OK InputManager module imported")
        
        return True
        
    except Exception as e:
        print(f"X PongSense module test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("PongSense Installation Test")
    print("=" * 40)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test camera
    if not test_camera():
        all_passed = False
    
    # Test microphone
    if not test_microphone():
        all_passed = False
    
    # Test PongSense modules
    if not test_pongsense_modules():
        all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("OK All tests passed! PongSense is ready to run.")
        print("\nTo start the game, run:")
        print("python src/main.py")
    else:
        print("X Some tests failed. Please check the error messages above.")
        print("\nCommon solutions:")
        print("- Install missing dependencies: pip install -r requirements.txt")
        print("- Check camera/microphone permissions")
        print("- Ensure camera/microphone are not being used by other applications")

if __name__ == "__main__":
    main()
