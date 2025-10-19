import threading
import time
import mido
import serial
from pathlib import Path

# Global thread control
_current_thread = None
_stop_flag = False
_lock = threading.Lock()

def _play_midi_worker(midi_file, start_time, playback_speed, port, baud):
    global _stop_flag

    try:
        midi_file = Path(midi_file).expanduser().resolve()
        print(f"🎵 Opening MIDI file: {midi_file}")
        mid = mido.MidiFile(midi_file)

        print(f"Opening serial port {port} @ {baud}")
        ser = serial.Serial(port, baud, timeout=0.1)
        time.sleep(2.0)

        events = []
        pending_notes = {}

        time_acc = 0.0
        for msg in mid:
            time_acc += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                pending_notes.setdefault(msg.note, []).append(time_acc)
            elif msg.type in ('note_off',) or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in pending_notes and pending_notes[msg.note]:
                    start = pending_notes[msg.note].pop(0)
                    duration_s = time_acc - start
                    events.append((start, msg.note, int(round((duration_s / playback_speed) * 1000.0))))

        events.sort(key=lambda e: e[0])
        events = [((ev_time - start_time) / playback_speed, note, dur_ms)
                  for ev_time, note, dur_ms in events if ev_time >= start_time]

        if not events:
            print("No events to play from the specified start time.")
            ser.close()
            return

        print(f"Prepared {len(events)} events. Starting in 2 seconds...")
        time.sleep(2.0)

        real_start = time.time()

        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        letter_to_note = {
            'C': 60, 'C#': 61, 'D': 62, 'D#': 63, 'E': 64,
            'F': 65, 'F#': 66, 'G': 67, 'G#': 68, 'A': 69, 'A#': 70, 'B': 71
        }

        sent = 0
        for ev_time, note, dur_ms in events:
            if _stop_flag:
                print("🛑 Playback stopped by new command.")
                break

            # Timing control
            while not _stop_flag:
                now = time.time() - real_start
                to_sleep = ev_time - now
                if to_sleep <= 0:
                    break
                time.sleep(0.01 if to_sleep > 0.02 else to_sleep)

            if _stop_flag:
                print("🛑 Playback interrupted mid-event.")
                break

            pitch_class = note % 12
            note_letter = note_names[pitch_class]
            mapped_note = letter_to_note[note_letter]
            line = f"E,{mapped_note},{dur_ms}\n"

            print(f"Mapping {note} ({note_letter}) → {mapped_note} | "
                  f"event_t={ev_time:.3f}s real_t={time.time() - real_start:.3f}s dur={dur_ms}ms")
            ser.write(line.encode('ascii'))
            sent += 1

        print("✅ Playback complete or interrupted.")
        ser.flush()
        ser.close()

    except Exception as e:
        print(f"[MIDI worker error] {e}")

def play_midi(midi_file, start_time=0, playback_speed=1.0, port="COM3", baud=115200):
    """Launch non-blocking MIDI playback, interrupting any current one."""
    global _current_thread, _stop_flag

    with _lock:
        # Stop any currently playing thread
        if _current_thread and _current_thread.is_alive():
            print("⚠️ Stopping current MIDI playback...")
            _stop_flag = True
            _current_thread.join(timeout=1.0)

        # Reset and start new one
        _stop_flag = False
        _current_thread = threading.Thread(
            target=_play_midi_worker,
            args=(midi_file, start_time, playback_speed, port, baud),
            daemon=True
        )
        _current_thread.start()
        print(f"🎶 Started new MIDI playback for {midi_file}")