from openai import OpenAI
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
from dotenv import load_dotenv
import pyttsx3

load_dotenv()
client = OpenAI()

# Initialize free TTS engine
tts_engine = pyttsx3.init()

def record_audio_smart(silence_threshold=0.01, max_duration=10):
    """Record until silence is detected (MUCH FASTER!)"""
    print("🎤 Speak now! (will stop when you're done)")
    
    sample_rate = 16000
    chunk_duration = 0.1  # 100ms chunks
    chunk_size = int(sample_rate * chunk_duration)
    
    audio_chunks = []
    silent_chunks = 0
    max_silent_chunks = 10  # 1 second of silence
    
    stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32')
    stream.start()
    
    try:
        while len(audio_chunks) < max_duration * 10:
            chunk, _ = stream.read(chunk_size)
            audio_chunks.append(chunk)
            
            # Check if silent
            if np.abs(chunk).mean() < silence_threshold:
                silent_chunks += 1
                if silent_chunks > max_silent_chunks and len(audio_chunks) > 5:
                    print("✅ Detected end of speech!")
                    break
            else:
                silent_chunks = 0
    finally:
        stream.stop()
        stream.close()
    
    audio = np.concatenate(audio_chunks)
    return audio, sample_rate

def ultra_fast_assistant():
    """ULTRA FAST - Voice activation + streaming"""
    print("🎙️  ULTRA FAST AI Voice Assistant")
    print("=" * 50)
    
    # 1. Smart recording (stops when you stop talking)
    audio, sample_rate = record_audio_smart()
    
    # 2. Save and transcribe
    audio_file = "audio.wav"
    sf.write(audio_file, audio, sample_rate)
    
    print("🔄 Transcribing...")
    with open(audio_file, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="text"
        )
    print(f"📝 You: {transcript}")
    
    # 3. Stream GPT response for instant feedback
    print("🤖 AI: ", end="", flush=True)
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Be concise. Keep responses under 50 words."},
            {"role": "user", "content": transcript}
        ],
        stream=True,
        max_tokens=100  # Limit length for speed
    )
    
    full_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_response += content
    print()
    
    # 4. Fast FREE TTS
    print("🔊 Speaking (FREE)...")
    voices = tts_engine.getProperty('voices')
    if voices:
        tts_engine.setProperty('voice', voices[0].id)
    tts_engine.setProperty('rate', 180)  # Faster speech rate
    tts_engine.say(full_response)
    tts_engine.runAndWait()
    
    # Cleanup
    os.remove(audio_file)
    print("✅ Done!\n")

if __name__ == "__main__":
    while True:
        try:
            ultra_fast_assistant()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
