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
        Determine the user's intent. 
        Options:
        1. "eligibility" (wants to check what schemes they are eligible for, or general chat)
        2. "kcc" (wants to apply for Kisan Credit Card)
        3. "nlm" (wants to apply for National Livestock Mission)
        4. "pm_kisan" (wants to apply for PM-KISAN)
        5. "pmfby" (wants to apply for PMFBY / crop insurance)
        
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
            reply_text += "\n\n(Error loading full scheme details)"
            
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
        Determine the user's intent. 
        Options:
        1. "eligibility" 
        2. "kcc" 
        3. "nlm" 
        4. "pm_kisan" 
        5. "pmfby" 
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
                clean_json = res["rag_response"].strip()
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                elif clean_json.startswith("```"):
                    clean_json = clean_json[3:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]
                rag_data = json.loads(clean_json.strip())
                
                # To prevent endless loops on the frontend, map the state specifically like Twilio did
                session["current_state"] = "scheme_selection"
                return {"response": reply_text, "rag_payload": rag_data, "state": "end"}
            except Exception as e:
                print("Web JSON Error:", e)
        
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
