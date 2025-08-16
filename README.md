# Piano Code Project 🎹

A comprehensive Python piano simulation application with multiple interfaces for playing musical notes using your Mac's sound card.

## Features

🎵 **Multiple Interfaces**
- **Real-time Terminal Mode** - Direct keyboard input without pressing Enter
- **Simple Terminal Mode** - Type keys and press Enter to play
- **GUI Mode** - Visual Mac keyboard layout with clickable keys

🎼 **Audio System** 
- PyAudio-based sound generation with realistic instrument sounds
- 3-octave note system (low, base, high) using solfege notation
- Chord playing capability
- Configurable basetones (C, D, E, F, G, A, B with sharps)
- 4 instrument types: Piano, Guitar, Saxophone, Violin

🖥️ **Visual Interface**
- Complete Mac keyboard layout visualization
- Piano keys highlighted in green, non-piano keys in gray
- Real-time visual feedback when keys are pressed
- Integrated controls for basetone and waveform selection

## Project Structure

```
piano_code/
├── code/
│   ├── piano_sound.py       # Core audio generation class
│   ├── keyboard_interface.py # Terminal-based keyboard interface  
│   ├── piano_gui.py         # GUI interface with Mac keyboard layout
│   └── __init__.py
├── config/
│   ├── keyboard_layout.json # Default key mappings configuration
│   ├── a_as_la_layout.json  # Alternative layout with 'a' as low la (.6)
│   ├── a_as_mi_layout.json  # Alternative layout with 'a' as low mi (.3)
│   └── a_as_so_layout.json  # Alternative layout with 'a' as low sol (.5)
├── test/
│   ├── test_piano_sound.py  # Unit tests for audio system
│   ├── key_ord_test.py      # Utility for testing keyboard input
│   ├── ode_to_joy.json      # Sample song file
│   └── __init__.py
├── main.py                  # Main entry point
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Installation

1. **Clone or download the project**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application:**
   ```bash
   python main.py          # Real-time terminal mode (default)
   python main.py simple   # Simple terminal mode  
   python main.py gui      # Visual GUI mode
   ```

## Usage Modes

### 🎹 GUI Mode (Recommended)
```bash
python main.py gui
```
- Visual Mac keyboard layout
- Click keys with mouse or use real keyboard
- Piano keys highlighted in green
- Real-time controls for basetone/waveform

### ⌨️ Real-time Terminal Mode  
```bash
python main.py
```
- Press keys directly (no Enter needed)
- ESC to quit
- Keys 1/2 to change basetone/waveform
- Space to stop sounds

### 📝 Simple Terminal Mode
```bash
python main.py simple
```
- Type keys and press Enter
- Type 'quit' to exit
- Same 1/2 controls for settings

## Note System

### Three Octave Ranges
- **Low octave**: `.1` `.2` `.3` `.4` `.5` `.6` `.7` (C3-B3)
- **Base octave**: `1` `2` `3` `4` `5` `6` `7` (C4-B4) 
- **High octave**: `^1` `^2` `^3` `^4` `^5` `^6` `^7` (C5-B5)

### Keyboard Mapping (Configurable)
```
a→.1(C3)  s→.2(D3)  d→.3(E3)  f→.5(G3)  g→.6(A3)
h→1(C4)   j→2(D4)   k→3(E4)   l→5(G4)   ;→6(A4)
```

### Programming API

```python
from code.piano_sound import PianoSound

# Create piano instance
piano = PianoSound(duration=1.0, instrument='piano', basetone='C')

# Play single notes
piano.play_note('1')      # Play C4 (do)
piano.play_note('.1')     # Play C3 (low do)  
piano.play_note('^1')     # Play C5 (high do)

# Play chords
piano.play_chord(['1', '3', '5'])  # C major chord

# Change settings
piano.set_basetone('D')   # Change to D major
piano.set_instrument('guitar')  # Change instrument

# Play frequencies directly
piano.play_frequency(440)  # Play A4

# Cleanup when done
piano.close()
```

## Configuration

The `config/` directory contains multiple keyboard layout options:

### Available Layouts
- **`keyboard_layout.json`** - Default layout with standard key mappings
- **`a_as_la_layout.json`** - Alternative layout with 'a' key mapped to low la (.6)
- **`a_as_mi_layout.json`** - Alternative layout with 'a' key mapped to low mi (.3)  
- **`a_as_so_layout.json`** - Alternative layout with 'a' key mapped to low sol (.5)

### Customization Options
Each layout file can be customized to modify:
- Key mappings to musical notes
- Default basetone (C, D, E, F, G, A, B)
- Control key assignments (volume, instrument changes, etc.)

### Switching Layouts
Use the `3` key during runtime to cycle through available layouts, or modify the layout loading in `main.py` to set a different default.

## Testing

Run tests:
```bash
python -m pytest test/
# or
python test/test_piano_sound.py
```

Test keyboard input:
```bash
python test/key_ord_test.py
```

## Development

- **Core audio**: Modify `code/piano_sound.py`
- **Terminal interface**: Edit `code/keyboard_interface.py`  
- **GUI interface**: Update `code/piano_gui.py`
- **Key mappings**: Configure `config/keyboard_layout.json`
- **Add tests**: Create test files in `test/`

## Cross-Platform Support

- **macOS**: Full support (recommended)
- **Linux/Debian**: Supported with recent fixes for GUI key handling
- **Windows**: Basic support (GUI and terminal modes)

## Requirements

- Python 3.7+
- NumPy 1.20.0+
- PyAudio 0.2.11+
- Cross-platform audio support via PyAudio
- Tkinter (for GUI mode, usually included with Python)