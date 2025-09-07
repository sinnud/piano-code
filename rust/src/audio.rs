use crate::config::{AudioConfig, MusicConfig};
use anyhow::{anyhow, Result};
use rodio::{source::Source, OutputStream, OutputStreamHandle, Sink};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::Duration;

pub struct PianoSound {
    config: AudioConfig,
    music_config: MusicConfig,
    instrument: String,
    basetone: String,
    volume: f32,
    duration: f32,
    sample_rate: u32,
    _stream: OutputStream,
    #[allow(dead_code)]
    stream_handle: OutputStreamHandle,
    sink: Arc<Mutex<Sink>>,
    note_to_semitones: HashMap<String, i32>,
    instrument_cache: HashMap<String, Vec<f32>>,
    instruments: Vec<String>,
}

impl PianoSound {
    pub fn new(
        sample_rate: Option<u32>,
        duration: Option<f32>,
        instrument: Option<String>,
        basetone: Option<String>,
        volume: Option<f32>,
    ) -> Result<Self> {
        let config = AudioConfig::default();
        let music_config = MusicConfig::default();

        let sample_rate = sample_rate.unwrap_or(config.default_sample_rate);
        let duration = duration.unwrap_or(config.gui_duration);
        let instrument = instrument.unwrap_or(music_config.default_instrument.clone());
        let basetone = basetone.unwrap_or(music_config.default_basetone.clone());
        let volume = volume.unwrap_or(config.default_volume);

        let instruments = vec![
            "piano".to_string(),
            "guitar".to_string(),
            "saxophone".to_string(),
            "violin".to_string(),
        ];

        if !instruments.contains(&instrument) {
            return Err(anyhow!("Invalid instrument: {}", instrument));
        }

        let valid_basetones = vec!["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
        if !valid_basetones.contains(&basetone.as_str()) {
            return Err(anyhow!("Invalid basetone: {}", basetone));
        }

        let (_stream, stream_handle) = OutputStream::try_default()
            .map_err(|e| anyhow!("Failed to create audio stream: {}", e))?;

        let sink = Arc::new(Mutex::new(
            Sink::try_new(&stream_handle)
                .map_err(|e| anyhow!("Failed to create audio sink: {}", e))?,
        ));

        let mut note_to_semitones = HashMap::new();
        
        // Low octave (one octave below base)
        note_to_semitones.insert(".1".to_string(), -12);
        note_to_semitones.insert(".#1".to_string(), -11);
        note_to_semitones.insert(".2".to_string(), -10);
        note_to_semitones.insert(".#2".to_string(), -9);
        note_to_semitones.insert(".3".to_string(), -8);
        note_to_semitones.insert(".4".to_string(), -7);
        note_to_semitones.insert(".#4".to_string(), -6);
        note_to_semitones.insert(".5".to_string(), -5);
        note_to_semitones.insert(".#5".to_string(), -4);
        note_to_semitones.insert(".6".to_string(), -3);
        note_to_semitones.insert(".#6".to_string(), -2);
        note_to_semitones.insert(".7".to_string(), -1);

        // Base octave
        note_to_semitones.insert("1".to_string(), 0);
        note_to_semitones.insert("#1".to_string(), 1);
        note_to_semitones.insert("2".to_string(), 2);
        note_to_semitones.insert("#2".to_string(), 3);
        note_to_semitones.insert("3".to_string(), 4);
        note_to_semitones.insert("4".to_string(), 5);
        note_to_semitones.insert("#4".to_string(), 6);
        note_to_semitones.insert("5".to_string(), 7);
        note_to_semitones.insert("#5".to_string(), 8);
        note_to_semitones.insert("6".to_string(), 9);
        note_to_semitones.insert("#6".to_string(), 10);
        note_to_semitones.insert("7".to_string(), 11);

        // High octave (one octave above base)
        note_to_semitones.insert("^1".to_string(), 12);
        note_to_semitones.insert("^#1".to_string(), 13);
        note_to_semitones.insert("^2".to_string(), 14);
        note_to_semitones.insert("^#2".to_string(), 15);
        note_to_semitones.insert("^3".to_string(), 16);
        note_to_semitones.insert("^4".to_string(), 17);
        note_to_semitones.insert("^#4".to_string(), 18);
        note_to_semitones.insert("^5".to_string(), 19);
        note_to_semitones.insert("^#5".to_string(), 20);
        note_to_semitones.insert("^6".to_string(), 21);
        note_to_semitones.insert("^#6".to_string(), 22);
        note_to_semitones.insert("^7".to_string(), 23);

        let mut piano_sound = Self {
            config,
            music_config,
            instrument,
            basetone,
            volume,
            duration,
            sample_rate,
            _stream,
            stream_handle,
            sink,
            note_to_semitones,
            instrument_cache: HashMap::new(),
            instruments,
        };

        piano_sound.pregenerate_waveforms()?;

        Ok(piano_sound)
    }

    fn pregenerate_waveforms(&mut self) -> Result<()> {
        log::info!("Pregenerating waveforms for all notes...");
        
        for (note, semitones) in &self.note_to_semitones.clone() {
            let waveform = self.generate_waveform(note, *semitones)?;
            self.instrument_cache.insert(note.clone(), waveform);
        }
        
        log::info!("Pregenerated {} waveforms", self.instrument_cache.len());
        Ok(())
    }

    fn generate_waveform(&self, _note: &str, semitones: i32) -> Result<Vec<f32>> {
        let base_freq = self.music_config.base_frequencies
            .get(&self.basetone)
            .copied()
            .ok_or_else(|| anyhow!("Unknown basetone: {}", self.basetone))?;

        let frequency = base_freq * (2.0_f32).powf(semitones as f32 / 12.0);
        let samples = (self.sample_rate as f32 * self.duration) as usize;
        
        let mut waveform = Vec::with_capacity(samples);
        
        for i in 0..samples {
            let t = i as f32 / self.sample_rate as f32;
            let sample = match self.instrument.as_str() {
                "piano" => self.generate_piano_wave(frequency, t),
                "guitar" => self.generate_guitar_wave(frequency, t),
                "saxophone" => self.generate_saxophone_wave(frequency, t),
                "violin" => self.generate_violin_wave(frequency, t),
                _ => self.generate_piano_wave(frequency, t),
            };
            
            // Apply envelope (ADSR approximation)
            let envelope = self.apply_envelope(t);
            waveform.push(sample * envelope * self.volume);
        }
        
        Ok(waveform)
    }

    fn generate_piano_wave(&self, frequency: f32, t: f32) -> f32 {
        // Piano-like sound with harmonics
        let fundamental = (2.0 * std::f32::consts::PI * frequency * t).sin();
        let second = 0.5 * (2.0 * std::f32::consts::PI * frequency * 2.0 * t).sin();
        let third = 0.25 * (2.0 * std::f32::consts::PI * frequency * 3.0 * t).sin();
        fundamental + second + third
    }

    fn generate_guitar_wave(&self, frequency: f32, t: f32) -> f32 {
        // Guitar-like sound with string harmonics
        let fundamental = (2.0 * std::f32::consts::PI * frequency * t).sin();
        let fifth = 0.3 * (2.0 * std::f32::consts::PI * frequency * 1.5 * t).sin();
        let octave = 0.2 * (2.0 * std::f32::consts::PI * frequency * 2.0 * t).sin();
        fundamental + fifth + octave
    }

    fn generate_saxophone_wave(&self, frequency: f32, t: f32) -> f32 {
        // Saxophone-like sound with more complex harmonics
        let fundamental = (2.0 * std::f32::consts::PI * frequency * t).sin();
        let third = 0.6 * (2.0 * std::f32::consts::PI * frequency * 3.0 * t).sin();
        let fifth = 0.4 * (2.0 * std::f32::consts::PI * frequency * 5.0 * t).sin();
        fundamental + third + fifth
    }

    fn generate_violin_wave(&self, frequency: f32, t: f32) -> f32 {
        // Violin-like sound with string characteristics
        let fundamental = (2.0 * std::f32::consts::PI * frequency * t).sin();
        let second = 0.4 * (2.0 * std::f32::consts::PI * frequency * 2.0 * t).sin();
        let fourth = 0.3 * (2.0 * std::f32::consts::PI * frequency * 4.0 * t).sin();
        fundamental + second + fourth
    }

    fn apply_envelope(&self, t: f32) -> f32 {
        // Simple ADSR envelope
        let attack_time = 0.1;
        let decay_time = 0.2;
        let sustain_level = 0.7;
        let release_time = self.duration * 0.3;
        
        if t < attack_time {
            // Attack
            t / attack_time
        } else if t < attack_time + decay_time {
            // Decay
            1.0 - (1.0 - sustain_level) * ((t - attack_time) / decay_time)
        } else if t < self.duration - release_time {
            // Sustain
            sustain_level
        } else {
            // Release
            sustain_level * (1.0 - (t - (self.duration - release_time)) / release_time)
        }
    }

    pub fn play_note(&self, note: &str) -> Result<()> {
        if let Some(waveform) = self.instrument_cache.get(note) {
            let source = WaveformSource::new(waveform.clone(), self.sample_rate);
            
            if let Ok(sink_guard) = self.sink.lock() {
                // Stop previous notes for monophonic behavior (like piano mode)
                sink_guard.stop();
                sink_guard.append(source);
                sink_guard.play();
            }
        } else {
            log::warn!("Unknown note: {}", note);
        }
        Ok(())
    }

    pub fn set_basetone(&mut self, basetone: String) -> Result<()> {
        self.basetone = basetone;
        self.pregenerate_waveforms()?;
        Ok(())
    }

    pub fn set_instrument(&mut self, instrument: String) -> Result<()> {
        if !self.instruments.contains(&instrument) {
            return Err(anyhow!("Invalid instrument: {}", instrument));
        }
        self.instrument = instrument;
        self.pregenerate_waveforms()?;
        Ok(())
    }

    pub fn set_volume(&mut self, volume: f32) {
        self.volume = volume.clamp(self.config.min_volume, self.config.max_volume);
    }

    pub fn volume_up(&mut self) {
        self.set_volume(self.volume + self.config.volume_step);
    }

    pub fn volume_down(&mut self) {
        self.set_volume(self.volume - self.config.volume_step);
    }

    pub fn stop(&self) {
        if let Ok(sink_guard) = self.sink.lock() {
            sink_guard.stop();
        }
    }

    pub fn get_instruments(&self) -> &[String] {
        &self.instruments
    }

    pub fn get_base_frequencies(&self) -> &HashMap<String, f32> {
        &self.music_config.base_frequencies
    }
}

struct WaveformSource {
    waveform: Vec<f32>,
    sample_rate: u32,
    position: usize,
}

impl WaveformSource {
    fn new(waveform: Vec<f32>, sample_rate: u32) -> Self {
        Self {
            waveform,
            sample_rate,
            position: 0,
        }
    }
}

impl Source for WaveformSource {
    fn current_frame_len(&self) -> Option<usize> {
        None
    }

    fn channels(&self) -> u16 {
        1
    }

    fn sample_rate(&self) -> u32 {
        self.sample_rate
    }

    fn total_duration(&self) -> Option<Duration> {
        Some(Duration::from_secs_f32(self.waveform.len() as f32 / self.sample_rate as f32))
    }
}

impl Iterator for WaveformSource {
    type Item = f32;

    fn next(&mut self) -> Option<Self::Item> {
        if self.position < self.waveform.len() {
            let sample = self.waveform[self.position];
            self.position += 1;
            Some(sample)
        } else {
            None
        }
    }
}