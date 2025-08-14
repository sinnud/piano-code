import unittest
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

from piano_sound import PianoSound


class TestPianoSound(unittest.TestCase):
    
    def setUp(self):
        self.piano = PianoSound(sample_rate=44100, duration=0.1)  # Short duration for tests
    
    def test_initialization(self):
        self.assertEqual(self.piano.sample_rate, 44100)
        self.assertEqual(self.piano.duration, 0.1)
        self.assertFalse(self.piano.is_playing)
        self.assertIsNone(self.piano.current_stream)
    
    def test_generate_tone(self):
        frequency = 440.0  # A4
        duration = 0.1
        
        tone = self.piano.generate_tone(frequency, duration)
        
        # Check that tone is numpy array
        self.assertIsInstance(tone, np.ndarray)
        
        # Check expected length
        expected_length = int(self.piano.sample_rate * duration)
        self.assertEqual(len(tone), expected_length)
        
        # Check that values are in reasonable range (normalized)
        self.assertTrue(np.all(np.abs(tone) <= 1.0))
        
        # Check that it's not silent (has some non-zero values)
        self.assertTrue(np.any(tone != 0))
        
        # Check data type
        self.assertEqual(tone.dtype, np.float32)
    
    def test_generate_tone_default_duration(self):
        frequency = 440.0
        
        tone = self.piano.generate_tone(frequency)
        
        expected_length = int(self.piano.sample_rate * self.piano.duration)
        self.assertEqual(len(tone), expected_length)
    
    def test_generate_tone_different_frequencies(self):
        frequencies = [220.0, 440.0, 880.0]  # Different octaves of A
        
        for freq in frequencies:
            tone = self.piano.generate_tone(freq, 0.1)
            self.assertIsInstance(tone, np.ndarray)
            self.assertTrue(np.any(tone != 0))
    
    def test_generate_tone_envelope_decay(self):
        frequency = 440.0
        duration = 0.5
        
        tone = self.piano.generate_tone(frequency, duration)
        
        # Check that amplitude decreases over time (envelope effect)
        first_quarter = np.abs(tone[:len(tone)//4])
        last_quarter = np.abs(tone[3*len(tone)//4:])
        
        # Average amplitude should be higher at the beginning
        self.assertGreater(np.mean(first_quarter), np.mean(last_quarter))
    
    def test_play_frequency_blocking_no_error(self):
        # Test that play_frequency doesn't raise exceptions
        # Note: We can't easily test actual audio output in unit tests
        try:
            # Very short duration to minimize test time
            piano = PianoSound(duration=0.01, blocking=True)
            piano.play_frequency(440.0, duration=0.01)
        except Exception as e:
            # If pyaudio isn't available or configured, that's okay for testing
            if "pyaudio" not in str(e).lower():
                self.fail(f"Unexpected error in play_frequency: {e}")
    
    def test_stop_method(self):
        # Test stop method doesn't raise exceptions
        try:
            self.piano.stop()
        except Exception as e:
            self.fail(f"Stop method raised an exception: {e}")
    
    def test_play_note_with_duration(self):
        # Test playing a note with 1.5 second duration
        try:
            piano = PianoSound(blocking=True)
            # Play C4 (261.63 Hz) for 1.5 seconds
            piano.play_frequency(261.63, duration=1.5)
        except Exception as e:
            # If pyaudio isn't available or configured, that's okay for testing
            if "pyaudio" not in str(e).lower():
                self.fail(f"Unexpected error in play_frequency with 1.5s duration: {e}")
    
    def test_play_note_method(self):
        # Test the new play_note method
        try:
            piano = PianoSound(blocking=True)
            # Test playing note 1 (do) from C base
            piano.play_note('1', duration=1)
            # Test playing note #1 (do sharp) from C base  
            piano.play_note('#1', duration=1)
            # Test playing note 2 (re) from C base
            piano.play_note('2', duration=1)
        except Exception as e:
            # If pyaudio isn't available or configured, that's okay for testing
            if "pyaudio" not in str(e).lower():
                self.fail(f"Unexpected error in play_note method: {e}")
    
    def test_play_note_different_basetones(self):
        # Test play_note with different basetones
        try:
            piano = PianoSound(blocking=True)
            # Test with different basetones
            piano.set_basetone('D')
            piano.play_note('1', duration=1)
            piano.set_basetone('G')
            piano.play_note('1', duration=1)
        except Exception as e:
            # If pyaudio isn't available or configured, that's okay for testing
            if "pyaudio" not in str(e).lower():
                self.fail(f"Unexpected error in play_note with different basetones: {e}")
    
    def test_play_chord_c_major(self):
        # Test playing C major chord (C, E, G)
        try:
            piano = PianoSound(blocking=True)
            # Play C major chord: notes 1, 3, 5 from C base
            piano.play_chord(['1', '3', '5'], duration=1)
        except Exception as e:
            # If pyaudio isn't available or configured, that's okay for testing
            if "pyaudio" not in str(e).lower():
                self.fail(f"Unexpected error in play_chord: {e}")
    
    def test_play_chord_different_chords(self):
        # Test different chord types
        try:
            piano = PianoSound(blocking=True)
            # D major chord: D, F#, A (notes 1, 3, 5 from D base)
            piano.set_basetone('D')
            piano.play_chord(['1', '3', '5'], duration=1)
            # G minor chord: G, Bb, D (notes 1, b3, 5 from G base)
            piano.set_basetone('G')
            piano.play_chord(['1', 'b3', '5'], duration=1)
        except Exception as e:
            # If pyaudio isn't available or configured, that's okay for testing
            if "pyaudio" not in str(e).lower():
                self.fail(f"Unexpected error in play_chord with different chords: {e}")

    def test_play_song_ode_to_joy(self):
        """Test playing Ode to Joy from JSON file."""
        try:
            piano = PianoSound(blocking=True)
            # Test loading and playing Ode to Joy
            json_file = os.path.join(os.path.dirname(__file__), 'ode_to_joy.json')
            piano.play_song(json_file, blocking=True)
        except Exception as e:
            # If audio system isn't available or configured, that's okay for testing
            if "pyaudio" not in str(e).lower():
                self.fail(f"Unexpected error in play_song: {e}")
    
    def test_play_song_file_not_found(self):
        """Test play_song with non-existent file."""
        piano = PianoSound(blocking=True)
        with self.assertRaises(FileNotFoundError):
            piano.play_song('nonexistent_song.json')
    
    def test_play_song_invalid_json(self):
        """Test play_song with invalid JSON."""
        import tempfile
        import json
        
        # Create temporary invalid JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json content}')  # Invalid JSON
            temp_file = f.name
        
        try:
            piano = PianoSound(blocking=True)
            with self.assertRaises(json.JSONDecodeError):
                piano.play_song(temp_file)
        finally:
            os.unlink(temp_file)  # Clean up temp file

if __name__ == '__main__':
    unittest.main()