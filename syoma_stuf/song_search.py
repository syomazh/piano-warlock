"""
Song Search Module
Efficiently searches for MIDI files with lenient fuzzy matching
Works well for large datasets
"""
import os
from pathlib import Path
from difflib import SequenceMatcher
import re

# MIDI folder location
MIDI_FOLDER = r"C:\Users\semyo\OneDrive\Documents\GitHub\piano-warlock\assets\midi_datatbase"

def normalize_string(s):
    """
    Normalize a string for comparison by:
    - Converting to lowercase
    - Removing special characters and extra spaces
    - Keeping only alphanumeric characters and spaces
    """
    # Convert to lowercase
    s = s.lower()
    # Remove file extension if present
    s = re.sub(r'\.mid$', '', s)
    # Replace underscores and dashes with spaces
    s = s.replace('_', ' ').replace('-', ' ')
    # Remove special characters but keep spaces
    s = re.sub(r'[^a-z0-9\s]', '', s)
    # Collapse multiple spaces into one
    s = re.sub(r'\s+', ' ', s)
    # Strip leading/trailing spaces
    return s.strip()

def similarity_score(query, filename):
    """
    Calculate similarity score between query and filename
    Uses multiple strategies for best matching
    
    Returns: float between 0 and 1 (1 = perfect match)
    """
    query_norm = normalize_string(query)
    filename_norm = normalize_string(filename)
    
    # Strategy 1: Exact match after normalization
    if query_norm == filename_norm:
        return 1.0
    
    # Strategy 2: Query is contained in filename
    if query_norm in filename_norm:
        return 0.95
    
    # Strategy 3: All words in query appear in filename
    query_words = query_norm.split()
    filename_words = filename_norm.split()
    
    if query_words and all(any(qw in fw for fw in filename_words) for qw in query_words):
        return 0.9
    
    # Strategy 4: Check if filename words start with query words (prefix matching)
    if query_words and all(any(fw.startswith(qw) for fw in filename_words) for qw in query_words):
        return 0.85
    
    # Strategy 5: Sequence matching (SequenceMatcher ratio)
    # This is efficient even for large datasets
    ratio = SequenceMatcher(None, query_norm, filename_norm).ratio()
    
    # Strategy 6: Word-level matching
    # Count how many words match
    if query_words and filename_words:
        matching_words = sum(1 for qw in query_words if any(qw in fw or fw in qw for fw in filename_words))
        word_ratio = matching_words / len(query_words)
        # Combine with sequence ratio
        return max(ratio, word_ratio * 0.8)
    
    return ratio

def search_song(query, top_n=5, min_score=0.3):
    """
    Search for a song in the MIDI folder
    
    Args:
        query: Song name to search for
        top_n: Number of top results to return
        min_score: Minimum similarity score (0-1) to include in results
    
    Returns:
        List of tuples: [(score, filename, full_path), ...]
        Sorted by score (highest first)
    """
    midi_folder = Path(MIDI_FOLDER)
    
    # Check if folder exists
    if not midi_folder.exists():
        print(f"❌ Error: MIDI folder not found: {MIDI_FOLDER}")
        return []
    
    # Get all MIDI files
    midi_files = list(midi_folder.glob("*.mid"))
    
    if not midi_files:
        print(f"❌ No MIDI files found in {MIDI_FOLDER}")
        return []
    
    # Calculate scores for all files
    results = []
    for midi_file in midi_files:
        score = similarity_score(query, midi_file.stem)
        if score >= min_score:
            results.append((score, midi_file.name, str(midi_file)))
    
    # Sort by score (highest first)
    results.sort(reverse=True, key=lambda x: x[0])
    
    # Return top N results
    return results[:top_n]

def find_best_match(query):
    """
    Find the best matching song
    
    Args:
        query: Song name to search for
    
    Returns:
        Full path to the best matching MIDI file, or None if no good match
    """
    results = search_song(query, top_n=1, min_score=0.3)
    
    if results:
        score, filename, full_path = results[0]
        return full_path
    
    return None

def list_all_songs():
    """
    List all available songs in the MIDI folder
    
    Returns:
        List of song names (without .mid extension)
    """
    midi_folder = Path(MIDI_FOLDER)
    
    if not midi_folder.exists():
        return []
    
    midi_files = list(midi_folder.glob("*.mid"))
    return sorted([f.stem for f in midi_files])


# Command-line interface for testing
if __name__ == "__main__":
    print("🔍 Song Search System - Testing\n")
    print("=" * 70)
    
    # List all songs
    print("\n📚 Available songs:")
    songs = list_all_songs()
    for i, song in enumerate(songs, 1):
        print(f"  {i}. {song}")
    
    print("\n" + "=" * 70)
    print("\n🧪 Testing search queries:\n")
    
    # Test various queries
    test_queries = [
        "queen",
        "another one bites",
        "beethoven",
        "ode to joy",
        "mario",
        "mama mia",
        "a teens",
        "dont wanna",
    ]
    
    for query in test_queries:
        print(f"Query: '{query}'")
        results = search_song(query, top_n=3)
        
        if results:
            print(f"  Top matches:")
            for score, filename, full_path in results:
                print(f"    {score:.2f} - {filename}")
        else:
            print(f"  ❌ No matches found")
        print()
    
    print("=" * 70)
    print("\n✅ Search system ready!")
    print("\nUsage examples:")
    print("  from song_search import find_best_match")
    print("  path = find_best_match('queen another one')")
    print("  # Returns: Full path to best matching song")
