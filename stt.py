import os
from fastapi import APIRouter, UploadFile, File, Form
from groq import Groq

router = APIRouter()

LANGUAGE_MAP = {
    "en": "en",
    "hi": "hi",
    "mr": "mr",
    "ta": "ta",
    "te": "te",
    "pa": "pa",
    "haryanvi": "hi" # Fallback to Hindi for Haryanvi
}

def stt(audio_bytes, language="en"):
  client = Groq()
  whisper_lang = LANGUAGE_MAP.get(language, "en")
  transcription = client.audio.transcriptions.create(
      file=("audio.webm", audio_bytes),
      model="whisper-large-v3",
      temperature=0,
      language=whisper_lang,
      response_format="verbose_json",
    )
  return transcription.text

@router.post("/stt")
async def process_audio(
    audio_file: UploadFile = File(...),
    language: str = Form("en")
):
    audio_bytes = await audio_file.read()
    transcribed_text = stt(audio_bytes, language)
    return {"text": transcribed_text}