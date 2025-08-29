import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
import os
import threading
import time
from pathlib import Path
import json

try:
    from mutagen.mp3 import MP3
    from mutagen.oggvorbis import OggVorbis
    from mutagen.wave import WAVE
    from mutagen.id3._util import ID3NoHeaderError
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("Mutagen not available - metadata extraction disabled")

class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Music Player")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        # Initialize pygame mixer with error handling for server environments
        self.audio_available = True
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error as e:
            print(f"Audio initialization failed: {e}")
            print("Running in silent mode - GUI will work but no audio playback")
            self.audio_available = False
        
        # Player state variables
        self.current_song = None
        self.playlist = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.7
        self.position = 0
        self.duration = 0
        self.position_update_thread = None
        self.stop_position_thread = False
        
        # Create GUI
        self.setup_gui()
        self.setup_keyboard_shortcuts()
        
        # Load saved playlist if exists
        self.load_playlist_from_file()
        
        # Set initial volume (only if audio is available)
        if self.audio_available:
            pygame.mixer.music.set_volume(self.volume)
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Song info frame
        info_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.song_title_label = tk.Label(info_frame, text="No song loaded", 
                                        font=('Arial', 14, 'bold'), 
                                        bg='#34495e', fg='white')
        self.song_title_label.pack(pady=5)
        
        self.song_artist_label = tk.Label(info_frame, text="", 
                                         font=('Arial', 10), 
                                         bg='#34495e', fg='#bdc3c7')
        self.song_artist_label.pack()
        
        # Progress frame
        progress_frame = tk.Frame(main_frame, bg='#2c3e50')
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.time_label = tk.Label(progress_frame, text="00:00 / 00:00", 
                                  font=('Arial', 10), bg='#2c3e50', fg='white')
        self.time_label.pack(side=tk.LEFT)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(progress_frame, from_=0, to=100, 
                                     orient=tk.HORIZONTAL, variable=self.progress_var,
                                     command=self.on_progress_change)
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Control buttons frame
        control_frame = tk.Frame(main_frame, bg='#2c3e50')
        control_frame.pack(pady=(0, 10))
        
        # Control buttons
        button_style = {'font': ('Arial', 12), 'bg': '#3498db', 'fg': 'white', 
                       'relief': tk.RAISED, 'bd': 2, 'padx': 10, 'pady': 5}
        
        self.prev_button = tk.Button(control_frame, text="⏮", command=self.previous_song, **button_style)
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        self.play_pause_button = tk.Button(control_frame, text="▶", command=self.toggle_play_pause, **button_style)
        self.play_pause_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(control_frame, text="⏹", command=self.stop_song, **button_style)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.next_button = tk.Button(control_frame, text="⏭", command=self.next_song, **button_style)
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        # Volume frame
        volume_frame = tk.Frame(main_frame, bg='#2c3e50')
        volume_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(volume_frame, text="Volume:", font=('Arial', 10), 
                bg='#2c3e50', fg='white').pack(side=tk.LEFT)
        
        self.volume_var = tk.DoubleVar(value=self.volume * 100)
        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=100, 
                                     orient=tk.HORIZONTAL, variable=self.volume_var,
                                     command=self.on_volume_change)
        self.volume_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        
        self.volume_label = tk.Label(volume_frame, text="70%", font=('Arial', 10), 
                                    bg='#2c3e50', fg='white')
        self.volume_label.pack(side=tk.LEFT)
        
        # Bottom frame for playlist and file operations
        bottom_frame = tk.Frame(main_frame, bg='#2c3e50')
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        
        # File operation buttons
        file_frame = tk.Frame(bottom_frame, bg='#2c3e50')
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        file_button_style = {'font': ('Arial', 10), 'bg': '#27ae60', 'fg': 'white', 
                            'relief': tk.RAISED, 'bd': 2, 'padx': 10, 'pady': 3}
        
        tk.Button(file_frame, text="Add Songs", command=self.add_songs, **file_button_style).pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="Remove Song", command=self.remove_song, **file_button_style).pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="Clear Playlist", command=self.clear_playlist, **file_button_style).pack(side=tk.LEFT, padx=5)
        
        # Playlist frame
        playlist_frame = tk.Frame(bottom_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        playlist_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(playlist_frame, text="Playlist", font=('Arial', 12, 'bold'), 
                bg='#34495e', fg='white').pack(pady=5)
        
        # Playlist listbox with scrollbar
        listbox_frame = tk.Frame(playlist_frame, bg='#34495e')
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.playlist_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set,
                                          bg='#2c3e50', fg='white', selectbackground='#3498db',
                                          font=('Arial', 10))
        self.playlist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.playlist_listbox.bind('<Double-Button-1>', self.on_song_select)
        
        scrollbar.config(command=self.playlist_listbox.yview)
    
    def setup_keyboard_shortcuts(self):
        self.root.bind('<space>', lambda e: self.toggle_play_pause())
        self.root.bind('<Right>', lambda e: self.next_song())
        self.root.bind('<Left>', lambda e: self.previous_song())
        self.root.bind('<Up>', lambda e: self.volume_up())
        self.root.bind('<Down>', lambda e: self.volume_down())
        self.root.bind('<Control-o>', lambda e: self.add_songs())
        self.root.focus_set()  # Make sure window can receive key events
    
    def add_songs(self):
        file_types = [
            ("Audio Files", "*.mp3 *.wav *.ogg"),
            ("MP3 Files", "*.mp3"),
            ("WAV Files", "*.wav"),
            ("OGG Files", "*.ogg"),
            ("All Files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(title="Select Music Files", filetypes=file_types)
        
        for file in files:
            if file not in self.playlist:
                self.playlist.append(file)
                filename = os.path.basename(file)
                self.playlist_listbox.insert(tk.END, filename)
        
        self.save_playlist_to_file()
    
    def remove_song(self):
        selection = self.playlist_listbox.curselection()
        if selection:
            index = selection[0]
            # If we're removing the currently playing song
            if index == self.current_index and self.is_playing:
                self.stop_song()
            
            # Remove from playlist and listbox
            del self.playlist[index]
            self.playlist_listbox.delete(index)
            
            # Adjust current_index if necessary
            if index < self.current_index:
                self.current_index -= 1
            elif index == self.current_index:
                self.current_index = min(self.current_index, len(self.playlist) - 1)
            
            self.save_playlist_to_file()
    
    def clear_playlist(self):
        if messagebox.askyesno("Clear Playlist", "Are you sure you want to clear the entire playlist?"):
            self.stop_song()
            self.playlist.clear()
            self.playlist_listbox.delete(0, tk.END)
            self.current_index = 0
            self.update_song_info("No song loaded", "")
            self.save_playlist_to_file()
    
    def on_song_select(self, event):
        selection = self.playlist_listbox.curselection()
        if selection:
            self.current_index = selection[0]
            self.play_song()
    
    def toggle_play_pause(self):
        if not self.playlist:
            messagebox.showwarning("No Songs", "Please add songs to the playlist first.")
            return
        
        if self.is_playing:
            if self.is_paused:
                self.resume_song()
            else:
                self.pause_song()
        else:
            self.play_song()
    
    def play_song(self):
        if not self.playlist or self.current_index >= len(self.playlist):
            return
        
        try:
            song_path = self.playlist[self.current_index]
            
            if not os.path.exists(song_path):
                messagebox.showerror("File Error", f"File not found: {os.path.basename(song_path)}")
                return
            
            # Stop current song if playing
            if self.is_playing:
                self.stop_song()
            
            # Load and play the song (only if audio is available)
            if self.audio_available:
                pygame.mixer.music.load(song_path)
                pygame.mixer.music.play()
            else:
                messagebox.showinfo("No Audio", "Audio device not available. Running in silent mode.")
            
            self.current_song = song_path
            self.is_playing = True
            self.is_paused = False
            self.position = 0
            
            # Update UI
            self.play_pause_button.config(text="⏸")
            self.update_song_info_from_file(song_path)
            self.highlight_current_song()
            
            # Start position tracking thread
            self.start_position_thread()
            
        except pygame.error as e:
            messagebox.showerror("Playback Error", f"Cannot play file: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def pause_song(self):
        if self.is_playing and not self.is_paused:
            if self.audio_available:
                pygame.mixer.music.pause()
            self.is_paused = True
            self.play_pause_button.config(text="▶")
    
    def resume_song(self):
        if self.is_playing and self.is_paused:
            if self.audio_available:
                pygame.mixer.music.unpause()
            self.is_paused = False
            self.play_pause_button.config(text="⏸")
    
    def stop_song(self):
        if self.audio_available:
            pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.position = 0
        self.progress_var.set(0)
        self.play_pause_button.config(text="▶")
        self.time_label.config(text="00:00 / 00:00")
        self.stop_position_thread = True
    
    def next_song(self):
        if self.playlist:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play_song()
    
    def previous_song(self):
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play_song()
    
    def on_volume_change(self, value):
        self.volume = float(value) / 100
        if self.audio_available:
            pygame.mixer.music.set_volume(self.volume)
        self.volume_label.config(text=f"{int(float(value))}%")
    
    def volume_up(self):
        new_volume = min(100, self.volume_var.get() + 5)
        self.volume_var.set(new_volume)
        self.on_volume_change(new_volume)
    
    def volume_down(self):
        new_volume = max(0, self.volume_var.get() - 5)
        self.volume_var.set(new_volume)
        self.on_volume_change(new_volume)
    
    def on_progress_change(self, value):
        # This would be used for seeking functionality
        # Currently pygame doesn't support seeking easily
        pass
    
    def update_song_info(self, title, artist=""):
        self.song_title_label.config(text=title)
        self.song_artist_label.config(text=artist)
    
    def update_song_info_from_file(self, file_path):
        filename = os.path.basename(file_path)
        title = os.path.splitext(filename)[0]
        artist = ""
        
        if MUTAGEN_AVAILABLE:
            try:
                audio_file = None
                if file_path.lower().endswith('.mp3'):
                    from mutagen.mp3 import MP3
                    audio_file = MP3(file_path)
                elif file_path.lower().endswith('.ogg'):
                    from mutagen.oggvorbis import OggVorbis
                    audio_file = OggVorbis(file_path)
                elif file_path.lower().endswith('.wav'):
                    from mutagen.wave import WAVE
                    audio_file = WAVE(file_path)
                
                if audio_file and hasattr(audio_file, 'info') and audio_file.info and hasattr(audio_file.info, 'length'):
                    self.duration = audio_file.info.length
                else:
                    self.duration = 0
                
                # Extract metadata if audio_file exists
                if audio_file:
                    if 'TIT2' in audio_file:  # MP3
                        title = str(audio_file['TIT2'])
                    elif 'TITLE' in audio_file:  # OGG
                        title = str(audio_file['TITLE'][0])
                    
                    if 'TPE1' in audio_file:  # MP3
                        artist = str(audio_file['TPE1'])
                    elif 'ARTIST' in audio_file:  # OGG
                        artist = str(audio_file['ARTIST'][0])
                    
            except Exception:
                # If metadata extraction fails, use filename
                self.duration = 0
        else:
            self.duration = 0
        
        self.update_song_info(title, artist)
    
    def highlight_current_song(self):
        # Clear previous selection
        self.playlist_listbox.selection_clear(0, tk.END)
        # Highlight current song
        if 0 <= self.current_index < len(self.playlist):
            self.playlist_listbox.selection_set(self.current_index)
            self.playlist_listbox.see(self.current_index)
    
    def start_position_thread(self):
        self.stop_position_thread = False
        if self.position_update_thread is None or not self.position_update_thread.is_alive():
            self.position_update_thread = threading.Thread(target=self.update_position, daemon=True)
            self.position_update_thread.start()
    
    def update_position(self):
        while self.is_playing and not self.stop_position_thread:
            if not self.is_paused:
                self.position += 1
                
                # Update progress bar
                if self.duration > 0:
                    progress = (self.position / self.duration) * 100
                    self.progress_var.set(min(progress, 100))
                
                # Update time label
                current_time = self.format_time(self.position)
                total_time = self.format_time(self.duration)
                self.time_label.config(text=f"{current_time} / {total_time}")
                
                # Check if song ended (only if audio is available)
                if self.audio_available and not pygame.mixer.music.get_busy() and self.is_playing:
                    self.root.after(100, self.next_song)
                    break
            
            time.sleep(1)
    
    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def save_playlist_to_file(self):
        try:
            playlist_data = {
                'playlist': self.playlist,
                'current_index': self.current_index,
                'volume': self.volume
            }
            with open('playlist.json', 'w') as f:
                json.dump(playlist_data, f, indent=2)
        except Exception as e:
            print(f"Error saving playlist: {e}")
    
    def load_playlist_from_file(self):
        try:
            if os.path.exists('playlist.json'):
                with open('playlist.json', 'r') as f:
                    playlist_data = json.load(f)
                
                self.playlist = playlist_data.get('playlist', [])
                self.current_index = playlist_data.get('current_index', 0)
                saved_volume = playlist_data.get('volume', 0.7)
                
                # Update volume
                self.volume = saved_volume
                self.volume_var.set(saved_volume * 100)
                if self.audio_available:
                    pygame.mixer.music.set_volume(self.volume)
                
                # Populate listbox
                for song in self.playlist:
                    filename = os.path.basename(song)
                    self.playlist_listbox.insert(tk.END, filename)
                
                # Validate current_index
                if self.current_index >= len(self.playlist):
                    self.current_index = 0
                    
        except Exception as e:
            print(f"Error loading playlist: {e}")
    
    def on_closing(self):
        # Stop any playing music and cleanup
        self.stop_position_thread = True
        if self.audio_available:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        self.save_playlist_to_file()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MusicPlayer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
