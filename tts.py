import uuid
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
import os

load_dotenv()

# Updated to standard free ElevenLabs voices to bypass the "paid_plan_required" API error.
voice_ids = {
  "english": "JBFqnCBsd6RMkjVDRZzb", # George
  "hindi": "pNInz6obpgDQGcFmaJgB",   # Adam
  "marathi": "21m00Tcm4TlvDq8ikWAM", # Rachel
  "bihari": "EXAVITQu4vr4xnSDxMaL",  # Sarah
  "haryanvi": "ErXwobaYiN019PkySvjV",# Antoni
  "tamil": "VR6AewLTigWG4xSOukaG"    # Arnold
}

client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)

def generate_tts(text: str, language: str = "english") -> str:
    # Use English as default fallback for unknown languages like Telugu
    voice_id = voice_ids.get(language.lower(), voice_ids["english"])
    
    audio_generator = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    
    # Generate unique URL path and save bytes to disk
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join("static", filename)
    with open(filepath, "wb") as f:
        for chunk in audio_generator:
            if chunk:
                f.write(chunk)
                
    return filename