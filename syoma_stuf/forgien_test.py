import midi_stream_to_arduino as mid

import os
default_midi_path = os.path.join(os.path.dirname(__file__), '..', 'other_folder', 'ode-to-joy.mid')
midi_file = default_midi_path
start_time = 0.0
playback_speed = 1.0
port = "COM5"
baud =115200

mid.play_midi(midi_file, start_time=start_time, playback_speed=playback_speed, port=port, baud=baud)
wait_time = 10  # seconds
print(f"Waiting {wait_time} seconds for playback...")
import time
time.sleep(wait_time)
print("Test complete.")
