"""
Voice-Controlled Music Player Interface
This shows how to use the voice commands with your music player
"""
from song_search import find_best_match, search_song, list_all_songs
import subprocess
import sys
from pathlib import Path

# Get the Python executable path
PYTHON_EXE = sys.executable
PLAY_MIDI_SCRIPT = Path(__file__).parent / "play_midi.py"

# Current playback state
current_song = None
current_process = None

# These are the functions that will be called based on voice commands
def play():
    """Start or resume playback"""
    print("▶️  Playing...")
    # Add your music player code here
    
def pause():
    """Pause playback"""
    print("⏸️  Paused")
    # Add your music player code here
    
def rewind(seconds):
    """
    Seek by X seconds
    - Negative values = go backwards (rewind)
    - Positive values = go forwards (fast forward)
    """
    if seconds < 0:
        print(f"⏪ Rewinding {abs(seconds)} seconds")
    else:
        print(f"⏩ Fast forwarding {seconds} seconds")
    # Add your music player code here
    # Example: your_player.seek(your_player.position + seconds)
    
def restart_song():
    """Restart current song from beginning"""
    print("🔄 Restarting song")
    # Add your music player code here
    
def select_song(song_name):
    """Select and play a specific song"""
    print(f"🔍 Searching for: {song_name}")
    
    # Search for the song
    results = search_song(song_name, top_n=3)
    
    if not results:
        print(f"❌ No songs found matching '{song_name}'")
        print("\n📚 Available songs:")
        for song in list_all_songs()[:10]:  # Show first 10
            print(f"  - {song}")
        return
    
    # Get best match
    score, filename, full_path = results[0]
    
    print(f"✅ Found: {filename} (match: {score:.0%})")
    
    # If there are other good matches, show them
    if len(results) > 1 and results[1][0] > 0.5:
        print(f"   Other matches:")
        for s, fn, _ in results[1:]:
            print(f"     - {fn} ({s:.0%})")
    
    # Update current song
    global current_song
    current_song = full_path
    
    print(f"🎵 Playing: {filename}")
    # Here you would integrate with your actual player
    # For now, we'll just store the path
    
def set_playback_speed(speed_factor):
    """Set playback speed (1.0 = normal, 2.0 = 2x, 0.5 = half)"""
    print(f"⚡ Setting playback speed to {speed_factor}x")
    # Add your music player code here
    
def no_understand():
    """Called when command is not understood"""
    print("❓ Command not understood")
    # Add your music player code here


# Example: Execute command from voice assistant
def execute_command(command_string):
    """
    Execute a command string returned by the voice assistant
    
    Args:
        command_string: String like "play()" or "rewind(5)" or "select_song('Bohemian Rhapsody')"
    """
    try:
        # Execute the command using eval (in a controlled environment)
        # Make only our music functions available
        safe_functions = {
            'play': play,
            'pause': pause,
            'rewind': rewind,
            'restart_song': restart_song,
            'select_song': select_song,
            'set_playback_speed': set_playback_speed,
            'no_understand': no_understand
        }
        
        # Execute the command
        eval(command_string, {"__builtins__": {}}, safe_functions)
        
    except Exception as e:
        print(f"Error executing command: {e}")
        no_understand()


# Test examples
if __name__ == "__main__":
    print("🎙️ Voice Command Music Player - Testing Commands\n")
    print("=" * 60)
    
    # Simulate commands from the voice assistant
    test_commands = [
        "play()",
        "pause()",
        "rewind(-10)",  # Go back 10 seconds
        "rewind(30)",   # Skip forward 30 seconds
        "restart_song()",
        "select_song('Bohemian Rhapsody')",
        "set_playback_speed(1.5)",
        "no_understand()"
    ]
    
    for cmd in test_commands:
        print(f"\n📝 Command: {cmd}")
        execute_command(cmd)
    
    print("\n" + "=" * 60)
    print("\n✅ Integration ready!")
    print("Connect this to your music player and the web interface.")
