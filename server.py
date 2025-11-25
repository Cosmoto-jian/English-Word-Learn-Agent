from flask import Flask, render_template, request, jsonify, send_from_directory, Response, stream_with_context
import os
import re
import json
import time
import socket
import subprocess
import signal
from threading import Thread
from generate_card import generate_card_data, clean_text
from explain_word import load_env_vars

# Load environment variables at startup
load_env_vars()

app = Flask(__name__, static_folder='static', template_folder='templates')

def is_port_in_use(port, host='127.0.0.1'):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True

def get_process_using_port(port):
    """Find the process ID using the specified port."""
    try:
        # Use lsof command to find process using the port
        result = subprocess.run(
            ['lsof', '-i', f':{port}', '-t'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            return [int(pid) for pid in pids if pid]
        return []
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        return []

def kill_process_on_port(port):
    """Kill the process using the specified port."""
    pids = get_process_using_port(port)
    if not pids:
        return False

    killed = False
    for pid in pids:
        try:
            # Check if it's a Python server process
            result = subprocess.run(
                ['ps', '-p', str(pid), '-o', 'command='],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                command = result.stdout.strip()
                print(f"Found process on port {port}:")
                print(f"  PID: {pid}")
                print(f"  Command: {command}")

                # Only kill if it looks like our server
                if 'python' in command.lower() and 'server.py' in command.lower():
                    print(f"  → Killing old server process (PID {pid})...")
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.5)  # Give it time to terminate
                    killed = True
                else:
                    print(f"  → Skipping (not a server.py process)")
        except (ProcessLookupError, OSError, subprocess.TimeoutExpired) as e:
            print(f"  → Could not kill process {pid}: {e}")

    return killed

def cleanup_port(port, host='127.0.0.1'):
    """Clean up the port if it's in use by an old server process."""
    if is_port_in_use(port, host):
        print(f"\n⚠️  Port {port} is already in use!")
        if kill_process_on_port(port):
            print(f"✓ Successfully cleaned up port {port}\n")
            time.sleep(1)  # Wait a bit for the port to be released
            return True
        else:
            print(f"✗ Could not clean up port {port}")
            print(f"  You may need to manually stop the process or use a different port.\n")
            return False
    return True

def cleanup_all_server_processes():
    """Find and kill all running server.py processes."""
    try:
        # Find all Python processes running server.py
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return False

        current_pid = os.getpid()
        killed_count = 0

        for line in result.stdout.split('\n'):
            # Look for python processes running server.py
            if 'python' in line.lower() and 'server.py' in line.lower():
                # Extract PID (second column)
                parts = line.split()
                if len(parts) < 2:
                    continue

                try:
                    pid = int(parts[1])

                    # Don't kill ourselves
                    if pid == current_pid:
                        continue

                    print(f"  Found old server.py process (PID {pid})")
                    os.kill(pid, signal.SIGTERM)
                    killed_count += 1

                except (ValueError, ProcessLookupError, OSError) as e:
                    continue

        if killed_count > 0:
            print(f"  ✓ Killed {killed_count} old server process(es)")
            time.sleep(1.5)  # Give processes time to terminate
            return True

        return False

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"  Could not check for old processes: {e}")
        return False

# Add custom static file handler for audio with correct MIME type
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files with proper MIME types and cache control"""
    response = send_from_directory(app.static_folder, filename)

    # Set correct MIME type for JavaScript modules
    if filename.endswith('.js'):
        response.headers['Content-Type'] = 'application/javascript; charset=utf-8'

    # Set correct MIME type for MP3 files
    elif filename.endswith('.mp3'):
        response.headers['Content-Type'] = 'audio/mpeg'
        response.headers['Accept-Ranges'] = 'bytes'

    # Disable caching for chat audio files (they're unique anyway)
    if filename.startswith('chat_audio_'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    return response

@app.route('/public/<path:filename>')
def serve_public(filename):
    """Serve public files (cached images) with proper MIME types"""
    public_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')
    response = send_from_directory(public_dir, filename)

    # Set correct MIME type for PNG files
    if filename.endswith('.png'):
        response.headers['Content-Type'] = 'image/png'
        # Enable long-term caching for images (they're content-addressed by word)
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year

    return response

def validate_word(word):
    """Validate that the word input is safe and reasonable."""
    if not word:
        return False, "Word cannot be empty"
    if len(word) > 50:
        return False, "Word is too long (max 50 characters)"
    # Only allow letters, hyphens, and apostrophes
    if not re.match(r"^[a-zA-Z\-']+$", word):
        return False, "Word contains invalid characters"
    return True, None

def validate_message(message):
    """Validate that the chat message is safe and reasonable."""
    if not message:
        return False, "Message cannot be empty"
    if len(message) > 1000:
        return False, "Message is too long (max 1000 characters)"
    # Basic check for potential injection attempts
    if any(char in message for char in ['<', '>', '\x00']):
        return False, "Message contains invalid characters"
    return True, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/voices', methods=['GET'])
def get_voices():
    """Return available English voices for selection"""
    voices = [
        {"id": "Joanna", "name": "Joanna (Female, US)", "gender": "Female", "language": "en-US"},
        {"id": "Matthew", "name": "Matthew (Male, US)", "gender": "Male", "language": "en-US"},
        {"id": "Salli", "name": "Salli (Female, US)", "gender": "Female", "language": "en-US"}
    ]
    return jsonify({"success": True, "voices": voices})

@app.route('/api/levels', methods=['GET'])
def get_levels():
    """Return available vocabulary levels for selection"""
    from word import get_available_levels
    levels = get_available_levels()
    return jsonify({"success": True, "levels": levels})

@app.route('/api/models', methods=['GET'])
def get_models():
    """Return available AI models for selection"""
    models = {
        "text_models": [
            {"id": "mistral", "name": "Mistral Large"},
            {"id": "deepseek", "name": "DeepSeek Chat"},
            {"id": "gemini", "name": "Google Gemini"}
        ],
        "audio_models": [
            {"id": "polly", "name": "Amazon Polly"},
            {"id": "deepgram", "name": "Deepgram TTS"}
        ]
    }
    return jsonify({"success": True, "models": models})

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    # Safely get parameters
    target_word = (data.get('word') or '').strip()
    voice_id = data.get('voice_id', 'Joanna')
    level = data.get('level', 'junior')
    text_model = data.get('text_model', 'mistral')
    audio_model = data.get('audio_model', 'polly')

    # Validate input if a word is provided
    if target_word:
        is_valid, error_msg = validate_word(target_word)
        if not is_valid:
            return jsonify({"success": False, "error": error_msg}), 400

    # Call the generation logic with all parameters
    result = generate_card_data(
        target_word if target_word else None,
        voice_id=voice_id,
        level=level,
        text_model=text_model,
        audio_model=audio_model
    )

    if "error" in result:
        return jsonify({"success": False, "error": result["error"]}), 500

    # Clean text for HTML display
    sections = result["sections"]
    cleaned_sections = {}
    for key, value in sections.items():
        if key == "Phonetic Transcription":
            # Keep phonetic transcription clean, no HTML conversion
            cleaned_sections[key] = value.strip()
        else:
            cleaned_sections[key] = clean_text(value)

    result["sections"] = cleaned_sections
    result["success"] = True

    return jsonify(result)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Original non-streaming chat endpoint (kept for compatibility)"""
    from explain_word import chat_with_ai
    from generate_audio import generate_audio

    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    # Safely get message and voice_id
    user_message = (data.get('message') or '').strip()
    voice_id = data.get('voice_id', 'Joanna')  # Default to Joanna

    # Validate message
    is_valid, error_msg = validate_message(user_message)
    if not is_valid:
        return jsonify({"success": False, "error": error_msg}), 400

    # 1. Get AI Response
    ai_response = chat_with_ai(user_message)

    if ai_response.startswith("Error") or ai_response.startswith("HTTP Error") or ai_response.startswith("Connection Error"):
        return jsonify({"success": False, "error": ai_response}), 500

    # 2. Generate Audio
    # Use timestamp for unique filename
    timestamp = int(time.time() * 1000)
    audio_filename = f"chat_audio_{timestamp}.mp3"

    # Ensure static directory exists
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    audio_path = os.path.join(static_dir, audio_filename)

    generate_audio(ai_response, audio_path, voice_id=voice_id)

    return jsonify({
        "success": True,
        "response": ai_response,
        "audio_url": f"/static/{audio_filename}"
    })

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Streaming chat endpoint with real-time text display"""
    from explain_word import chat_with_ai
    from generate_audio import generate_audio

    data = request.json
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    user_message = (data.get('message') or '').strip()
    voice_id = data.get('voice_id', 'Joanna')
    text_model = data.get('text_model', 'mistral')
    audio_model = data.get('audio_model', 'polly')

    # Validate message
    is_valid, error_msg = validate_message(user_message)
    if not is_valid:
        return jsonify({"success": False, "error": error_msg}), 400

    def generate():
        """Generator function for streaming response"""
        accumulated_text = ""

        try:
            # Stream text chunks using selected text model
            for chunk in chat_with_ai(user_message, stream=True, text_model=text_model):
                if chunk.startswith("Error"):
                    yield f"data: {json.dumps({'error': chunk})}\n\n"
                    return

                accumulated_text += chunk
                # Send each chunk to frontend
                yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"

            # After streaming is complete, generate audio asynchronously
            timestamp = int(time.time() * 1000)
            audio_filename = f"chat_audio_{timestamp}.mp3"

            static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
            if not os.path.exists(static_dir):
                os.makedirs(static_dir)

            audio_path = os.path.join(static_dir, audio_filename)

            # Generate audio in background thread to not block response
            def generate_audio_async():
                print(f"[Chat Audio] Starting audio generation for {audio_filename}")
                print(f"[Chat Audio] Text length: {len(accumulated_text)} characters")
                print(f"[Chat Audio] Voice: {voice_id}, Model: {audio_model}")
                success = generate_audio(accumulated_text, audio_path, voice_id=voice_id, audio_model=audio_model)
                if success:
                    print(f"[Chat Audio] Successfully generated: {audio_path}")
                    # Verify file exists and has content
                    if os.path.exists(audio_path):
                        file_size = os.path.getsize(audio_path)
                        print(f"[Chat Audio] File size: {file_size} bytes")
                    else:
                        print(f"[Chat Audio] ERROR: File not found after generation: {audio_path}")
                else:
                    print(f"[Chat Audio] ERROR: Audio generation failed")

            Thread(target=generate_audio_async, daemon=True).start()

            # Send completion message with audio URL
            # Note: Audio is being generated asynchronously, frontend will poll for it
            yield f"data: {json.dumps({'done': True, 'audio_url': f'/static/{audio_filename}'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

if __name__ == '__main__':
    # Ensure static folder exists
    if not os.path.exists('static'):
        os.makedirs('static')

    # Allow configuring port, host, and debug mode via environment variables
    default_port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    debug_mode = os.environ.get('DEBUG', 'false').lower() in ('true', '1', 'yes')

    # First, clean up any old server.py processes
    print("=" * 60)
    print("Checking for old server.py processes...")
    cleanup_all_server_processes()

    # Then check if the default port is available
    print(f"\nChecking port {default_port}...")
    port_cleaned = cleanup_port(default_port, host)

    # Determine which port to use
    if port_cleaned or not is_port_in_use(default_port, host):
        # Port is available, use it
        start_port = default_port
        print(f"✓ Port {default_port} is available\n")
    else:
        # Port couldn't be cleaned, find alternative
        print(f"ℹ️  Searching for alternative port...\n")
        start_port = default_port + 1
        while is_port_in_use(start_port, host) and start_port < default_port + 20:
            start_port += 1

        if start_port >= default_port + 20:
            print("❌ Could not find an available port")
            exit(1)

    # Try to start the server
    print("=" * 60)
    try:
        print(f"🚀 Starting server on {host}:{start_port}")
        print(f"📌 Access your server at: http://{host}:{start_port}")
        if debug_mode:
            print(f"⚙️  Debug mode: ON")
        else:
            print(f"⚙️  Debug mode: OFF (suitable for background running)")
        print("=" * 60 + "\n")
        app.run(debug=debug_mode, port=start_port, host=host, use_reloader=False)
    except OSError as e:
        print(f"\n❌ Failed to start server: {e}")
        exit(1)
