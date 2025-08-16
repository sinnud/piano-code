import json
import numpy as np
import pyaudio
import threading
import logging
from typing import Optional
from .config import Audio, Music, config_manager


class PianoSound:
    def __init__(self, sample_rate: int = 44100, duration: float = 1.0, blocking: bool = True, instrument: str = 'piano', basetone: str = 'C', volume: float = 0.7):
        # Use config defaults with user preference fallbacks
        self.sample_rate = sample_rate or Audio.DEFAULT_SAMPLE_RATE
        self.duration = duration or Audio.DEFAULT_DURATION
        self.blocking = blocking
        self.instrument = instrument or config_manager.get_user_preference('instrument', Music.DEFAULT_INSTRUMENT)
        self.basetone = basetone or config_manager.get_user_preference('basetone', Music.DEFAULT_BASETONE)
        self.volume = volume or config_manager.get_user_preference('volume', Audio.DEFAULT_VOLUME)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.audio = None
        self.stream = None
        self.is_playing = False
        self.stream_lock = threading.Lock()
        self.playback_thread = None
        self.stream_error_count = 0
        self.max_stream_errors = 3
        self.instruments = ['piano', 'guitar', 'saxophone', 'violin']
        
        # Validate parameters
        if self.instrument not in self.instruments:
            raise ValueError(f"Invalid instrument: {self.instrument}. Choose from {self.instruments}")
        if self.basetone not in ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']:
            raise ValueError(f"Invalid basetone: {self.basetone}")
        
        # Base frequencies from config
        self.base_frequencies = Music.BASE_FREQUENCIES
        
        # Note to semitones mapping (expanded to 3 octaves) - all strings
        self.note_to_semitones = {
            # Low octave (one octave below base)
            '.1': -12, '.#1': -11, '.b2': -11,
            '.2': -10, '.#2': -9, '.b3': -9,
            '.3': -8,
            '.4': -7, '.#4': -6, '.b5': -6,
            '.5': -5, '.#5': -4, '.b6': -4,
            '.6': -3, '.#6': -2, '.b7': -2,
            '.7': -1,
            
            # Base octave (converted to strings)
            '1': 0, '#1': 1, 'b2': 1,
            '2': 2, '#2': 3, 'b3': 3,
            '3': 4,
            '4': 5, '#4': 6, 'b5': 6,
            '5': 7, '#5': 8, 'b6': 8,
            '6': 9, '#6': 10, 'b7': 10,
            '7': 11,
            
            # High octave (one octave above base)
            '^1': 12, '^#1': 13, '^b2': 13,
            '^2': 14, '^#2': 15, '^b3': 15,
            '^3': 16,
            '^4': 17, '^#4': 18, '^b5': 18,
            '^5': 19, '^#5': 20, '^b6': 20,
            '^6': 21, '^#6': 22, '^b7': 22,
            '^7': 23
        }
        
        # Initialize instrument cache for all possible notes
        self.instrument_cache = {}
        
        # Initialize audio after all parameters are set
        self._init_audio()
        
        # Pre-generate all note waveforms for faster playback (before stream init)
        self._pregenerate_waveforms()
        
        # Initialize persistent stream for low-latency playback (after cache is ready)
        self._init_stream()
    
    def _init_audio(self):
        """Initialize PyAudio with error handling."""
        try:
            if self.audio is None:
                self.audio = pyaudio.PyAudio()
        except Exception as e:
            print(f"⚠️  Audio system initialization error: {e}")
            self.audio = None
    
    def _init_stream(self):
        """Initialize persistent PyAudio stream for low-latency playback."""
        if not self._ensure_audio():
            print("⚠️  Cannot initialize stream - audio system not available")
            return
            
        # Try different buffer sizes for compatibility
        buffer_sizes = [512, 1024, 2048, 4096]  # Start small, fallback to larger
        
        for buffer_size in buffer_sizes:
            try:
                if self.stream is None:
                    self.stream = self.audio.open(
                        format=pyaudio.paFloat32,
                        channels=1,
                        rate=self.sample_rate,
                        output=True,
                        frames_per_buffer=buffer_size,
                        stream_callback=None
                    )
                    print(f"🎵 Initialized persistent audio stream (buffer: {buffer_size} frames)")
                    self.stream_error_count = 0  # Reset error count on successful init
                    return
            except Exception as e:
                if buffer_size == buffer_sizes[-1]:  # Last attempt
                    print(f"⚠️  Stream initialization failed with all buffer sizes: {e}")
                    self.stream = None
                continue
    
    def _ensure_audio(self):
        """Ensure audio system is available."""
        if self.audio is None:
            self._init_audio()
        return self.audio is not None
    
    def _ensure_stream(self):
        """Ensure audio stream is available and active."""
        # Check if we've exceeded error limit
        if self.stream_error_count >= self.max_stream_errors:
            return False
            
        # Check stream health
        if self.stream is None:
            self._init_stream()
        elif not self._is_stream_healthy():
            print("⚠️  Stream unhealthy, reinitializing...")
            self._reinit_stream()
            
        return self.stream is not None and self._is_stream_healthy()
    
    def _is_stream_healthy(self):
        """Check if stream is in a healthy state."""
        if self.stream is None:
            return False
        try:
            # Check if stream is active and not stopped
            return self.stream.is_active() and not self.stream.is_stopped()
        except Exception:
            return False
    
    def _pregenerate_waveforms(self):
        """Pre-generate instrument sounds for all notes and basetones for instant playback."""
        self.logger.info("Starting waveform pre-generation for instant playback")
        print("🎼 Pre-generating instrument sounds for instant playback...")
        
        # Generate for all basetones and all notes
        for basetone in self.base_frequencies.keys():
            self.instrument_cache[basetone] = {}
            base_freq = self.base_frequencies[basetone]
            
            for note, semitones in self.note_to_semitones.items():
                frequency = base_freq * (2 ** (semitones / 12))
                
                # Generate for all instrument types and cache
                self.instrument_cache[basetone][note] = {}
                for instrument in self.instruments:
                    instrument_data = self._generate_tone_internal(frequency, self.duration, instrument)
                    self.instrument_cache[basetone][note][instrument] = instrument_data
        
        total_cached = len(self.base_frequencies) * len(self.note_to_semitones) * len(self.instruments)
        self.logger.info(f"Cached {total_cached} instrument sounds ({len(self.base_frequencies)} basetones × {len(self.note_to_semitones)} notes × {len(self.instruments)} instruments)")
        print(f"✅ Cached {total_cached} instrument sounds ({len(self.base_frequencies)} basetones × {len(self.note_to_semitones)} notes × {len(self.instruments)} instruments)")
    
    def _generate_tone_internal(self, frequency: float, duration: float, instrument: str) -> np.ndarray:
        """Internal method to generate instrument-specific tone without caching logic."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # Generate instrument-specific waveform
        if instrument == 'piano':
            # Piano: rich harmonics with exponential decay
            wave = np.sin(2 * np.pi * frequency * t)  # Fundamental
            wave += 0.5 * np.sin(2 * np.pi * frequency * 2 * t)  # 2nd harmonic
            wave += 0.25 * np.sin(2 * np.pi * frequency * 3 * t)  # 3rd harmonic
            wave += 0.125 * np.sin(2 * np.pi * frequency * 4 * t)  # 4th harmonic
            envelope = np.exp(-t * 2)  # Fast decay like piano
            
        elif instrument == 'guitar':
            # Guitar: plucked string with moderate decay
            wave = np.sin(2 * np.pi * frequency * t)  # Fundamental
            wave += 0.3 * np.sin(2 * np.pi * frequency * 2 * t)  # 2nd harmonic
            wave += 0.2 * np.sin(2 * np.pi * frequency * 3 * t)  # 3rd harmonic
            wave += 0.1 * np.sin(2 * np.pi * frequency * 4 * t)  # 4th harmonic
            # Add slight metallic character with sawtooth
            wave += 0.1 * (2 * (t * frequency - np.floor(t * frequency + 0.5)))
            envelope = np.exp(-t * 1.2)  # Medium decay
            
        elif instrument == 'saxophone':
            # Saxophone: reed instrument with rich, warm harmonics
            wave = np.sin(2 * np.pi * frequency * t)  # Fundamental (strong)
            wave += 0.8 * np.sin(2 * np.pi * frequency * 2 * t)  # Very strong 2nd harmonic
            wave += 0.6 * np.sin(2 * np.pi * frequency * 3 * t)  # Strong 3rd harmonic
            wave += 0.4 * np.sin(2 * np.pi * frequency * 4 * t)  # 4th harmonic
            wave += 0.3 * np.sin(2 * np.pi * frequency * 5 * t)  # 5th harmonic
            wave += 0.2 * np.sin(2 * np.pi * frequency * 7 * t)  # 7th harmonic for warmth
            
            # Add reed buzz characteristic (subharmonic)
            wave += 0.15 * np.sin(2 * np.pi * frequency * 0.5 * t)  # Subharmonic
            
            # Add controlled breathiness (less random, more musical)
            breath_freq = frequency * 8  # Higher frequency breath noise
            breath = 0.03 * np.sin(2 * np.pi * breath_freq * t) * np.random.normal(1, 0.1, len(t))
            wave += breath
            
            # Saxophone envelope: quick attack, sustain with slight vibrato
            attack_time = 0.05  # Quick attack
            attack_samples = int(attack_time * len(t))
            attack_env = np.linspace(0, 1, attack_samples)
            sustain_env = np.ones(len(t) - attack_samples)
            envelope = np.concatenate([attack_env, sustain_env])
            
            # Add subtle vibrato for expressiveness
            vibrato_freq = 5.5  # Slightly faster vibrato
            vibrato = 1 + 0.03 * np.sin(2 * np.pi * vibrato_freq * t)
            envelope = envelope * vibrato
            
        elif instrument == 'violin':
            # Violin: bowed string with rich harmonics
            wave = np.sin(2 * np.pi * frequency * t)  # Fundamental
            wave += 0.6 * np.sin(2 * np.pi * frequency * 2 * t)  # 2nd harmonic
            wave += 0.4 * np.sin(2 * np.pi * frequency * 3 * t)  # 3rd harmonic
            wave += 0.3 * np.sin(2 * np.pi * frequency * 4 * t)  # 4th harmonic
            wave += 0.2 * np.sin(2 * np.pi * frequency * 5 * t)  # 5th harmonic
            # Add slight vibrato
            vibrato = 1 + 0.02 * np.sin(2 * np.pi * 6 * t)  # 6 Hz vibrato
            wave = wave * vibrato
            envelope = np.ones_like(t) * (1 - 0.1 * np.exp(-t * 0.8))  # Sustained tone
        
        else:
            # Fallback to simple sine wave
            wave = np.sin(2 * np.pi * frequency * t)
            envelope = np.exp(-t * 2)
        
        # Apply envelope
        wave = wave * envelope
        
        # Apply volume and normalize to prevent clipping
        if np.max(np.abs(wave)) > 0:
            wave = wave / np.max(np.abs(wave)) * 0.5 * self.volume
        
        return wave.astype(np.float32)
    
    def set_blocking(self, blocking: bool):
        """Set blocking mode for audio playback."""
        self.blocking = blocking
    
    def set_instrument(self, instrument: str):
        """Set instrument for audio generation."""
        if instrument not in self.instruments:
            raise ValueError(f"Invalid instrument: {instrument}. Choose from {self.instruments}")
        
        old_instrument = self.instrument
        self.instrument = instrument
        
        # Save user preference
        config_manager.set_user_preference('instrument', instrument)
        self.logger.info(f"Instrument changed from {old_instrument} to {instrument}")
    
    def set_basetone(self, basetone: str):
        """Set base tone for note calculations."""
        if basetone not in self.base_frequencies:
            raise ValueError(f"Invalid basetone: {basetone}. Choose from {list(self.base_frequencies.keys())}")
        
        old_basetone = self.basetone
        self.basetone = basetone
        
        # Save user preference
        config_manager.set_user_preference('basetone', basetone)
        self.logger.info(f"Basetone changed from {old_basetone} to {basetone}")
    
    def set_volume(self, volume: float):
        """Set master volume (0.0 to 1.0)."""
        if not (Audio.MIN_VOLUME <= volume <= Audio.MAX_VOLUME):
            raise ValueError(f"Volume must be between {Audio.MIN_VOLUME} and {Audio.MAX_VOLUME}")
        
        old_volume = self.volume
        self.volume = volume
        
        # Save user preference
        config_manager.set_user_preference('volume', volume)
        self.logger.info(f"Volume changed from {old_volume:.2f} to {volume:.2f}")
    
    def adjust_volume(self, delta: float):
        """Adjust volume by delta amount."""
        new_volume = max(Audio.MIN_VOLUME, min(Audio.MAX_VOLUME, self.volume + delta))
        self.set_volume(new_volume)
    
    def volume_up(self):
        """Increase volume by one step."""
        self.adjust_volume(Audio.VOLUME_STEP)
    
    def volume_down(self):
        """Decrease volume by one step."""
        self.adjust_volume(-Audio.VOLUME_STEP)
    
    def get_settings(self):
        """Get current piano settings."""
        return {
            'sample_rate': self.sample_rate,
            'duration': self.duration,
            'blocking': self.blocking,
            'instrument': self.instrument,
            'basetone': self.basetone,
            'volume': self.volume,
            'is_playing': self.is_playing
        }
        
    def generate_tone(self, frequency: float, duration: float = None, instrument: str = None) -> np.ndarray:
        if duration is None:
            duration = self.duration
        if instrument is None:
            instrument = self.instrument
        
        if instrument not in self.instruments:
            raise ValueError(f"Invalid instrument: {instrument}. Choose from {self.instruments}")
        
        # Check if we can use cached instrument sound (same duration as cached)
        if duration == self.duration:
            # Try to find this frequency in our cached notes
            for note, semitones in self.note_to_semitones.items():
                cached_freq = self.base_frequencies[self.basetone] * (2 ** (semitones / 12))
                if abs(cached_freq - frequency) < 0.01:  # Match within 0.01 Hz
                    try:
                        cached_sound = self.instrument_cache[self.basetone][note][instrument]
                        return cached_sound.copy()  # Return copy to prevent modification
                    except KeyError:
                        break  # Cache miss, generate normally
        
        # Cache miss or different duration - generate dynamically
        return self._generate_tone_internal(frequency, duration, instrument)
    
    def get_cached_tone(self, note: str, instrument: str = None) -> np.ndarray:
        """Get pre-cached instrument sound for a note. Much faster than generate_tone for standard notes."""
        if instrument is None:
            instrument = self.instrument
            
        try:
            cached_sound = self.instrument_cache[self.basetone][note][instrument]
            return cached_sound.copy()  # Return copy to prevent modification
        except KeyError:
            # Fallback to frequency calculation if not cached
            if note in self.note_to_semitones:
                semitones = self.note_to_semitones[note]
                base_freq = self.base_frequencies[self.basetone]
                frequency = base_freq * (2 ** (semitones / 12))
                return self._generate_tone_internal(frequency, self.duration, instrument)
            else:
                raise ValueError(f"Invalid note: {note}")
    
    def play_frequency(self, frequency: float, duration: float = None):
        """Play a frequency with improved error handling."""
        if not self._ensure_audio():
            self.logger.warning("Audio system not available for frequency playback")
            print("⚠️  Audio system not available")
            return
            
        # Always stop current playback first
        self.stop()
        
        if duration is None:
            duration = self.duration
            
        try:
            tone = self.generate_tone(frequency, duration, self.instrument)
            audio_data = tone.tobytes()
            
            if self.blocking:
                self._play_stream(audio_data)
            else:
                self._play_stream_nonblocking(audio_data)
                
        except Exception as e:
            print(f"⚠️  Audio generation error: {e}")
            with self.stream_lock:
                self.is_playing = False
    
    def _play_stream(self, audio_data):
        """Play audio using persistent stream for low-latency playback."""
        if not self._ensure_stream():
            print("⚠️  Audio stream not available")
            return
            
        try:
            # Write data in chunks for smooth playback
            chunk_size = 2048  # bytes - smaller chunks for lower latency
            bytes_written = 0
            
            for i in range(0, len(audio_data), chunk_size):
                # Check stop signal with lock
                with self.stream_lock:
                    if not self.is_playing:
                        break
                        
                chunk = audio_data[i:i+chunk_size]
                
                # Write chunk with error handling
                try:
                    with self.stream_lock:
                        if self.stream and self._is_stream_healthy():
                            self.stream.write(chunk, exception_on_underflow=False)
                            bytes_written += len(chunk)
                        else:
                            break
                except Exception as chunk_error:
                    print(f"⚠️  Chunk write error: {chunk_error}")
                    break
                        
        except Exception as e:
            print(f"⚠️  Stream playback error: {e}")
            self.stream_error_count += 1
            # Try to reinitialize stream on error (outside of lock)
            if self.stream_error_count < self.max_stream_errors:
                self._reinit_stream()
    
    def _reinit_stream(self):
        """Reinitialize stream after error."""
        # Don't reinit if we've exceeded error limit
        if self.stream_error_count >= self.max_stream_errors:
            print(f"⚠️  Max stream errors ({self.max_stream_errors}) reached, giving up")
            return
            
        try:
            # Close existing stream outside of lock to prevent deadlock
            old_stream = self.stream
            self.stream = None
            
            if old_stream:
                try:
                    old_stream.stop_stream()
                    old_stream.close()
                except:
                    pass  # Ignore cleanup errors
                    
        except Exception as e:
            print(f"⚠️  Error during stream cleanup: {e}")
            
        # Initialize new stream
        self._init_stream()
    
    def _play_stream_nonblocking(self, audio_data):
        """Play audio using persistent stream in non-blocking mode."""
        with self.stream_lock:
            self.is_playing = True
        
        def play_audio_thread():
            try:
                self._play_stream(audio_data)
            finally:
                with self.stream_lock:
                    self.is_playing = False
                
        # Store thread reference to prevent race conditions
        self.playback_thread = threading.Thread(target=play_audio_thread, daemon=True)
        self.playback_thread.start()
    
    def stop(self):
        """Stop any currently playing audio immediately."""
        with self.stream_lock:
            self.is_playing = False  # Signal threads to stop immediately
        
        # Wait briefly for thread to detect stop signal
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=0.1)  # Short timeout to avoid blocking
    
    def play_note(self, note, duration: float = None):
        # Parse note input
        if note not in self.note_to_semitones:
            raise ValueError(f"Invalid note: {note}. Choose from {list(self.note_to_semitones.keys())}")
        
        if not self._ensure_audio():
            self.logger.warning(f"Audio system not available for note {note}")
            print("⚠️  Audio system not available")
            return
            
        self.logger.debug(f"Playing note: {note} (duration: {duration or self.duration}s, instrument: {self.instrument})")
            
        # Always stop current playback first
        self.stop()
        
        if duration is None:
            duration = self.duration
            
        try:
            # Use cached instrument sound if duration matches and note is cached
            if duration == self.duration:
                tone = self.get_cached_tone(note, self.instrument)
            else:
                # Generate dynamically for custom durations
                semitones = self.note_to_semitones[note]
                base_freq = self.base_frequencies[self.basetone]
                frequency = base_freq * (2 ** (semitones / 12))
                tone = self._generate_tone_internal(frequency, duration, self.instrument)
            
            audio_data = tone.tobytes()
            
            if self.blocking:
                self._play_stream(audio_data)
            else:
                self._play_stream_nonblocking(audio_data)
                
        except Exception as e:
            print(f"⚠️  Audio generation error: {e}")
            with self.stream_lock:
                self.is_playing = False
    
    def play_chord(self, notes, duration: float = None):
        if not notes:
            raise ValueError("Cannot play empty chord")
        
        if not self._ensure_audio():
            self.logger.warning(f"Audio system not available for chord {notes}")
            print("⚠️  Audio system not available")
            return
            
        self.logger.debug(f"Playing chord: {notes} (duration: {duration or self.duration}s, instrument: {self.instrument})")
            
        # Always stop current playback first
        self.stop()
        
        if duration is None:
            duration = self.duration
        
        try:
            # Calculate frequencies for all notes in the chord
            frequencies = []
            for note in notes:
                # Parse note input
                if note in self.note_to_semitones:
                    semitones = self.note_to_semitones[note]
                else:
                    raise ValueError(f"Invalid note: {note}. Choose from {list(self.note_to_semitones.keys())}")
                
                # Calculate frequency: start from basetone and add semitones
                base_freq = self.base_frequencies[self.basetone]
                frequency = base_freq * (2 ** (semitones / 12))
                frequencies.append(frequency)
            
            # Generate mixed tone
            t = np.linspace(0, duration, int(self.sample_rate * duration), False)
            mixed_wave = np.zeros_like(t)
            
            # Mix all frequencies together
            for frequency in frequencies:
                tone = self.generate_tone(frequency, duration, self.instrument)
                mixed_wave += tone
            
            # Normalize to prevent clipping
            mixed_wave = mixed_wave / len(frequencies) * 0.8
            mixed_wave = mixed_wave.astype(np.float32)
            
            # Convert to bytes
            audio_data = mixed_wave.tobytes()
            
            # Use persistent stream playback methods
            if self.blocking:
                self._play_stream(audio_data)
            else:
                self._play_stream_nonblocking(audio_data)
                
        except Exception as e:
            print(f"⚠️  Chord generation error: {e}")
            with self.stream_lock:
                self.is_playing = False

    def play_song(self, json_file: str, blocking: bool = True) -> None:
        """
        Play a song from a JSON file containing notes and timing.
        
        Args:
            json_file: Path to JSON file containing song data
            blocking: If True, wait for each note to finish before playing the next
        
        JSON format expected:
        {
            "title": "Song Title",
            "basetone": "C",
            "notes": [
                {"note": 1, "duration": 0.5},
                {"note": [1, 3, 5], "duration": 1.0}  // chord
            ]
        }
        """
        
        try:
            # Read JSON file
            with open(json_file, 'r') as f:
                song_data = json.load(f)
            
            # Extract song information
            title = song_data.get('title', 'Unknown Song')
            basetone = song_data.get('basetone', 'C')
            notes = song_data.get('notes', [])
            
            print(f"🎵 Playing: {title}")
            print(f"🎼 Key: {basetone} major")
            print(f"📝 Notes: {len(notes)} notes/chords")
            print("Starting playing...")
            
            if not blocking:
                # Play song in separate thread for non-blocking playback
                def play_thread():
                    self._play_song_sequence(notes, basetone)
                
                song_thread = threading.Thread(target=play_thread, daemon=True)
                song_thread.start()
                return
            else:
                # Play song in current thread (blocking)
                self._play_song_sequence(notes, basetone)
                
        except FileNotFoundError:
            print(f"❌ Song file not found: {json_file}")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON format in {json_file}: {e}")
            raise
        except Exception as e:
            print(f"❌ Error playing song: {e}")
            raise
    
    def _play_song_sequence(self, notes: list, basetone: str) -> None:
        """
        Internal method to play a sequence of notes/chords.
        
        Args:
            notes: List of note dictionaries
            basetone: Base tone for the song
        """
        
        for i, note_data in enumerate(notes):
            try:
                note = note_data.get('note')
                duration = note_data.get('duration', 0.5)
                
                if note is None:
                    print(f"⚠️ Skipping invalid note at position {i}: missing 'note' field")
                    continue
                
                # Save current basetone and set song basetone
                old_basetone = self.basetone
                self.set_basetone(basetone)
                
                # Determine if it's a single note or chord
                if isinstance(note, list):
                    # It's a chord
                    self.play_chord(note, duration=duration)
                else:
                    # It's a single note
                    self.play_note(note, duration=duration)
                
                # Restore original basetone
                self.set_basetone(old_basetone)
                
                # Optional small pause between notes for clarity
                # time.sleep(0.05)
                
            except Exception as e:
                print(f"⚠️ Error playing note/chord at position {i}: {e}")
                continue  # Continue with next note
        
        print("🎼 Song finished!")    
    def close(self):
        """Explicitly close the audio system and stream."""
        self.stop()  # Stop any playing audio first
        
        # Wait for playback thread to finish
        if hasattr(self, 'playback_thread') and self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=0.5)
        
        # Close persistent stream with lock
        with self.stream_lock:
            if hasattr(self, 'stream') and self.stream:
                try:
                    if not self.stream.is_stopped():
                        self.stream.stop_stream()
                    self.stream.close()
                    self.stream = None
                except Exception as e:
                    print(f"⚠️  Stream cleanup error: {e}")
        
        # Terminate PyAudio
        if hasattr(self, 'audio') and self.audio:
            try:
                self.audio.terminate()
                self.audio = None
            except Exception as e:
                print(f"⚠️  PyAudio cleanup error: {e}")
    
    def reset_error_count(self):
        """Reset stream error count (useful for recovery)."""
        self.stream_error_count = 0
        print("🔄 Stream error count reset")
    
    def regenerate_instrument_cache(self, instrument: str = None):
        """Regenerate instrument cache for updated sound algorithms."""
        if instrument is None:
            # Clear all caches and regenerate current combination
            print("🎼 Clearing all caches and regenerating current settings...")
            self.instrument_cache.clear()
            self.waveform_lru_cache.clear()
            self.cache_access_order.clear()
            self._pregenerate_current_combination()
            self._start_background_generation()
        else:
            # Regenerate specific instrument for current basetone
            if instrument not in self.instruments:
                raise ValueError(f"Invalid instrument: {instrument}")
            
            print(f"🎷 Regenerating {instrument} for {self.basetone}...")
            
            # Clear from main cache
            if (self.basetone in self.instrument_cache and 
                any(instrument in self.instrument_cache[self.basetone].get(note, {}) 
                   for note in self.note_to_semitones.keys())):
                for note in self.note_to_semitones.keys():
                    if note in self.instrument_cache[self.basetone]:
                        self.instrument_cache[self.basetone][note].pop(instrument, None)
            
            # Clear from LRU cache
            keys_to_remove = [key for key in self.waveform_lru_cache.keys() 
                            if key[0] == self.basetone and key[2] == instrument]
            for key in keys_to_remove:
                self.waveform_lru_cache.pop(key, None)
                if key in self.cache_access_order:
                    self.cache_access_order.remove(key)
            
            # Regenerate
            self._pregenerate_basetone_instrument(self.basetone, instrument)
            print(f"✅ {instrument.title()} sounds updated!")
    
    def __del__(self):
        """Cleanup resources when object is destroyed."""
        try:
            self.close()
        except Exception:
            pass  # Ignore all errors during destruction