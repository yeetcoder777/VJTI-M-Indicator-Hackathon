import json
from data_input import llm_call

title = "Regional Onion Relief Fund 2024"
description = "financial assistance of ₹25,000 for onion farmers located in Maharashtra who own less than 5 acres of land"
profile_json_str = '{"state": "Maharastra", "owns_land": "yes", "land_size": "2 acres", "farming_type": "onions", "irrigation": "rainwater", "income": "4 lakhs", "category": "none"}'
language = "english"

evaluation_prompt = f"""
You are a strict Agricultural Scheme Evaluator.

NEW SCHEME ANNOUNCED:
Title: {title}
Criteria: {description}

FARMER PROFILE (From VectorDB):
{profile_json_str}

TASK:
Based strictly on the Farmer Profile, are they eligible for this new scheme?
If NO, return exactly: FALSE - [REASON WHY THEY WERE REJECTED]
If YES, generate a short 2-sentence proactive outreach message in {language} offering them to apply.

Only return "FALSE - [Reason]" or the message string. NO generic conversational filler.
"""

try:
    eval_result = llm_call(evaluation_prompt).strip()
    print(f"RAW OUTPUT: {eval_result}")
    print(f"UPPER: {eval_result.upper()}")
    if eval_result.upper() != "FALSE":
        print("MATCH!")
    else:
        print("NO MATCH (FALSE)")
except Exception as e:
    print(f"ERROR: {e}")
