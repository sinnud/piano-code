#!/usr/bin/env python3
"""
Simple test script to show the ord() number of keys pressed.
Useful for debugging keyboard input and escape sequences.
"""

import sys
import os

def test_key_ord():
    """Test script to show ord() values of pressed keys."""
    print("🔍 Key Ord Number Test")
    print("=" * 30)
    print("Press keys to see their ord() numbers.")
    print("Press Ctrl+C to quit.")
    print()
    
    try:
        # Try to use raw mode for single character input
        import termios
        import tty
        
        print("📱 Raw input mode (single characters):")
        print("Press ESC to quit this mode.")
        print()
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            tty.setraw(sys.stdin.fileno())
            
            while True:
                char = sys.stdin.read(1)
                ord_val = ord(char)
                
                if ord_val == 27:  # ESC key
                    print(f"ESC pressed (ord: {ord_val}) - exiting raw mode")
                    break
                elif ord_val == 3:  # Ctrl+C
                    print(f"Ctrl+C pressed (ord: {ord_val}) - exiting")
                    break
                elif ord_val >= 32 and ord_val < 127:  # Printable ASCII
                    print(f"'{char}' pressed (ord: {ord_val})")
                else:  # Non-printable or special characters
                    print(f"Special key pressed (ord: {ord_val})")
                    
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
    except ImportError:
        print("⚠️  Raw mode not available on this system.")
        print("📝 Line input mode (press Enter after each key):")
        print("Type 'quit' to exit.")
        print()
        
        while True:
            try:
                user_input = input("Enter key(s): ")
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                    
                if len(user_input) == 1:
                    char = user_input[0]
                    ord_val = ord(char)
                    print(f"'{char}' has ord: {ord_val}")
                else:
                    print("Multiple characters:")
                    for i, char in enumerate(user_input):
                        ord_val = ord(char)
                        print(f"  [{i}] '{char}' has ord: {ord_val}")
                        
            except KeyboardInterrupt:
                print("\nCtrl+C pressed - exiting")
                break
            except EOFError:
                print("\nEOF - exiting")
                break
    
    except KeyboardInterrupt:
        print("\n\nCtrl+C pressed - exiting")
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    test_key_ord()