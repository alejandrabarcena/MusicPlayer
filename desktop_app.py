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
from PIL import Image, ImageTk

# Import music functionality
from music_player import MusicPlayer

class DesktopWidget:
    """Base class for desktop widgets"""
    def __init__(self, parent, title="Widget", bg_color="#ffffff"):
        self.parent = parent
        self.frame = tk.Frame(parent, bg=bg_color, relief=tk.FLAT, bd=0, highlightthickness=2, 
                             highlightbackground="#ff6b35", highlightcolor="#ff6b35")
        self.title = title
        self.bg_color = bg_color
        
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

class ClockWidget(DesktopWidget):
    """Digital clock and date widget"""
    def __init__(self, parent):
        super().__init__(parent, "Clock", "#ffffff")
        self.setup_ui()
        self.update_time()
        
    def setup_ui(self):
        # Add padding frame
        padding_frame = tk.Frame(self.frame, bg=self.bg_color)
        padding_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Time display
        self.time_label = tk.Label(padding_frame, text="09:00 AM", 
                                  font=('Arial', 42, 'bold'), 
                                  fg='#ff6b35', bg=self.bg_color)
        self.time_label.pack(pady=(0, 5))
        
        # Date display
        self.date_label = tk.Label(padding_frame, text="Friday, 29 August 2025", 
                                  font=('Arial', 16), 
                                  fg='#333333', bg=self.bg_color)
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
    """Enhanced Calendar widget with events and functionality"""
    def __init__(self, parent):
        super().__init__(parent, "Calendar", "#ffffff")
        self.current_date = datetime.now()
        self.events = self.load_events()
        self.setup_ui()
        
    def load_events(self):
        """Load events from file"""
        try:
            if os.path.exists('calendar_events.json'):
                with open('calendar_events.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def save_events(self):
        """Save events to file"""
        try:
            with open('calendar_events.json', 'w', encoding='utf-8') as f:
                json.dump(self.events, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving events: {e}")
        
    def setup_ui(self):
        # Navigation header
        nav_frame = tk.Frame(self.frame, bg=self.bg_color)
        nav_frame.pack(fill='x', padx=5, pady=5)
        
        # Previous month button
        tk.Button(nav_frame, text="◀", font=('Arial', 12), bg='#ff6b35', fg='white',
                 relief=tk.FLAT, width=3, command=self.prev_month).pack(side=tk.LEFT)
        
        # Month/Year title
        month_name = self.current_date.strftime("%B %Y").upper()
        self.title_label = tk.Label(nav_frame, text=month_name, 
                                   font=('Arial', 14, 'bold'), 
                                   fg='#333', bg=self.bg_color)
        self.title_label.pack(side=tk.LEFT, expand=True)
        
        # Next month button
        tk.Button(nav_frame, text="▶", font=('Arial', 12), bg='#ff6b35', fg='white',
                 relief=tk.FLAT, width=3, command=self.next_month).pack(side=tk.RIGHT)
        
        # Calendar grid
        self.cal_frame = tk.Frame(self.frame, bg=self.bg_color)
        self.cal_frame.pack(padx=10, pady=5)
        
        self.update_calendar()
        
        # Events section
        events_frame = tk.Frame(self.frame, bg=self.bg_color)
        events_frame.pack(fill='x', padx=10, pady=5)
        
        events_label = tk.Label(events_frame, text="Today's Events:", 
                               font=('Arial', 10, 'bold'), 
                               fg='#333', bg=self.bg_color)
        events_label.pack(anchor='w')
        
        self.events_text = tk.Label(events_frame, text="No events today", 
                                   font=('Arial', 9), fg='#666', bg=self.bg_color,
                                   justify=tk.LEFT, wraplength=200)
        self.events_text.pack(anchor='w')
        
        self.update_today_events()
    
    def update_calendar(self):
        """Update the calendar display"""
        # Clear existing calendar
        for widget in self.cal_frame.winfo_children():
            widget.destroy()
        
        # Day headers
        days = ['S', 'M', 'T', 'W', 'T', 'F', 'S']
        for i, day in enumerate(days):
            label = tk.Label(self.cal_frame, text=day, font=('Arial', 10, 'bold'),
                           fg='#666', bg=self.bg_color, width=3)
            label.grid(row=0, column=i, padx=1, pady=1)
        
        # Calendar days
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        now = datetime.now()
        
        for week_num, week in enumerate(cal, 1):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue
                
                date_key = f"{self.current_date.year}-{self.current_date.month:02d}-{day:02d}"
                has_events = date_key in self.events
                
                # Determine colors
                if (day == now.day and 
                    self.current_date.month == now.month and 
                    self.current_date.year == now.year):
                    bg_color = '#ff6b35'
                    fg_color = 'white'
                elif has_events:
                    bg_color = '#ffe5d4'
                    fg_color = '#333'
                else:
                    bg_color = self.bg_color
                    fg_color = '#333'
                
                # Create clickable day button
                day_btn = tk.Button(self.cal_frame, text=str(day), 
                                   font=('Arial', 10), width=3,
                                   fg=fg_color, bg=bg_color, relief=tk.FLAT,
                                   command=lambda d=day: self.day_clicked(d))
                day_btn.grid(row=week_num, column=day_num, padx=1, pady=1)
                
                # Add event indicator
                if has_events:
                    day_btn.config(font=('Arial', 10, 'bold'))
    
    def day_clicked(self, day):
        """Handle day click - add/view events"""
        date_key = f"{self.current_date.year}-{self.current_date.month:02d}-{day:02d}"
        
        # Create event dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title(f"Events for {self.current_date.strftime('%B')} {day}")
        dialog.geometry("400x300")
        dialog.configure(bg='#f7f4f1')
        
        # Center the dialog
        dialog.transient(self.frame.winfo_toplevel())
        dialog.grab_set()
        
        # Title
        title = tk.Label(dialog, text=f"Events for {self.current_date.strftime('%B')} {day}", 
                        font=('Arial', 14, 'bold'), fg='#333', bg='#f7f4f1')
        title.pack(pady=10)
        
        # Existing events
        events_frame = tk.Frame(dialog, bg='#f7f4f1')
        events_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Show existing events
        if date_key in self.events:
            for i, event in enumerate(self.events[date_key]):
                event_frame = tk.Frame(events_frame, bg='#ffffff', relief=tk.RAISED, bd=1)
                event_frame.pack(fill='x', pady=2)
                
                event_label = tk.Label(event_frame, text=event, font=('Arial', 10),
                                      fg='#333', bg='#ffffff', anchor='w')
                event_label.pack(side=tk.LEFT, fill='x', expand=True, padx=5, pady=5)
                
                delete_btn = tk.Button(event_frame, text="✖", font=('Arial', 8),
                                      bg='#ff6b35', fg='white', relief=tk.FLAT,
                                      command=lambda idx=i: self.delete_event(date_key, idx, dialog))
                delete_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Add new event
        add_frame = tk.Frame(dialog, bg='#f7f4f1')
        add_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(add_frame, text="Add new event:", font=('Arial', 10, 'bold'),
                fg='#333', bg='#f7f4f1').pack(anchor='w')
        
        entry = tk.Entry(add_frame, font=('Arial', 10), width=40)
        entry.pack(pady=5, fill='x')
        entry.focus()
        
        def add_event():
            event_text = entry.get().strip()
            if event_text:
                if date_key not in self.events:
                    self.events[date_key] = []
                self.events[date_key].append(event_text)
                self.save_events()
                self.update_calendar()
                self.update_today_events()
                dialog.destroy()
        
        add_btn = tk.Button(add_frame, text="Add Event", font=('Arial', 10),
                           bg='#ff6b35', fg='white', relief=tk.FLAT,
                           command=add_event)
        add_btn.pack(pady=5)
        
        # Bind Enter key to add event
        entry.bind('<Return>', lambda e: add_event())
    
    def delete_event(self, date_key, event_index, dialog):
        """Delete an event"""
        if date_key in self.events and event_index < len(self.events[date_key]):
            del self.events[date_key][event_index]
            if not self.events[date_key]:  # Remove date if no events left
                del self.events[date_key]
            self.save_events()
            self.update_calendar()
            self.update_today_events()
            dialog.destroy()
            # Reopen the dialog to show updated events
            self.day_clicked(int(date_key.split('-')[2]))
    
    def prev_month(self):
        """Go to previous month"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self.title_label.config(text=self.current_date.strftime("%B %Y").upper())
        self.update_calendar()
    
    def next_month(self):
        """Go to next month"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self.title_label.config(text=self.current_date.strftime("%B %Y").upper())
        self.update_calendar()
    
    def update_today_events(self):
        """Update today's events display"""
        today = datetime.now()
        today_key = f"{today.year}-{today.month:02d}-{today.day:02d}"
        
        if today_key in self.events and self.events[today_key]:
            events_text = "\n".join([f"• {event}" for event in self.events[today_key][:3]])
            if len(self.events[today_key]) > 3:
                events_text += f"\n... and {len(self.events[today_key]) - 3} more"
        else:
            events_text = "No events today"
        
        self.events_text.config(text=events_text)

class MusicPlayerWidget(DesktopWidget):
    """Modern music player widget with album art"""
    def __init__(self, parent):
        super().__init__(parent, "Music Player", "#ffffff")
        self.current_song = "No song playing"
        self.is_playing = False
        self.setup_ui()
        
    def setup_ui(self):
        # Main container with padding
        main_container = tk.Frame(self.frame, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Header
        header = tk.Label(main_container, text="MUSIC PLAYLIST", 
                         font=('Arial', 14, 'bold'), 
                         fg='#333333', bg=self.bg_color)
        header.pack(pady=(0, 15))
        
        # Content container
        content_frame = tk.Frame(main_container, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Album art - larger and more prominent
        art_frame = tk.Frame(content_frame, bg='#333333', width=120, height=120, relief=tk.FLAT)
        art_frame.pack_propagate(False)
        art_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        # Add album art placeholder with figure
        art_label = tk.Label(art_frame, text="♪\n♫\n♪", font=('Arial', 20), 
                           fg='white', bg='#333333')
        art_label.pack(expand=True)
        
        # Song info and controls
        info_frame = tk.Frame(content_frame, bg=self.bg_color)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Song title - larger and more prominent
        self.song_label = tk.Label(info_frame, text="HANNAH MORALES - I MISS YOU\nSO MUCH", 
                                  font=('Arial', 14, 'bold'), 
                                  fg='#333333', bg=self.bg_color, justify=tk.LEFT)
        self.song_label.pack(anchor='w', pady=(0, 15))
        
        # Progress bar with custom styling
        progress_frame = tk.Frame(info_frame, bg=self.bg_color)
        progress_frame.pack(fill='x', pady=(0, 15))
        
        # Progress track
        track_frame = tk.Frame(progress_frame, bg='#e0e0e0', height=6)
        track_frame.pack(fill='x')
        
        # Progress indicator
        progress_indicator = tk.Frame(track_frame, bg='#333333', height=6)
        progress_indicator.pack(side=tk.LEFT, fill='y')
        progress_indicator.configure(width=150)  # Simulated progress
        
        # Control buttons - larger and modern
        controls = tk.Frame(info_frame, bg=self.bg_color)
        controls.pack(anchor='w')
        
        button_style = {'font': ('Arial', 16), 'bg': '#333333', 'fg': 'white', 
                       'relief': tk.FLAT, 'width': 3, 'height': 2, 'bd': 0}
        
        tk.Button(controls, text="⇄", command=self.shuffle, **button_style).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(controls, text="⏮", command=self.prev_song, **button_style).pack(side=tk.LEFT, padx=5)
        
        # Play button - larger and centered
        play_style = button_style.copy()
        play_style.update({'width': 4, 'height': 2, 'font': ('Arial', 20)})
        self.play_btn = tk.Button(controls, text="▶", command=self.toggle_play, **play_style)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(controls, text="⏭", command=self.next_song, **button_style).pack(side=tk.LEFT, padx=5)
        tk.Button(controls, text="⇄", command=self.repeat, **button_style).pack(side=tk.LEFT, padx=(10, 0))
        
    def toggle_play(self):
        self.is_playing = not self.is_playing
        self.play_btn.config(text="⏸" if self.is_playing else "▶")
        
    def shuffle(self):
        # Implement shuffle logic
        pass
        
    def prev_song(self):
        # Implement previous song logic
        pass
        
    def next_song(self):
        # Implement next song logic
        pass
        
    def repeat(self):
        # Implement repeat logic
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
        super().__init__(parent, "Notes", "#ffffff")
        self.notes_file = "desktop_notes.txt"
        self.setup_ui()
        self.load_notes()
        
    def setup_ui(self):
        # Header
        header = tk.Label(self.frame, text="NOTE", 
                         font=('Arial', 14, 'bold'), 
                         fg='#333333', bg=self.bg_color)
        header.pack(pady=(15, 20))
        
        # Text area with modern styling
        text_frame = tk.Frame(self.frame, bg=self.bg_color)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        self.text_area = tk.Text(text_frame, width=35, height=12, 
                                font=('Arial', 11), bg='#f9f9f9', fg='#333333',
                                relief=tk.FLAT, bd=0, wrap=tk.WORD,
                                highlightthickness=1, highlightcolor='#ff6b35')
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
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
    """Modern application launcher with rounded icons"""
    def __init__(self, parent):
        super().__init__(parent, "Apps", "#ffffff")
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title = tk.Label(self.frame, text="APPS", 
                        font=('Arial', 14, 'bold'), 
                        fg='#333333', bg=self.bg_color)
        title.pack(pady=(15, 20))
        
        # App grid with padding
        apps_frame = tk.Frame(self.frame, bg=self.bg_color)
        apps_frame.pack(padx=20, pady=(0, 15))
        
        # Define apps with modern styling
        apps = [
            ("Music Player", self.open_music_player),
            ("Upload Music", self.open_upload_page),
            ("Calculator", self.open_calculator),
            ("Browser", self.open_browser),
            ("Files", self.open_files),
            ("Settings", self.open_settings)
        ]
        
        # Create app buttons in 3x2 grid with modern design
        for i, (name, command) in enumerate(apps):
            row = i // 3
            col = i % 3
            
            # Modern rounded button
            btn = tk.Button(apps_frame, text="+", font=('Arial', 20, 'bold'),
                           bg='#333333', fg='#ff6b35', relief=tk.FLAT,
                           width=5, height=3, command=command, bd=0,
                           highlightthickness=2, highlightbackground='#ff6b35')
            btn.grid(row=row*2, column=col, padx=8, pady=8)
            
            # App label below each icon
            label = tk.Label(apps_frame, text="APPS", font=('Arial', 10),
                           fg='#666666', bg=self.bg_color)
            label.grid(row=row*2+1, column=col, pady=(5, 0))
            
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
    """Modern files and folders widget"""
    def __init__(self, parent):
        super().__init__(parent, "Files", "#ffffff")
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header = tk.Label(self.frame, text="FILES", 
                         font=('Arial', 14, 'bold'), 
                         fg='#333333', bg=self.bg_color)
        header.pack(pady=(15, 20))
        
        # Files grid with modern styling
        files_frame = tk.Frame(self.frame, bg=self.bg_color)
        files_frame.pack(padx=20, pady=(0, 15))
        
        # Modern folder icons
        for i in range(4):
            folder_btn = tk.Button(files_frame, text="📁", font=('Arial', 32),
                                 bg='#ff6b35', fg='white', relief=tk.FLAT,
                                 width=4, height=2, bd=0,
                                 command=lambda: self.open_folder())
            folder_btn.grid(row=0, column=i, padx=8, pady=5)
            
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

class BrowserBar(tk.Frame):
    """Modern browser-style navigation bar"""
    def __init__(self, parent):
        super().__init__(parent, bg='#f5f5f5', height=50)
        self.pack_propagate(False)
        self.setup_ui()
        
    def setup_ui(self):
        # Navigation buttons
        nav_frame = tk.Frame(self, bg='#f5f5f5')
        nav_frame.pack(side=tk.LEFT, padx=15, pady=10)
        
        button_style = {'font': ('Arial', 12), 'bg': '#e0e0e0', 'fg': '#666', 
                       'relief': tk.FLAT, 'width': 3, 'bd': 0}
        
        tk.Button(nav_frame, text="←", **button_style).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="→", **button_style).pack(side=tk.LEFT, padx=2)
        
        # Address bar
        address_frame = tk.Frame(self, bg='#f5f5f5')
        address_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        
        self.address_entry = tk.Entry(address_frame, font=('Arial', 12), bg='white', 
                                     relief=tk.FLAT, bd=5)
        self.address_entry.pack(fill=tk.X)
        self.address_entry.insert(0, "🔒 localhost:desktop")
        
        # Right side buttons
        right_frame = tk.Frame(self, bg='#f5f5f5')
        right_frame.pack(side=tk.RIGHT, padx=15, pady=10)
        
        tk.Button(right_frame, text="🏠", **button_style).pack(side=tk.LEFT, padx=2)
        tk.Button(right_frame, text="+", **button_style).pack(side=tk.LEFT, padx=2)
        tk.Button(right_frame, text="👤", **button_style).pack(side=tk.LEFT, padx=2)

class CustomDesktop:
    """Main desktop application with modern design"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Welcome Classical Music Desktop")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f7f4f1')  # Cream background
        
        # Create browser bar
        self.browser_bar = BrowserBar(self.root)
        self.browser_bar.pack(fill=tk.X)
        
        # Create main container with cream background
        self.main_frame = tk.Frame(self.root, bg='#f7f4f1')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        self.setup_layout()
        
    def setup_layout(self):
        # Logo section using the real image
        logo_frame = tk.Frame(self.main_frame, bg='#f7f4f1')
        logo_frame.pack(fill='x', pady=(0, 30))
        
        try:
            # Load and display the actual logo image
            logo_image = Image.open('logo.png')
            # Keep original proportions but make it fit nicely (your logo is 500x500)
            logo_image = logo_image.resize((300, 300), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            
            logo_label = tk.Label(logo_frame, image=self.logo_photo, bg='#f7f4f1')
            logo_label.pack(side=tk.LEFT)
            
        except Exception as e:
            print(f"Could not load logo image: {e}")
            # Fallback to text if image fails to load
            welcome_label = tk.Label(logo_frame, text="Welcome", 
                                    font=('Arial', 48, 'italic'), 
                                    fg='#ff6b35', bg='#f7f4f1')
            welcome_label.pack(side=tk.LEFT)
            
            classical_frame = tk.Frame(logo_frame, bg='#f7f4f1')
            classical_frame.pack(side=tk.LEFT, padx=(10, 0))
            
            classical_label = tk.Label(classical_frame, text="CLASSICAL", 
                                     font=('Arial', 38, 'bold'), 
                                     fg='#4a4a4a', bg='#f7f4f1')
            classical_label.pack(anchor='w')
            
            music_label = tk.Label(classical_frame, text="MUSIC", 
                                 font=('Arial', 38, 'bold'), 
                                 fg='#4a4a4a', bg='#f7f4f1')
            music_label.pack(anchor='w')
        
        # Main content area with proper spacing
        content_frame = tk.Frame(self.main_frame, bg='#f7f4f1')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left column - Music Player focused
        left_column = tk.Frame(content_frame, bg='#f7f4f1')
        left_column.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        
        # Music player widget (large, top left)
        self.music_widget = MusicPlayerWidget(left_column)
        self.music_widget.pack(pady=(0, 20))
        
        # Notes widget (bottom left)
        self.notes_widget = NotesWidget(left_column)
        self.notes_widget.pack(fill=tk.BOTH, expand=True)
        
        # Right column - Clock, Apps, Files
        right_column = tk.Frame(content_frame, bg='#f7f4f1')
        right_column.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Clock widget (top right)
        self.clock_widget = ClockWidget(right_column)
        self.clock_widget.pack(pady=(0, 20))
        
        # App launcher widget (center right)
        self.app_launcher_widget = AppLauncherWidget(right_column)
        self.app_launcher_widget.pack(pady=(0, 20))
        
        # Files widget (bottom right)
        self.files_widget = FilesWidget(right_column)
        self.files_widget.pack()
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    print("🖥️  Iniciando Welcome Classical Music")
    print("🎵 Reproductor de música clásica elegante")
    print("🎼 Con tu logo personalizado integrado")
    
    desktop = CustomDesktop()
    desktop.run()