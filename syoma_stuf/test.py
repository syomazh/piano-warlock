from openai import OpenAI
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
from dotenv import load_dotenv
import pyttsx3

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI()

# Initialize free TTS engine
tts_engine = pyttsx3.init()

def record_audio(duration=5, sample_rate=16000):
    """Record audio from microphone"""
    print(f"🎤 Recording for {duration} seconds... Speak now!")
    audio = sd.rec(int(duration * sample_rate), 
                   samplerate=sample_rate, 
                   channels=1, 
                   dtype='float32')
    sd.wait()  # Wait until recording is finished
    print("✅ Recording finished!")
    return audio, sample_rate

def save_audio(audio, sample_rate, filename="audio.wav"):
    """Save audio to WAV file"""
    sf.write(filename, audio, sample_rate)
    return filename

def transcribe_audio(filename):
    """Transcribe audio using OpenAI Whisper"""
    print("🔄 Transcribing audio...")
    with open(filename, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    print(f"📝 You said: {transcript.text}")
    return transcript.text

def get_ai_response(text):
    """Get AI response using GPT"""
    print("🤖 Getting AI response...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": text}]
    )
    reply = response.choices[0].message.content
    print(f"💬 AI says: {reply}")
    return reply

def text_to_speech_free(text):
    """Convert text to speech using FREE pyttsx3 (works offline!)"""
    print("🔊 Converting to speech (FREE)...")
    
    c    # Use default US English voice (no Indian accent)
    voices = tts_engine.getProperty('voices')
    
    # Set to first available voice (usually Microsoft David/Zira)
    if voices:
        tts_engine.setProperty('voice', voices[0].id)
        print(f"🔊 Using voice: {voices[0].name}")
    
    # Set speech rate (adjust for preference)
    tts_engine.setProperty('rate', 150)  # Speed (default is ~200)
    
    # Speak the text
    tts_engine.say(text)
    tts_engine.runAndWait()
    
def text_to_speech(text, output_file="response.mp3"):
    """Convert text to speech"""
    print("🔊 Converting to speech...")
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=text
    )
    response.stream_to_file(output_file)
    return output_file

def play_audio(filename):
    """Play audio file"""
    print("▶️  Playing response...")
    data, sample_rate = sf.read(filename)
    sd.play(data, sample_rate)
    sd.wait()
    print("✅ Done!")

def main():
    """Main voice assistant loop"""
    print("🎙️  AI Voice Assistant")
    print("=" * 50)
    
    try:
        # 1. Record audio from microphone
        audio, sample_rate = record_audio(duration=5)
        
        # 2. Save audio to file
        audio_file = save_audio(audio, sample_rate)
        
        # 3. Transcribe with Whisper
        transcript = transcribe_audio(audio_file)
        
        # 4. Get AI response
        response_text = get_ai_response(transcript)
        
        # 5. Convert response to speech (FREE VERSION)
        text_to_speech_free(response_text)
        
        # Clean up files
        if os.path.exists(audio_file):
            os.remove(audio_file)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()