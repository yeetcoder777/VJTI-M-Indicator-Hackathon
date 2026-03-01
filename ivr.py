import json
import os
import time
import traceback
import requests
from fastapi import APIRouter, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/ivr")

# Load flow.json
current_dir = os.path.dirname(os.path.abspath(__file__))
flow_path = os.path.join(current_dir, "flow_call.json")
with open(flow_path, "r") as f:
    flow = json.load(f)

# Clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN"),
)
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
NGROK_URL = os.getenv("NGROK_URL", "").rstrip("/")
LLM_MODEL = "openai/gpt-oss-120b"

# In-memory session storage keyed by Twilio CallSid
sessions = {}

# Language config
LANGUAGE_MAP = {
    "1": {"name": "english", "tts_lang": "en-US", "voice": "Polly.Joanna"},
    "2": {"name": "hindi", "tts_lang": "hi-IN", "voice": "Polly.Aditi"},
    "3": {"name": "marathi", "tts_lang": "hi-IN", "voice": "Polly.Aditi"},
}


def get_url(path: str) -> str:
    """Build full webhook URL using NGROK_URL."""
    return f"{NGROK_URL}{path}"


def twiml_response(twiml: VoiceResponse) -> Response:
    xml = str(twiml)
    print(f"[TwiML] {xml[:500]}")
    return Response(content=xml, media_type="application/xml")


def llm_call(prompt: str) -> str:
    resp = groq_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_completion_tokens=512,
    )
    return resp.choices[0].message.content


def translate(text: str, language: str) -> str:
    if language == "english":
        return text
    try:
        return llm_call(
            f"Translate to {language}. Return ONLY the translated text:\n\n{text}"
        )
    except Exception:
        return text


def say_text(twiml_obj, text: str, session: dict):
    cfg = LANGUAGE_MAP.get(session.get("lang_key", "1"), LANGUAGE_MAP["1"])
    twiml_obj.say(text, voice=cfg["voice"], language=cfg["tts_lang"])


# ------------------------------------------------------------------ #
#  RECORDING DOWNLOAD + GROQ WHISPER TRANSCRIPTION                    #
# ------------------------------------------------------------------ #
def transcribe_recording(recording_url: str, session: dict) -> str:
    """Download Twilio recording and transcribe with Groq Whisper."""
    audio_url = recording_url + ".wav"
    print(f"[STT] Downloading recording: {audio_url}")

    # Retry download — recording may not be ready instantly
    audio_data = None
    for attempt in range(3):
        try:
            resp = requests.get(
                audio_url,
                auth=(
                    os.getenv("TWILIO_ACCOUNT_SID"),
                    os.getenv("TWILIO_AUTH_TOKEN"),
                ),
                timeout=10,
            )
            if resp.status_code == 200 and len(resp.content) > 1000:
                audio_data = resp.content
                break
            print(
                f"[STT] Attempt {attempt+1}: HTTP {resp.status_code}, "
                f"size={len(resp.content)} bytes"
            )
        except requests.exceptions.RequestException as e:
            print(f"[STT] Attempt {attempt+1} error: {e}")
        time.sleep(2)

    if not audio_data:
        print("[STT] Failed to download recording after 3 attempts")
        return ""

    print(f"[STT] Downloaded {len(audio_data)} bytes")

    # Save to a unique temp file
    call_sid = session.get("call_sid", "tmp")
    temp_path = os.path.join(current_dir, f"rec_{call_sid}.wav")
    with open(temp_path, "wb") as f:
        f.write(audio_data)

    # Whisper language code
    whisper_lang = {"english": "en", "hindi": "hi", "marathi": "mr"}
    lang_code = whisper_lang.get(session.get("language", "english"), "en")

    # Current question for prompt context
    cur_q = flow["questions"].get(session.get("current_state", ""), {}).get("text", "")

    # Build a context-aware prompt to guide Whisper
    state_key = session.get("current_state", "")
    prompt_hints = {
        "state": "Indian state names like Maharashtra, Punjab, Uttar Pradesh, Bihar, Karnataka, Tamil Nadu, Rajasthan, Gujarat, Madhya Pradesh",
        "land_size": "A number in acres like 2, 5, 10, 15, 20",
        "farming_type": "Crops like wheat, rice, cotton, sugarcane, soybean, or activities like dairy, poultry, fishery",
        "activity": "Farming activities like dairy farming, poultry, fishery, beekeeping, goat rearing",
        "income": "An amount in rupees like 50000, 100000, 200000, 500000",
    }
    hint = prompt_hints.get(state_key, "")
    whisper_prompt = f"Farmer answering: {cur_q}"
    if hint:
        whisper_prompt += f" Expected answers: {hint}"

    try:
        with open(temp_path, "rb") as af:
            result = groq_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=af,
                language=lang_code,
                prompt=whisper_prompt,
                temperature=0.0,
            )
        text = result.text.strip()
        print(f"[STT] Whisper result: '{text}'")

        # Filter common hallucinations on silence / short audio
        hallucinations = {
            "thank you", "thanks", "bye", "take care",
            "you", "thank you for watching", "thanks for watching",
            "please", "good luck", "my name is", "hello",
            "goodbye", "see you", "welcome", "okay",
            "yes", "no", "sure", "right",
        }
        cleaned = text.lower().strip(".!?, ")
        if cleaned in hallucinations or len(cleaned) < 2:
            print(f"[STT] Filtered hallucination: '{text}'")
            return ""
        return text
    except Exception as e:
        print(f"[STT] Whisper error: {e}")
        traceback.print_exc()
        return ""
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


# ------------------------------------------------------------------ #
#  BUILD QUESTION TwiML                                               #
# ------------------------------------------------------------------ #
def build_question_twiml(session: dict, state_key: str) -> VoiceResponse:
    state_data = flow["questions"][state_key]
    question_text = translate(state_data["text"], session["language"])
    twiml = VoiceResponse()

    if state_data.get("input_type") == "dtmf":
        gather = Gather(
            input="dtmf",
            num_digits=1,
            action=get_url("/ivr/handle-dtmf"),
            method="POST",
            timeout=10,
        )
        say_text(gather, question_text, session)
        twiml.append(gather)
        # No input → repeat the same question
        say_text(
            twiml,
            translate("No input detected. Let me repeat.", session["language"]),
            session,
        )
        twiml.redirect(get_url("/ivr/ask-next"))
    else:
        # Voice → record and send to Whisper
        say_text(twiml, question_text, session)
        twiml.record(
            action=get_url("/ivr/handle-voice"),
            method="POST",
            max_length=10,
            play_beep=True,
            trim="trim-silence",
            timeout=5,
        )

    return twiml


# ------------------------------------------------------------------ #
#  STEP 1 — LANGUAGE SELECTION                                        #
# ------------------------------------------------------------------ #
@router.post("/start")
async def ivr_start(request: Request):
    form = await request.form()
    print(f"[Start] CallSid={form.get('CallSid')}")

    twiml = VoiceResponse()
    gather = Gather(
        num_digits=1,
        action=get_url("/ivr/language"),
        method="POST",
        timeout=5,
    )
    gather.say(
        "Welcome to the Farmer Scheme Assistant.",
        voice="Polly.Joanna", language="en-US",
    )
    gather.say("Press 1 for English.", voice="Polly.Joanna", language="en-US")
    gather.say("Hindi ke liye 2 dabaye.", voice="Polly.Aditi", language="hi-IN")
    gather.say("Marathi sathi 3 daba.", voice="Polly.Aditi", language="hi-IN")
    twiml.append(gather)
    twiml.redirect(get_url("/ivr/start"))
    return twiml_response(twiml)


# ------------------------------------------------------------------ #
#  STEP 2 — LANGUAGE CHOSEN → FIRST QUESTION                         #
# ------------------------------------------------------------------ #
@router.post("/language")
async def ivr_language(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    digits = form.get("Digits", "1")
    print(f"[Lang] CallSid={call_sid}, Digits={digits}")

    if digits not in LANGUAGE_MAP:
        digits = "1"

    lang = LANGUAGE_MAP[digits]
    first_state = flow.get("start", "state")

    sessions[call_sid] = {
        "call_sid": call_sid,
        "lang_key": digits,
        "language": lang["name"],
        "current_state": first_state,
        "farmer_profile": {},
        "caller": form.get("To", "") if form.get("From", "") == TWILIO_PHONE_NUMBER else form.get("From", ""),
    }

    twiml = build_question_twiml(sessions[call_sid], first_state)
    return twiml_response(twiml)


# ------------------------------------------------------------------ #
#  STEP 3A — DTMF ANSWER                                             #
# ------------------------------------------------------------------ #
@router.post("/handle-dtmf")
async def handle_dtmf(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    digits = form.get("Digits", "")
    print(f"[DTMF] CallSid={call_sid}, Digits={digits}")

    session = sessions.get(call_sid)
    if not session:
        twiml = VoiceResponse()
        twiml.say("Session not found. Goodbye.")
        twiml.hangup()
        return twiml_response(twiml)

    try:
        cur = flow["questions"][session["current_state"]]
        answer = cur.get("dtmf_options", {}).get(digits, digits)
        session["farmer_profile"][cur.get("key", session["current_state"])] = answer
        print(f"[DTMF] Stored {cur.get('key')}={answer}")
        return advance_to_next(session, answer, cur, call_sid)
    except Exception as e:
        print(f"[DTMF] Error: {e}")
        traceback.print_exc()
        twiml = VoiceResponse()
        say_text(twiml, "An error occurred. Let me repeat.", session)
        twiml.redirect(get_url("/ivr/ask-next"))
        return twiml_response(twiml)


# ------------------------------------------------------------------ #
#  STEP 3B — VOICE RECORDING ANSWER                                  #
# ------------------------------------------------------------------ #
@router.post("/handle-voice")
async def handle_voice(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    recording_url = form.get("RecordingUrl", "")
    print(f"[Voice] CallSid={call_sid}, RecordingUrl={recording_url}")

    session = sessions.get(call_sid)
    if not session:
        twiml = VoiceResponse()
        twiml.say("Session not found. Goodbye.")
        twiml.hangup()
        return twiml_response(twiml)

    try:
        cur = flow["questions"][session["current_state"]]
        answer_key = cur.get("key", session["current_state"])

        # Transcribe recording with Groq Whisper
        answer = ""
        if recording_url:
            answer = transcribe_recording(recording_url, session)

        if not answer:
            # Transcription failed or empty → ask again
            print("[Voice] Empty transcription — repeating question")
            twiml = VoiceResponse()
            say_text(
                twiml,
                translate(
                    "Sorry, I could not understand. Let me ask again.",
                    session["language"],
                ),
                session,
            )
            twiml.redirect(get_url("/ivr/ask-next"))
            return twiml_response(twiml)

        session["farmer_profile"][answer_key] = answer
        print(f"[Voice] Stored {answer_key}={answer}")
        return advance_to_next(session, answer, cur, call_sid)

    except Exception as e:
        print(f"[Voice] Error: {e}")
        traceback.print_exc()
        twiml = VoiceResponse()
        say_text(twiml, "An error occurred. Let me ask again.", session)
        twiml.redirect(get_url("/ivr/ask-next"))
        return twiml_response(twiml)


# ------------------------------------------------------------------ #
#  DETERMINE NEXT STATE & REDIRECT                                   #
# ------------------------------------------------------------------ #
def advance_to_next(session, answer, current_data, call_sid):
    next_map = current_data.get("next")
    print(f"[Next] answer='{answer}', next_map={next_map}")

    if isinstance(next_map, str):
        next_key = next_map
    elif isinstance(next_map, dict):
        # Try direct lookup first (works for DTMF-mapped answers)
        if answer.lower() in next_map:
            next_key = next_map[answer.lower()]
        else:
            # LLM classification for free-form voice answers
            hints = current_data.get("classify", {})
            prompt = (
                f'The user was asked: "{current_data["text"]}"\n'
                f'The user responded: "{answer}"\n'
                f"Possible categories: {list(next_map.keys())}\n"
                + (f"Hints: {json.dumps(hints)}\n" if hints else "")
                + "Return ONLY the matching category key."
            )
            try:
                classified = llm_call(prompt).strip().lower()
                print(f"[Next] LLM classified: '{classified}'")
                matched = None
                for k in next_map:
                    if k.lower() in classified:
                        matched = k
                        break
                next_key = next_map.get(matched, list(next_map.values())[0])
            except Exception as e:
                print(f"[Next] Classification error: {e}")
                next_key = list(next_map.values())[0]
    else:
        next_key = "end"

    print(f"[Next] → {next_key}")

    if next_key == "end":
        return ivr_recommend_sync(call_sid)

    session["current_state"] = next_key
    twiml = VoiceResponse()
    twiml.redirect(get_url("/ivr/ask-next"))
    return twiml_response(twiml)


# ------------------------------------------------------------------ #
#  ASK-NEXT  (redirect target that builds question TwiML)             #
# ------------------------------------------------------------------ #
@router.post("/ask-next")
async def ask_next(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    print(f"[AskNext] CallSid={call_sid}")

    session = sessions.get(call_sid)
    if not session:
        twiml = VoiceResponse()
        twiml.say("Session not found. Goodbye.")
        twiml.hangup()
        return twiml_response(twiml)

    print(
        f"[AskNext] state={session['current_state']}, "
        f"profile={session['farmer_profile']}"
    )
    twiml = build_question_twiml(session, session["current_state"])
    return twiml_response(twiml)


# ------------------------------------------------------------------ #
#  RECOMMEND SCHEMES (end of questionnaire)                           #
# ------------------------------------------------------------------ #
def ivr_recommend_sync(call_sid: str):
    session = sessions[call_sid]
    profile = session["farmer_profile"]
    profile_text = ", ".join(f"{k}: {v}" for k, v in profile.items() if v)
    print(f"[Recommend] Profile: {profile_text}")

    prompt = (
        "You are an expert on Indian government schemes for farmers.\n"
        "Based on this farmer's profile, recommend the top 3 most relevant schemes.\n"
        "For each scheme give: name and one short line on why they qualify.\n"
        "Keep it very brief — it will be read aloud on a phone call.\n\n"
        f"Farmer profile: {profile_text}\n\n"
        "Schemes: PM-KISAN, PMFBY, Soil Health Card, PMKSY, "
        "Kisan Credit Card (KCC), National Livestock Mission (NLM)."
    )

    try:
        recommendation = llm_call(prompt)
        if not recommendation:
            recommendation = (
                "Based on your profile, you may be eligible for PM-KISAN, PMFBY, "
                "and Kisan Credit Card. Please visit your nearest CSC center for details."
            )
            print("[Recommend] LLM returned empty, using fallback")
        print(f"[Recommend] Result: {recommendation[:200]}")
        recommendation_translated = translate(recommendation, session["language"])
    except Exception as e:
        print(f"[Recommend] Error: {e}")
        recommendation = "We could not generate recommendations at this time."
        recommendation_translated = recommendation

    # Auto-send SMS with profile + recommendations (keep under 160 chars for trial)
    caller = session.get("caller", "")
    if caller:
        # Generate a short SMS-friendly version
        try:
            sms_prompt = (
                "List ONLY the names of the top 3 schemes for this farmer, "
                "separated by commas. No explanations. Max 100 characters.\n\n"
                f"Farmer: {profile_text}"
            )
            short_schemes = llm_call(sms_prompt).strip()
        except Exception:
            short_schemes = "PM-KISAN, PMFBY, KCC"
        # Build Google Maps link to nearest CSC using farmer's state
        state = profile.get("state", "").replace(" ", "+")
        csc_link = f"https://maps.google.com/maps?q=CSC+center+near+{state}" if state else "https://findmycsc.nic.in"
        sms_body = f"Farmer Scheme Assistant\nSchemes: {short_schemes}"
        try:
            twilio_client.messages.create(
                to=caller,
                from_=TWILIO_PHONE_NUMBER,
                body=sms_body,
            )
            print(f"[SMS] Sent to {caller}")
        except Exception as e:
            print(f"[SMS] Failed: {e}")

        # Send WhatsApp message with full recommendation details
        whatsapp_from = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
        if whatsapp_from:
            wa_body = (
                "*Farmer Scheme Assistant*\n\n"
                f"*Your Profile:*\n{profile_text}\n\n"
                f"*Recommended Schemes:*\n{recommendation}\n\n"
                "_Reply to this message to ask questions about any scheme._"
            )
            try:
                twilio_client.messages.create(
                    to=f"whatsapp:{caller}",
                    from_=f"whatsapp:{whatsapp_from}",
                    body=wa_body,
                )
                print(f"[WhatsApp] Sent to {caller}")
            except Exception as e:
                print(f"[WhatsApp] Failed: {e}")

    twiml = VoiceResponse()
    say_text(twiml, recommendation_translated, session)
    say_text(
        twiml,
        translate(
            "We have also sent these details to your phone. Thank you for calling. Goodbye!",
            session["language"],
        ),
        session,
    )
    twiml.hangup()
    sessions.pop(call_sid, None)
    return twiml_response(twiml)


# ------------------------------------------------------------------ #
#  SEND SMS WITH DETAILS                                              #
# ------------------------------------------------------------------ #
@router.post("/followup")
async def ivr_followup(request: Request):
    form = await request.form()
    call_sid = form.get("CallSid", "unknown")
    digits = form.get("Digits", "2")
    print(f"[Followup] CallSid={call_sid}, Digits={digits}")

    session = sessions.get(call_sid)
    twiml = VoiceResponse()

    if not session:
        twiml.say("Session not found. Goodbye.")
        twiml.hangup()
        return twiml_response(twiml)

    if digits == "1":
        caller = session.get("caller", "")
        profile = session["farmer_profile"]
        profile_text = "\n".join(f"- {k}: {v}" for k, v in profile.items() if v)

        sms_body = (
            "Farmer Scheme Assistant - Your Results\n\n"
            f"Your Profile:\n{profile_text}\n\n"
            "Based on your profile, check these schemes:\n"
            "1. PM-KISAN: pmkisan.gov.in\n"
            "2. PMFBY: pmfby.gov.in\n"
            "3. Soil Health Card: soilhealth.dac.gov.in\n"
            "4. KCC: Contact your nearest bank\n"
            "5. PMKSY: pmksy.gov.in\n\n"
            "Visit your nearest CSC center or bank for help applying."
        )

        try:
            if caller:
                twilio_client.messages.create(
                    to=caller,
                    from_=TWILIO_PHONE_NUMBER,
                    body=sms_body,
                )
            goodbye = translate(
                "Details have been sent to your phone via SMS. Thank you!",
                session["language"],
            )
        except Exception:
            goodbye = translate(
                "Sorry, we could not send the SMS. Please try again later.",
                session["language"],
            )
        say_text(twiml, goodbye, session)
    else:
        say_text(
            twiml,
            translate("Thank you for calling. Goodbye!", session["language"]),
            session,
        )

    twiml.hangup()
    sessions.pop(call_sid, None)
    return twiml_response(twiml)


# ------------------------------------------------------------------ #
#  RECORDING STATUS CALLBACK (logging only)                           #
# ------------------------------------------------------------------ #
@router.post("/recording-status")
async def recording_status(request: Request):
    form = await request.form()
    print(
        f"[RecStatus] {form.get('RecordingStatus')} "
        f"URL: {form.get('RecordingUrl')}"
    )
    return Response(status_code=200)


# ------------------------------------------------------------------ #
#  VIEW ALL SESSIONS (debug)                                          #
# ------------------------------------------------------------------ #
@router.get("/sessions")
def view_sessions():
    """Browse to /ivr/sessions to see all collected farmer profiles."""
    return {
        sid: {
            "language": s.get("language"),
            "current_state": s.get("current_state"),
            "farmer_profile": s.get("farmer_profile"),
        }
        for sid, s in sessions.items()
    }


# ------------------------------------------------------------------ #
#  TEST CALL — Twilio calls you                                       #
# ------------------------------------------------------------------ #
@router.get("/test-call")
def test_call(to: str):
    if not NGROK_URL:
        return {"error": "Set NGROK_URL in .env first"}

    twiml_bin_url = os.getenv("TWIML_BIN_URL", "")
    start_url = twiml_bin_url if twiml_bin_url else get_url("/ivr/start")

    call = twilio_client.calls.create(
        to=to,
        from_=TWILIO_PHONE_NUMBER,
        url=start_url,
    )
    return {
        "message": f"Calling {to}...",
        "call_sid": call.sid,
        "webhook_url": start_url,
    }
