#!/usr/bin/env python3
"""
Custom Desktop Application with integrated widgets
Based on the mockup design with calendar, clock, music player, notes, and app launcher
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pygame
import os
import json
import threading
import time
from datetime import datetime, timedelta
import calendar
import webbrowser
import subprocess
from pathlib import Path

# Import music functionality
from music_player import MusicPlayer

class DesktopWidget:
    """Base class for desktop widgets"""
    def __init__(self, parent, title="Widget", bg_color="#f8f9fa"):
        self.parent = parent
        self.frame = tk.Frame(parent, bg=bg_color, relief=tk.RAISED, bd=2)
        self.title = title
        self.bg_color = bg_color
        
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

class ClockWidget(DesktopWidget):
    """Digital clock and date widget"""
    def __init__(self, parent):
        super().__init__(parent, "Clock", "#ff6b35")
        self.setup_ui()
        self.update_time()
        
    def setup_ui(self):
        # Time display
        self.time_label = tk.Label(self.frame, text="09:00 AM", 
                                  font=('Arial', 36, 'bold'), 
                                  fg='white', bg=self.bg_color)
        self.time_label.pack(pady=10)
        
        # Date display
        self.date_label = tk.Label(self.frame, text="Monday, 11 August 2025", 
                                  font=('Arial', 14), 
                                  fg='white', bg=self.bg_color)
        self.date_label.pack()
        
    def update_time(self):
        """Update time and date display"""
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%A, %d %B %Y")
        
        self.time_label.config(text=time_str)
        self.date_label.config(text=date_str)
        
        # Schedule next update
        self.frame.after(1000, self.update_time)

class CalendarWidget(DesktopWidget):
    """Calendar widget showing current month"""
    def __init__(self, parent):
        super().__init__(parent, "Calendar", "#f8f9fa")
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title_label = tk.Label(self.frame, text="AUGUST 2025", 
                              font=('Arial', 14, 'bold'), 
                              fg='#333', bg=self.bg_color)
        title_label.pack(pady=5)
        
        # Calendar grid
        cal_frame = tk.Frame(self.frame, bg=self.bg_color)
        cal_frame.pack(padx=10, pady=5)
        
        # Day headers
        days = ['S', 'M', 'T', 'W', 'T', 'F', 'S']
        for i, day in enumerate(days):
            label = tk.Label(cal_frame, text=day, font=('Arial', 10, 'bold'),
                           fg='#666', bg=self.bg_color, width=3)
            label.grid(row=0, column=i, padx=1, pady=1)
        
        # Calendar days
        now = datetime.now()
        cal = calendar.monthcalendar(now.year, now.month)
        
        for week_num, week in enumerate(cal, 1):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue
                    
                # Highlight current day
                if day == now.day:
                    bg_color = '#ff6b35'
                    fg_color = 'white'
                else:
                    bg_color = self.bg_color
                    fg_color = '#333'
                    
                label = tk.Label(cal_frame, text=str(day), 
                               font=('Arial', 10), width=3,
                               fg=fg_color, bg=bg_color)
                label.grid(row=week_num, column=day_num, padx=1, pady=1)

class MusicPlayerWidget(DesktopWidget):
    """Compact music player widget"""
    def __init__(self, parent):
        super().__init__(parent, "Music Player", "#2c3e50")
        self.current_song = "No song playing"
        self.is_playing = False
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header = tk.Label(self.frame, text="MUSIC PLAYLIST", 
                         font=('Arial', 12, 'bold'), 
                         fg='white', bg=self.bg_color)
        header.pack(pady=5)
        
        # Album art placeholder
        art_frame = tk.Frame(self.frame, bg='#34495e', width=60, height=60)
        art_frame.pack_propagate(False)
        art_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Song info and controls
        info_frame = tk.Frame(self.frame, bg=self.bg_color)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        # Song title
        self.song_label = tk.Label(info_frame, text="HANNAH+MORALES • I MISS YOU SO MUCH", 
                                  font=('Arial', 10, 'bold'), 
                                  fg='white', bg=self.bg_color)
        self.song_label.pack(anchor='w')
        
        # Progress bar
        progress_frame = tk.Frame(info_frame, bg=self.bg_color)
        progress_frame.pack(fill='x', pady=2)
        
        self.progress_bar = ttk.Scale(progress_frame, from_=0, to=100, 
                                     orient=tk.HORIZONTAL)
        self.progress_bar.pack(fill='x')
        
        # Control buttons
        controls = tk.Frame(info_frame, bg=self.bg_color)
        controls.pack(anchor='w')
        
        button_style = {'font': ('Arial', 12), 'bg': '#3498db', 'fg': 'white', 
                       'relief': tk.FLAT, 'width': 3}
        
        tk.Button(controls, text="⏮", command=self.prev_song, **button_style).pack(side=tk.LEFT, padx=2)
        self.play_btn = tk.Button(controls, text="▶", command=self.toggle_play, **button_style)
        self.play_btn.pack(side=tk.LEFT, padx=2)
        tk.Button(controls, text="⏭", command=self.next_song, **button_style).pack(side=tk.LEFT, padx=2)
        tk.Button(controls, text="🎵", command=self.open_full_player, **button_style).pack(side=tk.LEFT, padx=2)
        
    def toggle_play(self):
        self.is_playing = not self.is_playing
        self.play_btn.config(text="⏸" if self.is_playing else "▶")
        
    def prev_song(self):
        # Implement previous song logic
        pass
        
    def next_song(self):
        # Implement next song logic
        pass
        
    def open_full_player(self):
        """Open the full music player application"""
        try:
            # Start music player in new window
            subprocess.Popen(['python', 'music_player.py'])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open music player: {e}")

class NotesWidget(DesktopWidget):
    """Simple notes widget"""
    def __init__(self, parent):
        super().__init__(parent, "Notes", "#f8f9fa")
        self.notes_file = "desktop_notes.txt"
        self.setup_ui()
        self.load_notes()
        
    def setup_ui(self):
        # Header
        header = tk.Label(self.frame, text="NOTE", 
                         font=('Arial', 14, 'bold'), 
                         fg='#333', bg=self.bg_color)
        header.pack(pady=5)
        
        # Text area
        self.text_area = tk.Text(self.frame, width=30, height=8, 
                                font=('Arial', 10), bg='white', fg='#333',
                                relief=tk.FLAT, bd=5)
        self.text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        # Auto-save when text changes
        self.text_area.bind('<KeyRelease>', self.save_notes)
        
    def load_notes(self):
        """Load notes from file"""
        try:
            if os.path.exists(self.notes_file):
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_area.insert('1.0', content)
        except Exception as e:
            print(f"Error loading notes: {e}")
            
    def save_notes(self, event=None):
        """Save notes to file"""
        try:
            content = self.text_area.get('1.0', tk.END)
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Error saving notes: {e}")

class AppLauncherWidget(DesktopWidget):
    """Application launcher with app icons"""
    def __init__(self, parent):
        super().__init__(parent, "Apps", "#f8f9fa")
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title = tk.Label(self.frame, text="APPS", 
                        font=('Arial', 12, 'bold'), 
                        fg='#333', bg=self.bg_color)
        title.pack(pady=5)
        
        # App grid
        apps_frame = tk.Frame(self.frame, bg=self.bg_color)
        apps_frame.pack(padx=10, pady=5)
        
        # Define apps
        apps = [
            ("Music Player", self.open_music_player, "#2c3e50"),
            ("Upload Music", self.open_upload_page, "#27ae60"),
            ("Calculator", self.open_calculator, "#e74c3c"),
            ("Browser", self.open_browser, "#3498db"),
            ("Files", self.open_files, "#f39c12"),
            ("Settings", self.open_settings, "#9b59b6")
        ]
        
        # Create app buttons in 3x2 grid
        for i, (name, command, color) in enumerate(apps):
            row = i // 3
            col = i % 3
            
            btn = tk.Button(apps_frame, text="+", font=('Arial', 16, 'bold'),
                           bg=color, fg='white', relief=tk.FLAT,
                           width=4, height=2, command=command)
            btn.grid(row=row, column=col, padx=3, pady=3)
            
            # App label
            label = tk.Label(apps_frame, text="APPS", font=('Arial', 8),
                           fg='#666', bg=self.bg_color)
            label.grid(row=row+2, column=col, pady=(0, 5))
            
    def open_music_player(self):
        try:
            subprocess.Popen(['python', 'music_player.py'])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open music player: {e}")
            
    def open_upload_page(self):
        try:
            webbrowser.open('http://localhost:5000')
        except Exception as e:
            messagebox.showerror("Error", f"Could not open upload page: {e}")
            
    def open_calculator(self):
        try:
            if os.name == 'nt':  # Windows
                subprocess.Popen(['calc'])
            else:  # Linux/Mac
                subprocess.Popen(['gnome-calculator'])
        except Exception as e:
            messagebox.showinfo("Info", "Calculator not available")
            
    def open_browser(self):
        try:
            webbrowser.open('https://google.com')
        except Exception as e:
            messagebox.showerror("Error", f"Could not open browser: {e}")
            
    def open_files(self):
        try:
            if os.name == 'nt':  # Windows
                subprocess.Popen(['explorer'])
            else:  # Linux
                subprocess.Popen(['nautilus'])
        except Exception as e:
            # Fallback to file dialog
            filedialog.askdirectory()
            
    def open_settings(self):
        messagebox.showinfo("Settings", "Settings panel coming soon!")

class FilesWidget(DesktopWidget):
    """Files and folders widget"""
    def __init__(self, parent):
        super().__init__(parent, "Files", "#f8f9fa")
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header = tk.Label(self.frame, text="FILES", 
                         font=('Arial', 12, 'bold'), 
                         fg='#333', bg=self.bg_color)
        header.pack(pady=5)
        
        # Files grid
        files_frame = tk.Frame(self.frame, bg=self.bg_color)
        files_frame.pack(padx=10, pady=5)
        
        # Folder icons
        for i in range(4):
            folder_btn = tk.Button(files_frame, text="📁", font=('Arial', 24),
                                 bg='#f39c12', fg='white', relief=tk.FLAT,
                                 width=4, height=2, 
                                 command=lambda: self.open_folder())
            folder_btn.grid(row=0, column=i, padx=3, pady=3)
            
    def open_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            try:
                if os.name == 'nt':
                    subprocess.Popen(['explorer', folder])
                else:
                    subprocess.Popen(['nautilus', folder])
            except Exception:
                messagebox.showinfo("Info", f"Selected folder: {folder}")

class MotivationalWidget(DesktopWidget):
    """Motivational quote widget"""
    def __init__(self, parent):
        super().__init__(parent, "Motivation", "#ff6b35")
        self.setup_ui()
        
    def setup_ui(self):
        # Background image placeholder
        img_frame = tk.Frame(self.frame, bg='#2c3e50', height=120)
        img_frame.pack(fill='x', padx=10, pady=10)
        img_frame.pack_propagate(False)
        
        # Quote text
        quote_label = tk.Label(img_frame, text="Just keep moving forward", 
                              font=('Arial', 14, 'italic'), 
                              fg='white', bg='#2c3e50')
        quote_label.pack(expand=True)

class CustomDesktop:
    """Main desktop application"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sou Jin AE Desktop")
        self.root.geometry("1400x900")
        self.root.configure(bg='#e8e9ea')
        
        # Create main container
        self.main_frame = tk.Frame(self.root, bg='#e8e9ea')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.setup_layout()
        
    def setup_layout(self):
        # Welcome title
        title_frame = tk.Frame(self.main_frame, bg='#e8e9ea')
        title_frame.pack(fill='x', pady=(0, 20))
        
        welcome_label = tk.Label(title_frame, text="Welcome", 
                                font=('Arial', 36, 'bold'), 
                                fg='#ff6b35', bg='#e8e9ea')
        welcome_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(title_frame, text="SOU JIN AE\nDESKTOP", 
                                 font=('Arial', 28, 'bold'), 
                                 fg='#333', bg='#e8e9ea')
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Main content area
        content_frame = tk.Frame(self.main_frame, bg='#e8e9ea')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left column
        left_column = tk.Frame(content_frame, bg='#e8e9ea')
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Calendar widget
        self.calendar_widget = CalendarWidget(left_column)
        self.calendar_widget.pack(fill='x', pady=(0, 20))
        
        # Motivational widget
        self.motivational_widget = MotivationalWidget(left_column)
        self.motivational_widget.pack(fill='x', pady=(0, 20))
        
        # Notes widget
        self.notes_widget = NotesWidget(left_column)
        self.notes_widget.pack(fill=tk.BOTH, expand=True)
        
        # Right column
        right_column = tk.Frame(content_frame, bg='#e8e9ea')
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Clock widget
        self.clock_widget = ClockWidget(right_column)
        self.clock_widget.pack(fill='x', pady=(0, 20))
        
        # Music player widget
        self.music_widget = MusicPlayerWidget(right_column)
        self.music_widget.pack(fill='x', pady=(0, 20))
        
        # App launcher widget
        self.app_launcher_widget = AppLauncherWidget(right_column)
        self.app_launcher_widget.pack(fill='x', pady=(0, 20))
        
        # Files widget
        self.files_widget = FilesWidget(right_column)
        self.files_widget.pack(fill='x')
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    print("🖥️  Iniciando Escritorio Personalizado Sou Jin AE")
    print("📅 Widgets: Calendario, Reloj, Música, Notas, Apps, Archivos")
    print("🎵 Reproductor de música integrado")
    
    desktop = CustomDesktop()
    desktop.run()