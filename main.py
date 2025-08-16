#!/usr/bin/env python3
"""
Main entry point for the piano code project.
"""

import sys
import os
import logging

# Add the code directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))

from code.keyboard_interface import KeyboardInterface
from code.config import config_manager


def main():
    """Main function."""
    # Initialize logging
    config_manager.setup_logging(console_only=True)
    logger = logging.getLogger(__name__)
    
    logger.info("🎹 Welcome to Piano Code!")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        mode_arg = sys.argv[1].lower()
        if mode_arg == 'simple':
            logger.info("Starting simple input mode...")
            mode = 'simple'
        elif mode_arg == 'gui':
            logger.info("Starting GUI mode...")
            mode = 'gui'
        else:
            logger.info("Starting real-time input mode...")
            mode = 'realtime'
    else:
        logger.info("Starting real-time input mode...")
        mode = 'realtime'
    
    interface = None
    app = None
    
    try:
        if mode == 'gui':
            from code.piano_gui import PianoGUI
            app = PianoGUI()
            app.run()
        else:
            interface = KeyboardInterface()
            if mode == 'simple':
                interface.run_simple_input()
            else:
                interface.run_realtime_input()
    except KeyboardInterrupt:
        logger.info("\n\n🛑 Shutting down...")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        # Ensure proper cleanup of audio resources
        if interface and hasattr(interface, 'piano'):
            interface.piano.close()
        if app and hasattr(app, 'piano'):
            app.piano.close()
        logger.info("Resources cleaned up")
        sys.exit(0)


if __name__ == "__main__":
    main()