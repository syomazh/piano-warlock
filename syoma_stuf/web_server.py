from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for web requests

# Initialize OpenAI client
client = OpenAI()

@app.route('/chat', methods=['POST'])
def chat():
    """Parse voice commands and return function calls"""
    try:
        data = request.json
        user_message = data.get('text', '').lower()
        
        print(f"📝 User said: {user_message}")
        
        # Use GPT to parse the command into function calls
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": """You are a voice command parser for a music player. Convert user commands into ONE of these function calls:

- play() - when user says play, start, resume, go, continue
- pause() - when user says pause, stop, halt, wait
- rewind(x) - when user says go back, rewind, back up, reverse (x = NEGATIVE seconds, e.g., rewind(-10) for 10 seconds back)
- rewind(x) - when user says fast forward, skip ahead, go forward (x = POSITIVE seconds, e.g., rewind(10) for 10 seconds forward)
- restart_song() - when user says restart, start over, from the beginning
- select_song("song_name") - when user says play [song name], play song [name], switch to [song]
- set_playback_speed(x) - when user says speed up, slow down, faster, slower (x = speed factor like 1.5, 2.0, 0.5)
- no_understand() - when command is unclear or unrelated to music playback

Rules:
1. Return ONLY the function call, nothing else
2. For BACKWARD: rewind(-10) means go back 10 seconds
3. For FORWARD: rewind(10) means skip ahead 10 seconds
4. If amount not specified, use rewind(-10) for backward, rewind(10) for forward
5. For speed: "faster" = 1.5, "slower" = 0.75, "2x" = 2.0, "half speed" = 0.5
6. Extract song names from phrases like "play Shape of You" -> select_song("Shape of You")
7. Be strict - only music control commands allowed

Examples:
User: "play" -> play()
User: "go back 5 seconds" -> rewind(-5)
User: "skip ahead 30 seconds" -> rewind(30)
User: "fast forward" -> rewind(10)
User: "rewind" -> rewind(-10)
User: "play Bohemian Rhapsody" -> select_song("Bohemian Rhapsody")
User: "make it faster" -> set_playback_speed(1.5)
User: "what's the weather" -> no_understand()"""
                },
                {"role": "user", "content": user_message}
            ],
            max_tokens=50,
            temperature=0.1  # Low temperature for consistent parsing
        )
        
        command = response.choices[0].message.content.strip()
        print(f"🎵 Command: {command}")
        
        return jsonify({
            'response': command,
            'command': command,
            'status': 'success'
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'response': 'no_understand()',
            'command': 'no_understand()',
            'status': 'error'
        }), 500

@app.route('/')
def home():
    return """
    <h1>🎙️ AI Voice Assistant Server</h1>
    <p>Server is running! Open index.html in your browser to use the assistant.</p>
    """

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting AI Voice Assistant Web Server...")
    print("=" * 60)
    print("📱 Open index.html in Chrome to use the assistant")
    print("🌐 Server running at: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
