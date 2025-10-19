import midi_stream_to_arduino as mid


mid.play_midi(
    midi_file=r"C:\Users\krish\Documents\Repos\piano-warlock\other_folder\ode-to-joy.mid",
    start_time=0.0,
    playback_speed=1,
    port="COM3",
    baud=115200
)

