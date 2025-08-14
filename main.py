#!/usr/bin/env python3
"""
Main entry point for the piano code project.
"""

import sys
import os

# Add the code directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))

from code.keyboard_interface import KeyboardInterface


def main():
    """Main function."""
    print("🎹 Welcome to Piano Code!")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        mode_arg = sys.argv[1].lower()
        if mode_arg == 'simple':
            print("Starting simple input mode...")
            mode = 'simple'
        elif mode_arg == 'gui':
            print("Starting GUI mode...")
            mode = 'gui'
        else:
            print("Starting real-time input mode...")
            mode = 'realtime'
    else:
        print("Starting real-time input mode...")
        mode = 'realtime'
    
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
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()