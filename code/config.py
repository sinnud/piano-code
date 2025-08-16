#!/usr/bin/env python3
"""
Configuration management for Piano Code project.

Centralizes all constants, settings, and configuration logic.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class AudioConfig:
    """Audio system configuration constants."""
    
    # Sample rates
    DEFAULT_SAMPLE_RATE = 44100
    FALLBACK_SAMPLE_RATES = [44100, 22050, 48000]
    
    # Buffer sizes for audio streaming
    BUFFER_SIZES = [512, 1024, 2048, 4096]
    DEFAULT_BUFFER_SIZE = 1024
    CHUNK_SIZE = 2048
    
    # Audio duration and timing
    DEFAULT_DURATION = 1.0
    GUI_DURATION = 0.8
    MIN_DURATION = 0.1
    MAX_DURATION = 10.0
    
    # Volume settings
    DEFAULT_VOLUME = 0.7
    MIN_VOLUME = 0.0
    MAX_VOLUME = 1.0
    VOLUME_STEP = 0.05
    
    # Performance settings
    MAX_STREAM_ERRORS = 3
    STREAM_TIMEOUT_MS = 100
    MAX_LRU_CACHE_SIZE = 200


class GUIConfig:
    """GUI interface configuration constants."""
    
    # Window settings
    DEFAULT_WINDOW_SIZE = "900x650"
    MIN_WINDOW_SIZE = "800x500"
    
    # Key visual feedback timing (milliseconds)
    KEY_HIGHLIGHT_DURATION = 400
    KEY_CLEANUP_DELAY = 1000
    STATUS_MESSAGE_DURATION = 2000
    
    # Colors
    PIANO_KEY_COLOR = "lightgreen"
    PIANO_KEY_TEXT_COLOR = "darkgreen"
    NON_PIANO_KEY_COLOR = "lightgray"
    NON_PIANO_KEY_TEXT_COLOR = "black"
    ACTIVE_KEY_COLOR = "#FF4500"
    ACTIVE_KEY_TEXT_COLOR = "blue"
    
    # Fonts
    DEFAULT_FONT = ("Arial", 8)
    TITLE_FONT = ("Arial", 18, "bold")
    BUTTON_FONT = ("Arial", 8, "normal")
    BUTTON_FONT_BOLD = ("Arial", 8, "bold")


class MusicConfig:
    """Musical notation and theory configuration."""
    
    # Base frequencies (4th octave in Hz)
    BASE_FREQUENCIES = {
        'C': 261.63,   'C#': 277.18,  'D': 293.66,   'D#': 311.13,
        'E': 329.63,   'F': 349.23,   'F#': 369.99,  'G': 392.00,
        'G#': 415.30,  'A': 440.00,   'A#': 466.16,  'B': 493.88,
    }
    
    # Available instruments
    INSTRUMENTS = ['piano', 'guitar', 'saxophone', 'violin']
    DEFAULT_INSTRUMENT = 'piano'
    
    # Default basetone
    DEFAULT_BASETONE = 'C'
    
    # Common basetones for background pre-generation
    COMMON_BASETONES = ['C', 'D', 'G', 'F']
    
    # Solfege display mapping
    SOLFEGE_DISPLAY = {
        '.1': 'low do', '.2': 'low re', '.3': 'low mi', '.4': 'low fa', 
        '.5': 'low sol', '.6': 'low la', '.7': 'low ti',
        '1': 'do', '2': 're', '3': 'mi', '4': 'fa', '5': 'sol', '6': 'la', '7': 'ti',
        '^1': 'high do', '^2': 'high re', '^3': 'high mi', '^4': 'high fa', 
        '^5': 'high sol', '^6': 'high la', '^7': 'high ti',
        '#1': 'do#', '#2': 're#', '#4': 'fa#', '#5': 'sol#', '#6': 'la#',
        '.#1': 'low do#', '.#2': 'low re#', '.#4': 'low fa#', 
        '.#5': 'low sol#', '.#6': 'low la#'
    }


class LoggingConfig:
    """Logging configuration."""
    
    # Log levels
    DEFAULT_LEVEL = logging.INFO
    DEBUG_LEVEL = logging.DEBUG
    
    # Log format
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    SIMPLE_FORMAT = "%(levelname)s: %(message)s"
    
    # Log file settings
    LOG_DIR = "logs"
    LOG_FILE = "piano_code.log"
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 3


class ConfigManager:
    """Centralized configuration management."""
    
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            # Auto-detect project root (directory containing main.py)
            current_file = Path(__file__)
            self.project_root = current_file.parent.parent
        else:
            self.project_root = Path(project_root)
            
        self.config_dir = self.project_root / "config"
        self.log_dir = self.project_root / LoggingConfig.LOG_DIR
        
        # User preferences (loaded from file)
        self.user_preferences = {}
        self.preferences_file = self.config_dir / "user_preferences.json"
        
        # Load user preferences
        self._load_user_preferences()
    
    def _load_user_preferences(self):
        """Load user preferences from JSON file."""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r') as f:
                    self.user_preferences = json.load(f)
                    logging.debug(f"Loaded user preferences: {self.preferences_file}")
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Could not load user preferences: {e}")
            self.user_preferences = {}
    
    def save_user_preferences(self):
        """Save current user preferences to file."""
        try:
            self.config_dir.mkdir(exist_ok=True)
            with open(self.preferences_file, 'w') as f:
                json.dump(self.user_preferences, f, indent=2)
                logging.debug(f"Saved user preferences: {self.preferences_file}")
        except IOError as e:
            logging.error(f"Could not save user preferences: {e}")
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference value with fallback to default."""
        return self.user_preferences.get(key, default)
    
    def set_user_preference(self, key: str, value: Any):
        """Set user preference and automatically save."""
        self.user_preferences[key] = value
        self.save_user_preferences()
    
    def get_config_file_path(self, filename: str) -> Path:
        """Get full path to a config file."""
        return self.config_dir / filename
    
    def get_log_file_path(self) -> Path:
        """Get full path to log file."""
        self.log_dir.mkdir(exist_ok=True)
        return self.log_dir / LoggingConfig.LOG_FILE
    
    def setup_logging(self, level: int = None, console_only: bool = False):
        """Set up logging configuration."""
        if level is None:
            level = LoggingConfig.DEFAULT_LEVEL
            
        # Create formatters
        detailed_formatter = logging.Formatter(LoggingConfig.LOG_FORMAT)
        simple_formatter = logging.Formatter(LoggingConfig.SIMPLE_FORMAT)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.handlers.clear()  # Clear any existing handlers
        
        # Console handler (always)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(simple_formatter)
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)
        
        # File handler (optional)
        if not console_only:
            try:
                from logging.handlers import RotatingFileHandler
                log_file = self.get_log_file_path()
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=LoggingConfig.MAX_LOG_SIZE,
                    backupCount=LoggingConfig.BACKUP_COUNT
                )
                file_handler.setFormatter(detailed_formatter)
                file_handler.setLevel(logging.DEBUG)  # File gets more detail
                root_logger.addHandler(file_handler)
                logging.info(f"Logging to file: {log_file}")
            except Exception as e:
                logging.warning(f"Could not set up file logging: {e}")


# Global configuration instance
config_manager = ConfigManager()

# Convenience access to config classes
Audio = AudioConfig
GUI = GUIConfig
Music = MusicConfig
Logging = LoggingConfig