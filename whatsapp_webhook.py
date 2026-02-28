import json
import os
import httpx
from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse

from data_input import chatbot, ChatRequest
from stt import stt

router = APIRouter()

# In-memory session tracking for WhatsApp numbers
# Format: { "+1234567890": {"current_state": "start", "answers": {}, "language": "english"} }
sessions = {}

@router.post("/whatsapp")
async def whatsapp_webhook(
  request: Request,
  Body: str = Form(""),
  From: str = Form(...),
  MediaUrl0: str | None = Form(None),
  MediaContentType0: str | None = Form(None),
):
    print(f"Received WhatsApp from {From}: {Body}")
    body_text = Body.strip()
    
    current_session = sessions.get(From, {})
    session_lang = current_session.get("language", "english")

    if MediaUrl0 and MediaContentType0 and MediaContentType0.startswith("audio/"):
        print(f"Downloading Audio Media from: {MediaUrl0}")
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_auth = os.getenv("TWILIO_AUTH_TOKEN")
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            media_resp = await client.get(MediaUrl0, auth=(twilio_sid, twilio_auth))
            if media_resp.status_code == 200:
                print("Audio downloaded, transcribing via Whisper...")
                try:
                    # Pass the audio bytes and the user's current session language
                    transcription = stt(media_resp.content, session_lang)
                    body_text = transcription
                    print(f"Transcribed Text: {body_text}")
                except Exception as e:
                    print(f"STT Transcription failed: {e}")
                    twiml_resp = MessagingResponse()
                    twiml_resp.message("Sorry, I couldn't understand that audio message. Please try typing instead. / क्षमा करें, मैं उस ऑडियो संदेश को समझ नहीं पाया। कृपया इसके बजाय टाइप करने का प्रयास करें।")
                    return Response(content=str(twiml_resp), media_type="application/xml")
            else:
                print(f"Failed to download Twilio audio media. HTTP Status: {media_resp.status_code}, Body: {media_resp.text}")
    
    LANGUAGE_OPTIONS = {
        "0": "english",
        "1": "hindi",
        "2": "marathi",
        "3": "tamil",
        "4": "telugu"
    }
    
    LANGUAGE_PROMPT = (
        "Welcome to the Farmer Assistant Chatbot! Please select your language:\n"
        "किसान सहायक चैटबॉट में आपका स्वागत है! कृपया अपनी भाषा चुनें:\n"
        "शेतकरी सहाय्यक चॅटबॉटमध्ये आपले स्वागत आहे! कृपया तुमची भाषा निवडा:\n\n"
        "0 - English\n"
        "1 - हिन्दी (Hindi)\n"
        "2 - मराठी (Marathi)\n"
        "3 - தமிழ் (Tamil)\n"
        "4 - తెలుగు (Telugu)"
    )

    # Initialize session for new numbers or reset
    if From not in sessions or body_text.lower() in ["reset", "restart", "hi", "hello"]:
        sessions[From] = {
            "current_state": "language_selection",
            "answers": {},
            "language": "english" # Default
        }
        twiml_resp = MessagingResponse()
        twiml_resp.message(LANGUAGE_PROMPT)
        return Response(content=str(twiml_resp), media_type="application/xml")
        
    session = sessions[From]
    
    # Track their input preference
    if MediaUrl0 and MediaContentType0 and MediaContentType0.startswith("audio/"):
        session["wants_audio"] = True
    else:
        session["wants_audio"] = False
    
    # Language selection handling
    if session["current_state"] == "language_selection":
        selected_num = body_text.strip()
        if selected_num in LANGUAGE_OPTIONS:
            session["language"] = LANGUAGE_OPTIONS[selected_num]
            session["current_state"] = "start"
            body_text = ""  # Clear so the chatbot just sends the first question
        else:
            twiml_resp = MessagingResponse()
            twiml_resp.message("Invalid selection / अमान्य विकल्प / चुकीची निवड.\n\n" + LANGUAGE_PROMPT)
            return Response(content=str(twiml_resp), media_type="application/xml")
            
    # Build the request identical to what the frontend sends
    req = ChatRequest(
        current_state=session["current_state"],
        user_answer=body_text,
        language=session["language"],
        answers=session.get("answers", {})
    )
    
    # Trigger the existing LLM flow logic
    res = chatbot(req)
    
    # Build Twilio TwiML response
    twiml_resp = MessagingResponse()
    
    if "error" in res:
        twiml_resp.message(f"Error: {res['error']}")
        return Response(content=str(twiml_resp), media_type="application/xml")
        
    # Update saved state
    session["current_state"] = res["next_state"]
    session["answers"] = res.get("answers", {})
    
    reply_text = res["question"]
    
    # Check if we reached the end
    if res["next_state"] == "end" and "rag_response" in res:
        try:
            clean_json = res["rag_response"].strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            elif clean_json.startswith("```"):
                clean_json = clean_json[3:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()
            
            rag_data = json.loads(clean_json)
            labels = res.get("labels", {"key_features": "Key Features", "documents": "Documents Required"})
            
            schemes_text = ""
            if rag_data.get("eligible_schemes") and len(rag_data["eligible_schemes"]) > 0:
                for s in rag_data["eligible_schemes"]:
                    schemes_text += f"\n\n🟢 *{s['scheme']}*\n"
                    schemes_text += f"_{s['reason']}_\n"
                    if s.get("key_features"):
                        schemes_text += f"➔ *{labels['key_features']}:* {s['key_features']}\n"
                    if s.get("documents"):
                        schemes_text += f"➔ *{labels['documents']}:* {s['documents']}\n"
            else:
                schemes_text = "\n\nBased on your answers, we couldn't find specific schemes, or further verification is required."
                
            reply_text += schemes_text
            
            # Reset state for next time
            del sessions[From]
            
        except Exception as e:
            print("Failed to parse rag:", e)
            reply_text += "\n\n(Error loading full scheme details)"
            
    # Send the final formatted message back to WhatsApp
    msg = twiml_resp.message(reply_text)
    
    if session.get("wants_audio"):
        import re
        import textwrap
        try:
            from tts import generate_tts
            
            # If we are at the "end" state, we want to read ONLY the scheme names (skipping the long documents array).
            # Otherwise, for normal conversation flow, we read `reply_text` directly (without markdown).
            if res.get("next_state") == "end" and "rag_data" in locals() and rag_data.get("eligible_schemes"):
                intro_map = {
                    "english": "Here are the schemes you are eligible for: ",
                    "hindi": "यहाँ वे योजनाएँ हैं जिनके लिए आप पात्र हैं: ",
                    "marathi": "येथे त्या योजना आहेत ज्यासाठी आपण पात्र आहात: ",
                    "tamil": "நீங்கள் தகுதியுடைய திட்டங்கள் இவை: ",
                    "telugu": "మీరు అర్హత పొందిన పథకాలు ఇవి: "
                }
                lang = session.get("language", "english")
                tts_text = intro_map.get(lang, intro_map["english"])
                for s in rag_data["eligible_schemes"]:
                    tts_text += f"{s['scheme']}. "
            else:
                # Normal intermediate questions or fallback (strip markdown emojis)
                tts_text = re.sub(r'[*_]', '', reply_text)
                tts_text = re.sub(r'[🟢➔✅]', '', tts_text)
                
            tts_text = tts_text.strip()
            
            # Truncate text prior to TTS synthesis to prevent hitting Free Tier API length limits.
            if len(tts_text) > 800:
                tts_text = tts_text[:800] + "... Please see the text message below."
                
            filename = generate_tts(tts_text.strip(), session.get("language", "english"))
            host = request.headers.get("host")
            scheme = request.headers.get("x-forwarded-proto", "https")
            audio_url = f"{scheme}://{host}/static/{filename}"
            msg.media(audio_url)
        except Exception as e:
            print(f"TTS generation failed: {e}")
            
    return Response(content=str(twiml_resp), media_type="application/xml")
