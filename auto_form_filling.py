import json
import os
import base64
import requests
from fastapi import APIRouter
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
from data_input import llm_call

load_dotenv()
router = APIRouter()

def verify_document_vlm(image_url: str, document_type: str) -> bool:
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth = os.getenv("TWILIO_AUTH_TOKEN")
    try:
        if image_url.startswith("data:"):
            import re
            match = re.match(r'data:(.*?);base64,(.*)', image_url)
            if not match:
                return False
            image_mime = match.group(1)
            base64_image = match.group(2)
        else:
            response = requests.get(image_url, auth=(twilio_sid, twilio_auth))
            if response.status_code != 200:
                print(f"Failed to download image: {response.status_code}")
                return True
                
            content_type = response.headers.get("Content-Type", "")
            if "pdf" in content_type:
                return True
                
            base64_image = base64.b64encode(response.content).decode('utf-8')
            image_mime = "image/jpeg"
            if "png" in content_type:
                image_mime = "image/png"
            
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        prompt = f"The user was asked to upload an image of: {document_type}. Does this image visually depict a {document_type} or a document directly satisfying this purpose? Reply ONLY with YES or NO."
            
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_mime};base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
        )
        result = chat_completion.choices[0].message.content.strip().upper()
        print(f"VLM Verification for {document_type}: {result}")
        return "YES" in result
    except Exception as e:
        print(f"VLM Error: {e}")
        return True

# Define the schema application flows
application_flows = {
    "kcc": {
        "name": "Kisan Credit Card (KCC)",
        "questions": {
            "state": {"key": "state", "text": "To apply for KCC, which state do you farm in?", "next": "district"},
            "district": {"key": "district", "text": "Which district do you live in?", "next": "personal_details"},
            "personal_details": {"key": "personal_details", "text": "Please provide your full name and date of birth.", "next": "land_details"},
            "land_details": {"key": "land_details", "text": "Please provide details about your land, crops, or livestock.", "next": "upload_id"},
            "upload_id": {"key": "id_proof", "text": "Please upload a clear photo of your Identity Proof (Aadhaar/PAN).", "next": "upload_land_record", "expected_doc": "Identity proof like Aadhaar or PAN card"},
            "upload_land_record": {"key": "land_record", "text": "Upload your land record or lease proof (if applicable). If none, reply 'Skip'.", "next": "end_kcc", "expected_doc": "Land record or lease proof document"}
        },
        "end_message": "Your Kisan Credit Card application has been submitted online. The bank will verify these details and may call you or ask you to visit the branch for biometrics. Expected output: Credit card + loan limit."
    },
    "nlm": {
        "name": "National Livestock Mission (NLM)",
        "questions": {
            "state": {"key": "state", "text": "To apply for NLM, which state are you located in?", "next": "district"},
            "district": {"key": "district", "text": "Which district?", "next": "livestock_details"},
            "livestock_details": {"key": "livestock_details", "text": "What type of livestock activity are you doing (e.g., dairy, goatery, poultry, fodder)?", "next": "project_cost"},
            "project_cost": {"key": "project_cost", "text": "What is the estimated project cost?", "next": "bank_details"},
            "bank_details": {"key": "bank_details", "text": "Please provide your bank account number and IFSC code.", "next": "upload_id"},
            "upload_id": {"key": "id_proof", "text": "Please upload a photo of your Identity Proof (Aadhaar).", "next": "upload_passbook", "expected_doc": "Identity proof like Aadhaar"},
            "upload_passbook": {"key": "passbook", "text": "Please upload a photo of your Bank Passbook.", "next": "upload_proposal", "expected_doc": "Bank Passbook"},
            "upload_proposal": {"key": "project_proposal", "text": "Please upload your project proposal document.", "next": "end_nlm", "expected_doc": "Project Proposal document"}
        },
        "end_message": "Your National Livestock Mission application has been submitted to the state animal husbandry portal. The district office will verify it. Expected output: Subsidy support released to your bank account."
    },
    "pm_kisan": {
        "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "questions": {
            "state": {"key": "state", "text": "To apply for PM-KISAN, which state do you farm in?", "next": "district"},
            "district": {"key": "district", "text": "Which district?", "next": "category"},
            "category": {"key": "category", "text": "Are you a Rural or Urban farmer?", "next": "aadhaar"},
            "aadhaar": {"key": "aadhaar", "text": "Please enter your 12-digit Aadhaar number.", "next": "land_ownership"},
            "land_ownership": {"key": "land_ownership", "text": "Please provide your land ownership details (Survey number, Area).", "next": "bank_details"},
            "bank_details": {"key": "bank_details", "text": "Please provide your bank account number and IFSC code for direct transfers.", "next": "end_pm_kisan"}
        },
        "end_message": "Your PM-KISAN new farmer registration has been submitted. Land records will be verified by state authorities. Expected output: ₹6,000 per year credited directly to your bank account."
    },
    "pmfby": {
        "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "questions": {
            "state": {"key": "state", "text": "To register for PMFBY, which state do you farm in?", "next": "district"},
            "district": {"key": "district", "text": "Which district?", "next": "season"},
            "season": {"key": "season", "text": "Which season are you insuring for (e.g., Kharif, Rabi)?", "next": "crop_name"},
            "crop_name": {"key": "crop_name", "text": "What crop are you insuring?", "next": "sowing_details"},
            "sowing_details": {"key": "sowing_details", "text": "Please provide your land survey number and sowing date.", "next": "upload_land_record"},
            "upload_land_record": {"key": "land_record", "text": "Please upload a document of your land record.", "next": "premium_payment", "expected_doc": "Land record document"},
            "premium_payment": {"key": "premium_payment", "text": "Your premium amount has been calculated. We have sent a payment link to your mobile number. Reply 'Paid' once completed.", "next": "end_pmfby"}
        },
        "end_message": "Your PMFBY crop insurance application is complete! You will receive confirmation and your policy number shortly. Expected output: Crop insurance coverage against losses."
    }
}

class FormRequest(BaseModel):
    scheme_target: str  # kcc, nlm, pm_kisan, pmfby
    current_state: str = "start"
    user_answer: str = ""
    language: str = "english"
    collected_data: dict = {}

@router.post("/auto_form")
def handle_form(request: FormRequest):
    scheme_id = request.scheme_target.lower()
    
    # Validation
    if scheme_id not in application_flows:
        return {"error": "Scheme currently not supported for auto-fill applications."}
        
    scheme_data = application_flows[scheme_id]
    
    # Initialization Step
    if request.current_state == "start" or not request.current_state:
        next_state_key = "state"
        next_state_data = scheme_data["questions"][next_state_key]
        question_text = next_state_data["text"]
        
        if request.language.lower() != "english":
            prompt = f"Translate the following question to {request.language}:\n\n{question_text}"
            try:
                response = llm_call(prompt)
                question_text = response.strip()
            except:
                pass
                
        return {"next_state": next_state_key, "question": question_text, "scheme": scheme_data["name"]}

    # Normal State Loop
    current_state_data = scheme_data["questions"].get(request.current_state)
    if not current_state_data:
        return {"error": "Invalid form state."}
        
    expected_doc = current_state_data.get("expected_doc")
    if expected_doc:
        if request.user_answer.lower().strip() == 'skip':
            pass
        elif "[DOCUMENT_UPLOADED]" in request.user_answer:
            import re
            match = re.search(r'\[DOCUMENT_UPLOADED\] \((.*?)\)', request.user_answer)
            if match:
                image_url = match.group(1)
                is_valid = verify_document_vlm(image_url, expected_doc)
                if not is_valid:
                    error_msg = f"This document does not look like a valid {expected_doc}. Please try again."
                    question_text = f"{error_msg}\n\n{current_state_data['text']}"
                    if request.language.lower() != "english":
                        try:
                            prompt = f"Translate the following to {request.language}:\n\n{question_text}"
                            response = llm_call(prompt)
                            question_text = response.strip()
                        except:
                            pass
                    return {
                        "next_state": request.current_state,
                        "question": question_text,
                        "collected_data": request.collected_data
                    }
        else:
            error_msg = f"Please upload an image of the expected document: {expected_doc}."
            question_text = f"{error_msg}\n\n{current_state_data['text']}"
            if request.language.lower() != "english":
                try:
                    prompt = f"Translate the following to {request.language}:\n\n{question_text}"
                    response = llm_call(prompt)
                    question_text = response.strip()
                except:
                    pass
            return {
                "next_state": request.current_state,
                "question": question_text,
                "collected_data": request.collected_data
            }

    # Eagerly store User Answer into collected_data AFTER successful logic passes
    request.collected_data[request.current_state] = request.user_answer

    next_state_key = current_state_data["next"]
    
    # Check if we hit the end of the form flow
    if next_state_key.startswith("end_"):
        end_text = scheme_data["end_message"]
        
        # Build a neat summary of what was collected
        summary = "\n\nApplication Summary collected securely:\n"
        for k, v in request.collected_data.items():
            # Truncate long uploaded blob markers visually for the summary
            val_display = v if "[DOCUMENT_UPLOADED]" not in v else "Document Upload Received ✅"
            summary += f"- {k.replace('_', ' ').title()}: {val_display}\n"
            
        final_reply = end_text + summary
        
        if request.language.lower() != "english":
            try:
                prompt = f"Translate the following confirmation text to {request.language}:\n\n{final_reply}"
                response = llm_call(prompt)
                final_reply = response.strip()
            except Exception:
                pass
                
        return {
            "next_state": "end",
            "question": final_reply,
            "collected_data": request.collected_data
        }
        
    # Fetch next question
    next_state_data = scheme_data["questions"].get(next_state_key)
    if not next_state_data:
        return {"error": "Form sequence broken."}
        
    question_text = next_state_data["text"]
    
    if request.language.lower() != "english":
        try:
            prompt = f"Translate the following question to {request.language}:\n\n{question_text}"
            response = llm_call(prompt)
            question_text = response.strip()
        except:
            pass
            
    return {
        "next_state": next_state_key,
        "question": question_text,
        "collected_data": request.collected_data
    }
