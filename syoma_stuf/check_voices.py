import pyttsx3

# Initialize TTS engine
engine = pyttsx3.init()

# Get all available voices
voices = engine.getProperty('voices')

print("=" * 60)
print("Available Voices on Your System:")
print("=" * 60)

for i, voice in enumerate(voices):
    print(f"\n{i+1}. {voice.name}")
    print(f"   ID: {voice.id}")
    print(f"   Languages: {voice.languages}")
    
    # Highlight if it might be Indian
    if any(keyword in voice.name.lower() for keyword in ['indian', 'hindi', 'india', 'ravi', 'heera']):
        print("   🇮🇳 *** INDIAN VOICE DETECTED! ***")

print("\n" + "=" * 60)
print("\nTo install more voices (including Indian accent):")
print("1. Windows: Settings > Time & Language > Speech")
print("2. Add 'English (India)' language pack")
print("3. This will add Indian English voices!")
print("=" * 60)
