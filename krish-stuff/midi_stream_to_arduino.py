#!/usr/bin/env python3
"""
Stream MIDI events to Arduino over serial in real-time.
Usage:
    python midi_stream_to_arduino.py song.mid COM3 115200
 (on Linux/Mac COM port is like /dev/ttyACM0 or /dev/ttyUSB0)
"""

import sys
import time
import mido
import serial

if len(sys.argv) < 4:
    print("Usage: python midi_stream_to_arduino.py input.mid SERIAL_PORT BAUD")
    sys.exit(1)

mid_path = sys.argv[1]
port = sys.argv[2]
baud = int(sys.argv[3])

# Map midi note numbers to Arduino LED channels (change to your mapping)
NOTE_TO_LED = {
    60: 2,  # note -> Arduino pin (for reference only in PC; pin numbers for reference)
    61: 3,
    62: 4,
    63: 5,
    64: 6,
    65: 7,
    66: 8,
    67: 9,
    68: 10,
    69: 11,
    70: 12,
    71: 13
}
# We'll only send note and duration; Arduino maps note->pin locally.
# You can adjust NOTE_TO_LED if you want to check mapping or filter notes on PC.

print("Opening MIDI:", mid_path)
mid = mido.MidiFile(mid_path)

print("Opening serial port", port, "@", baud)
ser = serial.Serial(port, baud, timeout=0.1)
time.sleep(2.0)  # wait for Arduino reset if needed

# Convert SMF ticks -> absolute times in seconds, respecting tempo changes
events = []  # list of (abs_time_seconds, note, duration_ms)
# We'll gather all note_on events with velocity>0 and compute duration by finding the matching note_off
ticks_per_beat = mid.ticks_per_beat

# Create per-track absolute ticks and linear list of messages with absolute ticks and track index
messages = []
for i, track in enumerate(mid.tracks):
    abs_ticks = 0
    for msg in track:
        abs_ticks += msg.time
        messages.append((abs_ticks, msg))

# Sort by abs_ticks
messages.sort(key=lambda x: x[0])

# Walk messages building note-on events and tracking tempo changes
current_tempo = 500000  # default microseconds per beat
# We need to convert each message's tick to seconds using mido.tick2second with the tempo in effect at that tick.
# To do this properly we walk original tracks in time order and update tempo when encountered.
# Easier approach: iterate the file using mido.MidiFile.tracks and keep per-track positions using MidiFile.play()
# But mido provides MidiFile.play() which yields messages in real time given tempo — we'll instead use MidiFile to create times.

abs_time = 0.0
pending_notes = dict()  # note -> list of (start_time_seconds)

# Use mido to iterate with real times:
time_acc = 0.0
for msg in mid:  # mido yields messages with .time in seconds when iterated this way
    time_acc += msg.time  # msg.time is seconds (mido converts ticks->seconds with tempo)
    if msg.type == 'note_on' and msg.velocity > 0:
        # find duration by searching ahead in the same iteration (not trivial), so we'll store start time in pending_notes
        if msg.note not in pending_notes:
            pending_notes[msg.note] = []
        pending_notes[msg.note].append(time_acc)
    elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
        if msg.note in pending_notes and len(pending_notes[msg.note]) > 0:
            start = pending_notes[msg.note].pop(0)
            duration_s = time_acc - start
            events.append((start, msg.note, int(round(duration_s * 1000.0))))
        else:
            # unmatched note_off — ignore
            pass
    # tempo messages already applied by mido when iterating

# If you want all note_on events (without matching note_off), treat them as fixed short notes or ignore.
events.sort(key=lambda e: e[0])

print("Prepared", len(events), "events. Streaming will start in 2 seconds...")
time.sleep(2.0)

start_time = time.time()
sent = 0


for ev in events:
    ev_time, note, dur_ms = ev
    # wait until the event time relative to start
    while True:
        now = time.time() - start_time
        to_sleep = ev_time - now
        if to_sleep <= 0:
            break
        # sleep in small chunks to stay responsive
        if to_sleep > 0.02:
            time.sleep(0.01)
        else:
            time.sleep(to_sleep)
    # send event to Arduino
    # Simple ASCII protocol: "E,<note>,<duration>\n"
    line = f"E,{note},{dur_ms}\n"

    if note < 60 or note > 71:
        print(f"Note {note} is outside the mapping range (60-71). No LED will light.")
    print(f"Sending {line.strip()} at t={time.time() - start_time:.3f}")
    ser.write(line.encode('ascii'))
    sent += 1

print("All events streamed:", sent)
ser.flush()
ser.close()