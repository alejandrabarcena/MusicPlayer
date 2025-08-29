#!/usr/bin/env python3
"""
Main entry point for the Classical Music Application
Supports both web server and desktop modes
"""

import sys
import os

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'desktop':
        # Run desktop application
        from desktop_app import CustomDesktop
        print("🖥️  Iniciando Escritorio Personalizado")
        print("📅 Widgets: Calendario, Reloj, Música, Notas, Apps, Archivos")
        print("🎵 Reproductor de música integrado")
        desktop = CustomDesktop()
        desktop.run()
    else:
        # Run web server (default for deployment)
        from server import app
        print("🎵 Servidor de música clásica iniciado")
        print("📁 Sube tus archivos MP3, WAV, OGG, FLAC o M4A")
        print("🎼 Después podrás usarlos en el reproductor de música")
        
        # Get port from environment or use default (5000 for deployment compatibility)
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()