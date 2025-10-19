"""
Example utility module for MIDI playback control.
"""


def play(midi_file, timestamp=0.0, playback_speed=1.0):
    """
    Example play function that prints the playback parameters.
    
    Parameters:
    -----------
    midi_file : str
        Path to the MIDI file to be played.
        
    timestamp : float, optional
        Timestamp at which to start playing, normalized from 0.0 to 1.0.
        0.0 = beginning, 1.0 = end of the file.
        Default is 0.0 (start from beginning).
        
    playback_speed : float, optional
        Speed at which to play the file.
        1.0 = normal speed
        0.5 = half speed
        2.0 = double speed
        0.0 = paused
        Default is 1.0.
    """
    print("\n")
    print("*" * 60)
    print("*" * 60)
    print("**                                                        **")
    print("**     WARNING: PLACEHOLDER UTILITY IS BEING USED!       **")
    print("**     This is NOT the real implementation!              **")
    print("**                                                        **")
    print("*" * 60)
    print("*" * 60)
    print()
    
    print("=" * 50)
    print("MIDI Playback Request:")
    print(f"  MIDI File: {midi_file}")
    print(f"  Timestamp: {timestamp} ({timestamp * 100:.1f}%)")
    print(f"  Playback Speed: {playback_speed}x")
    
    if playback_speed == 0.0:
        print("  Status: PAUSED")
    elif playback_speed < 1.0:
        print("  Status: Playing SLOWER than normal")
    elif playback_speed > 1.0:
        print("  Status: Playing FASTER than normal")
    else:
        print("  Status: Playing at NORMAL speed")
    print("=" * 50)


def get_current_timestamp():
    """
    Returns the current playback timestamp.
    
    Returns:
    --------
    float
        Current timestamp normalized from 0.0 to 1.0.
        0.0 = beginning, 1.0 = end of the file.
    """
    # This is a placeholder - in a real implementation,
    # this would track the actual playback position
    current_timestamp = 0.42  # Example value
    
    print(f"Current playback timestamp: {current_timestamp} ({current_timestamp * 100:.1f}%)")
    return current_timestamp


# Example usage
if __name__ == "__main__":
    # Example 1: Play from the beginning at normal speed
    play("midi_folder/mond_2.mid", timestamp=0.0, playback_speed=1.0)
    
    # Example 2: Play from 50% through the file at 1.5x speed
    play("midi_folder/mond_2.mid", timestamp=0.5, playback_speed=1.5)
    
    # Example 3: Play with speed 0 (paused state)
    play("midi_folder/beethoven_opus10_1.mid", timestamp=0.25, playback_speed=0.0)
    
    # Example 4: Play from 75% at half speed
    play("midi_folder/waldstein_2.mid", timestamp=0.75, playback_speed=0.5)
    
    # Example 5: Get current timestamp
    print("\n")
    current_pos = get_current_timestamp()
