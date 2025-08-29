#!/usr/bin/env python3
"""
Web server for music file upload functionality
Allows users to upload their own music files to use with the music player
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
import os
import shutil
from werkzeug.utils import secure_filename
import mimetypes

app = Flask(__name__)
app.secret_key = 'music_player_upload_secret_key_2024'

# Configuration
UPLOAD_FOLDER = 'uploaded_music'
SAMPLE_FOLDER = 'sample_music'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac', 'm4a'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAMPLE_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(filepath):
    """Get file size in MB"""
    return round(os.path.getsize(filepath) / (1024 * 1024), 2)

@app.route('/')
def index():
    """Main page showing uploaded music and upload form"""
    uploaded_files = []
    sample_files = []
    
    # Get uploaded music files
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                uploaded_files.append({
                    'name': filename,
                    'size': get_file_size_mb(filepath),
                    'type': 'uploaded'
                })
    
    # Get sample music files
    if os.path.exists(SAMPLE_FOLDER):
        for filename in os.listdir(SAMPLE_FOLDER):
            if allowed_file(filename):
                filepath = os.path.join(SAMPLE_FOLDER, filename)
                sample_files.append({
                    'name': filename,
                    'size': get_file_size_mb(filepath),
                    'type': 'sample'
                })
    
    return render_template('index.html', 
                         uploaded_files=uploaded_files, 
                         sample_files=sample_files,
                         total_uploaded=len(uploaded_files),
                         total_sample=len(sample_files))

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'files' not in request.files:
        flash('No se seleccionaron archivos', 'error')
        return redirect(url_for('index'))
    
    files = request.files.getlist('files')
    uploaded_count = 0
    
    for file in files:
        if file.filename == '':
            continue
            
        if file and allowed_file(file.filename):
            # Check file size
            file.seek(0, 2)  # Seek to end of file
            file_size = file.tell()
            file.seek(0)  # Seek back to beginning
            
            if file_size > MAX_FILE_SIZE:
                flash(f'El archivo {file.filename} es muy grande (máximo 50MB)', 'error')
                continue
            
            filename = secure_filename(file.filename)
            # Add timestamp if file already exists
            if os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
                name, ext = os.path.splitext(filename)
                import time
                timestamp = int(time.time())
                filename = f"{name}_{timestamp}{ext}"
            
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            uploaded_count += 1
        else:
            flash(f'Formato no válido: {file.filename}. Use MP3, WAV, OGG, FLAC o M4A', 'error')
    
    if uploaded_count > 0:
        flash(f'Se subieron {uploaded_count} archivo(s) exitosamente', 'success')
    
    return redirect(url_for('index'))

@app.route('/delete/<path:filename>')
def delete_file(filename):
    """Delete an uploaded file"""
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f'Archivo {filename} eliminado', 'success')
    else:
        flash(f'Archivo {filename} no encontrado', 'error')
    
    return redirect(url_for('index'))

@app.route('/music/<path:filename>')
def serve_music(filename):
    """Serve music files"""
    # Check uploaded files first
    uploaded_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    if os.path.exists(uploaded_path):
        return send_from_directory(UPLOAD_FOLDER, secure_filename(filename))
    
    # Check sample files
    sample_path = os.path.join(SAMPLE_FOLDER, secure_filename(filename))
    if os.path.exists(sample_path):
        return send_from_directory(SAMPLE_FOLDER, secure_filename(filename))
    
    return "Archivo no encontrado", 404

@app.route('/api/music-files')
def api_music_files():
    """API endpoint to get all music files for the music player"""
    all_files = []
    
    # Add uploaded files
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                all_files.append({
                    'name': filename,
                    'path': os.path.join(UPLOAD_FOLDER, filename),
                    'url': url_for('serve_music', filename=filename),
                    'type': 'uploaded'
                })
    
    # Add sample files
    if os.path.exists(SAMPLE_FOLDER):
        for filename in os.listdir(SAMPLE_FOLDER):
            if allowed_file(filename):
                all_files.append({
                    'name': filename,
                    'path': os.path.join(SAMPLE_FOLDER, filename),
                    'url': url_for('serve_music', filename=filename),
                    'type': 'sample'
                })
    
    return jsonify(all_files)

@app.route('/copy-to-player')
def copy_to_player():
    """Copy uploaded files to the music player directory"""
    copied_count = 0
    
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                src = os.path.join(UPLOAD_FOLDER, filename)
                # Copy to sample_music so the music player can access it
                dst = os.path.join(SAMPLE_FOLDER, filename)
                
                # Don't overwrite if file already exists
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    copied_count += 1
    
    if copied_count > 0:
        flash(f'Se copiaron {copied_count} archivo(s) al reproductor de música', 'success')
    else:
        flash('No hay archivos nuevos para copiar', 'info')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("🎵 Servidor de subida de música iniciado")
    print("📁 Sube tus archivos MP3, WAV, OGG, FLAC o M4A")
    print("🎼 Después podrás usarlos en el reproductor de música")
    app.run(host='0.0.0.0', port=5000, debug=True)