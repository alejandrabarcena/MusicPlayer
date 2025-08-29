# Music Player Application

## Overview

This is a desktop music player application built with Python using Tkinter for the GUI and Pygame for audio playback functionality. The application provides a complete music player experience with playlist management, audio controls, volume adjustment, metadata extraction, and classical music search capabilities. It supports common audio formats including MP3, OGG, and WAV files, with an intuitive graphical interface for managing and playing music collections. The application now includes integrated MusicBrainz API search functionality specifically designed for classical music discovery.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### GUI Framework
- **Tkinter-based Interface**: Uses Python's built-in Tkinter library with ttk widgets for a modern appearance
- **Event-driven Architecture**: Implements callback-based user interactions for all player controls
- **Threading Model**: Separates audio playback operations from UI updates using background threads to maintain interface responsiveness

### Audio Engine
- **Pygame Mixer**: Core audio playback functionality using pygame.mixer for cross-platform audio support
- **Audio Configuration**: Configured with 44.1kHz frequency, 16-bit depth, stereo channels, and 1024-byte buffer for quality playback
- **Volume Control**: Integrated volume management with real-time adjustment capabilities

### Playlist Management
- **In-memory Playlist**: Maintains current playlist as a Python list with index-based navigation
- **File Persistence**: Implements JSON-based playlist saving/loading for session persistence
- **Dynamic Loading**: Supports adding individual files or entire directories to playlists

### Metadata Handling
- **Mutagen Integration**: Optional metadata extraction using Mutagen library for MP3, OGG, and WAV files
- **Graceful Degradation**: Application continues to function even when Mutagen is not available, with metadata features disabled
- **Error Handling**: Implements proper exception handling for corrupted or unsupported audio files

### File System Integration
- **File Dialog Integration**: Uses native file dialogs for intuitive file and folder selection
- **Path Handling**: Leverages Python's pathlib for cross-platform file path management
- **Format Support**: Supports multiple audio formats with extensible architecture for adding new formats

### User Interface Components
- **Control Panel**: Standard playback controls (play, pause, stop, next, previous)
- **Progress Tracking**: Real-time position tracking with seek functionality
- **Volume Control**: Visual volume slider with instant feedback
- **Playlist Display**: Interactive playlist view with selection capabilities
- **Keyboard Shortcuts**: Comprehensive keyboard navigation support
- **Classical Music Search**: Integrated MusicBrainz API search with composer, work, and recording lookup
- **Historical Period Filters**: Quick search by musical periods (Baroque, Classical, Romantic, Modern)

## External Dependencies

### Core Dependencies
- **Tkinter**: Built-in Python GUI framework for cross-platform desktop interface
- **Pygame**: Audio playback engine and multimedia library for sound processing
- **Pathlib**: Modern Python path handling (part of standard library)
- **JSON**: Playlist persistence using standard library JSON module
- **Threading**: Background operations using Python's threading module
- **OS**: File system operations using standard library
- **Requests**: HTTP client library for MusicBrainz API integration
- **Time**: Rate limiting and timing operations for API compliance

### Optional Dependencies
- **Mutagen**: Third-party library for audio metadata extraction and manipulation
  - Supports MP3, OGG Vorbis, and WAV metadata
  - Gracefully handles absence with fallback functionality
  - Provides ID3 tag reading capabilities

### MusicBrainz Integration
- **MusicBrainz API**: Classical music database search integration
  - Composer search with biographical information and historical periods
  - Musical work (composition) search with type classification
  - Recording search with artist credits and album information
  - Rate-limited API calls (1 request/second) for server compliance
  - Background threading for non-blocking search operations

### System Requirements
- **Audio System**: Requires system audio drivers compatible with Pygame mixer
- **File System Access**: Needs read permissions for audio file directories
- **Display System**: Requires GUI display capability for Tkinter interface

## Deployment Configuration

### Application Modes
The application supports two distinct modes of operation:

1. **Web Server Mode (Default)**: 
   - Launched with `python main.py`
   - Provides a web-based music upload interface on port 5000
   - Suitable for cloud deployments (Autoscale or Reserved VM)
   - Includes Flask server for file management and music uploads

2. **Desktop GUI Mode**: 
   - Launched with `python main.py desktop`
   - Provides full desktop music player with Tkinter interface
   - Requires VNC for cloud deployments
   - Only suitable for Reserved VM deployments due to persistent GUI requirements

### Deployment Types
- **For Web Interface**: Use Autoscale Deployments (default) for cost-effective scaling
- **For Desktop GUI**: Must use Reserved VM Deployments due to:
  - GUI applications requiring persistent desktop environment
  - VNC display requirements for remote GUI access
  - Long-running desktop session needs
  - Audio output requirements

### Audio Configuration
- Desktop mode requires `audio = true` in .replit configuration
- GUI applications need VNC output type for proper display
- Audio drivers and desktop environment dependencies are handled by Nix packages