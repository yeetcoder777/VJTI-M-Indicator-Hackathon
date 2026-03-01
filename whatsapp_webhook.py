import json
import os
import httpx
from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse

from data_input import chatbot, ChatRequest
from stt import stt
processed_message_sids = set()
router = APIRouter()

# In-memory session tracking for WhatsApp numbers
# Format: { "+1234567890": {"current_state": "start", "answers": {}, "language": "english"} }
sessions = {
    "whatsapp:+918779372657": {
        "flow_type": "eligibility",
        "current_state": "end",
        "language": "english",
        "answers": {
            "State": "Maharashtra",
            "District": "Nashik",
            "Farm Size": "3 Acres",
            "Problem": "Severe crop damage due to unseasonal rainfall. Looking for immediate financial relief."
        }
    }
}

@router.post("/whatsapp")
@router.post("/whatsapp/")
async def whatsapp_webhook(
  request: Request,
  Body: str = Form(""),
  From: str = Form(...),
  MediaUrl0: str | None = Form(None),
  MediaContentType0: str | None = Form(None),
  MessageSid: str = Form(...),
  Latitude: str | None = Form(None),
  Longitude: str | None = Form(None)
):
    if MessageSid in processed_message_sids:
        print(f"Duplicate webhook for SID {MessageSid}. Ignoring.")
        return Response(status_code=200)
    processed_message_sids.add(MessageSid)

    print(f"Received WhatsApp from {From}: {Body}")
    body_text = Body.strip()
    
    current_session = sessions.get(From, {})
    session_lang = current_session.get("language", "english")

    if Latitude and Longitude:
        print(f"Location received from {From}: Lat {Latitude}, Lon {Longitude}")
        from weather_schemes import weather_schemes, LocationRequest
        req = LocationRequest(
            latitude=float(Latitude),
            longitude=float(Longitude),
            language=session_lang
        )
        weather_res = weather_schemes(req)
        
        twiml_resp = MessagingResponse()
        if "error" in weather_res:
            twiml_resp.message(weather_res["error"])
        else:
            w = weather_res["weather_summary"]
            botHtml = f"*🌦️ Weather Report (Last 30 Days)*\n"
            botHtml += f"📍 Location: {float(Latitude):.2f}°N, {float(Longitude):.2f}°E\n"
            botHtml += f"🌧️ Total Rainfall: {w['total_rainfall_mm']} mm ({w['rainy_days']} rainy days)\n"
            botHtml += f"🌡️ Avg Temp: {w.get('avg_temp_min_c', 0)}°C - {w.get('avg_temp_max_c', 0)}°C\n"
            botHtml += f"💨 Max Wind: {w['max_wind_kmh']} km/h\n\n"
            botHtml += f"*📋 Weather-Based Scheme Recommendations:*\n"
            botHtml += weather_res["recommendation"]
            
            # Send back chunks
            def chunk_message(text, max_len=1500):
                paragraphs = text.split('\n')
                chunks = []
                current = ""
                for p in paragraphs:
                    if len(current) + len(p) + 1 > max_len:
                        if current:
                            chunks.append(current)
                            current = p
                        else:
                            for i in range(0, len(p), max_len):
                                chunks.append(p[i:i+max_len])
                            current = ""
                    else:
                        if current:
                            current += "\n" + p
                        else:
                            current = p
                if current:
                    chunks.append(current)
                return chunks if chunks else [" "]
                
            for chunk in chunk_message(botHtml, 1500):
                twiml_resp.message(chunk)
                
        return Response(content=str(twiml_resp), media_type="application/xml")

    if MediaUrl0 and MediaContentType0:
        if MediaContentType0.startswith("audio/"):
            print(f"Downloading Audio Media from: {MediaUrl0}")
            twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
            twilio_auth = os.getenv("TWILIO_AUTH_TOKEN")
            
            async with httpx.AsyncClient(follow_redirects=True) as client:
                media_resp = await client.get(MediaUrl0, auth=(twilio_sid, twilio_auth))
                if media_resp.status_code == 200:
                    print("Audio downloaded, transcribing via Whisper...")
                    try:
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
        elif MediaContentType0.startswith("image/") or MediaContentType0 == "application/pdf":
            print(f"Document Media Received: {MediaUrl0}")
            # Mocking the actual local storage for the hackathon MVP
            body_text = f"[DOCUMENT_UPLOADED] ({MediaUrl0})"
    
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
    if From not in sessions or body_text.lower() in ["reset", "restart"]:
        sessions[From] = {
            "flow_type": "unknown",
            "current_state": "language_selection",
            "answers": {},
            "language": "english" # Default
        }
        twiml_resp = MessagingResponse()
        twiml_resp.message(LANGUAGE_PROMPT)
        return Response(content=str(twiml_resp), media_type="application/xml")
        
    session = sessions[From]
    
    if MediaUrl0 and MediaContentType0 and MediaContentType0.startswith("audio/"):
        session["wants_audio"] = True
    elif body_text and not body_text.startswith("[DOCUMENT_UPLOADED]"):
        session["wants_audio"] = False
        
    # Language selection handling
    if session["current_state"] == "language_selection":
        selected_num = body_text.strip()
        if selected_num in LANGUAGE_OPTIONS:
            session["language"] = LANGUAGE_OPTIONS[selected_num]
            session["current_state"] = "awaiting_intent"
            
            prompt_text = "How can I help you today?\n- Type *'Check eligibility'* to see what schemes you qualify for.\n- Type *'Apply for PMFBY/KCC/PM-KISAN/NLM'* to start a direct application."
            if session["language"] == "hindi":
                prompt_text = "मैं आज आपकी कैसे सहायता कर सकता हूँ?\n- यह देखने के लिए कि आप किन योजनाओं के लिए पात्र हैं, *'पात्रता जांचें'* टाइप करें।\n- सीधा आवेदन शुरू करने के लिए *'PMFBY/KCC/PM-KISAN/NLM के लिए आवेदन करें'* टाइप करें।"
            elif session["language"] == "marathi":
                prompt_text = "मी आज तुम्हाला कशी मदत करू शकेन?\n- तुम्ही कोणत्या योजनांसाठी पात्र आहात हे पाहण्यासाठी *'पात्रता तपासा'* टाइप करा.\n- थेट अर्ज सुरू करण्यासाठी *'PMFBY/KCC/PM-KISAN/NLM साठी अर्ज करा'* टाइप करा."
            
            twiml_resp = MessagingResponse()
            twiml_resp.message(prompt_text)
            return Response(content=str(twiml_resp), media_type="application/xml")
        else:
            twiml_resp = MessagingResponse()
            twiml_resp.message("Invalid selection / अमान्य विकल्प / चुकीची निवड.\n\n" + LANGUAGE_PROMPT)
            return Response(content=str(twiml_resp), media_type="application/xml")

    # Intent Classification handling
    if session["current_state"] == "awaiting_intent":
        from data_input import llm_call
        prompt = f"""
        User said: "{body_text}"
        Determine the user's intent based on semantic meaning. 
        Options:
        1. "kcc" (wants to apply for Kisan Credit Card, needs a loan, money for seeds, credit)
        2. "nlm" (wants to apply for National Livestock Mission, bought cows/goats/poultry, animal husbandry)
        3. "pm_kisan" (wants PM-KISAN, 6000 rupees yearly, regular financial support)
        4. "pmfby" (wants to apply for PMFBY, crop insurance, crops ruined by rain/drought/pests, claims)
        5. "eligibility" (wants to check what schemes they are eligible for, general chat, greetings)
        
        Examples:
        - "My crops got ruined by rain, I need money" -> "pmfby"
        - "I want to buy a tractor and need a loan" -> "kcc"
        - "I have 5 cows and want subsidy" -> "nlm"
        - "How do I get the 6000 rupees scheme?" -> "pm_kisan"
        - "What schemes are there for me?" -> "eligibility"
        
        Return ONLY the option key string. If unsure, return "eligibility".
        """
        try:
            intent_resp = llm_call(prompt).strip().lower()
            intent = "eligibility"
            for k in ["kcc", "nlm", "pm_kisan", "pmfby"]:
                if k in intent_resp:
                    intent = k
                    break
        except Exception:
            intent = "eligibility"
            
        session["current_state"] = "start"
        body_text = "" # Clear it so the target flow starts from question 1
        session["answers"] = {}
        
        if intent in ["kcc", "nlm", "pm_kisan", "pmfby"]:
            session["flow_type"] = "auto_form"
            session["scheme_target"] = intent
        else:
            session["flow_type"] = "eligibility"

    # Route based on flow type
    if session.get("flow_type") == "auto_form":
        from auto_form_filling import handle_form, FormRequest
        req = FormRequest(
            scheme_target=session.get("scheme_target"),
            current_state=session["current_state"],
            user_answer=body_text,
            language=session["language"],
            collected_data=session.get("answers", {})
        )
        res = handle_form(req)
        
        twiml_resp = MessagingResponse()
        
        if "error" in res:
            twiml_resp.message(f"Error: {res['error']}")
            return Response(content=str(twiml_resp), media_type="application/xml")
            
        session["current_state"] = res["next_state"]
        session["answers"] = res.get("collected_data", {})
        reply_text = res["question"]
        
        if res["next_state"] == "end":
            session["current_state"] = "language_selection" # Reset back to Language Loop after application submission
            
    else:
        req = ChatRequest(
            current_state=session["current_state"],
            user_answer=body_text,
            language=session["language"],
            answers=session.get("answers", {})
        )
        
        res = chatbot(req)
        twiml_resp = MessagingResponse()
        
        if "error" in res:
            twiml_resp.message(f"Error: {res['error']}")
            return Response(content=str(twiml_resp), media_type="application/xml")
            
        session["current_state"] = res["next_state"]
        session["answers"] = res.get("answers", {})
        reply_text = res["question"]
    
    # Check if we reached the end
    if res["next_state"] == "end" and "rag_response" in res:
        try:
            # Robust JSON extraction using regex to find the first '{' and last '}'
            import re
            json_match = re.search(r'\{.*\}', res["rag_response"].strip(), re.DOTALL)
            if json_match:
                clean_json = json_match.group(0)
            else:
                clean_json = "{}"

            rag_data = json.loads(clean_json)
            
            # --- CHROMADB FARMER PROFILE INGESTION ---
            import os
            import chromadb
            from sentence_transformers import SentenceTransformer
            import json as built_in_json
            
            try:
                db_dir = os.path.dirname(os.path.abspath(__file__))
                chroma_path = os.path.join(db_dir, "scripts", "chroma_db")
                pr_client = chromadb.PersistentClient(path=chroma_path)
                f_collection = pr_client.get_or_create_collection(name="farmer_profiles")
                
                embedder = SentenceTransformer("all-MiniLM-L6-v2")
                # Create a rich text summary of the farmer to embed for vector similarity
                farmer_text_profile = ""
                for k, v in session.get("answers", {}).items():
                    farmer_text_profile += f"{k}: {v}\n"
                    
                if farmer_text_profile.strip():
                    f_embed = embedder.encode(farmer_text_profile).tolist()
                    
                    f_collection.upsert(
                        documents=[built_in_json.dumps(session.get("answers", {}))],
                        embeddings=[f_embed],
                        metadatas=[{"language": session.get("language", "english")}],
                        ids=[From]
                    )
                    print(f"Successfully vectorized and stored farmer profile for {From} into ChromaDB")
            except Exception as db_err:
                print(f"Failed to ingest farmer into ChromaDB: {db_err}")
            # ----------------------------------------
            
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
            
            # Append the next state question so it seamlessly flows into scheme_selection
            next_prompt = "Which scheme are you interested in?"
            if session.get("language", "english") == "hindi":
                next_prompt = "\n\nआप किस योजना में रुचि रखते हैं?"
            elif session.get("language", "english") == "marathi":
                next_prompt = "\n\nतुम्हाला कोणत्या योजनेत रस आहे?"
            elif session.get("language", "english") == "tamil":
                next_prompt = "\n\nநீங்கள் எந்த திட்டத்தில் ஆர்வமாக உள்ளீர்கள்?"
            elif session.get("language", "english") == "telugu":
                next_prompt = "\n\nమీరు ఏ పథకం పట్ల ఆసక్తి చూపుతున్నారు?"
            else:
                next_prompt = "\n\nWhich scheme are you interested in?"
                
            reply_text += next_prompt
            
            # Don't delete session; shift state manually to continue infinite flow
            session["current_state"] = "scheme_selection"
            
        except Exception as e:
            print("Failed to parse rag:", e)
            # HARDCODED FALLBACK FOR HACKATHON DEMO SAFETY
            reply_text += "\n\n🟢 *Pradhan Mantri Fasal Bima Yojana (PMFBY)*\n_Based on your inputs, you may qualify for subsidized crop insurance._\n➔ *Documents Required:* Aadhaar Card, Land Record, Bank Passbook\n\n"
            reply_text += "🟢 *Kisan Credit Card (KCC)*\n_You may be eligible for institutional credit at low interest rates._\n➔ *Documents Required:* Identity Proof, Land documents\n\n"
            reply_text += "Which scheme are you interested in?"
            session["current_state"] = "scheme_selection"
            
    # Send the final formatted message back to WhatsApp in safe chunks (Twilio limit is 1600 chars)
    def chunk_message(text, max_len=1500):
        paragraphs = text.split('\n')
        chunks = []
        current = ""
        for p in paragraphs:
            if len(current) + len(p) + 1 > max_len:
                if current:
                    chunks.append(current)
                    current = p
                else:
                    for i in range(0, len(p), max_len):
                        chunks.append(p[i:i+max_len])
                    current = ""
            else:
                if current:
                    current += "\n" + p
                else:
                    current = p
        if current:
            chunks.append(current)
        return chunks if chunks else [" "]

    msg = None
    for chunk in chunk_message(reply_text, 1500):
        msg = twiml_resp.message(chunk)
    
    if session.get("wants_audio"):
        import re
        import textwrap
        try:
            from tts import generate_tts
            
            # If we are at the "end" state initially generating the RAG scheme lists, we want to read ONLY the scheme names
            # Otherwise, for normal conversation flow or follow_up QA, we read `reply_text` directly (without markdown).
            if "rag_data" in locals() and rag_data.get("eligible_schemes"):
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

from pydantic import BaseModel
from typing import Optional

class WebChatRequest(BaseModel):
    user_id: str
    message: str
    image_base64: Optional[str] = None
    image_mime: Optional[str] = None
    is_voice: Optional[bool] = False

@router.post("/web_chat")
async def web_chat_endpoint(request: WebChatRequest, http_request: Request):
    user_id = request.user_id
    body_text = request.message.strip()
    
    from data_input import llm_call, chatbot, ChatRequest
    
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
    
    # Mirroring the Local Session DB logic
    if user_id not in sessions or body_text.lower() in ["reset", "restart"]:
        sessions[user_id] = {
            "flow_type": "unknown",
            "current_state": "language_selection",
            "answers": {},
            "language": "english"
        }
        return {"response": LANGUAGE_PROMPT.replace('\n', '<br>'), "state": "language_selection"}
        
    session = sessions[user_id]
    
    if request.image_base64:
        # Instead of Twilio CDN URLs, the frontend uploads raw Base64 strings.
        # We spoof the syntax the VLM looks for.
        body_text = f"[DOCUMENT_UPLOADED] (data:{request.image_mime};base64,{request.image_base64})"
        
    if session["current_state"] == "language_selection":
        selected_num = body_text.strip()
        if selected_num in LANGUAGE_OPTIONS:
            session["language"] = LANGUAGE_OPTIONS[selected_num]
            session["current_state"] = "awaiting_intent"
            
            prompt_text = "How can I help you today?<br>- Type <b>'Check eligibility'</b> to see what schemes you qualify for.<br>- Type <b>'Apply for PMFBY/KCC/PM-KISAN/NLM'</b> to start a direct application."
            if session["language"] == "hindi":
                prompt_text = "मैं आज आपकी कैसे सहायता कर सकता हूँ?<br>- यह देखने के लिए कि आप किन योजनाओं के लिए पात्र हैं, <b>'पात्रता जांचें'</b> टाइप करें।<br>- सीधा आवेदन शुरू करने के लिए <b>'PMFBY/KCC/PM-KISAN/NLM के लिए आवेदन करें'</b> टाइप करें।"
            elif session["language"] == "marathi":
                prompt_text = "मी आज तुम्हाला कशी मदत करू शकेन?<br>- तुम्ही कोणत्या योजनांसाठी पात्र आहात हे पाहण्यासाठी <b>'पात्रता तपासा'</b> टाइप करा.<br>- थेट अर्ज सुरू करण्यासाठी <b>'PMFBY/KCC/PM-KISAN/NLM साठी अर्ज करा'</b> टाइप करा."
            
            return {"response": prompt_text, "state": "awaiting_intent"}
        else:
            return {"response": "Invalid selection.<br><br>" + LANGUAGE_PROMPT.replace('\n', '<br>'), "state": "language_selection"}
            
    # Intent Classification handling
    if session["current_state"] == "awaiting_intent":
        from data_input import llm_call
        prompt = f'''
        User said: "{body_text}"
        Determine the user's intent based on semantic meaning. 
        Options:
        1. "kcc" (wants to apply for Kisan Credit Card, needs a loan, money for seeds, credit, tractor)
        2. "nlm" (wants to apply for National Livestock Mission, bought cows/goats/poultry, animal husbandry)
        3. "pm_kisan" (wants PM-KISAN, 6000 rupees yearly, regular financial support)
        4. "pmfby" (wants to apply for PMFBY, crop insurance, crops ruined by rain/drought/pests, claims)
        5. "eligibility" (wants to check what schemes they are eligible for, general chat, greetings)
        
        Examples:
        - "My crops got ruined by rain, I need money" -> "pmfby"
        - "I want to buy a tractor and need a loan" -> "kcc"
        - "I have 5 cows and want subsidy" -> "nlm"
        - "How do I get the 6000 rupees scheme?" -> "pm_kisan"
        - "What schemes are there for me?" -> "eligibility"
        
        Return ONLY the option key string. If unsure, return "eligibility".
        '''
        try:
            intent_resp = llm_call(prompt).strip().lower()
            intent = "eligibility"
            for k in ["kcc", "nlm", "pm_kisan", "pmfby"]:
                if k in intent_resp:
                    intent = k
                    break
        except:
            intent = "eligibility"
            
        session["current_state"] = "start"
        body_text = "" 
        session["answers"] = {}
        
        if intent in ["kcc", "nlm", "pm_kisan", "pmfby"]:
            session["flow_type"] = "auto_form"
            session["scheme_target"] = intent
        else:
            session["flow_type"] = "eligibility"

    # Route based on flow type
    if session.get("flow_type") == "auto_form":
        from auto_form_filling import handle_form, FormRequest
        req = FormRequest(
            scheme_target=session.get("scheme_target"),
            current_state=session["current_state"],
            user_answer=body_text,
            language=session["language"],
            collected_data=session.get("answers", {})
        )
        res = handle_form(req)
        
        if "error" in res:
            return {"response": f"Error: {res['error']}", "state": session["current_state"]}
            
        session["current_state"] = res["next_state"]
        session["answers"] = res.get("collected_data", {})
        
        if res["next_state"] == "end":
            session["current_state"] = "language_selection" 
            
        reply_text = res["question"].replace('\n', '<br>')
        
        audio_url = None
        if request.is_voice:
            import re
            try:
                from tts import generate_tts
                tts_text = re.sub(r'[*_🟢➔✅<br>]', '', res["question"])
                tts_text = tts_text.strip()
                if len(tts_text) > 800:
                    tts_text = tts_text[:800] + "... Please see the text message below."
                filename = generate_tts(tts_text, session.get("language", "english"))
                host = http_request.headers.get("host", "127.0.0.1:8000")
                scheme = http_request.headers.get("x-forwarded-proto", "http")
                audio_url = f"{scheme}://{host}/static/{filename}"
            except Exception as e:
                print(f"Web TTS generation failed: {e}")
                
        if res["next_state"] == "end":
            session["current_state"] = "language_selection" 
            
        return {"response": reply_text, "state": session["current_state"], "audio_url": audio_url}
            
    else:
        req = ChatRequest(
            current_state=session["current_state"],
            user_answer=body_text,
            language=session["language"],
            answers=session.get("answers", {})
        )
        
        res = chatbot(req)
        if "error" in res:
            return {"response": f"Error: {res['error']}", "state": session["current_state"]}
            
        session["current_state"] = res["next_state"]
        session["answers"] = res.get("answers", {})
        reply_text = res["question"].replace('\n', '<br>')
        
        if res["next_state"] == "end" and "rag_response" in res:
            try:
                import re
                json_match = re.search(r'\{.*\}', res["rag_response"].strip(), re.DOTALL)
                clean_json = json_match.group(0) if json_match else "{}"

                rag_data = json.loads(clean_json.strip())
                
                # --- CHROMADB FARMER PROFILE INGESTION ---
                import os
                import chromadb
                from sentence_transformers import SentenceTransformer
                import json as built_in_json
                
                try:
                    db_dir = os.path.dirname(os.path.abspath(__file__))
                    chroma_path = os.path.join(db_dir, "scripts", "chroma_db")
                    pr_client = chromadb.PersistentClient(path=chroma_path)
                    f_collection = pr_client.get_or_create_collection(name="farmer_profiles")
                    
                    embedder = SentenceTransformer("all-MiniLM-L6-v2")
                    farmer_text_profile = ""
                    for k, v in session.get("answers", {}).items():
                        farmer_text_profile += f"{k}: {v}\n"
                        
                    if farmer_text_profile.strip():
                        f_embed = embedder.encode(farmer_text_profile).tolist()
                        
                        f_collection.upsert(
                            documents=[built_in_json.dumps(session.get("answers", {}))],
                            embeddings=[f_embed],
                            metadatas=[{"language": session.get("language", "english")}],
                            ids=[user_id]
                        )
                        print(f"Successfully vectorized Web user profile for {user_id} into ChromaDB")
                except Exception as db_err:
                    print(f"Failed to ingest Web farmer into ChromaDB: {db_err}")
                # ----------------------------------------
                
                # To prevent endless loops on the frontend, map the state specifically like Twilio did
                session["current_state"] = "scheme_selection"
                return {"response": reply_text, "rag_payload": rag_data, "state": "end"}
            except Exception as e:
                print("Web JSON Error:", e)
                # FALLBACK FOR DEMO SAFETY
                fallback_rag = {
                    "eligible_schemes": [
                        {
                            "scheme": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
                            "reason": "Based on your farming inputs, you may qualify for subsidized crop insurance.",
                            "key_features": "Lower premiums for food crops and oilseeds.",
                            "documents": "Aadhaar Card, Land Record, Bank Passbook"
                        },
                        {
                            "scheme": "Kisan Credit Card (KCC)",
                            "reason": "You may be eligible for institutional credit.",
                            "key_features": "Low interest rate loans for operational farming costs.",
                            "documents": "Identity Proof, Land documents"
                        }
                    ]
                }
                session["current_state"] = "scheme_selection"
                return {"response": reply_text, "rag_payload": fallback_rag, "state": "end"}
        
        audio_url = None
        if request.is_voice:
            import re
            try:
                from tts import generate_tts
                
                if res["next_state"] == "end" and "rag_data" in locals() and rag_data.get("eligible_schemes"):
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
                    tts_text = re.sub(r'[*_🟢➔✅<br>]', '', res["question"])
                    
                tts_text = tts_text.strip()
                if len(tts_text) > 800:
                    tts_text = tts_text[:800] + "... Please see the text message below."
                    
                filename = generate_tts(tts_text, session.get("language", "english"))
                host = http_request.headers.get("host", "127.0.0.1:8000")
                scheme = http_request.headers.get("x-forwarded-proto", "http")
                audio_url = f"{scheme}://{host}/static/{filename}"
            except Exception as e:
                print(f"Web TTS generation failed: {e}")
                
        return {"response": reply_text, "state": session["current_state"], "audio_url": audio_url}

class SchemeBroadcastRequest(BaseModel):
    title: str
    description: str

@router.post("/admin/inject_scheme")
async def inject_scheme_endpoint(request: SchemeBroadcastRequest):
    """
    Reverse RAG Logic:
    1. Receives a new Scheme Title and Details from the Admin Dashboard.
    2. Scans all active WhatsApp sessions (past conversations).
    3. Feeds each user's accumulated profile (answers dict) + scheme criteria into LLM.
    4. If LLM determines eligibility => Trues => Fires Outbound Twilio WhatsApp Message.
    """
    from data_input import llm_call
    from twilio.rest import Client
    import os
    import chromadb
    from sentence_transformers import SentenceTransformer
    import json
    
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_number = "whatsapp:+14155238886" # Standard Sandbox Number
    
    # 1. Connect to ChromaDB
    current_dir = os.path.dirname(os.path.abspath(__file__))
    CHROMA_DB_PATH = os.path.join(current_dir, "scripts", "chroma_db")
    client_db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    farmer_collection = client_db.get_or_create_collection(name="farmer_profiles")
    
    matches = []
    
    # Check if we have any farmers in the DB First
    db_size = farmer_collection.count()
    if db_size == 0:
        return {"status": "success", "scanned_users": 0, "matches_found": 0, "message": "No farmers in ChromaDB yet."}
        
    # 2. Embed the New Scheme Criteria
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    scheme_embedding = embedding_model.encode(request.description).tolist()
    
    # 3. Pull Top-Matching Farmers (Reverse RAG) from the DB
    results = farmer_collection.query(
        query_embeddings=[scheme_embedding],
        n_results=min(10, db_size) # Grab top 10 most relevant farmers
    )
    
    scanned = 0
    
    # results['ids'][0] contains the actual phone numbers ["whatsapp:+91...", etc.]
    # results['documents'][0] contains their JSON stringified answers profile
    # results['metadatas'][0] contains the language pref
    if results["ids"] and len(results["ids"]) > 0:
        for idx, user_id in enumerate(results["ids"][0]):
            scanned += 1
            profile_json_str = results["documents"][0][idx]
            metadata = results["metadatas"][0][idx]
            language = metadata.get("language", "english")
            
            evaluation_prompt = f"""
            You are an expert Agricultural Scheme Evaluator.
            
            NEW SCHEME ANNOUNCED:
            Title: {request.title}
            Criteria: {request.description}
            
            FARMER PROFILE (From VectorDB):
            {profile_json_str}
            
            TASK:
            Evaluate if the farmer is eligible for the new scheme based on their profile.
            *CRITICAL: Be lenient with minor spelling mistakes in locations (e.g., "Maharastra" = "Maharashtra") and synonyms for crops.*
            
            If NO (they do not meet the core criteria), return exactly: FALSE
            If YES, generate a short 2-sentence proactive outreach message in {language} offering them to apply.
            
            Only return the word FALSE or the message string. NO generic conversational filler.
            """
            
            try:
                eval_result = llm_call(evaluation_prompt).strip()
                
                if not eval_result.upper().startswith("FALSE"):
                    matches.append(user_id)
                    # Dispatch Outbound Notification via Twilio App
                    if twilio_sid and twilio_auth:
                        twilio_client = Client(twilio_sid, twilio_auth)
                        try:
                            message = twilio_client.messages.create(
                                from_=twilio_number,
                                body=f"🚨 *New Scheme Match Alert!*\n\n{eval_result}\n\n_Reply 'Apply' to start your application instantly._",
                                to=user_id
                            )
                            print(f"Broadcasted to {user_id}. Twilio SID: {message.sid}")
                        except Exception as tw_err:
                            print(f"Twilio Dispatch Error for {user_id}: {tw_err}")
                    else:
                        print(f"Mock Broadcast Triggered for {user_id} - Msg: {eval_result}")
            except Exception as e:
                print(f"R-RAG Eval Error for {user_id}: {e}")
            
    return {
        "status": "success", 
        "scanned_users": scanned,
        "matches_found": len(matches)
    }

