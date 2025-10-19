import time
import midi_stream_to_arduino as mid

# 1. Monkey-patch serial.Serial to prevent real COM usage
class DummySerial:
    def __init__(self, *args, **kwargs):
        print(f"[DummySerial] Opening {args} {kwargs}")
    def write(self, data):
        print("[DummySerial] Writing:", data.strip())
    def flush(self): pass
    def close(self): print("[DummySerial] Closed")

mid.serial.Serial = DummySerial  # override for testing

# 2. Use a short, simple MIDI file — or create a dummy one
midi_file = "test.mid"

# 3. Start playback
print("▶️ Starting first playback")
mid.play_midi(midi_file=r"C:\Users\krish\Documents\Repos\piano-warlock\other_folder\ode-to-joy.mid", start_time=0, playback_speed=1)

# Wait 2 seconds, then start a new one (should stop the old one)
time.sleep(2)
print("\n🔁 Starting second playback (should interrupt first)")
mid.play_midi(midi_file=r"C:\Users\krish\Documents\Repos\piano-warlock\other_folder\ode-to-joy.mid", start_time=2, playback_speed=1)

# Wait 2 more seconds, then start a third one
time.sleep(2)
print("\n⏩ Starting third playback (should interrupt second)")
mid.play_midi(midi_file=r"C:\Users\krish\Documents\Repos\piano-warlock\other_folder\ode-to-joy.mid", start_time=4, playback_speed=1)

# Wait for threads to finish
time.sleep(6)
print("\n✅ Test finished")
