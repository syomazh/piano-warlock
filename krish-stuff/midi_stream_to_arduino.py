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

def get_current_midi_timestamp(real_start_time, start_time, playback_speed):
    """
    Compute the current MIDI timestamp (in seconds) relative to the file,
    based on real-world time and playback speed.

    Args:
        real_start_time (float): time.time() value when playback started
        start_time (float): starting offset in the MIDI file (seconds)
        playback_speed (float): playback speed multiplier

    Returns:
        float: current MIDI timestamp (seconds) relative to MIDI file
    """
    elapsed_real = time.time() - real_start_time
    return start_time + (elapsed_real / playback_speed)




def play_midi(midi_file, start_time, playback_speed, port="COM3", baud=115200):
    print("Opening MIDI:", midi_file)
    mid = mido.MidiFile(midi_file)

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
    abs_time = 0.0
    pending_notes = dict()  # note -> list of (start_time_seconds)

    # Use mido to iterate with real times:
    time_acc = 0.0
    for msg in mid:  # mido yields messages with .time in seconds when iterated this way
        time_acc += msg.time  # msg.time is seconds (mido converts ticks->seconds with tempo)
        if msg.type == 'note_on' and msg.velocity > 0:
            if msg.note not in pending_notes:
                pending_notes[msg.note] = []
            pending_notes[msg.note].append(time_acc)
        elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in pending_notes and len(pending_notes[msg.note]) > 0:
                start = pending_notes[msg.note].pop(0)
                duration_s = time_acc - start
                events.append((start, msg.note, int(round(duration_s * 1000.0))))
            else:
                pass

    events.sort(key=lambda e: e[0])

    # Adjust events to start from the specified start_time
    events = [(ev_time - start_time, note, dur_ms) for ev_time, note, dur_ms in events if ev_time >= start_time]
    if not events:
        print("No events to play from the specified start time.")
        ser.close()
        return

    print("Prepared", len(events), "events. Streaming will start in 2 seconds...")
    time.sleep(2.0)

    start_time = time.time()
    sent = 0

    for ev in events:
        ev_time, note, dur_ms = ev
        while True:
            now = time.time() - start_time
            to_sleep = ev_time - now
            if to_sleep <= 0:
                break
            if to_sleep > 0.02:
                time.sleep(0.01)
            else:
                time.sleep(to_sleep)
        line = f"E,{note},{dur_ms}\n"

        if note < 60 or note > 71:
            print(f"Note {note} is outside the mapping range (60-71). No LED will light.")
        print(f"Sending {line.strip()} at t={time.time() - start_time:.3f}")
        ser.write(line.encode('ascii'))
        sent += 1

    print("All events streamed:", sent)
    ser.flush()
    ser.close()

# Main execution
if __name__ == "__main__":
    midi_file = sys.argv[1]
    port = sys.argv[2]
    baud = int(sys.argv[3])

    # Example parameters: starting at 0 seconds, playback speed 1.0x
    play_midi(midi_file, start_time=0, playback_speed=1.0)