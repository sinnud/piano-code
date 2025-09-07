use crate::audio::PianoSound;
use crate::config::{get_solfege_display, Config, KeyboardLayout};
use anyhow::Result;
use eframe::egui::{self, Color32, RichText, Ui};
use std::collections::{HashMap, HashSet};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

pub struct PianoApp {
    config: Config,
    piano: Arc<Mutex<PianoSound>>,
    key_mappings: HashMap<String, String>,
    current_layout: KeyboardLayout,
    available_layouts: Vec<KeyboardLayout>,
    current_layout_index: usize,
    status_message: String,
    status_color: Color32,
    status_timer: Option<Instant>,
    active_keys: HashSet<String>,
    highlighted_keys: HashSet<String>,
    key_timers: HashMap<String, Instant>,
    selected_basetone: String,
    selected_instrument: String,
}

impl PianoApp {
    pub fn new(_cc: &eframe::CreationContext<'_>) -> Result<Self> {
        let config = Config::default();
        
        let piano = PianoSound::new(
            None,
            Some(config.audio.gui_duration),
            Some(config.music.default_instrument.clone()),
            Some(config.music.default_basetone.clone()),
            Some(config.audio.default_volume),
        )?;

        // Load available keyboard layouts
        let available_layouts = KeyboardLayout::load_all_layouts();
        let current_layout = available_layouts.first().cloned()
            .unwrap_or_else(|| KeyboardLayout::create_default_layout());
        let key_mappings = current_layout.key_mappings.clone();

        Ok(Self {
            selected_basetone: config.music.default_basetone.clone(),
            selected_instrument: config.music.default_instrument.clone(),
            config,
            piano: Arc::new(Mutex::new(piano)),
            key_mappings,
            current_layout: current_layout.clone(),
            available_layouts: available_layouts,
            current_layout_index: 0,
            status_message: "Ready to play! 🎵".to_string(),
            status_color: Color32::GREEN,
            status_timer: None,
            active_keys: HashSet::new(),
            highlighted_keys: HashSet::new(),
            key_timers: HashMap::new(),
        })
    }


    fn update_status(&mut self, message: String, color: Color32) {
        self.status_message = message;
        self.status_color = color;
        self.status_timer = Some(Instant::now());
    }

    fn check_status_timer(&mut self) {
        if let Some(timer) = self.status_timer {
            if timer.elapsed() > Duration::from_millis(self.config.gui.status_message_duration) {
                self.status_message = "Ready to play! 🎵".to_string();
                self.status_color = Color32::GREEN;
                self.status_timer = None;
            }
        }
    }

    fn play_note(&self, note: &str) {
        if let Ok(piano) = self.piano.lock() {
            if let Err(e) = piano.play_note(note) {
                log::error!("Error playing note {}: {}", note, e);
            }
        }
    }

    fn on_key_press(&mut self, key: &str) {
        if let Some(note) = self.key_mappings.get(key) {
            self.active_keys.insert(key.to_string());
            self.highlighted_keys.insert(key.to_string());
            self.key_timers.insert(key.to_string(), Instant::now());
            self.play_note(note);
        }
    }

    fn on_key_release(&mut self, key: &str) {
        self.active_keys.remove(key);
        self.key_timers.remove(key);
        self.highlighted_keys.remove(key);
    }

    fn cleanup_stuck_keys(&mut self) {
        let now = Instant::now();
        let cleanup_delay = Duration::from_millis(1000);
        
        let keys_to_cleanup: Vec<String> = self.key_timers
            .iter()
            .filter(|(_, &timer)| now.duration_since(timer) > cleanup_delay)
            .map(|(key, _)| key.clone())
            .collect();

        for key in keys_to_cleanup {
            self.active_keys.remove(&key);
            self.highlighted_keys.remove(&key);
            self.key_timers.remove(&key);
        }
    }

    fn restore_highlighted_keys(&mut self) {
        let now = Instant::now();
        let highlight_duration = Duration::from_millis(self.config.gui.key_highlight_duration);
        
        let keys_to_restore: Vec<String> = self.key_timers
            .iter()
            .filter(|(_, &timer)| now.duration_since(timer) > highlight_duration)
            .map(|(key, _)| key.clone())
            .collect();

        for key in keys_to_restore {
            self.highlighted_keys.remove(&key);
        }
    }

    fn create_control_panel(&mut self, ui: &mut Ui) {
        ui.group(|ui| {
            ui.vertical(|ui| {
                ui.heading("🎹 Piano Code");
                
                ui.horizontal(|ui| {
                    ui.label("Basetone:");
                    // Define chromatic order for basetones
                    let chromatic_order = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
                    let mut basetone_keys: Vec<String> = self.config.music.base_frequencies.keys().cloned().collect();
                    // Sort according to chromatic order
                    basetone_keys.sort_by(|a, b| {
                        let pos_a = chromatic_order.iter().position(|&x| x == a).unwrap_or(12);
                        let pos_b = chromatic_order.iter().position(|&x| x == b).unwrap_or(12);
                        pos_a.cmp(&pos_b)
                    });
                    egui::ComboBox::from_id_source("basetone")
                        .selected_text(&self.selected_basetone)
                        .show_ui(ui, |ui| {
                            for basetone in basetone_keys {
                                let selected = ui.selectable_value(&mut self.selected_basetone, basetone.clone(), &basetone);
                                if selected.changed() {
                                    let status_msg = if let Ok(mut piano) = self.piano.lock() {
                                        if let Err(e) = piano.set_basetone(basetone.clone()) {
                                            log::error!("Error setting basetone: {}", e);
                                            None
                                        } else {
                                            Some(format!("Basetone changed to: {} 🎼", basetone))
                                        }
                                    } else {
                                        None
                                    };
                                    if let Some(msg) = status_msg {
                                        self.update_status(msg, Color32::BLUE);
                                    }
                                }
                            }
                        });
                    
                    ui.label(format!("1={}", self.selected_basetone));
                });

                ui.horizontal(|ui| {
                    ui.label("Instrument:");
                    let instruments = if let Ok(piano) = self.piano.lock() {
                        piano.get_instruments().to_vec()
                    } else {
                        vec![]
                    };
                    
                    egui::ComboBox::from_id_source("instrument")
                        .selected_text(&self.selected_instrument)
                        .show_ui(ui, |ui| {
                            for instrument in instruments {
                                let selected = ui.selectable_value(&mut self.selected_instrument, instrument.clone(), &instrument);
                                if selected.changed() {
                                    let status_msg = if let Ok(mut piano) = self.piano.lock() {
                                        if let Err(e) = piano.set_instrument(instrument.clone()) {
                                            log::error!("Error setting instrument: {}", e);
                                            None
                                        } else {
                                            let emoji = match instrument.as_str() {
                                                "piano" => "🎹",
                                                "guitar" => "🎸",
                                                "saxophone" => "🎷",
                                                "violin" => "🎻",
                                                _ => "🎵",
                                            };
                                            Some(format!("Instrument changed to: {} {}", instrument, emoji))
                                        }
                                    } else {
                                        None
                                    };
                                    if let Some(msg) = status_msg {
                                        self.update_status(msg, Color32::BLUE);
                                    }
                                }
                            }
                        });
                });

                ui.horizontal(|ui| {
                    ui.label("🔊 Volume:");
                    ui.colored_label(Color32::GRAY, "Use system volume control");
                });

                ui.horizontal(|ui| {
                    if ui.button("⏹ Stop").clicked() {
                        let stopped = if let Ok(piano) = self.piano.lock() {
                            piano.stop();
                            true
                        } else {
                            false
                        };
                        if stopped {
                            self.update_status("All sounds stopped 🛑".to_string(), Color32::from_rgb(255, 165, 0));
                            self.active_keys.clear();
                            self.highlighted_keys.clear();
                            self.key_timers.clear();
                        }
                    }
                });

                ui.horizontal(|ui| {
                    ui.label("Layout:");
                    let current_layout_name = self.current_layout.title.clone();
                    let mut layout_changed = false;
                    let mut new_layout_name = String::new();
                    
                    egui::ComboBox::from_id_source("layout")
                        .selected_text(&current_layout_name)
                        .show_ui(ui, |ui| {
                            for (index, layout) in self.available_layouts.iter().enumerate() {
                                let selected = ui.selectable_value(&mut self.current_layout_index, index, &layout.title);
                                if selected.changed() {
                                    self.current_layout = layout.clone();
                                    self.key_mappings = layout.key_mappings.clone();
                                    layout_changed = true;
                                    new_layout_name = layout.title.clone();
                                }
                            }
                        });
                    
                    // Update status after combo box is closed
                    if layout_changed {
                        self.update_status(format!("Layout changed to: {}", new_layout_name), Color32::BLUE);
                    }
                });
                
                ui.separator();
                ui.colored_label(self.status_color, &self.status_message);
            });
        });
    }

    fn create_piano_keyboard(&mut self, ui: &mut Ui) {
        ui.group(|ui| {
            ui.vertical(|ui| {
                ui.heading(&self.current_layout.title);
                
                // Mac keyboard layout - multiple rows
                let keyboard_rows = [
                    // Top letter row
                    vec!["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[", "]"],
                    // Middle letter row (main piano keys)
                    vec!["a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "'"],
                    // Bottom letter row
                    vec!["z", "x", "c", "v", "b", "n", "m", ",", ".", "/"],
                ];

                for (row_idx, keys) in keyboard_rows.iter().enumerate() {
                    ui.horizontal(|ui| {
                        // Add spacing for keyboard offset
                        if row_idx == 1 {
                            ui.add_space(20.0); // Half key offset
                        } else if row_idx == 2 {
                            ui.add_space(40.0); // Full key offset
                        }
                        
                        for &key in keys {
                            let is_piano_key = self.key_mappings.contains_key(key);
                            let note_value = self.key_mappings.get(key).cloned().unwrap_or_default();
                            
                            let (bg_color, text_color) = if is_piano_key {
                                if self.highlighted_keys.contains(key) {
                                    (Color32::from_rgb(255, 69, 0), Color32::BLUE) // Orange-red when pressed
                                } else {
                                    (Color32::LIGHT_GREEN, Color32::DARK_GREEN) // Light green for piano keys
                                }
                            } else {
                                (Color32::LIGHT_GRAY, Color32::BLACK) // Gray for non-piano keys
                            };

                            let display_text = if is_piano_key {
                                let solfege_name = get_solfege_display(&note_value);
                                format!("{}\n{}\n({})", key.to_uppercase(), note_value, solfege_name)
                            } else {
                                key.to_uppercase()
                            };

                            let button = egui::Button::new(RichText::new(display_text).color(text_color))
                                .fill(bg_color)
                                .min_size(egui::vec2(50.0, 60.0));

                            if ui.add(button).clicked() && is_piano_key {
                                self.on_key_press(key);
                            }
                        }
                    });
                }
            });
        });
    }

    fn create_instructions(&self, ui: &mut Ui) {
        ui.group(|ui| {
            ui.vertical(|ui| {
                ui.heading("Instructions");
                ui.horizontal(|ui| {
                    ui.label("🖱️ Click piano keys to play");
                    ui.separator();
                    ui.label("⌨️ Use computer keyboard");
                });
                ui.horizontal(|ui| {
                    ui.label("🎼 Change basetone/waveform above");
                    ui.separator();
                    ui.label("⏹️ Stop button or Space key");
                });
            });
        });
    }

    fn handle_keyboard_input(&mut self, ctx: &egui::Context) {
        let input = ctx.input(|i| i.clone());
        
        for event in &input.events {
            match event {
                egui::Event::Text(text) => {
                    // Handle punctuation keys that don't have direct Key mappings
                    if text.len() == 1 {
                        let char = text.chars().next().unwrap();
                        let key_str = match char {
                            '.' | '\'' | '[' | ']' | '\\' | ',' | '/' => {
                                char.to_string()
                            }
                            _ => continue,
                        };
                        self.on_key_press(&key_str);
                    }
                }
                egui::Event::Key { key, pressed, .. } => {
                    let key_str = match key {
                        egui::Key::A => "a",
                        egui::Key::S => "s",
                        egui::Key::D => "d",
                        egui::Key::F => "f",
                        egui::Key::G => "g",
                        egui::Key::H => "h",
                        egui::Key::J => "j",
                        egui::Key::K => "k",
                        egui::Key::L => "l",
                        egui::Key::Semicolon => ";",
                        egui::Key::Q => "q",
                        egui::Key::W => "w",
                        egui::Key::E => "e",
                        egui::Key::R => "r",
                        egui::Key::T => "t",
                        egui::Key::Y => "y",
                        egui::Key::U => "u",
                        egui::Key::I => "i",
                        egui::Key::O => "o",
                        egui::Key::P => "p",
                        egui::Key::Z => "z",
                        egui::Key::X => "x",
                        egui::Key::C => "c",
                        egui::Key::V => "v",
                        egui::Key::B => "b",
                        egui::Key::N => "n",
                        egui::Key::M => "m",
                        // TODO: Add missing keys - egui may not support all punctuation keys directly
                        egui::Key::Space => {
                            if *pressed {
                                let status_msg = if let Ok(piano) = self.piano.lock() {
                                    piano.stop();
                                    Some("All sounds stopped 🛑".to_string())
                                } else {
                                    None
                                };
                                if let Some(msg) = status_msg {
                                    self.update_status(msg, Color32::from_rgb(255, 165, 0));
                                }
                            }
                            continue;
                        },
                        _ => continue,
                    };

                    if *pressed {
                        self.on_key_press(key_str);
                    } else {
                        self.on_key_release(key_str);
                    }
                },
                _ => {}
            }
        }
    }
}

impl eframe::App for PianoApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // Handle keyboard input
        self.handle_keyboard_input(ctx);
        
        // Update timers
        self.check_status_timer();
        self.cleanup_stuck_keys();
        self.restore_highlighted_keys();
        
        // Request continuous repaints for animations
        ctx.request_repaint();

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.vertical(|ui| {
                // Control panel
                self.create_control_panel(ui);
                
                ui.add_space(10.0);
                
                // Piano keyboard
                self.create_piano_keyboard(ui);
                
                ui.add_space(10.0);
                
                // Instructions
                self.create_instructions(ui);
            });
        });
    }
}