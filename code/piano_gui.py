#!/usr/bin/env python3
"""
Piano GUI - Visual piano keyboard interface

Integrates with the existing PianoSound class to provide
a clickable piano keyboard interface.
"""

import tkinter as tk
from tkinter import ttk
import threading
import json
import os
import sys
import glob
import logging
from .piano_sound import PianoSound
from .config import Audio, GUI, Music, config_manager


class PianoGUI:
    """
    GUI Piano interface using Tkinter.
    
    Provides a visual piano keyboard that integrates with
    the existing PianoSound class for audio generation.
    """
    
    # Solfege notation mapping - shared across all methods
    SOLFEGE_DISPLAY = {
        '.1': 'low do', '.2': 'low re', '.3': 'low mi', '.4': 'low fa', 
        '.5': 'low sol', '.6': 'low la', '.7': 'low ti',
        '1': 'do', '2': 're', '3': 'mi', '4': 'fa', '5': 'sol', '6': 'la', '7': 'ti',
        '^1': 'high do', '^2': 'high re', '^3': 'high mi', '^4': 'high fa', 
        '^5': 'high sol', '^6': 'high la', '^7': 'high ti',
        '#1': 'do#', '#2': 're#', '#4': 'fa#', '#5': 'sol#', '#6': 'la#',
        '.#1': 'low do#', '.#2': 'low re#', '.#4': 'low fa#', 
        '.#5': 'low sol#', '.#6': 'low la#'
    }
    
    def __init__(self):
        """Initialize the piano GUI."""
        self.root = tk.Tk()
        self.root.title("🎹 Piano Code - GUI Mode")
        self.root.geometry(GUI.DEFAULT_WINDOW_SIZE)
        self.root.resizable(True, True)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize piano sound system with user preferences
        saved_instrument = config_manager.get_user_preference('instrument', Music.DEFAULT_INSTRUMENT)
        saved_basetone = config_manager.get_user_preference('basetone', Music.DEFAULT_BASETONE)
        saved_volume = config_manager.get_user_preference('volume', Audio.DEFAULT_VOLUME)
        self.piano = PianoSound(duration=Audio.GUI_DURATION, blocking=False, 
                               instrument=saved_instrument, basetone=saved_basetone, volume=saved_volume)
        
        # Layout management
        self.key_mappings = {}
        self.current_layout = {}
        self.available_layouts = []
        self.current_layout_index = 0
        self.config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        
        # Discover available layouts
        self._discover_layouts()
        
        # Load keyboard configuration
        self.load_config()
        
        self.logger.info("Piano GUI initialized successfully")
        
        # Track active keys for visual feedback
        self.active_keys = set()
        self.highlighted_keys = set()  # Track keys currently highlighted
        self.key_timers = {}  # Track cleanup timers for each key
        self.key_cleanup_delay = 1000  # ms - cleanup delay for stuck keys
        
        # Create GUI components
        self.create_widgets()
        
        # Bind keyboard events
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        self.root.focus_set()  # Enable keyboard focus
        
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
            
            print(f"🎹 GUI discovered {len(self.available_layouts)} keyboard layouts")
            
        except Exception as e:
            print(f"⚠️  Layout discovery error: {e}")
            self.available_layouts = []
    
    def load_config(self, config_path: str = None):
        """Load keyboard layout configuration."""
        if config_path is None:
            config_path = os.path.join(self.config_dir, 'keyboard_layout.json')
            
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            self.current_layout = config
            self.key_mappings = config.get('key_mappings', {})
            basetone = config.get('basetone', 'C')
            self.piano.set_basetone(basetone)
            
            # Update current layout index
            current_filename = os.path.basename(config_path)
            for i, layout in enumerate(self.available_layouts):
                if layout['filename'] == current_filename:
                    self.current_layout_index = i
                    break
                    
            print(f"🎹 GUI loaded: {config.get('title', 'Unknown Layout')}")
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠️ Config error: {e}. Using default mappings.")
            # Default mappings as fallback
            self.current_layout = {'title': 'Default Fallback', 'description': 'Fallback layout'}
            self.key_mappings = {
                'a': '.1', 's': '.2', 'd': '.3', 'f': '.5', 'g': '.6',
                'h': '1', 'j': '2', 'k': '3', 'l': '5', ';': '6'
            }
    
    def create_widgets(self):
        """Create all GUI widgets."""
        # Configure root grid weights for proper resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)  # Make keyboard area expandable
        
        # Title
        title_label = tk.Label(main_frame, text="🎹 Piano Code", 
                             font=("Arial", 18, "bold"), fg="darkblue")
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Control panel
        self.create_control_panel(main_frame)
        
        # Piano keyboard (main content area)
        self.create_piano_keyboard(main_frame)
        
        # Instructions
        self.create_instructions(main_frame)
    
    def create_control_panel(self, parent):
        """Create control panel with settings."""
        control_frame = tk.LabelFrame(parent, text="Controls", font=("Arial", 11, "bold"), padx=10, pady=8)
        control_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        control_frame.columnconfigure(8, weight=1)  # Make status expand (adjusted for volume control)
        
        # Layout selection (first row)
        tk.Label(control_frame, text="Layout:", font=("Arial", 9)).grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.layout_var = tk.StringVar()
        layout_values = [layout['title'] for layout in self.available_layouts] if self.available_layouts else ["Default"]
        self.layout_combo = ttk.Combobox(control_frame, textvariable=self.layout_var,
                                        values=layout_values,
                                        state="readonly", width=20)
        self.layout_combo.bind('<<ComboboxSelected>>', self.on_layout_change)
        self.layout_combo.grid(row=0, column=1, columnspan=2, padx=(0, 15), sticky="w")
        
        # Set initial layout value
        if self.available_layouts and self.current_layout_index < len(self.available_layouts):
            self.layout_var.set(self.available_layouts[self.current_layout_index]['title'])
        elif self.current_layout.get('title'):
            self.layout_var.set(self.current_layout['title'])
        else:
            self.layout_var.set("Default")
        
        # Layout info button
        info_btn = tk.Button(control_frame, text="📝 Info", command=self.show_layout_info,
                            bg="lightblue", font=("Arial", 8), width=6)
        info_btn.grid(row=0, column=3, padx=(0, 15))
        
        # Basetone selection (second row) - show as "basetone: 1="
        basetone_display = f"Basetone: 1={self.piano.basetone}"
        tk.Label(control_frame, text="Basetone:", font=("Arial", 9)).grid(row=1, column=0, padx=(0, 5), sticky="w")
        self.basetone_var = tk.StringVar(value=self.piano.basetone)
        basetone_combo = ttk.Combobox(control_frame, textvariable=self.basetone_var,
                                     values=list(self.piano.base_frequencies.keys()),
                                     state="readonly", width=4)
        basetone_combo.bind('<<ComboboxSelected>>', self.on_basetone_change)
        basetone_combo.grid(row=1, column=1, padx=(0, 15))
        
        # Add basetone display label
        self.basetone_display_var = tk.StringVar(value=f"1={self.piano.basetone}")
        self.basetone_display_label = tk.Label(control_frame, textvariable=self.basetone_display_var, 
                                              font=("Arial", 9), fg="darkblue")
        self.basetone_display_label.grid(row=1, column=2, padx=(5, 10), sticky="w")
        
        # Instrument selection (second row)
        tk.Label(control_frame, text="Instrument:", font=("Arial", 9)).grid(row=1, column=3, padx=(0, 5), sticky="w")
        self.instrument_var = tk.StringVar(value=self.piano.instrument)
        instrument_combo = ttk.Combobox(control_frame, textvariable=self.instrument_var,
                                       values=self.piano.instruments,
                                       state="readonly", width=10)
        instrument_combo.bind('<<ComboboxSelected>>', self.on_instrument_change)
        instrument_combo.grid(row=1, column=4, padx=(0, 15))
        
        # Volume control (second row)
        tk.Label(control_frame, text="Volume:", font=("Arial", 9)).grid(row=1, column=5, padx=(0, 5), sticky="w")
        self.volume_var = tk.DoubleVar(value=self.piano.volume)
        volume_scale = tk.Scale(control_frame, from_=Audio.MIN_VOLUME, to=Audio.MAX_VOLUME, 
                               resolution=Audio.VOLUME_STEP, orient=tk.HORIZONTAL, 
                               variable=self.volume_var, command=self.on_volume_change, length=100)
        volume_scale.grid(row=1, column=6, padx=(0, 10), sticky="w")
        
        # Volume display
        self.volume_display_var = tk.StringVar(value=f"{self.piano.volume:.0%}")
        volume_display_label = tk.Label(control_frame, textvariable=self.volume_display_var, 
                                        font=("Arial", 8), fg="darkblue", width=4)
        volume_display_label.grid(row=1, column=7, padx=(0, 15), sticky="w")
        
        # Stop button (third row)
        stop_btn = tk.Button(control_frame, text="⏹ Stop", command=self.stop_all,
                           bg="white", fg="red", font=("Arial", 9, "bold"), width=8)
        stop_btn.grid(row=2, column=0, columnspan=2, padx=(0, 15), pady=(5, 0))
        
        # Status display (spans all rows, expandable)
        self.status_label = tk.Label(control_frame, text="Ready to play! 🎵", 
                                   font=("Arial", 9), fg="green", anchor="w")
        self.status_label.grid(row=0, column=8, rowspan=3, padx=(15, 0), sticky="nsew")
    
    def create_piano_keyboard(self, parent):
        """Create visual Mac keyboard layout."""
        layout_title = self.current_layout.get('title', 'Mac Keyboard Layout')
        self.piano_frame = tk.LabelFrame(parent, text=layout_title, font=("Arial", 11, "bold"), padx=15, pady=15)
        self.piano_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        self.piano_frame.columnconfigure(0, weight=1)
        self.piano_frame.rowconfigure(0, weight=1)
        
        # Create Mac keyboard layout
        self.piano_keys = {}
        self._create_mac_keyboard_keys(self.piano_frame)
    
    def _recreate_keyboard(self):
        """Recreate the keyboard layout after config change."""
        # Clear existing keys
        for widget in self.piano_frame.winfo_children():
            widget.destroy()
        
        # Update frame title
        layout_title = self.current_layout.get('title', 'Mac Keyboard Layout')
        self.piano_frame.config(text=layout_title)
        
        # Recreate keyboard with new mappings
        self.piano_keys = {}
        self._create_mac_keyboard_keys(self.piano_frame)
        
        # Clear any active key states and timers
        self.active_keys.clear()
        self.highlighted_keys.clear()
        
        # Cancel all pending key cleanup timers
        for timer_id in self.key_timers.values():
            self.root.after_cancel(timer_id)
        self.key_timers.clear()
    
    def _create_mac_keyboard_keys(self, parent):
        """
        Create visual representation of Mac keyboard layout.
        
        Args:
            parent: Parent frame to contain the keyboard keys
        """
        # Mac keyboard layout - multiple rows (excluding number row per user request)
        keyboard_rows = [
            # Top letter row  
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']'],
            # Middle letter row (main piano keys) - will be offset by 0.5 keys
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'"],
            # Bottom letter row - will be offset by 1 key
            ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/']
        ]
        
        # Calculate total grid width needed (longest row + offset)
        max_keys = max(len(row) for row in keyboard_rows)
        total_cols = (max_keys + 1) * 2  # Double for half-key precision
        
        for row_idx, keys in enumerate(keyboard_rows):
            # Calculate starting column for this row
            if row_idx == 0:  # First row - no offset
                start_col = 0
            elif row_idx == 1:  # Second row - half key offset  
                start_col = 1
            elif row_idx == 2:  # Third row - full key offset
                start_col = 2
            
            for col_idx, key in enumerate(keys):
                # Check if key is mapped to a note
                is_piano_key = key.lower() in self.key_mappings
                note_value = self.key_mappings.get(key.lower(), '')
                
                # Create display text
                if is_piano_key:
                    # Use solfege notation that doesn't change with basetone
                    solfege_name = self.SOLFEGE_DISPLAY.get(note_value, note_value)
                    display_name = f"{note_value}\n({solfege_name})"
                    display_text = f"{key.upper()}\n{display_name}"
                    bg_color = "lightgreen"  # Piano keys are highlighted
                    text_color = "darkgreen"
                else:
                    display_text = key.upper()
                    bg_color = "lightgray"   # Non-piano keys are gray
                    text_color = "black"
                
                # Create button for each key
                btn = tk.Button(parent, 
                               text=display_text,
                               width=5,
                               height=3,
                               font=("Arial", 8),
                               relief="raised",
                               bd=1,
                               bg=bg_color,
                               fg=text_color,
                               activebackground="lightblue")
                
                # Grid position: each key takes 2 columns for uniform spacing
                grid_col = start_col + (col_idx * 2)
                btn.grid(row=row_idx, column=grid_col, columnspan=2, padx=1, pady=2, sticky="nsew")
                
                # Bind events only for piano keys
                if is_piano_key:
                    btn.bind("<Button-1>", lambda e, k=key.lower(): self._on_key_press(k))
                    btn.bind("<ButtonRelease-1>", lambda e, k=key.lower(): self._on_key_release(k))
                    btn.configure(command=lambda k=key.lower(): self.play_note_gui(self.key_mappings[k]))
                
                self.piano_keys[key.lower()] = btn
        
        # Configure grid weights for responsive layout
        for i in range(total_cols):
            parent.columnconfigure(i, weight=1)
        for i in range(len(keyboard_rows)):
            parent.rowconfigure(i, weight=1)
    
    def create_instructions(self, parent):
        """Create instruction panel."""
        instr_frame = tk.LabelFrame(parent, text="Instructions", font=("Arial", 10, "bold"), padx=10, pady=5)
        instr_frame.grid(row=3, column=0, sticky="ew")
        
        # Create a more compact layout with 2 columns
        instructions = [
            ("🖱️ Click piano keys to play", "⌨️ Use computer keyboard"),
            ("🎼 Change basetone/waveform above", "⏹️ Stop button or Space key")
        ]
        
        for row, (left_text, right_text) in enumerate(instructions):
            left_label = tk.Label(instr_frame, text=left_text, font=("Arial", 8))
            left_label.grid(row=row, column=0, sticky="w", padx=(0, 20), pady=1)
            
            right_label = tk.Label(instr_frame, text=right_text, font=("Arial", 8))
            right_label.grid(row=row, column=1, sticky="w", pady=1)
    
    def on_basetone_change(self, event=None):
        """Handle basetone change."""
        new_basetone = self.basetone_var.get()
        self.logger.info(f"GUI basetone change requested: {new_basetone}")
        self.piano.set_basetone(new_basetone)
        
        # Update the basetone display
        self.basetone_display_var.set(f"1={new_basetone}")
        
        self.status_label.config(text=f"Basetone changed to: {new_basetone} 🎼", fg="blue")
        self.root.after(GUI.STATUS_MESSAGE_DURATION, lambda: self.status_label.config(text="Ready to play! 🎵", fg="green"))
    
    def on_layout_change(self, event=None):
        """Handle layout change."""
        selected_title = self.layout_var.get()
        self.logger.info(f"GUI layout change requested: {selected_title}")
        
        # Find the selected layout
        for i, layout in enumerate(self.available_layouts):
            if layout['title'] == selected_title:
                self.current_layout_index = i
                try:
                    # Load the new layout
                    self.load_config(layout['path'])
                    
                    # Update GUI variables to reflect new layout settings
                    self.basetone_var.set(self.piano.basetone)
                    self.basetone_display_var.set(f"1={self.piano.basetone}")
                    self.instrument_var.set(self.piano.instrument)
                    
                    # Recreate the keyboard with new mappings
                    self._recreate_keyboard()
                    
                    self.status_label.config(text=f"Layout changed to: {selected_title} 🎹", fg="blue")
                    self.root.after(GUI.STATUS_MESSAGE_DURATION, lambda: self.status_label.config(text="Ready to play! 🎵", fg="green"))
                    
                except Exception as e:
                    self.status_label.config(text=f"Error loading layout: {e} ⚠️", fg="red")
                    print(f"Layout change error: {e}")
                break
    
    def show_layout_info(self):
        """Show information about available layouts."""
        info_window = tk.Toplevel(self.root)
        info_window.title("🎹 Layout Information")
        info_window.geometry("500x400")
        info_window.resizable(True, True)
        
        # Create scrollable text widget
        frame = tk.Frame(info_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(frame, wrap=tk.WORD, font=("Arial", 10))
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add layout information
        info_text = f"Available Keyboard Layouts ({len(self.available_layouts)}):\n"
        info_text += "=" * 50 + "\n\n"
        
        for i, layout in enumerate(self.available_layouts):
            current_marker = ">>> CURRENT: " if i == self.current_layout_index else "    "
            info_text += f"{current_marker}{layout['title']}\n"
            if layout['description']:
                info_text += f"     Description: {layout['description']}\n"
            info_text += f"     File: {layout['filename']}\n"
            
            # Show some key mappings as preview
            try:
                with open(layout['path'], 'r') as f:
                    layout_data = json.load(f)
                key_mappings = layout_data.get('key_mappings', {})
                preview_keys = list(key_mappings.items())[:5]  # First 5 mappings
                if preview_keys:
                    info_text += "     Key mappings preview: "
                    info_text += ", ".join([f"{k}->{v}" for k, v in preview_keys])
                    if len(key_mappings) > 5:
                        info_text += f" (and {len(key_mappings)-5} more)"
                    info_text += "\n"
            except Exception:
                pass
            
            info_text += "\n"
        
        info_text += "\nTo switch layouts, use the Layout dropdown in the main window."
        
        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)  # Make it read-only
        
        # Add close button
        close_btn = tk.Button(info_window, text="Close", command=info_window.destroy,
                             bg="lightgray", font=("Arial", 10))
        close_btn.pack(pady=(0, 10))
    
    def on_volume_change(self, value=None):
        """Handle volume change."""
        new_volume = self.volume_var.get()
        self.logger.debug(f"GUI volume change: {new_volume:.2f}")
        self.piano.set_volume(new_volume)
        
        # Update volume display
        self.volume_display_var.set(f"{new_volume:.0%}")
        
        self.status_label.config(text=f"Volume: {new_volume:.0%} 🔊", fg="blue")
        self.root.after(GUI.STATUS_MESSAGE_DURATION, lambda: self.status_label.config(text="Ready to play! 🎵", fg="green"))
    
    def volume_up(self):
        """Increase volume using hotkey."""
        try:
            self.piano.volume_up()
            self.volume_var.set(self.piano.volume)  # Update GUI slider
            self.volume_display_var.set(f"{self.piano.volume:.0%}")  # Update display
            self.logger.debug(f"GUI volume increased via hotkey: {self.piano.volume:.2f}")
            self.status_label.config(text=f"Volume up: {self.piano.volume:.0%} 🔊", fg="blue")
            self.root.after(GUI.STATUS_MESSAGE_DURATION, lambda: self.status_label.config(text="Ready to play! 🎵", fg="green"))
        except Exception as e:
            self.logger.error(f"GUI volume up error: {e}")
    
    def volume_down(self):
        """Decrease volume using hotkey."""
        try:
            self.piano.volume_down()
            self.volume_var.set(self.piano.volume)  # Update GUI slider
            self.volume_display_var.set(f"{self.piano.volume:.0%}")  # Update display
            self.logger.debug(f"GUI volume decreased via hotkey: {self.piano.volume:.2f}")
            self.status_label.config(text=f"Volume down: {self.piano.volume:.0%} 🔉", fg="blue")
            self.root.after(GUI.STATUS_MESSAGE_DURATION, lambda: self.status_label.config(text="Ready to play! 🎵", fg="green"))
        except Exception as e:
            self.logger.error(f"GUI volume down error: {e}")
    
    def on_instrument_change(self, event=None):
        """Handle instrument change."""
        new_instrument = self.instrument_var.get()
        self.logger.info(f"GUI instrument change requested: {new_instrument}")
        self.piano.set_instrument(new_instrument)
        
        # Choose appropriate emoji for instrument
        instrument_emojis = {
            'piano': '🎹',
            'guitar': '🎸',
            'saxophone': '🎷',
            'violin': '🎻'
        }
        emoji = instrument_emojis.get(new_instrument, '🎵')
        
        self.status_label.config(text=f"Instrument changed to: {new_instrument.title()} {emoji}", fg="blue")
        self.root.after(GUI.STATUS_MESSAGE_DURATION, lambda: self.status_label.config(text="Ready to play! 🎵", fg="green"))
    
    def on_key_press(self, event):
        """Handle keyboard key press with cross-platform support."""
        key = event.char.lower() if event.char else ''
        
        # Handle empty char (common on Linux/Debian)
        if not key and hasattr(event, 'keysym'):
            key = event.keysym.lower()
            
        # Normalize special key names
        if key == 'semicolon':
            key = ';'
        elif key == 'apostrophe':
            key = "'"
        elif key == 'bracketleft':
            key = '['
        elif key == 'bracketright':
            key = ']'
        elif key == 'comma':
            key = ','
        elif key == 'period':
            key = '.'
        elif key == 'slash':
            key = '/'
        elif key == 'space':
            key = ' '
        elif key == 'plus':
            key = '+'
        elif key == 'equal':
            key = '='
        elif key == 'minus':
            key = '-'
        elif key == 'underscore':
            key = '_'
            
        # Handle volume controls
        if key in ['+', '=']:
            self.volume_up()
            return
        elif key in ['-', '_']:
            self.volume_down()
            return
            
        if key in self.key_mappings:
            note = self.key_mappings[key]
            
            # Cancel any existing cleanup timer for this key
            if key in self.key_timers:
                self.root.after_cancel(self.key_timers[key])
                del self.key_timers[key]
            
            # Always allow key press - remove blocking logic for better responsiveness
            self.active_keys.add(key)
            self.play_note_gui(note)
            self._on_key_press(key)
            
            # Set a fallback cleanup timer in case KeyRelease doesn't fire
            timer_id = self.root.after(self.key_cleanup_delay, lambda: self._cleanup_stuck_key(key))
            self.key_timers[key] = timer_id
    
    def on_key_release(self, event):
        """Handle keyboard key release with cross-platform support."""
        key = event.char.lower() if event.char else ''
        
        # Handle empty char (common on Linux/Debian) 
        if not key and hasattr(event, 'keysym'):
            key = event.keysym.lower()
            
        # Normalize special key names (same as key_press)
        if key == 'semicolon':
            key = ';'
        elif key == 'apostrophe':
            key = "'"
        elif key == 'bracketleft':
            key = '['
        elif key == 'bracketright':
            key = ']'
        elif key == 'comma':
            key = ','
        elif key == 'period':
            key = '.'
        elif key == 'slash':
            key = '/'
        elif key == 'space':
            key = ' '
            
        if key in self.key_mappings:
            # Cancel cleanup timer since we got a proper release event
            if key in self.key_timers:
                self.root.after_cancel(self.key_timers[key])
                del self.key_timers[key]
                
            # Remove from active keys and trigger visual release
            self.active_keys.discard(key)
            self._on_key_release(key)
    
    def _on_key_press(self, key):
        """
        Handle key press (both keyboard and button) with Mac keyboard visual feedback.
        
        Args:
            key: The pressed key identifier
        """
        if key in self.key_mappings:
            note = self.key_mappings[key]
            
            # Visual feedback on Mac keyboard - make it much more prominent
            if key in self.piano_keys:
                self.highlighted_keys.add(key)  # Track this key as highlighted
                self.piano_keys[key].config(
                    bg="#FF4500",  # Bright orange-red background
                    fg="blue",     # Blue text for high contrast
                    font=("Arial", 8, "bold"),  # Bold font
                    relief="sunken"
                )
            
            # Don't show playing status - just keep ready status
            pass
    
    def _on_key_release(self, key):
        """
        Handle key release (both keyboard and button) with cross-platform visual feedback.
        
        Args:
            key: The released key identifier
        """
        if key in self.key_mappings:
            # Add a delay before restoring appearance for visual feedback
            def restore_key_appearance():
                if key in self.piano_keys and key in self.highlighted_keys:
                    self.highlighted_keys.discard(key)  # Use discard instead of remove to avoid KeyError
                    
                    # Restore original appearance for piano keys
                    self.piano_keys[key].config(
                        bg="lightgreen",
                        fg="darkgreen", 
                        font=("Arial", 8, "normal"),
                        relief="raised"
                    )
            
            # Delay restoration using config value
            self.root.after(GUI.KEY_HIGHLIGHT_DURATION, restore_key_appearance)
    
    def _cleanup_stuck_key(self, key):
        """Cleanup a key that might be stuck due to missed release events."""
        if key in self.active_keys:
            self.active_keys.discard(key)
            
        if key in self.key_timers:
            del self.key_timers[key]
            
        # Force visual cleanup for stuck highlighted keys
        if key in self.highlighted_keys and key in self.piano_keys:
            self.highlighted_keys.discard(key)
            self.piano_keys[key].config(
                bg="lightgreen",
                fg="darkgreen",
                font=("Arial", 8, "normal"),
                relief="raised"
            )
    
    def on_note_press(self, note):
        """Visual feedback when note is pressed (legacy method for compatibility)."""
        # Find the key that maps to this note
        for key, mapped_note in self.key_mappings.items():
            if mapped_note == note:
                self._on_key_press(key)
                break
    
    def on_note_release(self, note):
        """Visual feedback when note is released (legacy method for compatibility)."""
        # Find the key that maps to this note  
        for key, mapped_note in self.key_mappings.items():
            if mapped_note == note:
                self._on_key_release(key)
                break
    
    def play_note_gui(self, note):
        """Play a note with GUI feedback."""
        try:
            # Get solfege name for display
            display_name = self.SOLFEGE_DISPLAY.get(note, note)
            
            # Don't show playing status - keep it clean
            pass
            
            # Play note in separate thread to avoid GUI blocking
            thread = threading.Thread(target=self._play_note_thread, args=(note,), daemon=True)
            thread.start()
            
        except Exception as e:
            self.status_label.config(text=f"Error: {e} ⚠️", fg="red")
            print(f"Error playing note {note}: {e}")
    
    def _play_note_thread(self, note):
        """Play note in separate thread."""
        try:
            self.piano.play_note(note)
            # Keep status as ready - no need to update after each note
            pass
        except Exception as e:
            self.root.after_idle(lambda: self.status_label.config(text=f"Audio error: {e} ⚠️", fg="red"))
    
    def stop_all(self):
        """Stop all playing sounds."""
        self.logger.debug("GUI stop all sounds requested")
        self.piano.stop()
        self.status_label.config(text="All sounds stopped 🛑", fg="orange")
        self.root.after(GUI.STATUS_MESSAGE_DURATION, lambda: self.status_label.config(text="Ready to play! 🎵", fg="green"))
        
        # Reset all key visuals with proper Mac keyboard colors and fonts
        for key, btn in self.piano_keys.items():
            if key in self.key_mappings:
                btn.config(
                    relief="raised", 
                    bg="lightgreen", 
                    fg="darkgreen",
                    font=("Arial", 8, "normal")
                )  # Piano keys
            else:
                btn.config(
                    relief="raised", 
                    bg="lightgray", 
                    fg="black",
                    font=("Arial", 8, "normal")
                )   # Non-piano keys
        self.active_keys.clear()
        self.highlighted_keys.clear()
        
        # Cancel all pending key cleanup timers
        for timer_id in self.key_timers.values():
            self.root.after_cancel(timer_id)
        self.key_timers.clear()
    
    def run(self):
        """Run the piano GUI."""
        try:
            print("🎹 Starting Piano GUI...")
            print("✅ Interface loaded")
            print("🎵 Click keys or use keyboard to play!")
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down GUI...")
        finally:
            # Ensure complete cleanup of audio resources
            self.piano.close()


def main():
    """Main function to run the piano GUI."""
    try:
        app = PianoGUI()
        app.run()
    except Exception as e:
        print(f"❌ Error starting piano GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()