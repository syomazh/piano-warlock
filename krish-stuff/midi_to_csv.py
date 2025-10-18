# midi_to_csv.py
from mido import MidiFile
import sys

if len(sys.argv) < 3:
    print("Usage: python midi_to_csv.py input.mid output.csv")
    sys.exit(1)

mid = MidiFile(sys.argv[1])
# choose tempo: if file has tempo events, mido handles time in seconds if you use tick2second
# We'll accumulate absolute time in milliseconds

tempo = 500000  # default microseconds per quarter note
ticks_per_beat = mid.ticks_per_beat

def ticks_to_ms(ticks, tempo):
    # tempo in microseconds per beat
    # ticks_per_beat from mid
    seconds = mido.tick2second(ticks, ticks_per_beat, tempo)
    return seconds * 1000.0

import mido

events = []  # (absolute_ms, note, velocity, is_note_on, note_length_placeholder)

abs_ticks = 0
for track in mid.tracks:
    abs_ticks = 0
    for msg in track:
        abs_ticks += msg.time
        if msg.type == 'set_tempo':
            tempo = msg.tempo
        if msg.type == 'note_on' and msg.velocity > 0:
            # find matching note_off in the same track after this event to compute duration
            start_ticks = abs_ticks
            # search forward in same track to find note_off or note_on with velocity 0 for this note
            dur_ticks = None
            t_ticks = 0
            for future_msg in track[track.index(msg)+1:]:
                t_ticks += future_msg.time
                if (future_msg.type == 'note_off' and future_msg.note == msg.note) or \
                   (future_msg.type == 'note_on' and future_msg.note == msg.note and future_msg.velocity == 0):
                    dur_ticks = t_ticks
                    break
            if dur_ticks is None:
                dur_ticks = int(ticks_per_beat)  # fallback: 1 beat
            abs_ms = mido.tick2second(start_ticks, ticks_per_beat, tempo) * 1000.0
            dur_ms = mido.tick2second(dur_ticks, ticks_per_beat, tempo) * 1000.0
            events.append((int(round(abs_ms)), msg.note, msg.velocity, int(round(dur_ms))))

# Flatten events (multiple tracks combined)
events.sort(key=lambda e: e[0])

with open(sys.argv[2], 'w') as f:
    for ev in events:
        f.write("{},{},{},{}\n".format(ev[0], ev[1], ev[2], ev[3]))

print(f"Wrote {len(events)} events to {sys.argv[2]}")
