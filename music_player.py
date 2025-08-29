import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
import os
import threading
import time
from pathlib import Path
import json
from musicbrainz_api import MusicBrainzAPI

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
        
        # Initialize MusicBrainz API for classical music search
        self.mb_api = MusicBrainzAPI()
        
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
        
        # Classical Music Search Frame
        search_frame = tk.Frame(main_frame, bg='#8e44ad', relief=tk.RAISED, bd=2)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(search_frame, text="🎼 Búsqueda de Música Clásica", font=('Arial', 12, 'bold'), 
                bg='#8e44ad', fg='white').pack(pady=5)
        
        # Search controls
        search_controls = tk.Frame(search_frame, bg='#8e44ad')
        search_controls.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Search entry
        self.search_var = tk.StringVar()
        tk.Label(search_controls, text="Buscar:", font=('Arial', 10), 
                bg='#8e44ad', fg='white').pack(side=tk.LEFT)
        
        self.search_entry = tk.Entry(search_controls, textvariable=self.search_var, 
                                    font=('Arial', 10), width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 10))
        self.search_entry.bind('<Return>', lambda e: self.search_classical_music())
        
        # Search type selection
        self.search_type = tk.StringVar(value="composer")
        search_options = [("Compositor", "composer"), ("Obra", "work"), ("Grabación", "recording")]
        
        for text, value in search_options:
            tk.Radiobutton(search_controls, text=text, variable=self.search_type, 
                          value=value, bg='#8e44ad', fg='white', selectcolor='#6c3483',
                          font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        
        # Search buttons
        search_button_style = {'font': ('Arial', 10), 'bg': '#9b59b6', 'fg': 'white', 
                              'relief': tk.RAISED, 'bd': 2, 'padx': 15, 'pady': 3}
        
        tk.Button(search_controls, text="Buscar", command=self.search_classical_music, 
                 **search_button_style).pack(side=tk.LEFT, padx=5)
        
        # Classical periods quick search
        periods_frame = tk.Frame(search_frame, bg='#8e44ad')
        periods_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(periods_frame, text="Períodos:", font=('Arial', 9), 
                bg='#8e44ad', fg='white').pack(side=tk.LEFT)
        
        period_style = {'font': ('Arial', 8), 'bg': '#7d3c98', 'fg': 'white', 
                       'relief': tk.RAISED, 'bd': 1, 'padx': 8, 'pady': 2}
        
        periods = [("Barroco", "baroque"), ("Clásico", "classical"), ("Romántico", "romantic"), ("Moderno", "modern")]
        for text, period in periods:
            if period == "baroque":
                # Special styling for Baroque period
                baroque_style = period_style.copy()
                baroque_style['bg'] = '#8B4513'
                baroque_style['font'] = ('Arial', 8, 'bold')
                tk.Button(periods_frame, text=f"🎭 {text}", command=lambda p=period: self.search_baroque_detailed(), 
                         **baroque_style).pack(side=tk.LEFT, padx=2)
            else:
                tk.Button(periods_frame, text=text, command=lambda p=period: self.search_by_period(p), 
                         **period_style).pack(side=tk.LEFT, padx=2)
        
        # Search results frame
        self.search_results_frame = tk.Frame(search_frame, bg='#8e44ad')
        self.search_results_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Bottom frame for playlist and file operations
        bottom_frame = tk.Frame(main_frame, bg='#2c3e50')
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        
        # File operation buttons
        file_frame = tk.Frame(bottom_frame, bg='#2c3e50')
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        file_button_style = {'font': ('Arial', 10), 'bg': '#27ae60', 'fg': 'white', 
                            'relief': tk.RAISED, 'bd': 2, 'padx': 10, 'pady': 3}
        
        tk.Button(file_frame, text="Add Songs", command=self.add_songs, **file_button_style).pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="📁 Upload Music", command=self.open_upload_page, **file_button_style).pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="🔄 Refresh Library", command=self.refresh_music_library, **file_button_style).pack(side=tk.LEFT, padx=5)
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
    
    def open_upload_page(self):
        """Open the music upload web page"""
        import webbrowser
        try:
            webbrowser.open('http://localhost:5000')
            messagebox.showinfo("Upload Music", 
                              "Se abrió la página web para subir música.\n\n" +
                              "Instrucciones:\n" +
                              "1. Sube tus archivos MP3, WAV, OGG, etc.\n" +
                              "2. Haz clic en 'Copiar al Reproductor'\n" +
                              "3. Vuelve aquí y haz clic en 'Refresh Library'")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el navegador: {str(e)}\n\n" +
                               "Abre manualmente: http://localhost:5000")
    
    def refresh_music_library(self):
        """Refresh the music library with all available songs"""
        try:
            # Check for uploaded music files
            uploaded_dir = "uploaded_music"
            sample_dir = "sample_music"
            
            added_count = 0
            
            # Add files from uploaded_music directory
            if os.path.exists(uploaded_dir):
                for filename in os.listdir(uploaded_dir):
                    if filename.lower().endswith(('.mp3', '.wav', '.ogg', '.flac', '.m4a')):
                        file_path = os.path.join(uploaded_dir, filename)
                        if file_path not in self.playlist:
                            self.playlist.append(file_path)
                            self.playlist_listbox.insert(tk.END, f"📁 {filename}")
                            added_count += 1
            
            # Add files from sample_music directory  
            if os.path.exists(sample_dir):
                for filename in os.listdir(sample_dir):
                    if filename.lower().endswith(('.mp3', '.wav', '.ogg', '.flac', '.m4a')):
                        file_path = os.path.join(sample_dir, filename)
                        if file_path not in self.playlist:
                            self.playlist.append(file_path)
                            self.playlist_listbox.insert(tk.END, f"🎵 {filename}")
                            added_count += 1
            
            if added_count > 0:
                messagebox.showinfo("Library Updated", f"Se agregaron {added_count} archivo(s) nuevos a la biblioteca.")
                self.save_playlist_to_file()
            else:
                messagebox.showinfo("Library Current", "No se encontraron archivos nuevos.\n\n" +
                                  "Si subiste música nueva, asegúrate de hacer clic en\n" +
                                  "'Copiar al Reproductor' en la página web.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar la biblioteca: {str(e)}")
    
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
        # Stop any existing thread first
        self.stop_position_thread = True
        if self.position_update_thread and self.position_update_thread.is_alive():
            self.position_update_thread.join(timeout=1.0)
        
        # Start new thread
        self.stop_position_thread = False
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
                
                # Validate and populate listbox - only keep existing files
                valid_playlist = []
                for song in self.playlist:
                    if os.path.exists(song):
                        valid_playlist.append(song)
                        filename = os.path.basename(song)
                        self.playlist_listbox.insert(tk.END, filename)
                    else:
                        print(f"Warning: File not found, removing from playlist: {song}")
                
                # Update playlist with only valid files
                self.playlist = valid_playlist
                
                # Validate current_index
                if self.current_index >= len(self.playlist):
                    self.current_index = 0
                    
        except Exception as e:
            print(f"Error loading playlist: {e}")
    
    def search_classical_music(self):
        """Search for classical music using MusicBrainz API"""
        query = self.search_var.get().strip()
        search_type = self.search_type.get()
        
        if not query:
            messagebox.showwarning("Empty Search", "Please enter a search term.")
            return
        
        # Clear previous results
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()
        
        # Show loading message
        loading_label = tk.Label(self.search_results_frame, text="Searching...", 
                               bg='#8e44ad', fg='white', font=('Arial', 10))
        loading_label.pack(pady=5)
        
        # Start search in background thread
        search_thread = threading.Thread(target=self._perform_search, 
                                        args=(query, search_type), daemon=True)
        search_thread.start()
    
    def _perform_search(self, query, search_type):
        """Perform search in background thread"""
        try:
            if search_type == "composer":
                results = self.mb_api.search_artist(query, limit=8)
            elif search_type == "work":
                results = self.mb_api.search_work(query, limit=8)
            elif search_type == "recording":
                results = self.mb_api.search_recording(query, limit=8)
            else:
                results = []
            
            # Update UI in main thread
            self.root.after(0, self._display_search_results, results, search_type)
            
        except Exception as e:
            error_msg = f"Search error: {str(e)}"
            self.root.after(0, self._display_error, error_msg)
    
    def _display_search_results(self, results, search_type):
        """Display search results in the UI"""
        # Clear previous results
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()
        
        if not results:
            no_results = tk.Label(self.search_results_frame, text="No results found.", 
                                bg='#8e44ad', fg='white', font=('Arial', 10))
            no_results.pack(pady=5)
            return
        
        # Create results display
        results_title = tk.Label(self.search_results_frame, 
                               text=f"Resultados ({len(results)}):", 
                               bg='#8e44ad', fg='white', font=('Arial', 10, 'bold'))
        results_title.pack(pady=5)
        
        # Create scrollable frame for results
        canvas = tk.Canvas(self.search_results_frame, bg='#8e44ad', height=120)
        scrollbar_results = tk.Scrollbar(self.search_results_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#8e44ad')
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_results.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_results.pack(side="right", fill="y")
        
        # Display each result
        for i, result in enumerate(results):
            result_frame = tk.Frame(scrollable_frame, bg='#7d3c98', relief=tk.RAISED, bd=1)
            result_frame.pack(fill=tk.X, padx=5, pady=2)
            
            if search_type == "composer":
                self._create_composer_result(result_frame, result)
            elif search_type == "work":
                self._create_work_result(result_frame, result)
            elif search_type == "recording":
                self._create_recording_result(result_frame, result)
    
    def _create_composer_result(self, parent, composer):
        """Create display for composer search result"""
        main_text = f"{composer['name']} {composer['life_span']}"
        if composer['country']:
            main_text += f" ({composer['country']})"
        
        # Special styling for baroque composers
        if composer.get('period') == 'Barroco':
            parent.config(bg='#8B4513')
            main_text = f"🎭 {main_text}"
        
        tk.Label(parent, text=main_text, bg=parent.cget('bg'), fg='white', 
                font=('Arial', 9, 'bold'), anchor='w').pack(fill=tk.X, padx=5, pady=2)
        
        # Show baroque-specific information
        if 'baroque_info' in composer:
            baroque_info = composer['baroque_info']
            info_text = f"⚡ {baroque_info['speciality']} | 🎹 {baroque_info['instruments']}"
            tk.Label(parent, text=info_text, bg=parent.cget('bg'), fg='#FFD700', 
                    font=('Arial', 8), anchor='w').pack(fill=tk.X, padx=5)
            
            works_text = f"🎼 Obras: {', '.join(baroque_info['famous_works'][:2])}"
            if len(baroque_info['famous_works']) > 2:
                works_text += "..."
            tk.Label(parent, text=works_text, bg=parent.cget('bg'), fg='#F0E68C', 
                    font=('Arial', 7), anchor='w').pack(fill=tk.X, padx=5)
                    
            contribution_text = f"💡 {baroque_info['contribution']}"
            tk.Label(parent, text=contribution_text, bg=parent.cget('bg'), fg='#DDD', 
                    font=('Arial', 7, 'italic'), anchor='w').pack(fill=tk.X, padx=5)
        
        elif composer['sort_name'] != composer['name']:
            tk.Label(parent, text=f"También conocido como: {composer['sort_name']}", 
                    bg=parent.cget('bg'), fg='#d2b4de', font=('Arial', 8), anchor='w').pack(fill=tk.X, padx=5)
    
    def _create_work_result(self, parent, work):
        """Create display for work search result"""
        title_text = work['title']
        if work['composer']:
            title_text += f" - {work['composer']}"
        
        tk.Label(parent, text=title_text, bg='#7d3c98', fg='white', 
                font=('Arial', 9, 'bold'), anchor='w').pack(fill=tk.X, padx=5, pady=2)
        
        if work['type']:
            tk.Label(parent, text=f"Tipo: {work['type']}", 
                    bg='#7d3c98', fg='#d2b4de', font=('Arial', 8), anchor='w').pack(fill=tk.X, padx=5)
    
    def _create_recording_result(self, parent, recording):
        """Create display for recording search result"""
        title_text = recording['title']
        if recording['artist_credit']:
            title_text += f" - {recording['artist_credit']}"
        
        tk.Label(parent, text=title_text, bg='#7d3c98', fg='white', 
                font=('Arial', 9, 'bold'), anchor='w').pack(fill=tk.X, padx=5, pady=2)
        
        if recording['releases']:
            releases_text = "Álbumes: " + ", ".join(recording['releases'][:2])
            if len(recording['releases']) > 2:
                releases_text += f" (+{len(recording['releases']) - 2} más)"
            tk.Label(parent, text=releases_text, 
                    bg='#7d3c98', fg='#d2b4de', font=('Arial', 8), anchor='w').pack(fill=tk.X, padx=5)
        
        if recording['length']:
            duration = recording['length'] // 1000  # Convert from ms to seconds
            minutes = duration // 60
            seconds = duration % 60
            tk.Label(parent, text=f"Duración: {minutes}:{seconds:02d}", 
                    bg='#7d3c98', fg='#d2b4de', font=('Arial', 8), anchor='w').pack(fill=tk.X, padx=5)
    
    def search_by_period(self, period):
        """Search classical music by historical period"""
        # Clear search entry and set it to the period
        self.search_var.set("")
        self.search_type.set("composer")
        
        # Clear previous results
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()
        
        # Show loading message
        loading_label = tk.Label(self.search_results_frame, text=f"Buscando compositores del período {period}...", 
                               bg='#8e44ad', fg='white', font=('Arial', 10))
        loading_label.pack(pady=5)
        
        # Start search in background thread
        period_thread = threading.Thread(target=self._perform_period_search, 
                                        args=(period,), daemon=True)
        period_thread.start()
    
    def _perform_period_search(self, period):
        """Perform period search in background thread"""
        try:
            results = self.mb_api.search_classical_by_period(period)
            # Update UI in main thread
            self.root.after(0, self._display_search_results, results, "composer")
            
        except Exception as e:
            error_msg = f"Error en la búsqueda por período: {str(e)}"
            self.root.after(0, self._display_error, error_msg)
    
    def search_baroque_detailed(self):
        """Special detailed search for Baroque period composers"""
        # Clear search entry and set it to baroque
        self.search_var.set("")
        self.search_type.set("composer")
        
        # Clear previous results
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()
        
        # Show loading message with baroque styling
        loading_label = tk.Label(self.search_results_frame, text="🎭 Cargando maestros del Barroco...", 
                               bg='#8e44ad', fg='#FFD700', font=('Arial', 10, 'bold'))
        loading_label.pack(pady=5)
        
        # Start baroque search in background thread
        baroque_thread = threading.Thread(target=self._perform_baroque_search, daemon=True)
        baroque_thread.start()
    
    def _perform_baroque_search(self):
        """Perform detailed baroque search in background thread"""
        try:
            results = self.mb_api.get_baroque_composers()
            # Update UI in main thread
            self.root.after(0, self._display_search_results, results, "composer")
            
        except Exception as e:
            error_msg = f"Baroque search error: {str(e)}"
            self.root.after(0, self._display_error, error_msg)
    
    def _display_error(self, error_msg):
        """Display error message in search results"""
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()
        
        error_label = tk.Label(self.search_results_frame, text=error_msg, 
                             bg='#8e44ad', fg='#ff6b6b', font=('Arial', 10))
        error_label.pack(pady=5)
    
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
