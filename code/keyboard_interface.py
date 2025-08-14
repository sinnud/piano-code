import json
import os
import sys
import glob
from .piano_sound import PianoSound


class KeyboardInterface:
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default path relative to the project root
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'keyboard_layout.json')
        
        self.config_path = config_path
        self.config_dir = os.path.dirname(config_path)
        self.piano = PianoSound(duration=1.0, blocking=False, instrument='piano', basetone='C')  # Keyboard settings
        self.key_mappings = {}
        self.controls = {}
        self.current_layout = {}
        self.available_layouts = []
        self.current_layout_index = 0
        
        # Discover all available layouts
        self._discover_layouts()
        
        # Load initial layout
        self.load_config()
        
    def _discover_layouts(self):
        """Discover all available keyboard layout JSON files."""
        try:
            # Find all JSON files in config directory
            pattern = os.path.join(self.config_dir, '*.json')
            layout_files = glob.glob(pattern)
            
            self.available_layouts = []
            for file_path in sorted(layout_files):
                try:
                    with open(file_path, 'r') as f:
                        layout = json.load(f)
                    
                    # Validate layout has required fields
                    if 'title' in layout and 'key_mappings' in layout:
                        self.available_layouts.append({
                            'path': file_path,
                            'title': layout['title'],
                            'description': layout.get('description', ''),
                            'filename': os.path.basename(file_path)
                        })
                    else:
                        print(f"⚠️  Skipping invalid layout: {file_path}")
                        
                except (json.JSONDecodeError, IOError) as e:
                    print(f"⚠️  Could not load layout {file_path}: {e}")
            
            # Find current layout index
            current_filename = os.path.basename(self.config_path)
            for i, layout in enumerate(self.available_layouts):
                if layout['filename'] == current_filename:
                    self.current_layout_index = i
                    break
                    
            print(f"🎹 Discovered {len(self.available_layouts)} keyboard layouts")
            
        except Exception as e:
            print(f"⚠️  Layout discovery error: {e}")
            self.available_layouts = []
    
    def load_config(self, config_path: str = None):
        """Load keyboard layout configuration from JSON file."""
        if config_path:
            self.config_path = config_path
            
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            self.current_layout = config
            self.key_mappings = config.get('key_mappings', {})
            self.controls = config.get('controls', {})
            basetone = config.get('basetone', 'C')
            self.piano.set_basetone(basetone)
            
            layout_title = config.get('title', 'Unknown')
            print(f"🎹 Loaded keyboard layout: {layout_title}")
            print(f"🎼 Base tone: {self.piano.basetone}")
            print(f"🗝️  Mapped keys: {len(self.key_mappings)}")
            
        except FileNotFoundError:
            print(f"❌ Config file not found: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config file: {e}")
            raise
    
    def print_help(self):
        """Print keyboard layout help with configuration explanations."""
        layout_title = self.current_layout.get('title', 'Unknown Layout')
        layout_desc = self.current_layout.get('description', '')
        
        print(f"\n🎹 Piano Keyboard Interface")
        print("=" * 60)
        
        # Configuration explanations
        print("🔧 Current Configuration:")
        print(f"  Layout: {layout_title}")
        if layout_desc:
            print(f"  Description: {layout_desc}")
        print(f"  Base Tone (1=): {self.piano.basetone} - Sets the pitch of note '1' (do)")
        print(f"  Instrument: {self.piano.instrument.title()} - Changes the sound character")
        
        if len(self.available_layouts) > 1:
            print(f"  Available Layouts: {len(self.available_layouts)} total")
        print()
        
        # Show keyboard layout visually
        self._print_keyboard_layout()
        
        print("\n🎹 Controls:")
        for key, action in self.controls.items():
            if action == "change_basetone":
                print(f"  {key:6} → Cycle basetone (C, C#, D, D#, E, F, F#, G, G#, A, A#, B)")
            elif action == "change_instrument":
                print(f"  {key:6} → Cycle instrument (Piano, Guitar, Saxophone, Violin)")
            elif action == "change_layout":
                print(f"  {key:6} → Cycle keyboard layout")
            else:
                print(f"  {key:6} → {action}")
        
        print("\n📝 Special Commands (simple mode):")
        print("  help     → Show this help")
        print("  layouts  → List all available layouts")
        print("  config   → Show configuration details")
        print("  quit     → Exit application")
        
        print("\n🎵 Just press mapped keys to play notes!")
        print("=" * 60)
    
    def _print_keyboard_layout(self):
        """Print a visual representation of the keyboard layout."""
        print("⌨️  Keyboard Layout (your computer keyboard):")
        print()
        
        # Define keyboard rows as they appear on a real keyboard
        keyboard_rows = [
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'"],
            ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/']
        ]
        
        row_prefixes = ['     ', '      ', '       ']  # Simulate keyboard staggering
        
        for row_idx, keys in enumerate(keyboard_rows):
            print(row_prefixes[row_idx], end='')
            for key in keys:
                if key in self.key_mappings:
                    note = self.key_mappings[key]
                    # Show full note name with better spacing
                    if len(note) <= 2:  # Short notes like "1", ".1", "^1"
                        print(f"[{key.upper()}  {note}]", end=' ')
                    else:  # Longer notes like ".#1", "^#1"
                        print(f"[{key.upper()}{note}]", end=' ')
                else:
                    print(f"  {key.upper()}  ", end=' ')
            print()
        
        print()
        print("Legend: [KEY  Note] or [KEYNote] = Piano key | KEY = Regular key")
        print("Notes: .1=Low octave, 1=Middle octave, ^1=High octave | #=Sharp")
    
    def get_note_name(self, note: str) -> str:
        """Convert note to readable name."""
        note_names = {
            '.1': 'C3 (low do)', '.2': 'D3 (low re)', '.3': 'E3 (low mi)',
            '.4': 'F3 (low fa)', '.5': 'G3 (low sol)', '.6': 'A3 (low la)', '.7': 'B3 (low ti)',
            '1': 'C4 (do)', '2': 'D4 (re)', '3': 'E4 (mi)',
            '4': 'F4 (fa)', '5': 'G4 (sol)', '6': 'A4 (la)', '7': 'B4 (ti)',
            '^1': 'C5 (high do)', '^2': 'D5 (high re)', '^3': 'E5 (high mi)',
            '^4': 'F5 (high fa)', '^5': 'G5 (high sol)', '^6': 'A5 (high la)', '^7': 'B5 (high ti)'
        }
        return note_names.get(note, f"Note {note}")
    
    def play_key(self, key: str):
        """Play sound for the given keyboard key."""
        if key in self.key_mappings:
            note = self.key_mappings[key]
            try:
                self.piano.play_note(note, duration=1.0)
            except Exception as e:
                print(f"⚠️  Audio error for {note}: {e}")
        else:
            print(f"⚠️  Key '{key}' not mapped")
    
    def stop_sound(self):
        """Stop currently playing sound."""
        self.piano.stop()
        print("🛑 Sound stopped")
    
    def change_basetone(self):
        """Interactive basetone change."""
        available_tones = list(self.piano.base_frequencies.keys())
        print(f"\n🎼 Current basetone: {self.piano.basetone}")
        print(f"Available tones: {', '.join(available_tones)}")
        print("Type new basetone and press Enter (or Esc to cancel):")
        
        try:
            import termios
            import tty
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            # Restore normal terminal mode for line input
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
            # Get input with prompt
            user_input = ""
            print("🎼 > ", end="", flush=True)
            
            while True:
                # Read character by character to handle Esc
                tty.setraw(fd)
                char = sys.stdin.read(1)
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                
                if ord(char) == 27:  # Escape key
                    print("\n🚫 Basetone change cancelled")
                    break
                elif ord(char) == 13 or ord(char) == 10:  # Enter key
                    new_basetone = user_input.strip().upper()
                    if not new_basetone:
                        print("\n🚫 Basetone change cancelled")
                    elif new_basetone in available_tones:
                        self.piano.set_basetone(new_basetone)
                        print(f"\n✅ Basetone changed to: {new_basetone}")
                    else:
                        print(f"\n❌ Invalid basetone: {new_basetone}")
                        print(f"Available: {', '.join(available_tones)}")
                    break
                elif ord(char) == 127 or ord(char) == 8:  # Backspace
                    if user_input:
                        user_input = user_input[:-1]
                        print("\b \b", end="", flush=True)
                elif char.isprintable():
                    user_input += char
                    print(char, end="", flush=True)
                    
        except (KeyboardInterrupt, EOFError):
            print("\n🚫 Basetone change cancelled")
        finally:
            # Restore original terminal settings (don't assume raw mode)
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            except:
                pass
    
    def change_instrument(self):
        """Cycle through instruments."""
        current_index = self.piano.instruments.index(self.piano.instrument)
        next_index = (current_index + 1) % len(self.piano.instruments)
        new_instrument = self.piano.instruments[next_index]
        
        self.piano.set_instrument(new_instrument)
        
        # Choose appropriate emoji for instrument
        instrument_emojis = {
            'piano': '🎹',
            'guitar': '🎸',
            'saxophone': '🎷',
            'violin': '🎻'
        }
        emoji = instrument_emojis.get(new_instrument, '🎵')
        
        print(f"{emoji} Instrument changed: {new_instrument.title()}")
        
        # Show cycle order
        instrument_list = " → ".join([inst.title() for inst in self.piano.instruments])
        print(f"   Cycle: {instrument_list}")
    
    def change_layout(self):
        """Cycle through available keyboard layouts."""
        if len(self.available_layouts) <= 1:
            print("⚠️  Only one layout available")
            return
            
        # Move to next layout
        self.current_layout_index = (self.current_layout_index + 1) % len(self.available_layouts)
        next_layout = self.available_layouts[self.current_layout_index]
        
        try:
            # Load the new layout
            self.load_config(next_layout['path'])
            print(f"✨ Layout changed to: {next_layout['title']}")
            
            # Show available layouts with current indicator
            self._show_layout_cycle()
            
        except Exception as e:
            print(f"❌ Error changing layout: {e}")
            # Revert to previous layout
            self.current_layout_index = (self.current_layout_index - 1) % len(self.available_layouts)
    
    def _show_layout_cycle(self):
        """Show the layout cycle with current selection highlighted."""
        if len(self.available_layouts) <= 1:
            return
            
        layout_names = []
        for i, layout in enumerate(self.available_layouts):
            if i == self.current_layout_index:
                layout_names.append(f"[{layout['title']}]")  # Current layout
            else:
                layout_names.append(layout['title'])
        
        cycle_text = " → ".join(layout_names)
        print(f"   Layouts: {cycle_text}")
    
    def list_layouts(self):
        """List all available layouts with details."""
        print(f"\n🎹 Available Keyboard Layouts ({len(self.available_layouts)}):")
        print("=" * 50)
        
        for i, layout in enumerate(self.available_layouts):
            current_marker = ">>> " if i == self.current_layout_index else "    "
            print(f"{current_marker}{layout['title']}")
            if layout['description']:
                print(f"     {layout['description']}")
            print(f"     File: {layout['filename']}")
            if i < len(self.available_layouts) - 1:
                print()
        
        print("=" * 50)
    
    def show_config_details(self):
        """Show detailed configuration explanations."""
        print("\n🔧 Configuration Details")
        print("=" * 40)
        
        print("🎼 What is Base Tone?")
        print("  • Sets the pitch of note '1' (do in solfege)")
        print("  • C = Standard piano middle C")
        print("  • D = One tone higher than C")
        print("  • Each step changes all notes proportionally")
        print(f"  • Current: {self.piano.basetone} (press '1' to change)")
        print()
        
        print("🎹 What are Instruments?")
        print("  • Piano: Rich harmonics, fast decay (classic piano)")
        print("  • Guitar: Plucked string, medium decay (acoustic guitar)")
        print("  • Saxophone: Reed instrument, breathy (jazz sax)")
        print("  • Violin: Bowed string, sustained (orchestral violin)")
        print(f"  • Current: {self.piano.instrument.title()} (press '2' to change)")
        print()
        
        print("🗺️ What are Layouts?")
        print("  • Different key-to-note mappings")
        print("  • Default: 'a' plays low do (.1)")
        print("  • A as Mi: 'a' plays low mi (.3)")
        print("  • Changes which notes your fingers play")
        print(f"  • Current: {self.current_layout.get('title', 'Unknown')} (press '3' to change)")
        print()
        
        print("🎵 Note System:")
        print("  • Numbers 1-7 = Do, Re, Mi, Fa, Sol, La, Ti")
        print("  • .1-.7 = Low octave (one octave down)")
        print("  • ^1-^7 = High octave (one octave up)")
        print("  • # = Sharp (e.g., #1 = Do sharp)")
        print()
        
        print("Type 'help' to see keyboard layout")
    
    def run_simple_input(self):
        """Run keyboard interface with simple input() method."""
        self.print_help()
        
        print("\n🎮 Simple Input Mode")
        print("Type keys and press Enter (or 'quit' to exit):")
        
        try:
            while True:
                user_input = input("🎹 > ").strip().lower()
                
                if user_input in ['quit', 'exit']:
                    break
                elif user_input == 'help':
                    self.print_help()
                elif user_input == 'layouts':
                    self.list_layouts()
                elif user_input == 'config':
                    self.show_config_details()
                elif user_input == 'space' or user_input == ' ':
                    self.stop_sound()
                elif user_input in self.controls:
                    action = self.controls[user_input]
                    if action == 'stop':
                        self.stop_sound()
                    elif action == 'quit':
                        break
                    elif action == 'change_basetone':
                        self.change_basetone()
                    elif action == 'change_instrument':
                        self.change_instrument()
                    elif action == 'change_layout':
                        self.change_layout()
                elif len(user_input) == 1:
                    self.play_key(user_input)
                else:
                    # Handle multiple characters or special combinations
                    for char in user_input:
                        if char in self.key_mappings:
                            self.play_key(char)
                        elif char == ' ':
                            self.stop_sound()
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
        except EOFError:
            print("\n\n👋 Goodbye!")
    
    def run_realtime_input(self):
        """Run keyboard interface with real-time key detection."""
        print("\n🎮 Real-time Input Mode")
        print("Press keys directly (no Enter needed). Press ESC to quit.")
        
        # Show initial help to user
        print("\n📝 Keyboard Layout:")
        self._print_keyboard_layout()
        print("\n🔑 Control Keys: 1=Basetone | 2=Instrument | 3=Layout | SPACE=Stop | ESC=Quit")
        print("\n🎵 Ready! Press piano keys to play...")
        
        try:
            import termios
            import tty
            
            # Save original terminal settings
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            try:
                # Set terminal to raw mode for single character input
                tty.setraw(sys.stdin.fileno())
                
                while True:
                    # Read single character
                    char = sys.stdin.read(1)
                    
                    # Handle ESC key (quit immediately)
                    if ord(char) == 27:
                        print("\n👋 Goodbye!")
                        break
                    
                    # Convert to lowercase for consistency
                    char = char.lower()
                    
                    # Handle space (stop)
                    if char == ' ':
                        self.stop_sound()
                    
                    # Handle control keys
                    elif char in self.controls:
                        action = self.controls[char]
                        if action == 'change_basetone':
                            print(f"\n🎼 Control Mode: Basetone")
                            self.change_basetone()
                            # Show layout again after returning from control
                            print("\n📝 Keyboard Layout:")
                            self._print_keyboard_layout()
                            print("\n🎵 Back to playing mode. Press keys to play!")
                        elif action == 'change_instrument':
                            print(f"\n🎵 Control Mode: Instrument")
                            self.change_instrument()
                            # Show layout again after returning from control
                            print("\n📝 Keyboard Layout:")
                            self._print_keyboard_layout()
                            print("\n🎵 Back to playing mode. Press keys to play!")
                        elif action == 'change_layout':
                            print(f"\n🎹 Control Mode: Layout")
                            self.change_layout()
                            # Show layout again after returning from control (layout will have changed)
                            print("\n📝 New Keyboard Layout:")
                            self._print_keyboard_layout()
                            print("\n🎵 Back to playing mode. Press keys to play!")
                        elif action == 'stop':
                            self.stop_sound()
                        elif action == 'quit':
                            print("\n👋 Goodbye!")
                            break
                    
                    # Handle mapped keys
                    elif char in self.key_mappings:
                        self.play_key(char)
                    
                    # Handle special characters
                    elif char == ';':
                        self.play_key(char)
                    
                    # Ignore other characters (don't spam for unmapped keys)
                    else:
                        if ord(char) >= 32 and len(char) == 1:  # Printable character
                            pass  # Silently ignore unmapped keys
            
            finally:
                # Restore original terminal settings
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                
        except ImportError:
            print("❌ Real-time input requires Unix/Linux/macOS terminal.")
            print("Falling back to simple input mode...")
            self.run_simple_input()
        except Exception as e:
            print(f"❌ Error in real-time mode: {e}")
            print("Falling back to simple input mode...")
            self.run_simple_input()


def main():
    """Main function to run keyboard interface."""
    try:
        interface = KeyboardInterface()
        # Try real-time input first, fall back to simple input
        interface.run_realtime_input()
    except Exception as e:
        print(f"❌ Error starting keyboard interface: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()