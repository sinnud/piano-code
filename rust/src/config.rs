use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Clone)]
pub struct AudioConfig {
    pub default_sample_rate: u32,
    pub fallback_sample_rates: Vec<u32>,
    pub buffer_sizes: Vec<u32>,
    pub default_buffer_size: u32,
    pub chunk_size: u32,
    pub default_duration: f32,
    pub gui_duration: f32,
    pub min_duration: f32,
    pub max_duration: f32,
    pub default_volume: f32,
    pub min_volume: f32,
    pub max_volume: f32,
    pub volume_step: f32,
    pub max_stream_errors: u32,
    pub stream_timeout_ms: u32,
    pub max_lru_cache_size: usize,
}

impl Default for AudioConfig {
    fn default() -> Self {
        Self {
            default_sample_rate: 44100,
            fallback_sample_rates: vec![44100, 22050, 48000],
            buffer_sizes: vec![512, 1024, 2048, 4096],
            default_buffer_size: 1024,
            chunk_size: 2048,
            default_duration: 1.0,
            gui_duration: 0.8,
            min_duration: 0.1,
            max_duration: 10.0,
            default_volume: 0.7,
            min_volume: 0.0,
            max_volume: 1.0,
            volume_step: 0.05,
            max_stream_errors: 3,
            stream_timeout_ms: 100,
            max_lru_cache_size: 200,
        }
    }
}

#[derive(Debug, Clone)]
pub struct GuiConfig {
    pub default_window_size: (f32, f32),
    pub min_window_size: (f32, f32),
    pub status_message_duration: u64,
    pub key_highlight_duration: u64,
}

impl Default for GuiConfig {
    fn default() -> Self {
        Self {
            default_window_size: (900.0, 650.0),
            min_window_size: (800.0, 500.0),
            status_message_duration: 2000,
            key_highlight_duration: 150,
        }
    }
}

#[derive(Debug, Clone)]
pub struct MusicConfig {
    pub default_instrument: String,
    pub default_basetone: String,
    pub base_frequencies: HashMap<String, f32>,
}

impl Default for MusicConfig {
    fn default() -> Self {
        let mut base_frequencies = HashMap::new();
        base_frequencies.insert("C".to_string(), 261.63);
        base_frequencies.insert("C#".to_string(), 277.18);
        base_frequencies.insert("D".to_string(), 293.66);
        base_frequencies.insert("D#".to_string(), 311.13);
        base_frequencies.insert("E".to_string(), 329.63);
        base_frequencies.insert("F".to_string(), 349.23);
        base_frequencies.insert("F#".to_string(), 369.99);
        base_frequencies.insert("G".to_string(), 392.00);
        base_frequencies.insert("G#".to_string(), 415.30);
        base_frequencies.insert("A".to_string(), 440.00);
        base_frequencies.insert("A#".to_string(), 466.16);
        base_frequencies.insert("B".to_string(), 493.88);

        Self {
            default_instrument: "piano".to_string(),
            default_basetone: "C".to_string(),
            base_frequencies,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyboardLayout {
    pub title: String,
    pub description: Option<String>,
    pub key_mappings: HashMap<String, String>,
    pub basetone: Option<String>,
}

impl KeyboardLayout {
    /// Load a keyboard layout from a JSON file
    pub fn from_file<P: AsRef<Path>>(path: P) -> anyhow::Result<Self> {
        let content = fs::read_to_string(path)?;
        let layout: KeyboardLayout = serde_json::from_str(&content)?;
        Ok(layout)
    }

    /// Load all keyboard layouts from the config directory
    pub fn load_all_layouts() -> Vec<KeyboardLayout> {
        let mut layouts = Vec::new();
        
        // Try to find the config directory relative to the executable
        let config_dirs = [
            "../config",           // From rust/target/release/
            "../../config",        // Alternative path
            "config",             // If run from project root
            "../../../config",    // From rust/target/debug/
        ];
        
        for config_dir in &config_dirs {
            if let Ok(entries) = fs::read_dir(config_dir) {
                for entry in entries.flatten() {
                    let path = entry.path();
                    if let Some(extension) = path.extension() {
                        if extension == "json" && path.file_name().unwrap().to_string_lossy().contains("layout") {
                            if let Ok(layout) = Self::from_file(&path) {
                                layouts.push(layout);
                            }
                        }
                    }
                }
                break; // Found a valid config directory, stop looking
            }
        }
        
        // If no layouts found, add a default one
        if layouts.is_empty() {
            layouts.push(Self::create_default_layout());
        }
        
        layouts
    }
    
    /// Create a default keyboard layout
    pub fn create_default_layout() -> Self {
        let mut key_mappings = HashMap::new();
        
        // Default mappings similar to the JSON config files
        key_mappings.insert("a".to_string(), ".1".to_string());
        key_mappings.insert("s".to_string(), ".2".to_string());
        key_mappings.insert("d".to_string(), ".3".to_string());
        key_mappings.insert("f".to_string(), ".5".to_string());
        key_mappings.insert("g".to_string(), ".6".to_string());
        key_mappings.insert("h".to_string(), "1".to_string());
        key_mappings.insert("j".to_string(), "2".to_string());
        key_mappings.insert("k".to_string(), "3".to_string());
        key_mappings.insert("l".to_string(), "5".to_string());
        key_mappings.insert(";".to_string(), "6".to_string());

        Self {
            title: "Default Layout".to_string(),
            description: Some("Default piano key mappings".to_string()),
            key_mappings,
            basetone: Some("C".to_string()),
        }
    }
}

#[derive(Debug, Clone)]
pub struct Config {
    pub audio: AudioConfig,
    pub gui: GuiConfig,
    pub music: MusicConfig,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            audio: AudioConfig::default(),
            gui: GuiConfig::default(),
            music: MusicConfig::default(),
        }
    }
}

pub const SOLFEGE_DISPLAY: &[(&str, &str)] = &[
    (".1", "low do"),
    (".2", "low re"),
    (".3", "low mi"),
    (".4", "low fa"),
    (".5", "low sol"),
    (".6", "low la"),
    (".7", "low ti"),
    ("1", "do"),
    ("2", "re"),
    ("3", "mi"),
    ("4", "fa"),
    ("5", "sol"),
    ("6", "la"),
    ("7", "ti"),
    ("^1", "high do"),
    ("^2", "high re"),
    ("^3", "high mi"),
    ("^4", "high fa"),
    ("^5", "high sol"),
    ("^6", "high la"),
    ("^7", "high ti"),
    ("#1", "do#"),
    ("#2", "re#"),
    ("#4", "fa#"),
    ("#5", "sol#"),
    ("#6", "la#"),
    (".#1", "low do#"),
    (".#2", "low re#"),
    (".#4", "low fa#"),
    (".#5", "low sol#"),
    (".#6", "low la#"),
];

pub fn get_solfege_display(note: &str) -> String {
    SOLFEGE_DISPLAY
        .iter()
        .find(|(key, _)| *key == note)
        .map(|(_, value)| value.to_string())
        .unwrap_or_else(|| note.to_string())
}