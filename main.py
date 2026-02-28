import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from data_input import router as data_input_router
from scripts.rag import router as rag_router
from whatsapp_webhook import router as whatsapp_router
from ivr import router as ivr_router
from stt import router as stt_router

app = FastAPI()

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_input_router)
app.include_router(rag_router)
app.include_router(whatsapp_router)
app.include_router(ivr_router)
app.include_router(stt_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the M-Indicator Hackathon API"}