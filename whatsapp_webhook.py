import json
from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse

from data_input import chatbot, ChatRequest

router = APIRouter()

# In-memory session tracking for WhatsApp numbers
# Format: { "+1234567890": {"current_state": "start", "answers": {}, "language": "english"} }
sessions = {}

@router.post("/whatsapp")
async def whatsapp_webhook(
  request: Request,
  Body: str = Form(...),
  From: str = Form(...),
  MediaUrl0: str | None = Form(None),
  MediaContentType0: str | None = Form(None),
):
    print(f"Received WhatsApp from {From}: {Body}")
    body_text = Body.strip()
    
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
        answers=session["answers"]
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
    session["answers"] = res["answers"]
    
    reply_text = res["question"]
    
    # Check if we reached the end
    if res["next_state"] == "end" and "rag_response" in res:
        try:
            rag_data = json.loads(res["rag_response"])
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
    twiml_resp.message(reply_text)
    return Response(content=str(twiml_resp), media_type="application/xml")
