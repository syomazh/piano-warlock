"""
MIDI Piano Player
Takes a MIDI file and plays it using piano sounds with real-time synthesis
Supports polyphony (multiple notes at once)
"""
import mido
import time
import numpy as np
import sounddevice as sd
from pathlib import Path
import threading
from collections import defaultdict

# Piano note frequencies (A4 = 440 Hz)
def note_to_freq(note):
    """Convert MIDI note number to frequency in Hz"""
    return 440.0 * (2.0 ** ((note - 69) / 12.0))

class PolyphonicSynthesizer:
    """Synthesizer that can play multiple notes simultaneously"""
    
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.active_notes = {}  # note -> note info dict
        self.releasing_notes = {}  # notes in release phase
        self.lock = threading.Lock()
        self.master_volume = 0.12
        
    def note_on(self, note, velocity):
        """Start playing a note"""
        with self.lock:
            # Remove from releasing if it was there
            if note in self.releasing_notes:
                del self.releasing_notes[note]
            
            self.active_notes[note] = {
                'phases': [0.0] * 5,  # One phase per harmonic
                'velocity': velocity / 127.0,
                'start_time': time.time(),
                'sample_count': 0
            }
    
    def note_off(self, note):
        """Stop playing a note (move to release phase)"""
        with self.lock:
            if note in self.active_notes:
                # Move to releasing notes instead of deleting
                self.releasing_notes[note] = self.active_notes[note]
                self.releasing_notes[note]['release_start'] = time.time()
                del self.active_notes[note]
    
    def generate_sample(self, num_samples):
        """Generate audio samples for all active notes"""
        output = np.zeros(num_samples, dtype=np.float32)
        
        with self.lock:
            # Process active notes
            for note, info in list(self.active_notes.items()):
                tone = self._generate_note_samples(note, info, num_samples, False)
                output += tone
            
            # Process releasing notes
            for note, info in list(self.releasing_notes.items()):
                tone = self._generate_note_samples(note, info, num_samples, True)
                output += tone
                
                # Remove if release is complete
                release_time = time.time() - info['release_start']
                if release_time > 0.3:  # 300ms release
                    del self.releasing_notes[note]
        
        # Soft limiting to prevent clipping
        output = np.tanh(output)
        
        return output
    
    def _generate_note_samples(self, note, info, num_samples, is_releasing):
        """Generate samples for a single note"""
        freq = note_to_freq(note)
        velocity = info['velocity']
        
        # Generate tone with harmonics
        tone = np.zeros(num_samples, dtype=np.float32)
        harmonics = [1.0, 0.5, 0.25, 0.125, 0.0625]
        
        for i, amp in enumerate(harmonics):
            harmonic_freq = freq * (i + 1)
            
            # Generate continuous phase
            phase_inc = 2 * np.pi * harmonic_freq / self.sample_rate
            phases = info['phases'][i] + phase_inc * np.arange(num_samples)
            
            tone += amp * np.sin(phases)
            
            # Update phase for next buffer, keeping it wrapped
            info['phases'][i] = (phases[-1] + phase_inc) % (2 * np.pi)
        
        # Apply envelope
        envelope = self._get_envelope_samples(info, num_samples, is_releasing)
        tone *= envelope * velocity * self.master_volume
        
        # Update sample count
        info['sample_count'] += num_samples
        
        return tone
    
    def _get_envelope_samples(self, info, num_samples, is_releasing):
        """Generate smooth ADSR envelope samples"""
        envelope = np.ones(num_samples, dtype=np.float32)
        
        attack_samples = int(0.005 * self.sample_rate)  # 5ms attack
        decay_samples = int(0.1 * self.sample_rate)     # 100ms decay
        sustain_level = 0.7
        
        if is_releasing:
            # Release phase
            release_samples = int(0.3 * self.sample_rate)  # 300ms release
            release_time = time.time() - info['release_start']
            release_sample_count = int(release_time * self.sample_rate)
            
            for i in range(num_samples):
                progress = (release_sample_count + i) / release_samples
                if progress < 1.0:
                    envelope[i] = sustain_level * (1.0 - progress)
                else:
                    envelope[i] = 0.0
        else:
            # Attack/Decay/Sustain phase
            start_sample = info['sample_count']
            
            for i in range(num_samples):
                sample_num = start_sample + i
                
                if sample_num < attack_samples:
                    # Attack
                    envelope[i] = sample_num / attack_samples
                elif sample_num < attack_samples + decay_samples:
                    # Decay
                    decay_progress = (sample_num - attack_samples) / decay_samples
                    envelope[i] = 1.0 - decay_progress * (1.0 - sustain_level)
                else:
                    # Sustain
                    envelope[i] = sustain_level
        
        return envelope

def audio_callback(outdata, frames, time_info, status):
    """Callback function for audio stream"""
    if status:
        print(f"Audio status: {status}")
    
    samples = synthesizer.generate_sample(frames)
    outdata[:, 0] = samples

def play_midi(midi_file):
    """
    Play a MIDI file using real-time polyphonic synthesis
    
    Args:
        midi_file: Path to the MIDI file to play
    """
    global synthesizer
    
    # Check if file exists
    if not Path(midi_file).exists():
        print(f"❌ Error: File '{midi_file}' not found!")
        return
    
    print(f"🎹 Loading MIDI file: {midi_file}")
    
    # Load MIDI file
    mid = mido.MidiFile(midi_file)
    
    print(f"Song duration: {mid.length:.2f} seconds")
    print("▶️  Playing MIDI file...")
    print("   Press Ctrl+C to stop playback")
    
    sample_rate = 44100
    synthesizer = PolyphonicSynthesizer(sample_rate)
    
    try:
        # Start audio stream with callback
        with sd.OutputStream(samplerate=sample_rate, channels=1, 
                            callback=audio_callback, blocksize=2048):
            # Play through all MIDI messages
            for msg in mid.play():
                if msg.type == 'note_on' and msg.velocity > 0:
                    synthesizer.note_on(msg.note, msg.velocity)
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    synthesizer.note_off(msg.note)
            
            # Let final notes decay
            time.sleep(0.5)
        
    except KeyboardInterrupt:
        print("\n⏹️  Playback stopped by user")
    except Exception as e:
        print(f"❌ Error during playback: {e}")
        import traceback
        traceback.print_exc()
    
    print("✅ Finished")


def main():
    """Main function to handle command line arguments"""
    # Hardcoded MIDI file path
    midi_file = "syoma_stuf\midi_folder\Beethhoven_-_Beethoven_-_9th_Symphony_(Ode_To_Joy)_[Easy_Piano_Tutorial].mid"
    play_midi(midi_file)


if __name__ == "__main__":
    main()
