from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
from song_search import find_best_match, search_song, list_all_songs
import os
import midi_stream_to_arduino as mid

# Global playback state
current_song_path = None
current_playback_speed = 1.0
current_start_time = 0.0
is_playing = False

app = Flask(__name__)
CORS(app)  # Enable CORS for web requests

# MIDI playback endpoints
@app.route('/play', methods=['POST'])
def play(midi_file=None, start_time=0.0, playback_speed=1.0, port="COM5", baud=115200):
    global current_song_path, current_playback_speed, current_start_time, is_playing
    data = request.get_json(force=True)
    # Use current_song_path if set, else default
    if midi_file is None:
        midi_file = current_song_path or os.path.join(os.path.dirname(__file__), '..', 'other_folder', 'ode-to-joy.mid')
    else:
        current_song_path = midi_file
    start_time = float(data.get("start_time", start_time))
    playback_speed = float(data.get("playback_speed", playback_speed))
    port = data.get("port", "COM5")  # Always use COM5 by default
    baud = int(data.get("baud", baud))

    current_playback_speed = playback_speed
    current_start_time = start_time
    is_playing = True

    mid.play_midi(midi_file, start_time=start_time, playback_speed=playback_speed, port=port, baud=baud)
    return jsonify({"status": "playing", "file": midi_file})

@app.route('/stop', methods=['POST'])
def stop():
    global is_playing
    from midi_stream_to_arduino import _stop_flag, _current_thread, _lock
    with _lock:
        if _current_thread and _current_thread.is_alive():
            print("🛑 Stop requested from web interface.")
            mid._stop_flag = True
            _current_thread.join(timeout=1.0)
            is_playing = False
            return jsonify({"status": "stopped"})
    is_playing = False
    return jsonify({"status": "no active playback"})

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for web requests

# Initialize OpenAI client
client = OpenAI()

@app.route('/chat', methods=['POST'])
def chat():
    """Parse voice commands and return function calls"""
    global current_song_path, current_playback_speed, current_start_time, is_playing
    try:
        data = request.json
        user_message = data.get('text', '').lower()
        
        print(f"📝 User said: {user_message}")
        
        # Use GPT to parse the command into function calls
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": """You are a voice command parser for a music player. Convert user commands into ONE of these function calls:

- play() - when user says play, start, resume, go, continue
- pause() - when user says pause, stop, halt, wait
- rewind(x) - when user says go back, rewind, back up, reverse (x = NEGATIVE seconds, e.g., rewind(-10) for 10 seconds back)
- rewind(x) - when user says fast forward, skip ahead, go forward (x = POSITIVE seconds, e.g., rewind(10) for 10 seconds forward)
- restart_song() - when user says restart, start over, from the beginning
- select_song("song_name") - when user says play [song name], play song [name], switch to [song]
- set_playback_speed(x) - when user says speed up, slow down, faster, slower (x = speed factor like 1.5, 2.0, 0.5)
- no_understand() - when command is unclear or unrelated to music playback

Rules:
1. Return ONLY the function call, nothing else
2. For BACKWARD: rewind(-10) means go back 10 seconds
3. For FORWARD: rewind(10) means skip ahead 10 seconds
4. If amount not specified, use rewind(-10) for backward, rewind(10) for forward
5. For speed: "faster" = 1.5, "slower" = 0.75, "2x" = 2.0, "half speed" = 0.5
6. Extract song names from phrases like "play Shape of You" -> select_song("Shape of You")
7. Be strict - only music control commands allowed

Examples:
User: "play" -> play()
User: "go back 5 seconds" -> rewind(-5)
User: "skip ahead 30 seconds" -> rewind(30)
User: "fast forward" -> rewind(10)
User: "rewind" -> rewind(-10)
User: "play Bohemian Rhapsody" -> select_song("Bohemian Rhapsody")
User: "make it faster" -> set_playback_speed(1.5)
User: "what's the weather" -> no_understand()"""
                },
                {"role": "user", "content": user_message}
            ],
            max_tokens=50,
            temperature=0.1  # Low temperature for consistent parsing
        )
        
        command = response.choices[0].message.content.strip()
        print(f"🎵 Command: {command}")

        # --- Handle voice command logic for Arduino/MIDI control ---
        import re

        # PLAY
        if command == "play()":
            if current_song_path:
                mid.play_midi(current_song_path, start_time=current_start_time, playback_speed=current_playback_speed, port="COM5")
                is_playing = True
            else:
                default_midi = os.path.join(os.path.dirname(__file__), '..', 'other_folder', 'ode-to-joy.mid')
                current_song_path = default_midi
                mid.play_midi(current_song_path, start_time=0, playback_speed=1.0, port="COM5")
                is_playing = True

        # PAUSE/STOP
        elif command == "pause()":
            from midi_stream_to_arduino import _stop_flag, _current_thread, _lock
            with _lock:
                if _current_thread and _current_thread.is_alive():
                    print("🛑 Pause requested from voice command.")
                    mid._stop_flag = True
                    _current_thread.join(timeout=1.0)
                    is_playing = False

        # REWIND(x) (can be negative or positive)
        elif command.startswith("rewind("):
            match = re.match(r"rewind\(([-\d]+)\)", command)
            if match:
                seconds = int(match.group(1))
                if current_song_path:
                    if not is_playing:
                        current_start_time = max(0, current_start_time + seconds)
                    else:
                        from midi_stream_to_arduino import _stop_flag, _current_thread, _lock
                        with _lock:
                            if _current_thread and _current_thread.is_alive():
                                mid._stop_flag = True
                                _current_thread.join(timeout=1.0)
                        current_start_time = max(0, current_start_time + seconds)
                        mid.play_midi(current_song_path, start_time=current_start_time, playback_speed=current_playback_speed, port="COM5")
                        is_playing = True

        # RESTART SONG
        elif command == "restart_song()":
            if current_song_path:
                from midi_stream_to_arduino import _stop_flag, _current_thread, _lock
                with _lock:
                    if _current_thread and _current_thread.is_alive():
                        mid._stop_flag = True
                        _current_thread.join(timeout=1.0)
                current_start_time = 0
                mid.play_midi(current_song_path, start_time=0, playback_speed=current_playback_speed, port="COM5")
                is_playing = True

        # SELECT SONG
        elif command.startswith('select_song('):
            match = re.search(r'select_song\(["\'](.+?)["\']\)', command)
            if match:
                song_query = match.group(1)
                print(f"🔍 Searching for song: {song_query}")
                results = search_song(song_query, top_n=3)
                if results:
                    score, filename, full_path = results[0]
                    print(f"✅ Found: {filename} (match: {score:.0%})")
                    current_song_path = full_path
                    current_start_time = 0
                    mid.play_midi(current_song_path, start_time=0, playback_speed=current_playback_speed, port="COM5")
                    is_playing = True

                    # Create response with search results
                    search_info = f"Found: {filename} ({score:.0%} match)"
                    if len(results) > 1 and results[1][0] > 0.5:
                        search_info += f"\nAlternatives: {results[1][1]}"
                    return jsonify({
                        'response': command,
                        'command': command,
                        'status': 'success',
                        'search_result': {
                            'found': True,
                            'filename': filename,
                            'full_path': full_path,
                            'score': score,
                            'message': search_info
                        }
                    })
                else:
                    print(f"❌ Song not found: {song_query}")
                    available_songs = list_all_songs()[:5]
                    return jsonify({
                        'response': command,
                        'command': 'no_understand()',
                        'status': 'success',
                        'search_result': {
                            'found': False,
                            'query': song_query,
                            'message': f"Song '{song_query}' not found",
                            'available_songs': available_songs
                        }
                    })

        # SET PLAYBACK SPEED
        elif command.startswith("set_playback_speed("):
            match = re.match(r"set_playback_speed\(([\d.]+)\)", command)
            if match:
                speed = float(match.group(1))
                current_playback_speed = speed
                if current_song_path and is_playing:
                    from midi_stream_to_arduino import _stop_flag, _current_thread, _lock
                    with _lock:
                        if _current_thread and _current_thread.is_alive():
                            mid._stop_flag = True
                            _current_thread.join(timeout=1.0)
                    mid.play_midi(current_song_path, start_time=current_start_time, playback_speed=current_playback_speed, port="COM5")

        return jsonify({
            'response': command,
            'command': command,
            'status': 'success'
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'response': 'no_understand()',
            'command': 'no_understand()',
            'status': 'error'
        }), 500

@app.route('/')
def home():
    play()
    return """
    <h1>🎙️ AI Voice Assistant Server</h1>
    <p>Server is running! Open index.html in your browser to use the assistant.</p>
    """

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting AI Voice Assistant Web Server...")
    print("=" * 60)
    print("📱 Open index.html in Chrome to use the assistant")
    print("🌐 Server running at: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
