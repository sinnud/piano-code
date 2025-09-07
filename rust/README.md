# Piano Code - Rust GUI Implementation

A Rust translation of the Python Piano Code GUI application, focusing on the GUI mode functionality.

## Features

- 🎹 Interactive piano keyboard interface using egui
- 🎵 Real-time audio synthesis with rodio
- 🎼 Multiple instruments (piano, guitar, saxophone, violin)
- 🔄 Adjustable basetone and volume
- ⌨️ Computer keyboard input support
- 🖱️ Mouse click support for piano keys
- 🎨 Visual feedback for key presses

## Key Mappings

The application uses a Mac keyboard layout with the following default mappings:

- `a s d f g` - Low octave notes (.1 .2 .3 .5 .6)
- `h j k l ;` - Base octave notes (1 2 3 5 6)
- `+/=` - Volume up
- `-` - Volume down  
- `Space` - Stop all sounds

## Building and Running

1. Make sure you have Rust installed
2. Navigate to the rust directory
3. Build and run:

```bash
cd rust
cargo build --release
cargo run
```

## Architecture

- `config.rs` - Configuration constants and structures
- `audio.rs` - Audio synthesis and playback using rodio
- `gui.rs` - GUI implementation using eframe/egui
- `main.rs` - Entry point focusing on GUI mode only

## Dependencies

- **eframe/egui** - Modern immediate mode GUI framework
- **rodio** - Pure Rust audio library
- **cpal** - Cross-platform audio I/O
- **serde/serde_json** - Serialization for configuration
- **anyhow/thiserror** - Error handling
- **log/env_logger** - Logging

## Differences from Python Version

This Rust implementation focuses solely on GUI mode and includes these changes:

- Uses egui instead of Tkinter for the GUI
- Uses rodio for audio instead of PyAudio
- Simplified to focus on core GUI functionality
- No layout file loading (uses default layout)
- Real-time waveform synthesis instead of cached samples

## Audio Synthesis

The application generates waveforms in real-time for different instruments:

- **Piano**: Fundamental + harmonics (2nd, 3rd)  
- **Guitar**: Fundamental + fifth + octave harmonics
- **Saxophone**: Complex harmonic structure (3rd, 5th)
- **Violin**: String-like harmonics (2nd, 4th)

All instruments use a basic ADSR envelope for realistic sound shaping.