import chromadb
from fastapi import APIRouter
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from data_input import llm_call
import os

load_dotenv()

router = APIRouter()

current_dir = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_PATH = os.path.join(current_dir, "chroma_db")
COLLECTION_NAME = "farmer_schemes"

# Initialize Chroma client and collection
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

# Initialize embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

@router.post("/rag")
def rag(query: str, language: str = "english"):
  query_embedding = embedding_model.encode(query).tolist()
  result_chunks = collection.query(
      query_embeddings=query_embedding,
      n_results=12
  )

  response = llm_call(f"""
SYSTEM ROLE:
You are an eligibility advisor for Indian government farmer schemes.

INPUTS:
1) Farmer profile (JSON):
{query}

2) Retrieved document chunks (may include forms, annexures, or guidelines):
{result_chunks}

YOUR TASK:
- Decide which schemes the farmer is likely ELIGIBLE for.
- Decide which schemes the farmer is NOT ELIGIBLE for.
- Use the farmer profile as the PRIMARY source for eligibility.
- Use the retrieved chunks ONLY to support or explain (not to block eligibility).

IMPORTANT PERMISSIONS (explicitly allowed):
- You MAY infer eligibility using well-known scheme rules
  (e.g., land ownership, crop type, livestock activity).
- You MAY include a scheme even if eligibility text is not explicitly present
  in the chunks, as long as the farmer profile clearly matches the scheme.
- You MAY describe scheme features in HIGH-LEVEL terms (no numbers).

STRICT LIMITS (do not violate):
- Do NOT invent schemes outside the allowed list.
- Do NOT quote numbers, percentages, limits, or monetary values.
- Do NOT invent documents (PAN, GST, income proof).
- Do NOT invent state-specific schemes.
- Do NOT invent implementation details.

UNCERTAINTY RULE:
- If eligibility depends on information NOT present in the farmer profile,
  include the scheme under "uncertain_schemes".

OUTPUT REQUIREMENTS:
- Output VALID JSON only.
- You MUST respond ENTIRELY in this language: {language.upper()}.
- Be concise and factual.

OUTPUT FORMAT:
{{
  "eligible_schemes": [
    {{
      "scheme": "<scheme name>",
      "reason": "<factual reason (answer in first person, like you're directly advising the farmer)>",
      "key_features": "<key features of the scheme in brief (use general knowledge if knowledge in context is limited)>",
      "documents": "<documents required for the scheme (use general knowledge if knowledge in context is limited)>"
    }}
  ]
}}
"""
)
  return {"response": response}