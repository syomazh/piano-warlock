from flask import Flask, render_template, request, jsonify
import midi_stream_to_arduino as mid

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/play', methods=['POST'])
def play():
    data = request.get_json(force=True)
    import os
    default_midi_path = os.path.join(os.path.dirname(__file__), '..', 'other_folder', 'ode-to-joy.mid')
    midi_file = default_midi_path
    start_time = float(data.get("start_time", 0))
    playback_speed = float(data.get("playback_speed", 1))
    port = data.get("port", "COM5")
    baud = int(data.get("baud", 115200))

    mid.play_midi(midi_file, start_time=start_time, playback_speed=playback_speed, port=port, baud=baud)
    return jsonify({"status": "playing", "file": midi_file})

@app.route('/stop', methods=['POST'])
def stop():
    # Simple way to stop current playback without starting new one
    from midi_stream_to_arduino import _stop_flag, _current_thread, _lock
    with _lock:
        if _current_thread and _current_thread.is_alive():
            print("🛑 Stop requested from web interface.")
            mid._stop_flag = True
            _current_thread.join(timeout=1.0)
            return jsonify({"status": "stopped"})
    return jsonify({"status": "no active playback"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)