import midi_stream_to_arduino as mid

import sys, os
print("Working directory:", os.getcwd())
print("Module path:", mid.__file__)



mid.play_midi(
    midi_file=r"C:\Users\semyo\OneDrive\Documents\GitHub\piano-warlock\other_folder\ode-to-joy.mid",
    start_time=0.0,
    playback_speed=1,
    port="COM5",
    baud=115200
)

