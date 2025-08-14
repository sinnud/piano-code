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
from .piano_sound import PianoSound


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
        self.root.geometry("900x650")  # Slightly taller for new controls
        self.root.resizable(True, True)
        
        # Initialize piano sound system
        self.piano = PianoSound(duration=0.8, blocking=False, instrument='piano', basetone='C')
        
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
        
        # Track active keys for visual feedback
        self.active_keys = set()
        self.highlighted_keys = set()  # Track keys currently highlighted
        
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
        control_frame.columnconfigure(7, weight=1)  # Make status expand (adjusted for basetone display)
        
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
        
        # Stop button (second row)
        stop_btn = tk.Button(control_frame, text="⏹ Stop", command=self.stop_all,
                           bg="white", fg="red", font=("Arial", 9, "bold"), width=8)
        stop_btn.grid(row=1, column=5, padx=(0, 15))
        
        # Status display (spans both rows, expandable)
        self.status_label = tk.Label(control_frame, text="Ready to play! 🎵", 
                                   font=("Arial", 9), fg="green", anchor="w")
        self.status_label.grid(row=0, column=6, rowspan=2, padx=(15, 0), sticky="nsew")
    
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
        
        # Clear any active key states
        self.active_keys.clear()
        self.highlighted_keys.clear()
    
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
            # Middle letter row (main piano keys)
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'"],
            # Bottom letter row
            ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/']
        ]
        
        for row_idx, keys in enumerate(keyboard_rows):
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
                
                # Add padding for keyboard layout authenticity
                padx = 2
                pady = 2
                if row_idx == 0 and col_idx == 0:  # Tab key area (now first row)
                    padx = (15, 2)
                elif row_idx == 1 and col_idx == 0:  # Caps lock area  
                    padx = (20, 2)
                elif row_idx == 2 and col_idx == 0:  # Shift key area
                    padx = (25, 2)
                
                btn.grid(row=row_idx, column=col_idx, padx=padx, pady=pady, sticky="nsew")
                
                # Bind events only for piano keys
                if is_piano_key:
                    btn.bind("<Button-1>", lambda e, k=key.lower(): self._on_key_press(k))
                    btn.bind("<ButtonRelease-1>", lambda e, k=key.lower(): self._on_key_release(k))
                    btn.configure(command=lambda k=key.lower(): self.play_note_gui(self.key_mappings[k]))
                
                self.piano_keys[key.lower()] = btn
        
        # Configure grid weights for responsive layout
        for i in range(len(keyboard_rows[0])):
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
        self.piano.set_basetone(new_basetone)
        
        # Update the basetone display
        self.basetone_display_var.set(f"1={new_basetone}")
        
        self.status_label.config(text=f"Basetone changed to: {new_basetone} 🎼", fg="blue")
        self.root.after(2000, lambda: self.status_label.config(text="Ready to play! 🎵", fg="green"))
    
    def on_layout_change(self, event=None):
        """Handle layout change."""
        selected_title = self.layout_var.get()
        
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
                    self.root.after(3000, lambda: self.status_label.config(text="Ready to play! 🎵", fg="green"))
                    
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
    
    def on_instrument_change(self, event=None):
        """Handle instrument change."""
        new_instrument = self.instrument_var.get()
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
        self.root.after(2000, lambda: self.status_label.config(text="Ready to play! 🎵", fg="green"))
    
    def on_key_press(self, event):
        """Handle keyboard key press."""
        key = event.char.lower()
        if key in self.key_mappings and key not in self.active_keys:
            note = self.key_mappings[key]
            self.active_keys.add(key)
            self.play_note_gui(note)
            self._on_key_press(key)
    
    def on_key_release(self, event):
        """Handle keyboard key release."""
        key = event.char.lower()
        if key in self.key_mappings and key in self.active_keys:
            note = self.key_mappings[key]
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
        Handle key release (both keyboard and button) with Mac keyboard visual feedback.
        
        Args:
            key: The released key identifier
        """
        if key in self.key_mappings:
            # Add a longer delay before restoring original appearance for better visual feedback
            def restore_key_appearance():
                if key in self.piano_keys and key in self.highlighted_keys:
                    self.highlighted_keys.remove(key)  # Remove from highlighted set
                    
                    # Restore all original properties based on whether it's a piano key
                    if key in self.key_mappings:
                        # Piano key restoration
                        original_bg = "lightgreen"
                        original_fg = "darkgreen"
                    else:
                        # Non-piano key restoration
                        original_bg = "lightgray"
                        original_fg = "black"
                    
                    self.piano_keys[key].config(
                        bg=original_bg,
                        fg=original_fg,
                        font=("Arial", 8, "normal"),  # Reset to normal weight
                        relief="raised"
                    )
            
            # Delay the restoration by 500ms so user can clearly see the press effect
            self.root.after(500, restore_key_appearance)
    
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
        self.piano.stop()
        self.status_label.config(text="All sounds stopped 🛑", fg="orange")
        self.root.after(1500, lambda: self.status_label.config(text="Ready to play! 🎵", fg="green"))
        
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
        self.highlighted_keys.clear()  # Clear highlighted tracking
    
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
            self.piano.stop()


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