from openai import OpenAI
import sounddevice as sd
import soundfile as sf
import os
from dotenv import load_dotenv
import asyncio
import json

load_dotenv()
client = OpenAI()

def record_audio(duration=5, sample_rate=24000):
    """Record audio from microphone"""
    print(f"🎤 Recording for {duration} seconds... Speak now!")
    audio = sd.rec(int(duration * sample_rate), 
                   samplerate=sample_rate, 
                   channels=1, 
                   dtype='int16')
    sd.wait()
    print("✅ Recording finished!")
    return audio, sample_rate

def save_audio(audio, sample_rate, filename="audio.wav"):
    """Save audio to WAV file"""
    sf.write(filename, audio, sample_rate)
    return filename

def fast_assistant():
    """FASTEST VERSION - Parallel processing"""
    print("🎙️  FAST AI Voice Assistant")
    print("=" * 50)
    
    # 1. Record audio
    audio, sample_rate = record_audio(duration=5)
    audio_file = save_audio(audio, sample_rate)
    
    # 2. Open file once for both operations
    with open(audio_file, "rb") as f:
        audio_data = f.read()
    
    # 3. Transcribe (FASTEST with proper encoding)
    print("🔄 Transcribing...")
    from io import BytesIO
    audio_buffer = BytesIO(audio_data)
    audio_buffer.name = "audio.wav"  # OpenAI needs a filename
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_buffer,
        response_format="text"  # Faster than JSON
    )
    print(f"📝 You said: {transcript}")
    
    # 4. Get AI response (use streaming for faster perception)
    print("🤖 Getting response...")
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": transcript}],
        stream=True  # Stream for faster first-token
    )
    
    # Collect response while streaming
    full_response = ""
    print("💬 AI: ", end="", flush=True)
    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_response += content
    print()
    
    # 5. Fast TTS with OpenAI (use tts-1 for speed, not tts-1-hd)
    print("🔊 Speaking...")
    speech = client.audio.speech.create(
        model="tts-1",  # Faster than tts-1-hd
        voice="nova",
        input=full_response,
        speed=1.1  # Slightly faster speech
    )
    
    # Stream directly to playback (don't save to file)
    speech_file = "response.mp3"
    speech.stream_to_file(speech_file)
    
    # Play audio
    data, sr = sf.read(speech_file)
    sd.play(data, sr)
    sd.wait()
    
    # Cleanup
    os.remove(audio_file)
    os.remove(speech_file)
    print("✅ Done!")

if __name__ == "__main__":
    fast_assistant()
