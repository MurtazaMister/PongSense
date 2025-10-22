"""
Voice recognition module using SpeechRecognition.
Implements deterministic interface: start(), stop(), drain_commands()
"""

import speech_recognition as sr
import threading
import time
from typing import List, Optional
from queue import Queue, Empty
import pyaudio

from utils.logger import logger
from utils.config import config


class VoiceRecognizer:
    """Voice recognition with deterministic interface."""
    
    def __init__(self):
        """Initialize voice recognizer."""
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_running = False
        self.thread = None
        self.command_queue = Queue()
        self._lock = threading.Lock()
        
        # Configuration
        self.language = config.get('voice_recognition.language', 'en-US')
        self.timeout = config.get('voice_recognition.timeout', 1.0)
        self.phrase_timeout = config.get('voice_recognition.phrase_timeout', 0.3)
        self.energy_threshold = config.get('voice_recognition.energy_threshold', 300)
        self.dynamic_energy_threshold = config.get('voice_recognition.dynamic_energy_threshold', True)
        self.command_cooldown = config.get('voice_recognition.command_cooldown', 2.0)
        self.supported_commands = config.get('voice_recognition.supported_commands', ['faster', 'slower'])
        
        # Command tracking
        self._last_command_time = 0
        self._command_history = []
        
        logger.info("VoiceRecognizer initialized")
    
    def start(self) -> bool:
        """Start voice recognition.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                logger.warning("Voice recognizer already running")
                return True
            
            # Initialize microphone
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Configure recognizer
            self.recognizer.energy_threshold = self.energy_threshold
            self.recognizer.dynamic_energy_threshold = self.dynamic_energy_threshold
            
            self.is_running = True
            self.thread = threading.Thread(target=self._recognition_loop, daemon=True)
            self.thread.start()
            
            logger.info("Voice recognizer started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start voice recognizer: {e}")
            return False
    
    def stop(self) -> None:
        """Stop voice recognition."""
        try:
            self.is_running = False
            
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2.0)
            
            # Clear command queue
            while not self.command_queue.empty():
                try:
                    self.command_queue.get_nowait()
                except Empty:
                    break
            
            logger.info("Voice recognizer stopped")
            
        except Exception as e:
            logger.error(f"Error stopping voice recognizer: {e}")
    
    def drain_commands(self) -> List[str]:
        """Drain all pending voice commands.
        
        Returns:
            List of recognized commands
        """
        commands = []
        
        try:
            while not self.command_queue.empty():
                command = self.command_queue.get_nowait()
                commands.append(command)
                
        except Empty:
            pass
        
        return commands
    
    def _recognition_loop(self) -> None:
        """Main recognition loop running in separate thread."""
        logger.info("Voice recognition loop started")
        
        while self.is_running:
            try:
                # Listen for audio
                with self.microphone as source:
                    # Use timeout to prevent blocking
                    audio = self.recognizer.listen(
                        source, 
                        timeout=self.timeout,
                        phrase_time_limit=self.phrase_timeout
                    )
                
                # Recognize speech
                try:
                    text = self.recognizer.recognize_google(audio, language=self.language)
                    text = text.lower().strip()
                    
                    logger.debug(f"Recognized text: '{text}'")
                    
                    # Check if it's a supported command
                    command = self._parse_command(text)
                    if command:
                        self._add_command(command)
                    
                except sr.UnknownValueError:
                    # Speech was unintelligible
                    pass
                except sr.RequestError as e:
                    logger.error(f"Speech recognition error: {e}")
                    time.sleep(1)
                
            except sr.WaitTimeoutError:
                # Timeout waiting for speech
                pass
            except Exception as e:
                logger.error(f"Error in recognition loop: {e}")
                time.sleep(0.1)
        
        logger.info("Voice recognition loop ended")
    
    def _parse_command(self, text: str) -> Optional[str]:
        """Parse recognized text for supported commands.
        
        Args:
            text: Recognized speech text
            
        Returns:
            Command string if valid, None otherwise
        """
        # Check for exact matches first
        for command in self.supported_commands:
            if command in text:
                return command
        
        # Check for partial matches or synonyms
        if 'speed' in text or 'velocity' in text:
            if 'up' in text or 'increase' in text or 'more' in text:
                return 'faster'
            elif 'down' in text or 'decrease' in text or 'less' in text:
                return 'slower'
        
        return None
    
    def _add_command(self, command: str) -> None:
        """Add command to queue with cooldown check.
        
        Args:
            command: Command to add
        """
        current_time = time.time()
        
        # Check cooldown
        if current_time - self._last_command_time < self.command_cooldown:
            logger.debug(f"Command '{command}' ignored due to cooldown")
            return
        
        # Add to queue
        try:
            self.command_queue.put_nowait(command)
            self._last_command_time = current_time
            
            # Track command history
            self._command_history.append({
                'command': command,
                'timestamp': current_time
            })
            
            # Keep only last 10 commands
            if len(self._command_history) > 10:
                self._command_history = self._command_history[-10:]
            
            logger.info(f"Voice command recognized: '{command}'")
            
        except Exception as e:
            logger.error(f"Error adding command to queue: {e}")
    
    def get_command_history(self) -> List[dict]:
        """Get command history for debugging.
        
        Returns:
            List of recent commands with timestamps
        """
        return self._command_history.copy()
    
    def clear_command_history(self) -> None:
        """Clear command history."""
        self._command_history.clear()
        logger.info("Command history cleared")
