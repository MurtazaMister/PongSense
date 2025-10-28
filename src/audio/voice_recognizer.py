"""
Voice recognition module using Vosk for offline speech recognition.
Implements deterministic interface: start(), stop(), drain_commands()
"""

import json
import os
import threading
import time
from typing import List, Optional
from queue import Queue, Empty
import pyaudio
import vosk

from utils.logger import logger
from utils.config import config


class VoiceRecognizer:
    """Real offline speech recognition using Vosk."""
    
    def __init__(self):
        """Initialize voice recognizer."""
        self.model = None
        self.recognizer = None
        self.microphone = None
        self.audio_stream = None
        self.is_running = False
        self.thread = None
        self.command_queue = Queue()
        self._lock = threading.Lock()
        
        # Audio configuration
        self.sample_rate = 16000  # Vosk works best with 16kHz
        self.chunk_size = 4000    # Larger chunks for better recognition
        self.channels = 1
        self.format = pyaudio.paInt16
        
        # Configuration
        self.command_cooldown = config.get('voice_recognition.command_cooldown', 2.0)
        self.supported_commands = config.get('voice_recognition.supported_commands', ['faster', 'slower'])
        
        # Command tracking
        self._last_command_time = 0
        self._command_history = []
        self._last_recognized_text = ''  # Track the last recognized text for caption display
        self._last_command_word = ''  # Track the specific word that triggered a command
        self._last_word_timestamp = 0  # Track when the word was recognized for fade-out
        
        # Model path
        self.model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models', 'vosk-model-small-en-us-0.15')
        
        logger.info("Vosk-based VoiceRecognizer initialized")
    
    def start(self) -> bool:
        """Start offline speech recognition using Vosk.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                logger.warning("Voice recognizer already running")
                return True
            
            # Check if model exists
            if not os.path.exists(self.model_path):
                logger.error(f"Vosk model not found at: {self.model_path}")
                return False
            
            # Initialize Vosk model
            logger.info(f"Loading Vosk model from: {self.model_path}")
            self.model = vosk.Model(self.model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
            
            # Initialize PyAudio
            self.microphone = pyaudio.PyAudio()
            
            # Open audio stream
            self.audio_stream = self.microphone.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info("Vosk model loaded and microphone initialized")
            
            self.is_running = True
            self.thread = threading.Thread(target=self._recognition_loop, daemon=True)
            self.thread.start()
            
            logger.info("Offline speech recognizer started successfully")
            logger.info("Say 'faster' or 'slower' to control game speed")
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
            
            # Close audio stream
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            
            # Terminate PyAudio
            if self.microphone:
                self.microphone.terminate()
                self.microphone = None
            
            # Clear command queue
            while not self.command_queue.empty():
                try:
                    self.command_queue.get_nowait()
                except Empty:
                    break
            
            logger.info("Offline speech recognizer stopped")
            
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
        """Main recognition loop using Vosk for offline speech recognition."""
        logger.info("Vosk recognition loop started")
        
        while self.is_running:
            try:
                # Read audio data
                data = self.audio_stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Feed audio to recognizer
                if self.recognizer.AcceptWaveform(data):
                    # Get final result
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').strip().lower()
                    
                    if text:
                        logger.info(f"Recognized speech: '{text}'")
                        
                        # Store the last recognized text for caption display
                        self._last_recognized_text = text
                        
                        # Parse command from recognized text
                        command = self._parse_command(text)
                        if command:
                            # Find and store the specific word that triggered the command
                            self._last_command_word = self._find_command_word(text, command)
                            self._last_word_timestamp = time.time()  # Record timestamp for fade-out
                            self._add_command(command)
                            logger.info(f"Voice command detected: '{command}'")
                
                else:
                    # Get partial result
                    partial_result = json.loads(self.recognizer.PartialResult())
                    partial_text = partial_result.get('partial', '').strip().lower()
                    
                    if partial_text:
                        logger.debug(f"Partial recognition: '{partial_text}'")
                
                time.sleep(0.01)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                logger.error(f"Error in recognition loop: {e}")
                time.sleep(0.1)
        
        logger.info("Vosk recognition loop ended")
    
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
        
        # Check for synonyms and variations
        faster_words = ['faster', 'fast', 'quicker', 'quick', 'speed up', 'increase speed', 'more speed']
        slower_words = ['slower', 'slow', 'slow down', 'decrease speed', 'less speed']
        
        text_lower = text.lower()
        
        # Check for faster variations
        for word in faster_words:
            if word in text_lower:
                return 'faster'
        
        # Check for slower variations
        for word in slower_words:
            if word in text_lower:
                return 'slower'
        
        # Check for context-based recognition
        if 'speed' in text_lower or 'velocity' in text_lower:
            if any(word in text_lower for word in ['up', 'increase', 'more', 'higher', 'boost']):
                return 'faster'
            elif any(word in text_lower for word in ['down', 'decrease', 'less', 'lower', 'reduce']):
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
    
    def get_last_recognized_text(self) -> str:
        """Get the last recognized text for caption display.
        
        Returns:
            Last recognized text/word
        """
        # Return the specific command word if available, otherwise return the last recognized text
        return self._last_command_word if self._last_command_word else self._last_recognized_text
    
    def get_last_word_timestamp(self) -> float:
        """Get the timestamp when the last word was recognized.
        
        Returns:
            Timestamp of the last recognized word
        """
        return self._last_word_timestamp
    
    def _find_command_word(self, text: str, command: str) -> str:
        """Find the specific word in the text that matched the command.
        
        Args:
            text: The full recognized text
            command: The extracted command ('faster' or 'slower')
            
        Returns:
            The specific word that triggered the command
        """
        words = text.lower().split()
        command_lower = command.lower()
        
        # Look for the command word in the text
        for word in words:
            if command_lower in word or word in command_lower:
                return word
        
        # Fall back to command if not found
        return command
