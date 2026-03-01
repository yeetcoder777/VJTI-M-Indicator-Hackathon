import json
import os
from fastapi import APIRouter
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

# Load the flow from flow.json
current_dir = os.path.dirname(os.path.abspath(__file__))
flow_path = os.path.join(current_dir, 'flow.json')
with open(flow_path, 'r') as f:
    flow = json.load(f)

class ChatRequest(BaseModel):
    current_state: str = "start"
    user_answer: str = ""
    language: str = "english"
    answers: dict = {}

def llm_call(prompt: str):
    print("llm call")
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

@router.post("/chatbot")
def chatbot(request: ChatRequest):
    """
    After every question, the LLM is called with the question, the answer,
    and it determines the next question to ask based on 'next' mappings.
    """
    # Eagerly store the incoming answer for the CURRENT state before resolving the NEXT state
    if request.user_answer and request.current_state:
        request.answers[request.current_state] = request.user_answer

    # Base case: Starting the flow
    if request.current_state == "start" or not request.current_state:
        next_state_key = flow.get("start", "state")
        next_state_data = flow["questions"][next_state_key]
        question_text = next_state_data["text"]
        
        # Translate to desired language
        if request.language.lower() != "english":
            prompt = f"Translate the following question to {request.language}:\n\n{question_text}"
            response = llm_call(prompt)
            question_text = response.strip()
            
        return {"next_state": next_state_key, "question": question_text}

    # Fetch current question logic
    current_state_data = flow["questions"].get(request.current_state)
    if not current_state_data:
        return {"error": "Invalid state provided"}

    # Fetch current question logic

    next_mapping = current_state_data.get("next")
    
    # Determine next statekey
    if isinstance(next_mapping, str):
        # Direct string mapping, no LLM classification needed
        next_state_key = next_mapping
    elif isinstance(next_mapping, dict):
        # We need the LLM to classify where to route the user's response
        classify_hint = current_state_data.get("classify", {})
        
        prompt = f"""
        The user was asked: "{current_state_data['text']}"
        The user responded with: "{request.user_answer}"
        
        We need to determine the next step based on the provided mapping: {json.dumps(next_mapping)}
        {'Use these classification hints for guidance: ' + json.dumps(classify_hint) if classify_hint else ''}
        
        Based on the user's response, which key from the mapping logic applies best?
        Return ONLY the exact key name from the allowed keys: {list(next_mapping.keys())}.
        """
        try:
            response = llm_call(prompt)
            classified_key = response.text.strip().lower()
            
            # Clean and map the LLM response to one of our exact dictionary keys
            matched_key = None
            for k in next_mapping.keys():
                if k.lower() in classified_key:
                    matched_key = k
                    break
            
            if matched_key:
                next_state_key = next_mapping[matched_key]
            else:
                next_state_key = list(next_mapping.values())[0] # Fallback route
        except Exception as e:
            # Fallback for errors to ensure flow continues
            next_state_key = list(next_mapping.values())[0]
            
    if next_state_key == "end":
        end_text = "Thank you! We have collected all needed information. Analyzing your profile..."
        
        # Fire off to the RAG system
        from scripts.rag import rag
        rag_query_str = json.dumps(request.answers)
        try:
            rag_output = rag(rag_query_str, request.language)
            rag_json_str = rag_output.get("response", "{}")
        except Exception as e:
            print("RAG query failed:", e)
            rag_json_str = "{}"
            
        if request.language.lower() != "english":
            try:
                prompt = f"Translate the following completion text to {request.language}:\n\n{end_text}"
                response = llm_call(prompt)
                end_text = response.strip()
            except Exception:
                pass
                
        return {
            "next_state": "end", 
            "question": end_text,
            "answers": request.answers,
            "rag_response": rag_json_str
        }
        
    # Dynamic QA state hooks
    if request.current_state == "scheme_selection":
        # The user's answer is the scheme name they want to learn about
        request.answers["selected_scheme"] = request.user_answer
        from scripts.rag import rag_specific_qa
        try:
            summary = rag_specific_qa(request.user_answer, "Provide a 2 sentence high level summary of this scheme.", request.language)
            summary_text = summary.get("response", "")
        except Exception as e:
            print("Scheme summary failed:", e)
            summary_text = ""
            
        next_state_data = flow["questions"]["followup_qa"]
        question_text = f"{summary_text}\n\n{next_state_data['text']}"
        
        # We manually translate below if necessary, but RAG should handle it
        if request.language.lower() != "english":
            try:
                prompt = f"Translate the following question to {request.language}:\n\n{next_state_data['text']}"
                response = llm_call(prompt)
                question_text = f"{summary_text}\n\n{response.strip()}"
            except Exception:
                pass
                
        return {
            "next_state": "followup_qa",
            "question": question_text,
            "answers": request.answers
        }

    if request.current_state == "followup_qa":
        scheme_name = request.answers.get("selected_scheme", "the farming scheme")
        from scripts.rag import rag_specific_qa
        try:
            qa_reply = rag_specific_qa(scheme_name, request.user_answer, request.language)
            qa_text = qa_reply.get("response", "")
        except Exception as e:
            print("Followup QA failed:", e)
            qa_text = ""
            
        next_state_data = flow["questions"]["followup_qa"]
        question_text = f"{qa_text}\n\n{next_state_data['text']}"
        
        if request.language.lower() != "english":
            try:
                prompt = f"Translate the following question to {request.language}:\n\n{next_state_data['text']}"
                response = llm_call(prompt)
                question_text = f"{qa_text}\n\n{response.strip()}"
            except Exception:
                pass
        
        # Infinite loop hook
        return {
            "next_state": "followup_qa",
            "question": question_text,
            "answers": request.answers
        }
        
    next_state_data = flow["questions"].get(next_state_key)
    if not next_state_data:
        return {"error": f"State '{next_state_key}' not found in flow.json"}
        
    question_text = next_state_data["text"]
    
    # Final step: translate next question using the LLM
    if request.language.lower() != "english":
        try:
            prompt = f"Translate the following question to {request.language}:\n\n{question_text}"
            response = llm_call(prompt)
            question_text = response.strip()
        except Exception:
            pass
            
    return {
        "next_state": next_state_key,
        "question": question_text,
        "answers": request.answers
    }